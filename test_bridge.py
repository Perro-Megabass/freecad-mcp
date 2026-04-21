# -*- coding: utf-8 -*-
# FreeCAD MCP — test_bridge.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""
Cliente de prueba para freecad_bridge.
Requiere: FreeCAD abierto + macro freecad_bridge.FCMacro ejecutada.
Uso: python test_bridge.py
"""

import json
import socket
import uuid

HOST = "127.0.0.1"
PORT = 9877
TIMEOUT = 10.0


def call(sock_file, action, params=None):
    req = {"id": str(uuid.uuid4()), "action": action, "params": params or {}}
    sock_file.write(json.dumps(req) + "\n")
    sock_file.flush()
    line = sock_file.readline()
    if not line:
        raise RuntimeError("Empty response")
    return json.loads(line)


def main():
    s = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
    f = s.makefile("rw", encoding="utf-8", newline="\n")
    try:
        tests = [
            ("ping", None),
            ("list_documents", None),
            ("new_document", {"name": "TestDoc"}),
            ("list_documents", None),
            ("list_objects", {"document": "TestDoc"}),
            ("bogus_action", None),
        ]
        for action, params in tests:
            resp = call(f, action, params)
            status = "OK" if resp.get("ok") else "FAIL"
            print(f"[{status}] {action}: {json.dumps(resp, ensure_ascii=False)}")
    finally:
        f.close()
        s.close()


if __name__ == "__main__":
    main()
