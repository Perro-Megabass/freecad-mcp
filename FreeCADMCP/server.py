# -*- coding: utf-8 -*-
# FreeCAD MCP — server.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""TCP JSONL server singleton for the FreeCAD MCP Bridge."""

import json
import queue
import socket
import threading
import traceback

import FreeCAD as App

from handlers import HANDLERS

# Task queue for execution on FreeCAD's main (GUI) thread.
_main_queue = queue.Queue()


def _pump_main_queue():
    """Called by QTimer on the GUI thread. Drains pending tasks."""
    try:
        while True:
            fn, args, result_holder, event = _main_queue.get_nowait()
            try:
                result_holder["value"] = fn(*args)
            except Exception as e:
                result_holder["error"] = e
            finally:
                event.set()
    except queue.Empty:
        pass


def run_on_main(fn, *args, timeout=30.0):
    """Dispatch fn to the GUI thread and wait for the result."""
    result_holder = {}
    event = threading.Event()
    _main_queue.put((fn, args, result_holder, event))
    if not event.wait(timeout):
        raise TimeoutError("Main-thread dispatch timeout")
    if "error" in result_holder:
        raise result_holder["error"]
    return result_holder.get("value")

HOST = "127.0.0.1"
PORT = 9877
MAX_MSG_BYTES = 5 * 1024 * 1024


class BridgeServer:
    _instance = None

    def __init__(self):
        self._thread = None
        self._sock = None
        self._running = False
        self._clients = 0
        self._lock = threading.Lock()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = BridgeServer()
        return cls._instance

    # ---- state ----
    @property
    def running(self):
        return self._running

    def status(self):
        if not self._running:
            return "Disconnected"
        if self._clients > 0:
            return f"Client connected ({self._clients})"
        return f"Listening on {HOST}:{PORT}"

    # ---- dispatch ----
    def _dispatch(self, request):
        req_id = request.get("id")
        action = request.get("action")
        params = request.get("params") or {}
        handler = HANDLERS.get(action)
        if handler is None:
            return {"id": req_id, "ok": False,
                    "error": {"code": "INVALID_PARAMS", "message": f"Unknown action: {action}"}}
        try:
            return {"id": req_id, "ok": True, "result": run_on_main(handler, params)}
        except LookupError as e:
            return {"id": req_id, "ok": False,
                    "error": {"code": "NOT_FOUND", "message": str(e)}}
        except Exception as e:
            return {"id": req_id, "ok": False,
                    "error": {"code": "FREECAD_ERROR", "message": str(e),
                              "details": {"trace": traceback.format_exc()}}}

    # ---- client loop ----
    def _handle_client(self, conn, addr):
        with self._lock:
            self._clients += 1
        App.Console.PrintMessage(f"[MCP] Client connected {addr}\n")
        buffer = b""
        try:
            while self._running:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data
                if len(buffer) > MAX_MSG_BYTES:
                    err = {"id": None, "ok": False,
                           "error": {"code": "INVALID_PARAMS", "message": "Message too large"}}
                    conn.sendall(json.dumps(err).encode("utf-8") + b"\n")
                    break
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        req = json.loads(line.decode("utf-8"))
                        resp = self._dispatch(req)
                    except Exception as e:
                        resp = {"id": None, "ok": False,
                                "error": {"code": "INVALID_PARAMS", "message": f"Bad JSON: {e}"}}
                    conn.sendall(json.dumps(resp).encode("utf-8") + b"\n")
        except Exception as e:
            App.Console.PrintError(f"[MCP] Client error: {e}\n")
        finally:
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._clients -= 1
            App.Console.PrintMessage(f"[MCP] Client disconnected {addr}\n")

    # ---- server loop ----
    def _server_loop(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((HOST, PORT))
            self._sock.listen(1)
            self._sock.settimeout(1.0)
        except Exception as e:
            App.Console.PrintError(f"[MCP] Bind error: {e}\n")
            self._running = False
            return
        App.Console.PrintMessage(f"[MCP] Listening on {HOST}:{PORT}\n")
        while self._running:
            try:
                conn, addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
            t.start()
        try:
            self._sock.close()
        except Exception:
            pass
        self._sock = None
        App.Console.PrintMessage("[MCP] Server stopped\n")

    # ---- control ----
    def start(self):
        if self._running:
            return False
        self._running = True
        self._thread = threading.Thread(target=self._server_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if not self._running:
            return False
        self._running = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        return True
