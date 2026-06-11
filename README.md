# FreeCAD MCP

Control FreeCAD from Claude Desktop using the Model Context Protocol (MCP).  
Inspired by [blender-mcp](https://github.com/ahujasid/blender-mcp).

> **Instagram:** https://www.instagram.com/perromods/

---

## Version

**Current:** 1.2.2 | **Target FreeCAD:** 1.0.2

### What's New in 1.2.2 — Audit round 2

14 fixes from a second full audit. Validated live against FreeCAD 1.0.2 — smoke test **11/11** (3 new checks). Highlights:

- ✅ **No more double execution** — the bridge client no longer resends a request after a read timeout; slow operations (large booleans, meshing) could previously run twice.
- ✅ **No more ghost tasks** — a main-thread dispatch timeout now cancels the queued task instead of letting it mutate the document later.
- ✅ **`run_python` gated in FreeCAD itself** — new **"Allow run_python"** checkbox in the workbench dock; the port can no longer be used to execute arbitrary code while the option is off.
- ✅ **Handlers survive the dock closing** — the main-thread pump timer is owned by the server, not the UI.
- ✅ **Clean `Shape` guards everywhere** — fillet/chamfer/arrays/measurements on sketches or spreadsheets now return `INVALID_PARAMS` instead of raw tracebacks; failed fillets/chamfers are rolled back instead of leaving broken objects.
- ✅ **Sketch plane orientation corrected** — XZ back to +90° about X (1.2.1 had inverted it), YZ uses FreeCAD's origin-plane quaternion.
- ✅ **`fem_add_force` reports honestly** — response includes `direction_applied` (FreeCAD 1.0 cannot take a raw vector direction).
- ✅ Misc: `get_distance` name pairing validated, `sides >= 3` for polygon prisms, `save_document` path validation, screenshot error envelope, `geo_index` required for constraints.

### What's New in 1.2.1 — Bug-fix round

Full audit: 18 bugs identified and corrected across handlers, server, MCP envelope and smoke tests. Validated live against FreeCAD 1.0.2 — smoke test 8/8.

User / agent-visible changes:

- ✅ **Coherent error classification** — `ValueError`/`KeyError` from handlers now return `INVALID_PARAMS` (previously fell through to an opaque `FREECAD_ERROR`).
- ✅ **`freecad_import_file` actually supports STL** — used to advertise STL but `Part.insert` rejected it; now dispatches by extension to `Mesh.insert`.
- ✅ **`freecad_polar_array` fixed** — removed dead conditional and div-by-zero with `count=0`; semantics clarified (`360°` → `total/count`; partial → `total/(count-1)`).
- ✅ **`freecad_fem_add_force` applies direction** — the `direction` parameter is no longer silently dropped; assigned to `DirectionVector` when the build exposes it.
- ✅ **`freecad_duplicate` validates `Shape`** — clear error when trying to duplicate sketches/spreadsheets.
- ✅ **`freecad_gui_screenshot` validates active GUI** — informative `LookupError` in headless mode.
- ✅ **`freecad_fillet` / `freecad_chamfer`** — validate edge index range (1..N) before calling FreeCAD.
- ✅ **`freecad_set_property`** — accepts `{x,y,z}` dicts in addition to primitives.
- ✅ **`freecad_create_sketch` XZ plane** — orientation fixed (rotation −90° around X).
- ✅ **`freecad_export` / `freecad_export_stl`** — validate that the destination directory exists.
- ✅ **Bridge envelope** — `error.details.trace` from the backend is now preserved through to the MCP client.
- ✅ **More robust server** — `listen(8)` instead of `listen(1)`, `stop()` joins the thread.
- ✅ **Smoke test** extended with `invalid_params_error` (8 checks instead of 7).
- ✅ **Array docstrings** clarify that `count` includes the original (`count-1` duplicates generated).
- ✅ **FEM init** without the dead `from femtools import ccxtools` import.
- ✅ **`_get_obj(None)`** now produces `INVALID_PARAMS: Missing 'name'`.
- ✅ **`bridge_client` retry** regenerates UUID so logs can distinguish attempts.

### What's New in 1.2.0

This release focuses on **agent decision quality** — fewer dead-ends, fewer wrong-workbench attempts, fewer wasted tool calls:

- ✅ Three new MCP prompts steering Claude toward the correct workbench and workflow:
  - `workbench_selection_strategy` — decision tree Part/PartDesign/Draft/Sketcher/Arch/TechDraw/FEM/Spreadsheet/Mesh/CAM
  - `drafting_2d_strategy` — canonical Draft workflow for 2D deliverables (DXF/SVG)
  - `fem_workflow_strategy` — strict FEM precondition order (single solid → material → BCs → mesh → solve)
- ✅ Hardened `freecad_parametric_modeling_strategy` with 5 parametric-correctness rules (sketch-on-face, External Geometry, fully-constrained before extrude, Pad locked to sketch, prefer Pattern over duplication) and an explicit internal-name reference policy
- ✅ Refined tool docstrings: `freecad_create_sketch` documents face attachment + constraint state, `freecad_boolean_cut` documents selection order + the oversize trick to avoid face-on-face failures
- ✅ All guidance sourced from the official FreeCAD manual (Yorik) — verbatim rules where applicable

### What's New in 1.1.1

Compared to `1.0.0`, this release focuses on **production stability** and **agent UX predictability**:

- ✅ Standardized MCP response envelope: `{ok, result|error}` for consistent parsing
- ✅ Actionable bridge error taxonomy with stable error codes (ADDON_NOT_CONNECTED, BRIDGE_IO_TIMEOUT, etc.)
- ✅ Runtime capability reporting with per-domain status objects (`enabled` + guidance message)
- ✅ Text-first scene inspection policy (`freecad_get_scene_info`) — preferred over screenshots
- ✅ Deterministic smoke tests with process-friendly exit codes
- ✅ Explicit Error Code Reference for operator troubleshooting
- ✅ FreeCAD-native parametric workflow alignment (Body → Sketch → constraints → Pad/Pocket)

---

## Features

79 tools organized in 12 domains:

| Domain | Tools |
|---|---|
| Documents | new, open, save, list, set active |
| Capabilities | **get_capabilities** (status-first runtime checks) |
| Inspection | **get_scene_info** (rich textual snapshot — *preferred over screenshot*) |
| Primitives | box, cylinder, sphere, cone, torus, polygon prism |
| Booleans | cut, fuse, common |
| Transformations | translate, rotate, set placement, mirror |
| Operations | extrude, revolve, fillet, chamfer, loft, sweep |
| Arrays | linear, polar |
| Sketcher | sketch, line, circle, arc, rectangle, constraints (basic & advanced) |
| PartDesign | body, pad, pocket, hole |
| Measurements | bounding box, volume, area, distance |
| Mesh | shape to mesh, export STL |
| TechDraw | page, view |
| Draft | line, dimension, text |
| FEM | analysis, material, fixed, force |
| CAM | job, profile |
| Spreadsheet | create, set cell, get cell |
| GUI | screenshot, viewport control, selection, color, transparency |
| Dev | run_python (arbitrary FreeCAD API access) |

### Why `get_scene_info` is Better Than Screenshots

When you ask Claude to *"look at,"* *"describe,"* *"analyze,"* or *"take a screenshot"* of the scene:

**Claude uses `freecad_get_scene_info`** — a single textual snapshot containing:
- Active document (name, label, path, modified state, object count)
- Every object (name, label, type, placement, visibility, bounding box, volume, area)
- Active viewport camera (type, position, orientation)
- Current GUI selection

**Why?** You already see the FreeCAD viewport in real time. Sending an image back wastes tokens. `freecad_gui_screenshot` is still available for explicit image requests, but text inspection is the default.

### Agent Behavior Alignment

Five global MCP prompts guide Claude's behavior:

1. **`scene_inspection_strategy`**  
   Always start with `freecad_get_scene_info`; use `freecad_gui_screenshot` only on explicit image request.

2. **`workbench_selection_strategy`**  
   Decision tree for picking the right workbench/domain *before* picking tools. Covers Part vs PartDesign, Draft vs Sketcher, Arch/BIM, TechDraw, FEM, Spreadsheet, Mesh and CAM.

3. **`freecad_parametric_modeling_strategy`**  
   Follow `Body → Sketch 2D → constraints → Pad/Pocket (and details)` workflow until final part. Includes hard parametric-correctness rules: sketch-on-face for face extension, External Geometry for constraints against existing solids, fully-constrained sketch before Pad/Pocket, never move a Pad (move its sketch), prefer Pattern over manual duplication, reference objects by internal name.

4. **`drafting_2d_strategy`**  
   Canonical Draft workflow when the deliverable is paper/DXF/SVG. Guidelines first, snapped final geometry on top, dimensions/text last. Never mix Draft and Sketcher for the same deliverable.

5. **`fem_workflow_strategy`**  
   Strict FEM order: capability gate → single fused solid → analysis → material → fixed support → load → mesh → solve. Surfaces typical root causes when results look wrong.

All five enforce:
- **Prefer structured text over images** to reduce token usage
- **Recompute and validate** before declaring completion
- **Do not export automatically** — only on explicit user request
- **Status-first checks** (`freecad_get_capabilities`) before optional domains (FEM/CAM/TechDraw/Mesh/Assembly)

---

## Prerequisites

- [FreeCAD 1.0+](https://www.freecad.org)
- Python 3.10+
- [Claude Desktop](https://claude.ai/download)

---

## Installation

### Step 1 — Install MCP SDK

Open a terminal (PowerShell on Windows) and run:

```powershell
python -m pip install --upgrade mcp
```

Verify:

```powershell
python -c "import mcp; print(mcp.__version__)"
```

---

### Step 2 — Clone the Repository

```powershell
git clone https://github.com/Perro-Megabass/freecad-mcp.git
cd freecad-mcp
```

---

### Step 3 — Install FreeCAD Workbench

Find your FreeCAD user Mod directory.  
Open FreeCAD → View → Panels → Python console, and run:

```python
import os, FreeCAD
print(os.path.join(FreeCAD.getUserAppDataDir(), "Mod"))
```

Typical paths:

| OS | Path |
|---|---|
| Windows | `C:\Users\<you>\AppData\Roaming\FreeCAD\Mod` |
| macOS | `~/Library/Preferences/FreeCAD/Mod` |
| Linux | `~/.local/share/FreeCAD/Mod` |

Copy the `FreeCADMCP` folder into that Mod directory:

```
<MOD_DIR>/FreeCADMCP/
    __init__.py
    Init.py
    InitGui.py
    server.py
    handlers.py
    ui.py
```

Restart FreeCAD after copying.

---

### Step 4 — Activate the Workbench

In FreeCAD:

1. **View → Workbench → MCP Bridge**
2. A dock panel appears on the right
3. Click **Connect**

Expected status: `Listening on 127.0.0.1:9877`

---

### Step 5 — Configure Claude Desktop

Locate the config file:

| OS | Path |
|---|---|
| Windows (Store) | `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude_desktop_config.json` |
| Windows (classic) | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Add the `freecad` entry. Replace `<PROJECT_DIR>` with the absolute path where you cloned this repo:

**Windows:**
```json
{
  "mcpServers": {
    "freecad": {
      "command": "python",
      "args": ["-m", "freecad_mcp"],
      "cwd": "<PROJECT_DIR>",
      "env": {
        "PYTHONPATH": "<PROJECT_DIR>",
        "FREECAD_ALLOW_RUN_PYTHON": "true"
      }
    }
  }
}
```

**macOS / Linux:**
```json
{
  "mcpServers": {
    "freecad": {
      "command": "python3",
      "args": ["-m", "freecad_mcp"],
      "cwd": "<PROJECT_DIR>",
      "env": {
        "PYTHONPATH": "<PROJECT_DIR>",
        "FREECAD_ALLOW_RUN_PYTHON": "true"
      }
    }
  }
}
```

---

### Step 6 — Restart Claude Desktop

Fully quit Claude Desktop (system tray → Quit), then relaunch.

Verify:  
**Settings → Developer → Local MCP servers → freecad** → status: `running`

---

## Validation

With FreeCAD running and the bridge connected, test the integration independently:

```powershell
cd <PROJECT_DIR>
python test_bridge.py
```

This smoke test validates:

| Check | Validates |
|---|---|
| `ping` | Bridge connectivity and FreeCAD version |
| `get_capabilities` | Workbench availability and per-domain status |
| `new_document` | Document creation |
| `list_objects` | Object enumeration |
| `recompute` | Parametric model updates and stable response envelope |
| `get_scene_info` | Rich textual scene snapshot (preferred tool) |
| `bogus_action_error` | Error envelope and code taxonomy (expects `INVALID_PARAMS`) |
| `invalid_params_error` | Missing-parameter dispatch maps to `INVALID_PARAMS` (not `FREECAD_ERROR`) |

Expected output:

```
[PASS] ping
[PASS] get_capabilities
[PASS] new_document
[PASS] list_objects
[PASS] recompute
[PASS] get_scene_info
[PASS] bogus_action_error
[PASS] invalid_params_error

Summary: 8/8 checks passed
```

Exit code: `0` (success) or `1` (failures) or `2` (connection error).

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FREECAD_HOST` | `127.0.0.1` | Bridge host |
| `FREECAD_PORT` | `9877` | Bridge port |
| `FREECAD_TIMEOUT_SEC` | `60` | Per-call timeout (seconds) |
| `FREECAD_ALLOW_RUN_PYTHON` | `false` | Enable `freecad_run_python` tool (MCP side; FreeCAD side also requires the **Allow run_python** dock checkbox) |
| `FREECAD_MCP_TELEMETRY` | `true` | Enable lightweight per-tool telemetry |
| `FREECAD_MCP_TELEMETRY_PATH` | system temp | JSONL telemetry output path |

---

## Daily Use

1. Open FreeCAD → activate **MCP Bridge** workbench → click **Connect**
2. Open Claude Desktop
3. Ask Claude to operate FreeCAD

Example prompts:
- *"Create a 20×20×20 mm box in a new document"*
- *"Boolean cut the box with a cylinder of radius 5"*
- *"Export the result as STEP to my Desktop"*
- *"Create a TechDraw page with a top view at scale 1:1"*

---

## Troubleshooting

### Error Code Reference

Bridge and client errors use **stable, actionable codes**. When something fails, the error code tells you exactly what to check:

| Code | Meaning | Action |
|---|---|---|
| `ADDON_NOT_CONNECTED` | FreeCAD bridge is not listening | Open FreeCAD, activate MCP Bridge workbench, click **Connect** |
| `CONNECTION_TIMEOUT` | TCP handshake timed out | Confirm FreeCAD is responsive; check port availability |
| `BRIDGE_CONNECT_FAILED` | Socket connection error (OS/network) | Verify `FREECAD_HOST` and `FREECAD_PORT`; check firewall |
| `BRIDGE_IO_TIMEOUT` | Request/response timed out mid-call | Retry; if persistent, simplify operation or restart bridge |
| `EMPTY_RESPONSE` | Connection accepted but no payload | Reconnect bridge; ensure port is not hijacked by another service |
| `INVALID_BRIDGE_RESPONSE` | Non-JSON response on configured port | Verify `FREECAD_PORT` points to FreeCAD MCP bridge (not another service) |
| `NOT_CONNECTED` | Generic client-side connection failure | Verify FreeCAD is running and MCP Bridge workbench is connected |
| `INVALID_PARAMS` | Unknown action or malformed parameters | Check action name; verify parameter schema in tool docs |
| `NOT_FOUND` | Requested object/document not found | Verify object/document names; check active document context |
| `FREECAD_ERROR` | Handler or runtime error inside FreeCAD | Review error message; verify inputs; retry with corrected values |

### Common Issues

**`NOT_CONNECTED` or `ADDON_NOT_CONNECTED`**  
→ Open FreeCAD, activate **MCP Bridge** workbench, click **Connect**. Check status shows `Listening on 127.0.0.1:9877`.

**`No module named freecad_mcp`**  
→ Verify `PYTHONPATH` and `cwd` in Claude Desktop config point to the correct directory (where you cloned the repo).

**`No module named mcp`**  
→ The Python interpreter Claude uses doesn't have the MCP SDK. Install it:
```powershell
<python_path> -m pip install mcp
```

**Port 9877 already in use**  
→ Set `FREECAD_PORT` to a free port and edit `PORT = 9877` in `FreeCADMCP/server.py`.

**`run_python disabled`**  
→ Two gates must both be open: add `"FREECAD_ALLOW_RUN_PYTHON": "true"` to the `env` section in Claude Desktop config, **and** enable the **Allow run_python** checkbox in the FreeCAD MCP Bridge dock (or launch FreeCAD with the same env var set).

**Workbench not visible in FreeCAD**  
→ Confirm `FreeCADMCP/` folder was copied to the correct Mod directory and restart FreeCAD.

---

## Security Notes

- The socket binds to `127.0.0.1` only — not exposed to the network.
- `FREECAD_ALLOW_RUN_PYTHON=true` enables arbitrary Python execution inside FreeCAD (file system access included). Only enable on machines you control.
- Keep the workbench **Disconnected** when not actively using Claude with FreeCAD.

---

## License

MIT

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Disclaimer

This is a third-party integration and not made by FreeCAD. Made by [PerroMods](https://www.instagram.com/perromods/).
