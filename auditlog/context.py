import weakref
from contextvars import ContextVar, Token
from typing import Any

from sqlalchemy.orm import Session

REMOTE_ADDR_CTX_KEY = "remote_addr"
_remote_addr_ctx_var: ContextVar[str] = ContextVar(REMOTE_ADDR_CTX_KEY, default=None)


def get_user(session: Session) -> weakref.ref:
    return session.info.get('user')


def set_user(session: Session, user: Any) -> None:
    session.info.setdefault('user', weakref.ref(user))


def get_remote_addr() -> str:
    return _remote_addr_ctx_var.get()


def set_remote_addr(remote_addr: str) -> Token:
    return _remote_addr_ctx_var.set(remote_addr)


def remove_remote_addr(token: Token) -> None:
    _remote_addr_ctx_var.reset(token)
