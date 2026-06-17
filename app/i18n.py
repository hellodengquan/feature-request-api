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
    "jwt_rotated": {
        "zh": "JWT Token 已因密钥轮换失效，请重新获取",
        "en": "JWT token invalidated by key rotation, please re-authenticate",
        "ja": "JWT トークンは鍵ローテーションにより無効化されました。再認証してください",
        "ko": "JWT 토큰이 키 로테이션으로 무효화되었습니다. 다시 인증해 주세요",
        "ru": "JWT-токен недействителен из-за ротации ключей, пожалуйста, переавторизуйтесь",
    },
    "jwt_revoked": {
        "zh": "JWT Token 已被吊销",
        "en": "JWT token has been revoked",
        "ja": "JWT トークンは取り消されました",
        "ko": "JWT 토큰이 취소되었습니다",
        "ru": "JWT-токен был отозван",
    },
    "account_revoked": {
        "zh": "该账号已被管理员吊销，请联系管理员",
        "en": "This account has been revoked by admin, please contact administrator",
        "ja": "このアカウントは管理者により取り消されました。管理者にお問い合わせください",
        "ko": "이 계정은 관리자에 의해 취소되었습니다. 관리자에게 문의하세요",
        "ru": "Учётная запись отозвана администратором, пожалуйста, обратитесь к нему",
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
    "role_admin_denied": {
        "zh": "此操作需要管理员权限",
        "en": "Admin permission required for this operation",
        "ja": "この操作には管理者権限が必要です",
        "ko": "이 작업에는 관리자 권한이 필요합니다",
        "ru": "Для этой операции требуются права администратора",
    },
    "revoke_params_required": {
        "zh": "必须提供 jti 或 user_id 参数",
        "en": "Either jti or user_id parameter is required",
        "ja": "jti または user_id パラメータのいずれかが必要です",
        "ko": "jti 또는 user_id 매개변수 중 하나가 필요합니다",
        "ru": "Требуется параметр jti или user_id",
    },
    "rotate_version_invalid": {
        "zh": "新的 rotation 版本号必须大于当前版本",
        "en": "New rotation version must be greater than current version",
        "ja": "新しいローテーションバージョンは現在のバージョンより大きい必要があります",
        "ko": "새 로테이션 버전은 현재 버전보다 커야 합니다",
        "ru": "Новая версия ротации должна быть больше текущей",
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


LOCALE_CURRENCY_MAP = {
    "zh": "CNY",
    "en": "USD",
    "ja": "JPY",
    "ko": "KRW",
    "ru": "RUB",
}

CURRENCY_SYMBOLS = {
    "CNY": "¥",
    "USD": "$",
    "JPY": "¥",
    "KRW": "₩",
    "RUB": "₽",
}

CURRENCY_DECIMALS = {
    "CNY": 2,
    "USD": 2,
    "JPY": 0,
    "KRW": 0,
    "RUB": 2,
}

THOUSANDS_SEP_MAP = {
    "zh": ",",
    "en": ",",
    "ja": ",",
    "ko": ",",
    "ru": " ",
}

DECIMAL_SEP_MAP = {
    "zh": ".",
    "en": ".",
    "ja": ".",
    "ko": ".",
    "ru": ",",
}


def _resolve_locale(accept_language: Optional[str]) -> str:
    langs = _parse_accept_language(accept_language)
    return langs[0] if langs else "en"


def format_number(value, locale: str = "en") -> str:
    if isinstance(value, float):
        int_part = int(abs(value))
        dec_part = round(abs(value) - int_part, 10)
    elif isinstance(value, int):
        int_part = abs(value)
        dec_part = 0
    else:
        return str(value)

    thousands_sep = THOUSANDS_SEP_MAP.get(locale, ",")
    int_str = str(int_part)
    groups = []
    while int_str:
        groups.append(int_str[-3:])
        int_str = int_str[:-3]
    formatted_int = thousands_sep.join(reversed(groups))

    sign = "-" if (isinstance(value, (int, float)) and value < 0) else ""

    decimal_sep = DECIMAL_SEP_MAP.get(locale, ".")
    if isinstance(value, float) and dec_part > 0:
        dec_str = f"{dec_part:.10f}".lstrip("0.")[:10].rstrip("0")
        return f"{sign}{formatted_int}{decimal_sep}{dec_str}"

    return f"{sign}{formatted_int}"


def format_currency(value, locale: str = "en") -> str:
    currency = LOCALE_CURRENCY_MAP.get(locale, "USD")
    symbol = CURRENCY_SYMBOLS.get(currency, "$")
    decimals = CURRENCY_DECIMALS.get(currency, 2)
    thousands_sep = THOUSANDS_SEP_MAP.get(locale, ",")
    decimal_sep = DECIMAL_SEP_MAP.get(locale, ".")

    if isinstance(value, (int, float)):
        abs_val = abs(value)
    else:
        return f"{symbol}{value}"

    formatted = f"{abs_val:,.{decimals}f}"
    if thousands_sep != ",":
        formatted = formatted.replace(",", "\x00")
    formatted = formatted.replace(",", thousands_sep)
    if thousands_sep != ",":
        formatted = formatted.replace("\x00", thousands_sep)
    formatted = formatted.replace(".", decimal_sep)

    sign = "-" if (isinstance(value, (int, float)) and value < 0) else ""
    return f"{sign}{symbol}{formatted}"


def format_number_locale(value, accept_language: Optional[str] = None) -> str:
    locale = _resolve_locale(accept_language)
    return format_number(value, locale)


def format_currency_locale(value, accept_language: Optional[str] = None) -> str:
    locale = _resolve_locale(accept_language)
    return format_currency(value, locale)
