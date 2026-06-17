import json
import logging
from typing import Dict, List, Optional, Tuple

import redis

from app.database import SessionLocal
from app.models import Feedback

logger = logging.getLogger(__name__)

REDIS_URL = "redis://localhost:6379/0"
CACHE_KEY_PREFIX = "feedback_count:topic:"
CACHE_KEY_UNGROUPED = "feedback_count:ungrouped"
CACHE_KEY_HOT_TOPICS = "feedback_count:hot_topics"
CACHE_TTL_SECONDS = 300
HOT_TOPIC_LIMIT = 100

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


def _collect_topic_counts(limit: int = 5000) -> List[Tuple[int, int]]:
    db = SessionLocal()
    try:
        from app.models import Topic
        from sqlalchemy import func

        rows = (
            db.query(Feedback.topic_id, func.count(Feedback.id))
            .filter(Feedback.topic_id.isnot(None))
            .group_by(Feedback.topic_id)
            .order_by(func.count(Feedback.id).desc())
            .limit(limit)
            .all()
        )
        return [(tid if tid is not None else 0, cnt) for tid, cnt in rows]
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
        r.delete(CACHE_KEY_HOT_TOPICS)
    except (redis.RedisError, Exception):
        logger.warning("Redis invalidate all failed")


def refresh_hot_topic_counts_async(top_n: int = HOT_TOPIC_LIMIT):
    import threading

    def _refresh():
        db = SessionLocal()
        r = get_redis()
        try:
            from app.models import Topic
            from sqlalchemy import func

            hot_rows = (
                db.query(Feedback.topic_id, func.count(Feedback.id).label("cnt"))
                .filter(Feedback.topic_id.isnot(None))
                .group_by(Feedback.topic_id)
                .order_by(func.count(Feedback.id).desc())
                .limit(top_n)
                .all()
            )
            hot_ids = [int(tid) for tid, _ in hot_rows if tid is not None]
            pipe = r.pipeline()

            if hot_ids:
                hot_topics_data = [
                    {"topic_id": tid, "count": cnt}
                    for tid, cnt in hot_rows
                    if tid is not None
                ]
                pipe.setex(CACHE_KEY_HOT_TOPICS, CACHE_TTL_SECONDS, json.dumps(hot_topics_data))

                all_topics = {t.id: t.id for t in db.query(Topic.id).all()}
                for tid, cnt in hot_rows:
                    if tid is not None:
                        pipe.setex(f"{CACHE_KEY_PREFIX}{tid}", CACHE_TTL_SECONDS, str(cnt))
                        all_topics.pop(int(tid), None)
                remaining_ids = list(all_topics.keys())
                if remaining_ids:
                    from sqlalchemy import case
                    counts_stmt = (
                        db.query(Feedback.topic_id, func.count(Feedback.id))
                        .filter(Feedback.topic_id.in_(remaining_ids))
                        .group_by(Feedback.topic_id)
                    )
                    counts_map = {tid: cnt for tid, cnt in counts_stmt.all() if tid is not None}
                    for rid in remaining_ids:
                        cnt = counts_map.get(rid, 0)
                        pipe.setex(f"{CACHE_KEY_PREFIX}{rid}", CACHE_TTL_SECONDS, str(cnt))
            else:
                topics = db.query(Topic).all()
                for topic in topics:
                    cnt = db.query(Feedback).filter(Feedback.topic_id == topic.id).count()
                    pipe.setex(f"{CACHE_KEY_PREFIX}{topic.id}", CACHE_TTL_SECONDS, str(cnt))

            ungrouped = db.query(Feedback).filter(Feedback.topic_id.is_(None)).count()
            pipe.setex(CACHE_KEY_UNGROUPED, CACHE_TTL_SECONDS, str(ungrouped))
            pipe.execute()
            logger.info("Hot-topic warm-up completed, top-%d topics cached", len(hot_ids) if hot_ids else 0)
        except Exception:
            logger.exception("Hot-topic async warm-up failed")
        finally:
            db.close()

    thread = threading.Thread(target=_refresh, daemon=True)
    thread.start()


def refresh_topic_counts_async():
    refresh_hot_topic_counts_async(HOT_TOPIC_LIMIT)
