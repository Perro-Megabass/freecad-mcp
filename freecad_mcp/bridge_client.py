# -*- coding: utf-8 -*-
# FreeCAD MCP — bridge_client.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""Thread-safe TCP JSONL client for the FreeCAD MCP bridge."""

import json
import os
import socket
import threading
import uuid

HOST = os.environ.get("FREECAD_HOST", "127.0.0.1")
PORT = int(os.environ.get("FREECAD_PORT", "9877"))
TIMEOUT = float(os.environ.get("FREECAD_TIMEOUT_SEC", "60"))


class BridgeClientError(Exception):
    """Typed bridge error with stable code/message for MCP callers."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class BridgeClient:
    def __init__(self):
        self._sock = None
        self._file = None
        self._lock = threading.Lock()

    def _connect(self):
        try:
            self._sock = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
            self._file = self._sock.makefile("rw", encoding="utf-8", newline="\n")
        except ConnectionRefusedError:
            self._close()
            raise BridgeClientError(
                "ADDON_NOT_CONNECTED",
                f"Cannot connect to FreeCAD bridge at {HOST}:{PORT}. "
                "Start FreeCAD and click Connect in FreeCADMCP workbench.",
            )
        except socket.timeout:
            self._close()
            raise BridgeClientError(
                "CONNECTION_TIMEOUT",
                f"Timed out connecting to FreeCAD bridge at {HOST}:{PORT}.",
            )
        except OSError as e:
            self._close()
            raise BridgeClientError(
                "BRIDGE_CONNECT_FAILED",
                f"Bridge connection failed at {HOST}:{PORT}: {e}",
            )

    def _close(self):
        try:
            if self._file:
                self._file.close()
        except Exception:
            pass
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        self._file = None
        self._sock = None

    def call(self, action, params=None):
        with self._lock:
            fresh = self._sock is None
            if fresh:
                self._connect()
            req = {"id": str(uuid.uuid4()), "action": action, "params": params or {}}
            # Write phase. A stale connection (server restarted) typically
            # fails here; retrying is safe because the request was not
            # processed. Only retry when the connection was being reused.
            try:
                self._file.write(json.dumps(req) + "\n")
                self._file.flush()
            except (socket.timeout, OSError):
                self._close()
                if fresh:
                    raise BridgeClientError(
                        "BRIDGE_IO_TIMEOUT",
                        "IO error while sending request to FreeCAD bridge. "
                        "Verify FreeCAD is responsive and retry.",
                    )
                self._connect()
                req["id"] = str(uuid.uuid4())  # distinguish attempts in logs
                try:
                    self._file.write(json.dumps(req) + "\n")
                    self._file.flush()
                except (socket.timeout, OSError):
                    self._close()
                    raise BridgeClientError(
                        "BRIDGE_IO_TIMEOUT",
                        "IO error while sending request to FreeCAD bridge. "
                        "Verify FreeCAD is responsive and retry.",
                    )
            # Read phase. NEVER retry here: the request may already be
            # executing in FreeCAD, and resending it would run the action
            # twice (duplicate objects, double cuts, etc.).
            try:
                line = self._file.readline()
            except (socket.timeout, OSError):
                self._close()
                raise BridgeClientError(
                    "BRIDGE_IO_TIMEOUT",
                    "Timeout waiting for FreeCAD's response. The action may "
                    "still complete inside FreeCAD — inspect the scene "
                    "(freecad_get_scene_info) before retrying to avoid "
                    "duplicate operations.",
                )
            if not line:
                self._close()
                raise BridgeClientError(
                    "EMPTY_RESPONSE",
                    "Empty response from FreeCAD bridge. "
                    "The addon may be disconnected or another service is using this port.",
                )
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                self._close()
                raise BridgeClientError(
                    "INVALID_BRIDGE_RESPONSE",
                    f"Invalid JSON response from {HOST}:{PORT}. "
                    "This port may be occupied by a non-FreeCAD service.",
                )


CLIENT = BridgeClient()
