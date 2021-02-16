import threading

from auditlog.context import set_remote_addr, remove_remote_addr

try:
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError:
    pass


class FastAPIAuditlogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        remote_addr = request.client.host
        token = set_remote_addr(remote_addr)
        response = await call_next(request)
        remove_remote_addr(token)

        return response
