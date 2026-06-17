import json
import logging
from typing import Optional

import redis

from app.database import SessionLocal
from app.models import Feedback

logger = logging.getLogger(__name__)

REDIS_URL = "redis://localhost:6379/0"
CACHE_KEY_PREFIX = "feedback_count:topic:"
CACHE_KEY_UNGROUPED = "feedback_count:ungrouped"
CACHE_TTL_SECONDS = 300

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def close_redis():
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None


def _compute_topic_count(topic_id: int) -> int:
    db = SessionLocal()
    try:
        return db.query(Feedback).filter(Feedback.topic_id == topic_id).count()
    finally:
        db.close()


def _compute_ungrouped_count() -> int:
    db = SessionLocal()
    try:
        return db.query(Feedback).filter(Feedback.topic_id.is_(None)).count()
    finally:
        db.close()


def get_cached_topic_count(topic_id: Optional[int]) -> int:
    r = get_redis()
    cache_key = f"{CACHE_KEY_PREFIX}{topic_id}" if topic_id is not None else CACHE_KEY_UNGROUPED
    try:
        cached = r.get(cache_key)
        if cached is not None:
            return int(cached)
    except (redis.RedisError, Exception):
        logger.warning("Redis read failed for key %s, falling back to DB", cache_key)

    if topic_id is not None:
        count = _compute_topic_count(topic_id)
    else:
        count = _compute_ungrouped_count()

    try:
        r.setex(cache_key, CACHE_TTL_SECONDS, str(count))
    except (redis.RedisError, Exception):
        logger.warning("Redis write failed for key %s", cache_key)

    return count


def invalidate_topic_count(topic_id: Optional[int]):
    r = get_redis()
    cache_key = f"{CACHE_KEY_PREFIX}{topic_id}" if topic_id is not None else CACHE_KEY_UNGROUPED
    try:
        r.delete(cache_key)
    except (redis.RedisError, Exception):
        logger.warning("Redis delete failed for key %s", cache_key)


def invalidate_all_topic_counts():
    r = get_redis()
    try:
        keys = r.keys(f"{CACHE_KEY_PREFIX}*")
        if keys:
            r.delete(*keys)
        r.delete(CACHE_KEY_UNGROUPED)
    except (redis.RedisError, Exception):
        logger.warning("Redis invalidate all failed")


def refresh_topic_counts_async():
    import threading

    def _refresh():
        db = SessionLocal()
        r = get_redis()
        try:
            from app.models import Topic
            topics = db.query(Topic).all()
            pipe = r.pipeline()
            for topic in topics:
                count = db.query(Feedback).filter(Feedback.topic_id == topic.id).count()
                pipe.setex(f"{CACHE_KEY_PREFIX}{topic.id}", CACHE_TTL_SECONDS, str(count))
            ungrouped = db.query(Feedback).filter(Feedback.topic_id.is_(None)).count()
            pipe.setex(CACHE_KEY_UNGROUPED, CACHE_TTL_SECONDS, str(ungrouped))
            pipe.execute()
        except Exception:
            logger.exception("Async topic count refresh failed")
        finally:
            db.close()

    thread = threading.Thread(target=_refresh, daemon=True)
    thread.start()
