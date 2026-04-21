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


class BridgeClient:
    def __init__(self):
        self._sock = None
        self._file = None
        self._lock = threading.Lock()

    def _connect(self):
        self._sock = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
        self._file = self._sock.makefile("rw", encoding="utf-8", newline="\n")

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
            except Exception:
                self._close()
                # One retry after reconnect
                self._connect()
                self._file.write(json.dumps(req) + "\n")
                self._file.flush()
                line = self._file.readline()
            if not line:
                self._close()
                raise ConnectionError("Empty response from FreeCAD bridge")
            return json.loads(line)


CLIENT = BridgeClient()
