# FreeCAD MCP

Control FreeCAD from Claude Desktop using the Model Context Protocol (MCP).  
Inspired by [blender-mcp](https://github.com/ahujasid/blender-mcp).

> **Instagram:** https://www.instagram.com/perromods/

---

## Features

79 tools organized in 12 categories:

| Category | Tools |
|---|---|
| Documents | new, open, save, list, set active |
| Primitives | box, cylinder, sphere, cone, torus, polygon prism |
| Booleans | cut, fuse, common |
| Transformations | translate, rotate, set placement, mirror |
| Operations | extrude, revolve, fillet, chamfer, loft, sweep |
| Arrays | linear, polar |
| Sketcher | sketch, line, circle, arc, rectangle, constraints |
| PartDesign | body, pad, pocket, hole |
| Measurements | bounding box, volume, area, distance |
| Mesh | shape to mesh, export STL |
| TechDraw | page, view |
| Draft | line, dimension, text |
| FEM | analysis, material, fixed, force |
| CAM | job, profile |
| Spreadsheet | create, set cell, get cell |
| GUI | screenshot, views, selection, color, transparency |
| Dev | run_python (arbitrary FreeCAD API access) |

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

### Step 2 — Clone the repository

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

With FreeCAD connected, run this in a terminal to test the bridge independently:

```powershell
cd <PROJECT_DIR>
python test_bridge.py
```

Expected output:

```
[OK] ping
[OK] list_documents
[OK] new_document
[OK] list_objects
[FAIL] bogus_action   ← expected, tests error handling
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FREECAD_HOST` | `127.0.0.1` | Bridge host |
| `FREECAD_PORT` | `9877` | Bridge port |
| `FREECAD_TIMEOUT_SEC` | `60` | Per-call timeout |
| `FREECAD_ALLOW_RUN_PYTHON` | `false` | Enable `freecad_run_python` tool |

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

**`NOT_CONNECTED` error**  
FreeCAD is not running or the workbench is not connected.  
→ Activate MCP Bridge workbench and click Connect.

**`No module named freecad_mcp`**  
`PYTHONPATH` or `cwd` in the config points to the wrong directory.  
→ Verify `<PROJECT_DIR>` is the absolute path of this cloned repo.

**`No module named mcp`**  
MCP SDK not installed in the Python interpreter Claude uses.  
→ Check the interpreter path in the Claude Desktop log and install there:
```powershell
<python_path> -m pip install mcp
```

**Port 9877 already in use**  
→ Set `FREECAD_PORT` to another port and edit `PORT` in `FreeCADMCP/server.py`.

**`run_python disabled`**  
→ Add `"FREECAD_ALLOW_RUN_PYTHON": "true"` to the `env` block in config.

**Workbench not visible in FreeCAD**  
→ Confirm `FreeCADMCP/` was copied to the correct Mod directory and restart FreeCAD.

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


