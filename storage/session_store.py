"""
用户 / 会话 / 消息 持久化（SQLite）。

表结构:
  users    — user_name（主键）、uid（内部整数ID）、password_hash、lang、created_at
  sessions — session_id、user_name、name、thread_id、created_at
  messages — id、session_id、role、content、thinking、created_at

说明：
- user_name：用户登录时输入的名称（可读）
- uid：内部固定自增整数ID，用于文件系统目录命名等（推荐使用这个）
- thread_id 规则: "{user_name}::{session_id}"
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional


# ── 密码哈希工具（pbkdf2，纯标准库）────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """返回 'salt_hex:key_hex' 格式的哈希字符串。"""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored: str) -> bool:
    """验证明文密码与存储哈希是否匹配（恒定时间比较，防时序攻击）。"""
    try:
        salt_hex, key_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


class SessionStore:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")  # 提升并发安全性
        self._init_tables()

    def _init_tables(self):
        """创建表 + 安全迁移 uid 列"""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_name     TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL DEFAULT '',
                lang          TEXT DEFAULT 'zh_CN',
                uid           INTEGER UNIQUE,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_name  TEXT NOT NULL,
                name       TEXT NOT NULL,
                thread_id  TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_name) REFERENCES users(user_name)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                thinking   TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );
        """)
        self._conn.commit()

        # === 安全迁移 uid 列（避免列不存在的错误）===
        try:
            self._conn.execute("SELECT uid FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("[SessionStore] 添加 uid 列到 users 表...")
            self._conn.execute("ALTER TABLE users ADD COLUMN uid INTEGER UNIQUE")
            self._conn.commit()

        # 回填 uid（使用 rowid）
        print("[SessionStore] 正在回填 uid...")
        self._conn.execute("UPDATE users SET uid = rowid WHERE uid IS NULL")
        self._conn.commit()

        # 保险起见：再次确保所有用户都有 uid
        self._conn.execute("""
            UPDATE users 
            SET uid = rowid 
            WHERE uid IS NULL OR uid = 0
        """)
        self._conn.commit()

    # ── User ──────────────────────────────────────────────────────────────────

    def get_or_create_user(self, user_name: str) -> str:
        """确保用户存在，返回 user_name。"""
        self._conn.execute(
            "INSERT OR IGNORE INTO users (user_name) VALUES (?)", (user_name,)
        )
        self._conn.commit()
        return user_name

    def get_user_uid(self, user_name: str) -> Optional[int]:
        """返回用户的内部整数 uid（强烈推荐用于文件系统路径）"""
        row = self._conn.execute(
            "SELECT uid FROM users WHERE user_name=?", (user_name,)
        ).fetchone()
        return row["uid"] if row else None

    def verify_login(self, user_name: str, password: str) -> bool:
        """验证用户名 + 密码"""
        row = self._conn.execute(
            "SELECT password_hash FROM users WHERE user_name=?", (user_name,)
        ).fetchone()
        if not row:
            return False
        return _verify_password(password, row["password_hash"])

    def set_user_password(self, user_name: str, password: str):
        """更新用户密码"""
        self._conn.execute(
            "UPDATE users SET password_hash=? WHERE user_name=?",
            (_hash_password(password), user_name),
        )
        self._conn.commit()

    def seed_default_users(self, defaults: dict[str, str]):
        """
        写入默认用户（admin, alice, bob 等）
        - 新用户 → 插入并自动生成 uid
        - 老用户无密码 → 补写密码
        - 已存在且有密码 → 跳过
        """
        for user_name, password in defaults.items():
            row = self._conn.execute(
                "SELECT user_name, password_hash, uid FROM users WHERE user_name=?",
                (user_name,)
            ).fetchone()

            if not row:
                # 新用户
                print(f"[SessionStore] 创建默认用户: {user_name}")
                cursor = self._conn.execute(
                    "INSERT INTO users (user_name, password_hash) VALUES (?, ?)",
                    (user_name, _hash_password(password))
                )
                # 使用 SQLite 的 rowid 作为 uid
                self._conn.execute(
                    "UPDATE users SET uid = ? WHERE user_name = ?",
                    (cursor.lastrowid, user_name)
                )
            elif row["uid"] is None or row["uid"] == 0:
                # 补 uid
                self._conn.execute(
                    "UPDATE users SET uid = rowid WHERE user_name = ?",
                    (user_name,)
                )
            elif not row["password_hash"] or row["password_hash"] == '':
                # 补写密码
                print(f"[SessionStore] 为用户 {user_name} 补写密码")
                self._conn.execute(
                    "UPDATE users SET password_hash=? WHERE user_name=?",
                    (_hash_password(password), user_name)
                )
            else:
                print(f"[SessionStore] 用户 {user_name} 已存在且有密码，跳过")

        self._conn.commit()

    def get_user_lang(self, user_name: str) -> str:
        row = self._conn.execute(
            "SELECT lang FROM users WHERE user_name=?", (user_name,)
        ).fetchone()
        return row["lang"] if row and row["lang"] else "zh_CN"

    def set_user_lang(self, user_name: str, lang: str):
        self._conn.execute(
            "UPDATE users SET lang=? WHERE user_name=?", (lang, user_name)
        )
        self._conn.commit()

    def list_users(self) -> List[str]:
        rows = self._conn.execute(
            "SELECT user_name FROM users ORDER BY created_at"
        ).fetchall()
        return [r["user_name"] for r in rows]

    # ── Session ───────────────────────────────────────────────────────────────

    def create_session(self, user_name: str, name: str = "") -> Dict:
        """新建会话，返回 {session_id, name, thread_id}"""
        session_id = uuid.uuid4().hex[:10]
        thread_id = f"{user_name}::{session_id}"
        if not name:
            name = f"会话 {datetime.now().strftime('%m-%d %H:%M')}"
        self._conn.execute(
            "INSERT INTO sessions (session_id, user_name, name, thread_id) VALUES (?,?,?,?)",
            (session_id, user_name, name, thread_id),
        )
        self._conn.commit()
        return {"session_id": session_id, "name": name, "thread_id": thread_id}

    def get_user_sessions(self, user_name: str) -> List[Dict]:
        """返回用户的所有会话（倒序）"""
        rows = self._conn.execute(
            "SELECT session_id, name, thread_id, created_at "
            "FROM sessions WHERE user_name=? ORDER BY created_at DESC",
            (user_name,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: str) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT session_id, name, thread_id FROM sessions WHERE session_id=?",
            (session_id,)
        ).fetchone()
        return dict(row) if row else None

    def rename_session(self, session_id: str, name: str):
        self._conn.execute(
            "UPDATE sessions SET name=? WHERE session_id=?", (name, session_id)
        )
        self._conn.commit()

    def delete_session(self, session_id: str):
        self._conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
        self._conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        self._conn.commit()

    # ── Messages ──────────────────────────────────────────────────────────────

    def append_message(self, session_id: str, role: str, content: str, thinking: str = ""):
        self._conn.execute(
            "INSERT INTO messages (session_id, role, content, thinking) VALUES (?,?,?,?)",
            (session_id, role, content, thinking),
        )
        self._conn.commit()

    def get_messages(self, session_id: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT role, content, thinking FROM messages "
            "WHERE session_id=? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def message_count(self, session_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as n FROM messages WHERE session_id=?", (session_id,)
        ).fetchone()
        return row["n"]


# ── 模块级单例 ────────────────────────────────────────────────────────────────

_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        from configs.path_config import OTHER_PATH
        _store = SessionStore(OTHER_PATH["session_db"])
    return _store