import socket
from contextlib import AbstractContextManager


class DobotDashboardClient(AbstractContextManager):
    """Small line-oriented TCP client for DOBOT dashboard/motion command tests."""

    def __init__(self, host: str, port: int, timeout: float = 2.0, dry_run: bool = True):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.dry_run = dry_run
        self._socket = None

    def connect(self):
        if self.dry_run:
            return self
        self._socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self._socket.settimeout(self.timeout)
        return self

    def close(self):
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def send(self, command: str) -> str:
        line = command.strip()
        if self.dry_run:
            return f"DRY_RUN: {line}"
        if self._socket is None:
            self.connect()
        self._socket.sendall((line + "\n").encode("utf-8"))
        try:
            return self._socket.recv(4096).decode("utf-8", errors="replace").strip()
        except socket.timeout:
            return ""
