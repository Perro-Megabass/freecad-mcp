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
            if self._sock is None:
                self._connect()
            req = {"id": str(uuid.uuid4()), "action": action, "params": params or {}}
            try:
                self._file.write(json.dumps(req) + "\n")
                self._file.flush()
                line = self._file.readline()
            except (socket.timeout, OSError):
                self._close()
                # One retry after reconnect — regenerate id so logs distinguish attempts
                self._connect()
                req["id"] = str(uuid.uuid4())
                try:
                    self._file.write(json.dumps(req) + "\n")
                    self._file.flush()
                    line = self._file.readline()
                except (socket.timeout, OSError):
                    self._close()
                    raise BridgeClientError(
                        "BRIDGE_IO_TIMEOUT",
                        "Timeout/IO error while talking to FreeCAD bridge. "
                        "Verify FreeCAD is responsive and retry.",
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
