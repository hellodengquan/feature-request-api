from typing import Dict, Optional

MESSAGES: Dict[str, Dict[str, str]] = {
    "changed_by_required": {
        "zh": "状态变更必须指定操作人 (changed_by)，不允许匿名操作",
        "en": "changed_by is required when changing status, anonymous operation is not allowed",
    },
    "feedback_not_found": {
        "zh": "反馈不存在",
        "en": "Feedback not found",
    },
    "topic_not_found": {
        "zh": "主题不存在",
        "en": "Topic not found",
    },
    "customer_not_found": {
        "zh": "一个或多个客户不存在",
        "en": "One or more customers not found",
    },
    "customer_not_found_single": {
        "zh": "客户不存在",
        "en": "Customer not found",
    },
    "enum_priority": {
        "zh": "priority 字段取值非法，允许值: low, medium, high, urgent",
        "en": "Invalid priority value, allowed: low, medium, high, urgent",
    },
    "enum_status": {
        "zh": "status 字段取值非法，允许值: pending, evaluated, scheduled, developing, completed, rejected",
        "en": "Invalid status value, allowed: pending, evaluated, scheduled, developing, completed, rejected",
    },
    "status_change_by_required": {
        "zh": "状态变更操作必须指定操作人 (changed_by)，不允许匿名操作",
        "en": "changed_by is required for status change, anonymous operation is not allowed",
    },
}


def _parse_accept_language(header_value: Optional[str]) -> str:
    if not header_value:
        return "zh"
    primary = header_value.split(",")[0].strip().lower()
    if primary.startswith("en"):
        return "en"
    return "zh"


def t(key: str, accept_language: Optional[str] = None) -> str:
    lang = _parse_accept_language(accept_language)
    entry = MESSAGES.get(key, {})
    return entry.get(lang, entry.get("zh", key))
