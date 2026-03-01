from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

from .const import (
    CR,
    MIN_SEND_INTERVAL_MS,
    SOCKET_TIMEOUT,
    CONNECT_TIMEOUT,
    RECONNECT_BACKOFF_S,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class HegelState:
    power: Optional[bool] = None          # True = awake (ECO off), False = ECO/standby
    mute: Optional[bool] = None           # True/False
    volume: Optional[int] = None          # 0..100
    input_code: Optional[int] = None      # 1..N


class HegelTcpClient:
    """Safety-first TCP client: single connection, single send at a time (lock),
    rate-limited, with reconnect and timeouts.
    """

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

        self._lock = asyncio.Lock()
        self._last_send_ts = 0.0
        self._last_connect_fail_ts = 0.0

        self._closed = False
        self.last_tx: str | None = None
        self.last_set_tx: str | None = None

    async def async_close(self) -> None:
        self._closed = True
        await self._disconnect()

    async def _disconnect(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
        self._reader = None
        self._writer = None

    async def _ensure_connected(self) -> None:
        if self._closed:
            raise RuntimeError("Client is closed")

        if self._writer is not None and not self._writer.is_closing():
            return

        # backoff po błędzie connect (żeby nie młócić)
        now = time.monotonic()
        if self._last_connect_fail_ts and (now - self._last_connect_fail_ts) < RECONNECT_BACKOFF_S:
            raise ConnectionError("Reconnect backoff")

        try:
            _LOGGER.debug("Connecting to Hegel %s:%s", self._host, self._port)
            fut = asyncio.open_connection(self._host, self._port)
            self._reader, self._writer = await asyncio.wait_for(fut, timeout=CONNECT_TIMEOUT)
        except Exception as e:  # noqa: BLE001
            self._last_connect_fail_ts = time.monotonic()
            await self._disconnect()
            raise ConnectionError(str(e)) from e

    async def _rate_limit(self) -> None:
        # min przerwa pomiędzy komendami
        min_interval = MIN_SEND_INTERVAL_MS / 1000.0
        now = time.monotonic()
        delta = now - self._last_send_ts
        if delta < min_interval:
            await asyncio.sleep(min_interval - delta)

    async def async_send_only(self, cmd: str) -> None:
        """Wyślij komendę SET i NIE czekaj na odpowiedź (Hegel może nie odpowiadać)."""
        async with self._lock:
            await self._ensure_connected()
            await self._rate_limit()

            assert self._writer is not None
            payload = (cmd + CR).encode("ascii", errors="ignore")
            _LOGGER.debug("TX(no-reply): %s", cmd)

            try:
                self.last_tx = cmd
                self.last_set_tx = cmd
                self._writer.write(payload)
                await self._writer.drain()
                self._last_send_ts = time.monotonic()
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Socket error for %s: %s", cmd, e)
                await self._disconnect()
                raise

    async def async_send_and_readline(self, cmd: str) -> str:
        """Wyślij pojedynczą komendę i przeczytaj 1 linię odpowiedzi (do CR/LF).
        Komendy w protokole kończą się CR. Odpowiedzi u Ciebie mają format '-x.y'.
        """
        async with self._lock:
            await self._ensure_connected()
            await self._rate_limit()

            assert self._writer is not None
            assert self._reader is not None

            payload = (cmd + CR).encode("ascii", errors="ignore")
            _LOGGER.debug("TX: %s", cmd)

            try:
                self.last_tx = cmd
                self._writer.write(payload)
                await self._writer.drain()
                self._last_send_ts = time.monotonic()

                # czytamy do '\n' albo '\r' — StreamReader.readline() czyta do '\n',
                # ale wiele urządzeń wysyła '\r\n'. To nadal działa.
                raw = await asyncio.wait_for(self._reader.readuntil(b"\r"), timeout=SOCKET_TIMEOUT)
                line = raw.decode(errors="ignore").strip()
                _LOGGER.debug("RX: %s", line)
                return line
            except asyncio.TimeoutError as e:
                _LOGGER.warning("Timeout waiting response for %s", cmd)
                await self._disconnect()
                raise TimeoutError("No response") from e
            except Exception as e:  # noqa: BLE001
                _LOGGER.warning("Socket error for %s: %s", cmd, e)
                await self._disconnect()
                raise

