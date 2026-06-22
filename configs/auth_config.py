# 默认用户及初始密码（仅用于首次写入数据库，之后以数据库为准）
# 实际密码在 config.local.yaml 的 users 块中设置（已在 .gitignore 中）
# Set real passwords in config.local.yaml (gitignored), not here.
DEFAULT_USERS: dict[str, str] = {
    "admin": "CHANGE_ME",
}
