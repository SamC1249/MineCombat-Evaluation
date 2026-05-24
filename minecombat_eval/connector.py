"""TCP newline-delimited JSON client for MineCombat-Evaluation."""

from __future__ import annotations

import json
import socket
from typing import Any, Mapping

from .models import PROTOCOL_VERSION, Action


class EvaluationProtocolError(RuntimeError):
    """Server returned type \"error\" or unexpected payload."""

    def __init__(self, message: str, raw: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.raw = raw


class EvaluationConnector:
    """
    One connection; send one JSON object per line, read one response line per request.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        *,
        timeout: float = 130.0,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._reader: Any = None

    def connect(self) -> None:
        if self._sock is not None:
            return
        s = socket.create_connection((self.host, self.port), timeout=self.timeout)
        s.settimeout(self.timeout)
        self._sock = s
        self._reader = s.makefile("r", encoding="utf-8", newline="\n")

    def close(self) -> None:
        if self._reader is not None:
            try:
                self._reader.close()
            except OSError:
                pass
            self._reader = None
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def __enter__(self) -> EvaluationConnector:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._sock is None or self._reader is None:
            raise RuntimeError("not connected")
        line = json.dumps(payload, separators=(",", ":")) + "\n"
        self._sock.sendall(line.encode("utf-8"))
        resp_line = self._reader.readline()
        if not resp_line:
            raise ConnectionError("server closed connection (empty read)")
        try:
            out = json.loads(resp_line)
        except json.JSONDecodeError as e:
            raise EvaluationProtocolError(f"invalid json response: {e}") from e
        if not isinstance(out, dict):
            raise EvaluationProtocolError("response is not a JSON object")
        if out.get("type") == "error":
            raise EvaluationProtocolError(
                str(out.get("message", "error")),
                raw=out,
            )
        return out

    def reset(
        self,
        scenario_id: str,
        seed: int,
        *,
        task_spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "reset",
            "protocol": PROTOCOL_VERSION,
            "scenario_id": scenario_id,
            "seed": int(seed),
        }
        if task_spec is not None:
            payload["task_spec"] = task_spec
        return self._request(payload)

    def step(self, episode_id: str, action: Action) -> dict[str, Any]:
        return self._request(
            {
                "type": "step",
                "protocol": PROTOCOL_VERSION,
                "episode_id": episode_id,
                "action": action.to_wire(),
            }
        )
