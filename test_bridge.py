# -*- coding: utf-8 -*-
# FreeCAD MCP — test_bridge.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""
Standalone test client for the FreeCAD MCP bridge.
Requires: FreeCAD running with the MCP Bridge workbench connected.
Usage: python test_bridge.py
"""

import argparse
import json
import socket
import sys
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


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


def _assert_envelope(resp):
    _assert(isinstance(resp, dict), "response is not a JSON object")
    _assert("ok" in resp, "missing top-level 'ok'")
    if resp.get("ok"):
        _assert("result" in resp, "ok response missing 'result'")
    else:
        err = resp.get("error")
        _assert(isinstance(err, dict), "error response missing error object")
        _assert("code" in err and "message" in err, "error response missing code/message")


def main():
    parser = argparse.ArgumentParser(description="Smoke tests for FreeCAD MCP bridge")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--timeout", type=float, default=TIMEOUT)
    args = parser.parse_args()

    try:
        s = socket.create_connection((args.host, args.port), timeout=args.timeout)
    except Exception as e:
        print(
            f"[FAIL] connect: Cannot connect to bridge at {args.host}:{args.port}. "
            f"Ensure FreeCAD MCP workbench is connected. ({e})"
        )
        return 2

    f = s.makefile("rw", encoding="utf-8", newline="\n")
    doc_name = f"Smoke_{uuid.uuid4().hex[:8]}"
    checks = 0
    failures = 0

    def run_check(name, fn):
        nonlocal checks, failures
        checks += 1
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as e:
            failures += 1
            print(f"[FAIL] {name}: {e}")

    try:
        def t_ping():
            resp = call(f, "ping")
            _assert_envelope(resp)
            _assert(resp["ok"], "ping should succeed")
            freecad = resp["result"].get("freecad", {})
            _assert(bool(freecad.get("version")), "ping missing freecad.version")

        def t_capabilities():
            resp = call(f, "get_capabilities")
            _assert_envelope(resp)
            _assert(resp["ok"], "get_capabilities should succeed")
            caps = resp["result"].get("capabilities", {})
            _assert(isinstance(caps.get("features"), dict), "missing capabilities.features")
            _assert(isinstance(caps.get("domains"), dict), "missing capabilities.domains")

        def t_new_document():
            resp = call(f, "new_document", {"name": doc_name})
            _assert_envelope(resp)
            _assert(resp["ok"], "new_document should succeed")
            got = ((resp["result"] or {}).get("document") or {}).get("name")
            _assert(got == doc_name, f"new_document returned unexpected name: {got}")

        def t_list_objects():
            resp = call(f, "list_objects", {"document": doc_name})
            _assert_envelope(resp)
            _assert(resp["ok"], "list_objects should succeed")
            _assert("objects" in (resp["result"] or {}), "list_objects missing objects")

        def t_recompute():
            resp = call(f, "recompute", {"document": doc_name})
            _assert_envelope(resp)
            _assert(resp["ok"], "recompute should succeed")
            _assert((resp["result"] or {}).get("recomputed") is True, "recompute missing recomputed=true")

        def t_scene_info():
            resp = call(f, "get_scene_info", {"document": doc_name})
            _assert_envelope(resp)
            _assert(resp["ok"], "get_scene_info should succeed")
            result = resp["result"] or {}
            _assert("document" in result, "scene_info missing document")
            _assert("objects" in result, "scene_info missing objects")

        def t_unknown_action_error():
            resp = call(f, "bogus_action")
            _assert_envelope(resp)
            _assert(not resp["ok"], "bogus_action should fail")
            _assert((resp["error"] or {}).get("code") == "INVALID_PARAMS", "unexpected error code")

        def t_invalid_params_error():
            # set_active_document without 'name' should map to INVALID_PARAMS, not FREECAD_ERROR
            resp = call(f, "set_active_document", {})
            _assert_envelope(resp)
            _assert(not resp["ok"], "set_active_document without name should fail")
            code = (resp["error"] or {}).get("code")
            _assert(code == "INVALID_PARAMS",
                    f"expected INVALID_PARAMS, got {code}")

        run_check("ping", t_ping)
        run_check("get_capabilities", t_capabilities)
        run_check("new_document", t_new_document)
        run_check("list_objects", t_list_objects)
        run_check("recompute", t_recompute)
        run_check("get_scene_info", t_scene_info)
        run_check("bogus_action_error", t_unknown_action_error)
        run_check("invalid_params_error", t_invalid_params_error)
    finally:
        f.close()
        s.close()

    passed = checks - failures
    print(f"\nSummary: {passed}/{checks} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
