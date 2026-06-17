from typing import Dict, List, Optional

SUPPORTED_LANGS = ["zh", "en", "ja", "ko", "ru"]
FALLBACK_CHAIN = ["zh", "en", "ja", "ko", "ru"]

MESSAGES: Dict[str, Dict[str, str]] = {
    "changed_by_required": {
        "zh": "状态变更必须指定操作人 (changed_by)，不允许匿名操作",
        "en": "changed_by is required when changing status, anonymous operation is not allowed",
        "ja": "ステータス変更には操作担当者(changed_by)の指定が必須です。匿名操作は許可されません",
        "ko": "상태 변경 시 담당자(changed_by)를 지정해야 합니다. 익명 작업은 허용되지 않습니다",
        "ru": "При изменении статуса необходимо указать исполнителя (changed_by). Анонимные операции не допускаются",
    },
    "feedback_not_found": {
        "zh": "反馈不存在",
        "en": "Feedback not found",
        "ja": "フィードバックが存在しません",
        "ko": "피드백을 찾을 수 없습니다",
        "ru": "Отзыв не найден",
    },
    "topic_not_found": {
        "zh": "主题不存在",
        "en": "Topic not found",
        "ja": "トピックが存在しません",
        "ko": "주제를 찾을 수 없습니다",
        "ru": "Тема не найдена",
    },
    "customer_not_found": {
        "zh": "一个或多个客户不存在",
        "en": "One or more customers not found",
        "ja": "一部の顧客が存在しません",
        "ko": "일부 고객을 찾을 수 없습니다",
        "ru": "Один или несколько клиентов не найдены",
    },
    "customer_not_found_single": {
        "zh": "客户不存在",
        "en": "Customer not found",
        "ja": "顧客が存在しません",
        "ko": "고객을 찾을 수 없습니다",
        "ru": "Клиент не найден",
    },
    "enum_priority": {
        "zh": "priority 字段取值非法，允许值: low, medium, high, urgent",
        "en": "Invalid priority value, allowed: low, medium, high, urgent",
        "ja": "priority の値が不正です。許可値: low, medium, high, urgent",
        "ko": "priority 값이 유효하지 않습니다. 허용값: low, medium, high, urgent",
        "ru": "Недопустимое значение priority, разрешены: low, medium, high, urgent",
    },
    "enum_status": {
        "zh": "status 字段取值非法，允许值: pending, evaluated, scheduled, developing, completed, rejected",
        "en": "Invalid status value, allowed: pending, evaluated, scheduled, developing, completed, rejected",
        "ja": "status の値が不正です。許可値: pending, evaluated, scheduled, developing, completed, rejected",
        "ko": "status 값이 유효하지 않습니다. 허용값: pending, evaluated, scheduled, developing, completed, rejected",
        "ru": "Недопустимое значение status, разрешены: pending, evaluated, scheduled, developing, completed, rejected",
    },
    "status_change_by_required": {
        "zh": "状态变更操作必须指定操作人 (changed_by)，不允许匿名操作",
        "en": "changed_by is required for status change, anonymous operation is not allowed",
        "ja": "ステータス変更には操作担当者(changed_by)の指定が必須です。匿名操作は許可されません",
        "ko": "상태 변경 시 담당자(changed_by)를 지정해야 합니다. 익명 작업은 허용되지 않습니다",
        "ru": "Для изменения статуса требуется указать исполнителя (changed_by). Анонимные операции не допускаются",
    },
    "jwt_missing": {
        "zh": "缺少 JWT Token 认证凭证",
        "en": "JWT Bearer token is missing",
        "ja": "JWT Bearer トークンがありません",
        "ko": "JWT Bearer 토큰이 없습니다",
        "ru": "JWT Bearer-токен отсутствует",
    },
    "jwt_invalid": {
        "zh": "JWT Token 无效或已过期",
        "en": "JWT token is invalid or expired",
        "ja": "JWT トークンが無効または期限切れです",
        "ko": "JWT 토큰이 유효하지 않거나 만료되었습니다",
        "ru": "JWT-токен недействителен или срок его действия истёк",
    },
    "role_write_denied": {
        "zh": "当前角色不具备写操作权限，请联系管理员授权",
        "en": "Your role has no write permission, please contact admin",
        "ja": "現在のロールには書き込み権限がありません。管理者にお問い合わせください",
        "ko": "현재 역할에는 쓰기 권한이 없습니다. 관리자에게 문의하세요",
        "ru": "У вашей роли нет прав на запись, пожалуйста, обратитесь к администратору",
    },
    "role_status_change_denied": {
        "zh": "只有 admin 或 pm 角色可以变更反馈状态",
        "en": "Only admin or pm can change feedback status",
        "ja": "ステータス変更は admin または pm ロールのみ可能です",
        "ko": "상태 변경은 admin 또는 pm 역할만 가능합니다",
        "ru": "Изменять статус отзыва могут только роли admin или pm",
    },
    "role_delete_denied": {
        "zh": "只有 admin 或 pm 角色可以删除反馈",
        "en": "Only admin or pm can delete feedback",
        "ja": "フィードバック削除は admin または pm ロールのみ可能です",
        "ko": "피드백 삭제는 admin 또는 pm 역할만 가능합니다",
        "ru": "Удалять отзыв могут только роли admin или pm",
    },
}


def _parse_accept_language(header_value: Optional[str]) -> List[str]:
    if not header_value:
        return list(FALLBACK_CHAIN)

    entries = header_value.split(",")
    parsed = []
    for entry in entries:
        entry = entry.strip().lower()
        lang = entry.split(";")[0]
        if lang.startswith("zh") or lang.startswith("cn"):
            parsed.append("zh")
        elif lang.startswith("en"):
            parsed.append("en")
        elif lang.startswith("ja") or lang.startswith("jp"):
            parsed.append("ja")
        elif lang.startswith("ko") or lang.startswith("kr"):
            parsed.append("ko")
        elif lang.startswith("ru"):
            parsed.append("ru")
    for fallback in FALLBACK_CHAIN:
        if fallback not in parsed:
            parsed.append(fallback)
    return parsed


def t(key: str, accept_language: Optional[str] = None) -> str:
    langs = _parse_accept_language(accept_language)
    entry = MESSAGES.get(key, {})
    for lang in langs:
        if lang in entry and entry[lang]:
            return entry[lang]
    return key
