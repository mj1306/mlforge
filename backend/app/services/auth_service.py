import hashlib
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.domain.schemas.auth import User

# scrypt cost parameters (stdlib hashlib.scrypt). n=2**14 keeps login under
# ~100ms on modest hardware while still being a memory-hard KDF -- fine for a
# local-first app; bump n before ever exposing this to the open internet.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash BLOB NOT NULL,
    salt BLOB NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
"""


class AuthError(Exception):
    pass


class UsernameTakenError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )


def _hash_token(token: str) -> str:
    # Only the SHA-256 of the session token is stored, so a leaked/backed-up
    # auth.db cannot be replayed as live sessions.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    """SQLite-backed users + sessions. A connection is opened per operation --
    trivial at this app's scale and sidesteps sqlite's cross-thread rules
    (requests are handled on FastAPI's threadpool, jobs on worker threads)."""

    def __init__(self, settings: Settings) -> None:
        self.db_path = settings.auth_db_path
        self.session_ttl = timedelta(days=settings.session_ttl_days)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # -- users ------------------------------------------------------------

    def register(self, username: str, password: str) -> User:
        user = User(id=uuid.uuid4().hex, username=username, created_at=_utcnow())
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO users (id, username, password_hash, salt, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (user.id, user.username, password_hash, salt, user.created_at.isoformat()),
                )
        except sqlite3.IntegrityError as exc:
            raise UsernameTakenError(f"Username '{username}' is already taken") from exc
        return user

    def authenticate(self, username: str, password: str) -> User:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
        if row is None:
            # Hash anyway so response timing doesn't reveal whether the
            # username exists.
            _hash_password(password, b"\x00" * 16)
            raise InvalidCredentialsError("Invalid username or password")
        expected = row["password_hash"]
        actual = _hash_password(password, row["salt"])
        if not secrets.compare_digest(expected, actual):
            raise InvalidCredentialsError("Invalid username or password")
        return _row_to_user(row)

    # -- sessions ---------------------------------------------------------

    def create_session(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (token_hash, user_id, created_at, expires_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    _hash_token(token),
                    user_id,
                    now.isoformat(),
                    (now + self.session_ttl).isoformat(),
                ),
            )
        return token

    def get_user_by_session(self, token: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT u.*, s.expires_at FROM sessions s"
                " JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?",
                (_hash_token(token),),
            ).fetchone()
            if row is None:
                return None
            if datetime.fromisoformat(row["expires_at"]) < _utcnow():
                conn.execute(
                    "DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),)
                )
                return None
        return _row_to_user(row)

    def delete_session(self, token: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
