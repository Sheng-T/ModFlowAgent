# 默认用户及初始密码（仅用于首次写入数据库，之后以数据库为准）
# 上线后建议通过 storage/session_store.py 的 set_user_password() 修改密码
DEFAULT_USERS: dict[str, str] = {
    "admin": "admin2026",
    "alice": "alice2026",
    "bob":   "bob2026",
}
