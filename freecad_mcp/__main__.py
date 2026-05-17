# -*- coding: utf-8 -*-
# FreeCAD MCP — __main__.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""FreeCAD MCP stdio server. Run with: python -m freecad_mcp"""

import base64
import json
import os
import tempfile
import time

from mcp.server.fastmcp import FastMCP, Image

from .bridge_client import CLIENT, BridgeClientError

mcp = FastMCP("freecad")

_TELEMETRY_ENABLED = os.getenv("FREECAD_MCP_TELEMETRY", "true").strip().lower() in {
    "1", "true", "yes", "on"
}
_TELEMETRY_PATH = os.getenv(
    "FREECAD_MCP_TELEMETRY_PATH",
    os.path.join(tempfile.gettempdir(), "freecad_mcp_tool_events.jsonl"),
)


def _log_tool_event(action: str, success: bool, duration_ms: float, error: str | None = None) -> None:
    """Append a lightweight per-tool execution event to local JSONL telemetry."""
    if not _TELEMETRY_ENABLED:
        return
    event = {
        "ts": time.time(),
        "action": action,
        "success": bool(success),
        "duration_ms": round(float(duration_ms), 3),
    }
    if error:
        event["error"] = str(error)
    try:
        with open(_TELEMETRY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # Telemetry should never break tool execution.
        pass


def _error_envelope(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}


def _normalize_envelope(resp) -> dict:
    """Normalize bridge payload into stable {ok, result|error} envelope."""
    if not isinstance(resp, dict):
        return _error_envelope("INVALID_BRIDGE_RESPONSE", "Bridge returned a non-object response")
    if "ok" not in resp:
        # Backward-compatible fallback for older bridge payloads.
        return {"ok": True, "result": resp}
    if resp.get("ok"):
        return {"ok": True, "result": resp.get("result")}
    err = resp.get("error")
    if isinstance(err, dict) and err.get("code") and err.get("message"):
        return {"ok": False, "error": {"code": err["code"], "message": err["message"]}}
    return _error_envelope("FREECAD_ERROR", "Bridge returned an error without details")


def _call(action: str, params: dict | None = None) -> str:
    start = time.perf_counter()
    try:
        resp = CLIENT.call(action, params or {})
    except BridgeClientError as e:
        _log_tool_event(action, False, (time.perf_counter() - start) * 1000.0, e.message)
        return json.dumps(_error_envelope(e.code, e.message), ensure_ascii=False)
    except Exception as e:
        _log_tool_event(action, False, (time.perf_counter() - start) * 1000.0, str(e))
        return json.dumps(_error_envelope("NOT_CONNECTED", str(e)), ensure_ascii=False)
    normalized = _normalize_envelope(resp)
    success = bool(normalized.get("ok"))
    _log_tool_event(action, success, (time.perf_counter() - start) * 1000.0)
    return json.dumps(normalized, ensure_ascii=False)


@mcp.tool()
def freecad_ping() -> str:
    """Ping FreeCAD bridge. Returns version info."""
    return _call("ping")


@mcp.tool()
def freecad_get_capabilities() -> str:
    """Get runtime capabilities/workbenches. Use this status-first before optional tools."""
    return _call("get_capabilities")


@mcp.tool()
def freecad_list_documents() -> str:
    """List open documents and the active document."""
    return _call("list_documents")


@mcp.tool()
def freecad_new_document(name: str = "Unnamed") -> str:
    """Create a new FreeCAD document with the given name."""
    return _call("new_document", {"name": name})


@mcp.tool()
def freecad_list_objects(document: str | None = None) -> str:
    """List objects in a document (uses active document if not specified)."""
    params = {"document": document} if document else {}
    return _call("list_objects", params)


@mcp.tool()
def freecad_get_scene_info(document: str | None = None) -> str:
    """Rich textual snapshot of the FreeCAD scene — use this to "see" / "look at" / "describe" / "analyze" the scene WITHOUT taking a screenshot.

    Returns JSON with: active document metadata, every object (name, label, type, placement, visibility, bounding box, volume, area), current viewport camera (type, position, orientation) and the current GUI selection.

    PREFER THIS over freecad_gui_screenshot for any scene-inspection request — the user is already viewing the FreeCAD viewport on screen, so a screenshot is redundant and wastes tokens.
    """
    params = {"document": document} if document else {}
    return _call("get_scene_info", params)


@mcp.tool()
def freecad_set_active_document(name: str) -> str:
    """Set the active document by name."""
    return _call("set_active_document", {"name": name})


@mcp.tool()
def freecad_open_document(path: str) -> str:
    """Open a .FCStd file from an absolute path."""
    return _call("open_document", {"path": path})


@mcp.tool()
def freecad_save_document(path: str | None = None, document: str | None = None) -> str:
    """Save document. If path is given, performs Save As; otherwise overwrites."""
    params = {}
    if path:
        params["path"] = path
    if document:
        params["document"] = document
    return _call("save_document", params)


@mcp.tool()
def freecad_recompute(document: str | None = None) -> str:
    """Force recompute of the document."""
    params = {"document": document} if document else {}
    return _call("recompute", params)


@mcp.tool()
def freecad_create_box(length: float = 10.0, width: float = 10.0, height: float = 10.0,
                       name: str = "Box", document: str | None = None) -> str:
    """Create a parametric box (Part::Box). Units: mm."""
    params = {"length": length, "width": width, "height": height, "name": name}
    if document:
        params["document"] = document
    return _call("create_box", params)


@mcp.tool()
def freecad_create_cylinder(radius: float = 5.0, height: float = 10.0,
                            name: str = "Cylinder", document: str | None = None) -> str:
    """Create a parametric cylinder (Part::Cylinder). Units: mm."""
    params = {"radius": radius, "height": height, "name": name}
    if document:
        params["document"] = document
    return _call("create_cylinder", params)


@mcp.tool()
def freecad_boolean_cut(base: str, tool: str, name: str = "Cut",
                        document: str | None = None) -> str:
    """Boolean cut: base minus tool. Returns new Part::Cut object.

    Selection order: base first (kept), tool second (subtracted).
    Tip: to avoid face-on-face failures, make the tool geometry overhang
    the base on both sides instead of matching its face exactly."""
    params = {"base": base, "tool": tool, "name": name}
    if document:
        params["document"] = document
    return _call("boolean_cut", params)


@mcp.tool()
def freecad_boolean_fuse(base: str, tool: str, name: str = "Fusion",
                         document: str | None = None) -> str:
    """Boolean union: base + tool (Part::Fuse)."""
    params = {"base": base, "tool": tool, "name": name}
    if document:
        params["document"] = document
    return _call("boolean_fuse", params)


@mcp.tool()
def freecad_boolean_common(base: str, tool: str, name: str = "Common",
                           document: str | None = None) -> str:
    """Boolean intersection: base ∩ tool (Part::Common)."""
    params = {"base": base, "tool": tool, "name": name}
    if document:
        params["document"] = document
    return _call("boolean_common", params)


@mcp.tool()
def freecad_export(path: str, objects: list[str] | None = None,
                   document: str | None = None) -> str:
    """Export objects to file (STEP/STL/IGES/BREP detected by extension)."""
    params = {"path": path}
    if objects:
        params["objects"] = objects
    if document:
        params["document"] = document
    return _call("export", params)


@mcp.tool()
def freecad_delete_object(name: str, document: str | None = None) -> str:
    """Delete an object by name."""
    params = {"name": name}
    if document:
        params["document"] = document
    return _call("delete_object", params)


@mcp.tool()
def freecad_create_sphere(radius: float = 5.0, name: str = "Sphere",
                          document: str | None = None) -> str:
    """Create a sphere (Part::Sphere). Units: mm."""
    p = {"radius": radius, "name": name}
    if document: p["document"] = document
    return _call("create_sphere", p)


@mcp.tool()
def freecad_create_cone(radius1: float = 5.0, radius2: float = 0.0, height: float = 10.0,
                        name: str = "Cone", document: str | None = None) -> str:
    """Create a cone/truncated cone (radius2=0 → sharp tip)."""
    p = {"radius1": radius1, "radius2": radius2, "height": height, "name": name}
    if document: p["document"] = document
    return _call("create_cone", p)


@mcp.tool()
def freecad_create_torus(radius1: float = 10.0, radius2: float = 2.0,
                         name: str = "Torus", document: str | None = None) -> str:
    """Create a torus. radius1=major radius, radius2=tube radius."""
    p = {"radius1": radius1, "radius2": radius2, "name": name}
    if document: p["document"] = document
    return _call("create_torus", p)


@mcp.tool()
def freecad_create_polygon_prism(sides: int = 6, radius: float = 5.0, height: float = 5.0,
                                 name: str = "Prism", document: str | None = None) -> str:
    """Regular polygon prism (sides=6 for hex nut/bolt head)."""
    p = {"sides": sides, "radius": radius, "height": height, "name": name}
    if document: p["document"] = document
    return _call("create_polygon_prism", p)


@mcp.tool()
def freecad_set_placement(name: str, base_x: float = 0, base_y: float = 0, base_z: float = 0,
                          axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                          angle_deg: float = 0, document: str | None = None) -> str:
    """Set position and rotation (axis-angle) of an object."""
    p = {"name": name,
         "base": {"x": base_x, "y": base_y, "z": base_z},
         "rot": {"axis": {"x": axis_x, "y": axis_y, "z": axis_z}, "angle_deg": angle_deg}}
    if document: p["document"] = document
    return _call("set_placement", p)


@mcp.tool()
def freecad_translate(name: str, dx: float = 0, dy: float = 0, dz: float = 0,
                      document: str | None = None) -> str:
    """Translate an object by a delta vector."""
    p = {"name": name, "delta": {"x": dx, "y": dy, "z": dz}}
    if document: p["document"] = document
    return _call("translate", p)


@mcp.tool()
def freecad_rotate(name: str, axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                   angle_deg: float = 0, cx: float = 0, cy: float = 0, cz: float = 0,
                   document: str | None = None) -> str:
    """Rotate an object around an axis and center point."""
    p = {"name": name,
         "axis": {"x": axis_x, "y": axis_y, "z": axis_z},
         "angle_deg": angle_deg,
         "center": {"x": cx, "y": cy, "z": cz}}
    if document: p["document"] = document
    return _call("rotate", p)


@mcp.tool()
def freecad_extrude(source: str, dx: float = 0, dy: float = 0, dz: float = 10,
                    solid: bool = True, name: str = "Extrude",
                    document: str | None = None) -> str:
    """Extrude source object along a direction vector."""
    p = {"source": source, "direction": {"x": dx, "y": dy, "z": dz},
         "solid": solid, "name": name}
    if document: p["document"] = document
    return _call("extrude", p)


@mcp.tool()
def freecad_revolve(source: str, axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                    angle_deg: float = 360.0, bx: float = 0, by: float = 0, bz: float = 0,
                    solid: bool = True, name: str = "Revolve",
                    document: str | None = None) -> str:
    """Revolve a source object around an axis."""
    p = {"source": source, "axis": {"x": axis_x, "y": axis_y, "z": axis_z},
         "angle_deg": angle_deg, "base": {"x": bx, "y": by, "z": bz},
         "solid": solid, "name": name}
    if document: p["document"] = document
    return _call("revolve", p)


@mcp.tool()
def freecad_fillet(source: str, radius: float = 1.0, edges: list[int] | None = None,
                   name: str = "Fillet", document: str | None = None) -> str:
    """Round edges. edges=None means all edges."""
    p = {"source": source, "radius": radius, "name": name}
    if edges: p["edges"] = edges
    if document: p["document"] = document
    return _call("fillet", p)


@mcp.tool()
def freecad_chamfer(source: str, size: float = 1.0, edges: list[int] | None = None,
                    name: str = "Chamfer", document: str | None = None) -> str:
    """Chamfer edges. edges=None means all edges."""
    p = {"source": source, "size": size, "name": name}
    if edges: p["edges"] = edges
    if document: p["document"] = document
    return _call("chamfer", p)


@mcp.tool()
def freecad_mirror(source: str, nx: float = 0, ny: float = 0, nz: float = 1,
                   bx: float = 0, by: float = 0, bz: float = 0,
                   name: str = "Mirror", document: str | None = None) -> str:
    """Mirror an object across a plane (normal + base)."""
    p = {"source": source, "normal": {"x": nx, "y": ny, "z": nz},
         "base": {"x": bx, "y": by, "z": bz}, "name": name}
    if document: p["document"] = document
    return _call("mirror", p)


@mcp.tool()
def freecad_get_object(name: str, document: str | None = None) -> str:
    """Return all available object properties."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_object", p)


@mcp.tool()
def freecad_set_property(name: str, property: str, value, document: str | None = None) -> str:
    """Assign a value to an object property."""
    p = {"name": name, "property": property, "value": value}
    if document: p["document"] = document
    return _call("set_property", p)


@mcp.tool()
def freecad_set_label(name: str, label: str, document: str | None = None) -> str:
    """Change the object's Label (display name)."""
    p = {"name": name, "label": label}
    if document: p["document"] = document
    return _call("set_label", p)


@mcp.tool()
def freecad_set_visibility(name: str, visible: bool = True, document: str | None = None) -> str:
    """Show/hide object in the viewport (requires GUI)."""
    p = {"name": name, "visible": visible}
    if document: p["document"] = document
    return _call("set_visibility", p)


@mcp.tool()
def freecad_duplicate(name: str, new_name: str | None = None,
                      document: str | None = None) -> str:
    """Duplicate object (shape + placement copy)."""
    p = {"name": name}
    if new_name: p["new_name"] = new_name
    if document: p["document"] = document
    return _call("duplicate", p)


@mcp.tool()
def freecad_import_file(path: str, document: str | None = None) -> str:
    """Import a file (STEP/IGES/BREP/STL) into the document."""
    p = {"path": path}
    if document: p["document"] = document
    return _call("import_file", p)


@mcp.tool()
def freecad_run_python(code: str) -> str:
    """Execute arbitrary Python code with App/Part/Gui/doc in scope. Requires FREECAD_ALLOW_RUN_PYTHON=true."""
    return _call("run_python", {"code": code})


# ==================== SKETCHER ====================

@mcp.tool()
def freecad_create_sketch(name: str = "Sketch", plane: str = "XY",
                          document: str | None = None) -> str:
    """Create a sketch on XY|XZ|YZ base plane.

    To extend an existing solid, prefer creating the sketch on a selected face
    of the body (use freecad_gui_select first) so FreeCAD attaches the sketch
    to that face. Use External Geometry to constrain against existing edges
    instead of absolute coordinates. After adding geometry, the sketch must be
    fully constrained before Pad/Pocket."""
    p = {"name": name, "plane": plane}
    if document: p["document"] = document
    return _call("create_sketch", p)


@mcp.tool()
def freecad_sketch_add_line(sketch: str, x1: float, y1: float, x2: float, y2: float,
                            document: str | None = None) -> str:
    """Add a line segment to the sketch."""
    p = {"sketch": sketch, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if document: p["document"] = document
    return _call("sketch_add_line", p)


@mcp.tool()
def freecad_sketch_add_circle(sketch: str, cx: float, cy: float, radius: float,
                              document: str | None = None) -> str:
    """Add a circle to the sketch."""
    p = {"sketch": sketch, "cx": cx, "cy": cy, "radius": radius}
    if document: p["document"] = document
    return _call("sketch_add_circle", p)


@mcp.tool()
def freecad_sketch_add_arc(sketch: str, cx: float, cy: float, radius: float,
                           start_deg: float = 0, end_deg: float = 90,
                           document: str | None = None) -> str:
    """Add an arc to the sketch (degrees)."""
    p = {"sketch": sketch, "cx": cx, "cy": cy, "radius": radius,
         "start_deg": start_deg, "end_deg": end_deg}
    if document: p["document"] = document
    return _call("sketch_add_arc", p)


@mcp.tool()
def freecad_sketch_add_rectangle(sketch: str, x1: float, y1: float, x2: float, y2: float,
                                 document: str | None = None) -> str:
    """Add a rectangle (4 lines) to the sketch."""
    p = {"sketch": sketch, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if document: p["document"] = document
    return _call("sketch_add_rectangle", p)


@mcp.tool()
def freecad_sketch_add_constraint(sketch: str, type: str, geo_index: int = -1,
                                  value: float = 0.0, document: str | None = None) -> str:
    """Constraint: horizontal|vertical|distance|radius."""
    p = {"sketch": sketch, "type": type, "geo_index": geo_index, "value": value}
    if document: p["document"] = document
    return _call("sketch_add_constraint", p)


# ==================== PARTDESIGN ====================

@mcp.tool()
def freecad_create_body(name: str = "Body", document: str | None = None) -> str:
    """Create a PartDesign Body."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("create_body", p)


@mcp.tool()
def freecad_pad(body: str, sketch: str, length: float = 10.0,
                reversed: bool = False, midplane: bool = False,
                name: str = "Pad", document: str | None = None) -> str:
    """Pad (extrude) a sketch inside a Body."""
    p = {"body": body, "sketch": sketch, "length": length,
         "reversed": reversed, "midplane": midplane, "name": name}
    if document: p["document"] = document
    return _call("pad", p)


@mcp.tool()
def freecad_pocket(body: str, sketch: str, length: float = 10.0,
                   reversed: bool = False, name: str = "Pocket",
                   document: str | None = None) -> str:
    """Pocket (cut) from a sketch inside a Body."""
    p = {"body": body, "sketch": sketch, "length": length,
         "reversed": reversed, "name": name}
    if document: p["document"] = document
    return _call("pocket", p)


# ==================== ARRAYS ====================

@mcp.tool()
def freecad_linear_array(source: str, count: int = 2,
                         dx: float = 10.0, dy: float = 0.0, dz: float = 0.0,
                         name: str | None = None, document: str | None = None) -> str:
    """Linear pattern of copies along XYZ delta."""
    p = {"source": source, "count": count, "dx": dx, "dy": dy, "dz": dz}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("linear_array", p)


@mcp.tool()
def freecad_polar_array(source: str, count: int = 4, total_angle_deg: float = 360.0,
                        axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                        cx: float = 0, cy: float = 0, cz: float = 0,
                        name: str | None = None, document: str | None = None) -> str:
    """Polar pattern of copies around an axis."""
    p = {"source": source, "count": count, "total_angle_deg": total_angle_deg,
         "axis": {"x": axis_x, "y": axis_y, "z": axis_z},
         "center": {"x": cx, "y": cy, "z": cz}}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("polar_array", p)


# ==================== GUI ====================

@mcp.tool()
def freecad_gui_screenshot(width: int = 1280, height: int = 720, path: str | None = None):
    """Capture active viewport screenshot and return the image to the agent.

    By default, the image is returned directly to the agent without saving it
    to disk. If a 'path' (absolute path) is provided, it also writes the PNG
    file at that location.
    """
    keep_file = bool(path)
    target_path = path
    if not target_path:
        fd, target_path = tempfile.mkstemp(suffix=".png", prefix="freecad_mcp_shot_")
        os.close(fd)

    start = time.perf_counter()
    try:
        resp = CLIENT.call(
            "gui_screenshot",
            {"path": target_path, "width": width, "height": height},
        )
    except BridgeClientError as e:
        _log_tool_event("gui_screenshot", False, (time.perf_counter() - start) * 1000.0, e.message)
        if not keep_file:
            try:
                os.remove(target_path)
            except Exception:
                pass
        return json.dumps(_error_envelope(e.code, e.message), ensure_ascii=False)
    except Exception as e:
        _log_tool_event("gui_screenshot", False, (time.perf_counter() - start) * 1000.0, str(e))
        if not keep_file:
            try:
                os.remove(target_path)
            except Exception:
                pass
        return json.dumps(_error_envelope("NOT_CONNECTED", str(e)), ensure_ascii=False)

    resp = _normalize_envelope(resp)
    if not resp.get("ok"):
        _log_tool_event("gui_screenshot", False, (time.perf_counter() - start) * 1000.0,
                        str((resp.get("error") or {}).get("message", "gui_screenshot failed")))
        if not keep_file:
            try:
                os.remove(target_path)
            except Exception:
                pass
        return json.dumps(resp, ensure_ascii=False)

    # Prefer base64 from handler (works in remote setups). Fallback: read local file.
    result_data = resp.get("result") or {}
    b64 = result_data.get("image_base64") if isinstance(result_data, dict) else None
    try:
        if b64:
            image_bytes = base64.b64decode(b64)
        else:
            with open(target_path, "rb") as f:
                image_bytes = f.read()
        _log_tool_event("gui_screenshot", True, (time.perf_counter() - start) * 1000.0)
        return Image(data=image_bytes, format="png")
    finally:
        if not keep_file:
            try:
                os.remove(target_path)
            except Exception:
                pass


@mcp.tool()
def freecad_gui_set_view(view: str = "iso") -> str:
    """Set standard viewport: iso|top|bottom|front|back|left|right."""
    return _call("gui_set_view", {"view": view})


@mcp.tool()
def freecad_gui_fit_all() -> str:
    """Fit view to all objects."""
    return _call("gui_fit_all")


# ==================== MEASUREMENTS ====================

@mcp.tool()
def freecad_get_bounding_box(name: str, document: str | None = None) -> str:
    """Object bounding box: min/max/size."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_bounding_box", p)


@mcp.tool()
def freecad_get_volume(name: str, document: str | None = None) -> str:
    """Shape volume (mm^3)."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_volume", p)


@mcp.tool()
def freecad_get_area(name: str, document: str | None = None) -> str:
    """Surface area of the shape (mm²)."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_area", p)


@mcp.tool()
def freecad_get_distance(name1: str | None = None, name2: str | None = None,
                         ax: float = 0, ay: float = 0, az: float = 0,
                         bx: float = 0, by: float = 0, bz: float = 0,
                         document: str | None = None) -> str:
    """Distance between 2 objects (by name) or 2 points (a/b)."""
    if name1 and name2:
        p = {"name1": name1, "name2": name2}
    else:
        p = {"a": {"x": ax, "y": ay, "z": az},
             "b": {"x": bx, "y": by, "z": bz}}
    if document: p["document"] = document
    return _call("get_distance", p)


# ==================== MESH ====================

@mcp.tool()
def freecad_shape_to_mesh(source: str, linear_deflection: float = 0.1,
                          angular_deflection: float = 0.523599,
                          name: str | None = None, document: str | None = None) -> str:
    """Convert shape to mesh (for STL/3D printing)."""
    p = {"source": source, "linear_deflection": linear_deflection,
         "angular_deflection": angular_deflection}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("shape_to_mesh", p)


@mcp.tool()
def freecad_export_stl(path: str, objects: list[str] | None = None,
                       document: str | None = None) -> str:
    """Export objects to STL."""
    p = {"path": path}
    if objects: p["objects"] = objects
    if document: p["document"] = document
    return _call("export_stl", p)


# ==================== TECHDRAW ====================

@mcp.tool()
def freecad_techdraw_create_page(name: str = "Page", template: str | None = None,
                                 document: str | None = None) -> str:
    """Create a TechDraw page with an SVG template (default: A4 landscape)."""
    p = {"name": name}
    if template: p["template"] = template
    if document: p["document"] = document
    return _call("techdraw_create_page", p)


@mcp.tool()
def freecad_techdraw_add_view(page: str, source: str, name: str = "View",
                              dir_x: float = 0, dir_y: float = 0, dir_z: float = 1,
                              scale: float = 1.0, x: float = 100.0, y: float = 100.0,
                              document: str | None = None) -> str:
    """Add a 2D view of an object to a TechDraw page."""
    p = {"page": page, "source": source, "name": name,
         "direction": {"x": dir_x, "y": dir_y, "z": dir_z},
         "scale": scale, "x": x, "y": y}
    if document: p["document"] = document
    return _call("techdraw_add_view", p)


# ==================== DRAFT ====================

@mcp.tool()
def freecad_draft_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float,
                       name: str | None = None, document: str | None = None) -> str:
    """Create a Draft line (3D)."""
    p = {"p1": {"x": x1, "y": y1, "z": z1}, "p2": {"x": x2, "y": y2, "z": z2}}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("draft_line", p)


@mcp.tool()
def freecad_draft_dimension(x1: float, y1: float, z1: float,
                            x2: float, y2: float, z2: float,
                            tx: float = 0, ty: float = 0, tz: float = 0,
                            document: str | None = None) -> str:
    """Draft linear dimension between 2 points (tx,ty,tz = text position)."""
    p = {"p1": {"x": x1, "y": y1, "z": z1}, "p2": {"x": x2, "y": y2, "z": z2},
         "p_text": {"x": tx, "y": ty, "z": tz}}
    if document: p["document"] = document
    return _call("draft_dimension", p)


@mcp.tool()
def freecad_draft_text(text: str, x: float = 0, y: float = 0, z: float = 0,
                       document: str | None = None) -> str:
    """Place a Draft text annotation at a 3D position."""
    p = {"text": text, "position": {"x": x, "y": y, "z": z}}
    if document: p["document"] = document
    return _call("draft_text", p)


# ==================== ASSEMBLY ====================

@mcp.tool()
def freecad_assembly_attach(name: str, parent: str,
                            offset_x: float = 0, offset_y: float = 0, offset_z: float = 0,
                            axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                            angle_deg: float = 0, document: str | None = None) -> str:
    """Attach object relative to parent (composed placement)."""
    p = {"name": name, "parent": parent,
         "offset": {"x": offset_x, "y": offset_y, "z": offset_z},
         "rot": {"axis": {"x": axis_x, "y": axis_y, "z": axis_z}, "angle_deg": angle_deg}}
    if document: p["document"] = document
    return _call("assembly_attach", p)


# ==================== FEM ====================

@mcp.tool()
def freecad_fem_create_analysis(name: str = "Analysis", document: str | None = None) -> str:
    """Create a FEM analysis with CalculiX solver."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("fem_create_analysis", p)


@mcp.tool()
def freecad_fem_add_material(analysis: str, material: str = "Steel-Generic",
                             name: str = "Material", document: str | None = None) -> str:
    """Add a FEM material to the analysis."""
    p = {"analysis": analysis, "material": material, "name": name}
    if document: p["document"] = document
    return _call("fem_add_material", p)


@mcp.tool()
def freecad_fem_add_fixed(analysis: str, object: str | None = None,
                          faces: list[int] | None = None,
                          name: str = "Fixed", document: str | None = None) -> str:
    """Add FEM fixed constraint on object faces."""
    p = {"analysis": analysis, "name": name}
    if object and faces:
        p["references"] = {"object": object, "faces": faces}
    if document: p["document"] = document
    return _call("fem_add_fixed", p)


@mcp.tool()
def freecad_fem_add_force(analysis: str, force: float = 1.0,
                          dx: float = 0, dy: float = 0, dz: float = -1,
                          object: str | None = None, faces: list[int] | None = None,
                          name: str = "Force", document: str | None = None) -> str:
    """Add FEM force constraint on faces."""
    p = {"analysis": analysis, "force": force,
         "direction": {"x": dx, "y": dy, "z": dz}, "name": name}
    if object and faces:
        p["references"] = {"object": object, "faces": faces}
    if document: p["document"] = document
    return _call("fem_add_force", p)


# ==================== CAM ====================

@mcp.tool()
def freecad_cam_create_job(source: str, name: str = "Job",
                           document: str | None = None) -> str:
    """Create a CAM/Path Job for source object."""
    p = {"source": source, "name": name}
    if document: p["document"] = document
    return _call("cam_create_job", p)


@mcp.tool()
def freecad_cam_profile(job: str, name: str = "Profile",
                        document: str | None = None) -> str:
    """Add a Profile (contour) operation to a CAM Job."""
    p = {"job": job, "name": name}
    if document: p["document"] = document
    return _call("cam_profile", p)


# ==================== SPREADSHEET ====================

@mcp.tool()
def freecad_spreadsheet_create(name: str = "Spreadsheet",
                               document: str | None = None) -> str:
    """Create a spreadsheet object."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("spreadsheet_create", p)


@mcp.tool()
def freecad_spreadsheet_set(sheet: str, cell: str, value, alias: str | None = None,
                            document: str | None = None) -> str:
    """Set cell value (e.g. 'A1'). Optional alias for references."""
    p = {"sheet": sheet, "cell": cell, "value": value}
    if alias: p["alias"] = alias
    if document: p["document"] = document
    return _call("spreadsheet_set", p)


@mcp.tool()
def freecad_spreadsheet_get(sheet: str, cell: str, document: str | None = None) -> str:
    """Read cell content and evaluated value."""
    p = {"sheet": sheet, "cell": cell}
    if document: p["document"] = document
    return _call("spreadsheet_get", p)


# ==================== COLOR ====================

@mcp.tool()
def freecad_set_color(name: str, r: float = 0.8, g: float = 0.8, b: float = 0.8,
                      document: str | None = None) -> str:
    """Set object RGB color in range 0-1 (GUI)."""
    p = {"name": name, "r": r, "g": g, "b": b}
    if document: p["document"] = document
    return _call("set_color", p)


@mcp.tool()
def freecad_set_transparency(name: str, transparency: int = 50,
                             document: str | None = None) -> str:
    """Set object transparency in range 0-100 (GUI)."""
    p = {"name": name, "transparency": transparency}
    if document: p["document"] = document
    return _call("set_transparency", p)


# ==================== LOFT / SWEEP ====================

@mcp.tool()
def freecad_loft(sections: list[str], solid: bool = True, ruled: bool = False,
                 name: str = "Loft", document: str | None = None) -> str:
    """Create loft between sections (>=2 objects with Shape)."""
    p = {"sections": sections, "solid": solid, "ruled": ruled, "name": name}
    if document: p["document"] = document
    return _call("loft", p)


@mcp.tool()
def freecad_sweep(profile: str, path: str, solid: bool = True, frenet: bool = False,
                  name: str = "Sweep", document: str | None = None) -> str:
    """Sweep a profile along a path."""
    p = {"profile": profile, "path": path, "solid": solid, "frenet": frenet, "name": name}
    if document: p["document"] = document
    return _call("sweep", p)


# ==================== HOLE ====================

@mcp.tool()
def freecad_hole(body: str, sketch: str, diameter: float = 6.0, depth: float = 10.0,
                 threaded: bool = False, thread_type: str | None = None,
                 name: str = "Hole", document: str | None = None) -> str:
    """PartDesign Hole in a Body using a sketch with circles as profile."""
    p = {"body": body, "sketch": sketch, "diameter": diameter, "depth": depth,
         "threaded": threaded, "name": name}
    if thread_type: p["thread_type"] = thread_type
    if document: p["document"] = document
    return _call("hole", p)


# ==================== ADVANCED SKETCH CONSTRAINTS ====================

@mcp.tool()
def freecad_sketch_add_constraint_advanced(sketch: str, type: str,
                                           geo1: int = -1, geo2: int = -1,
                                           vertex1: int = 1, vertex2: int = 1,
                                           geo_sym: int = -1,
                                           document: str | None = None) -> str:
    """Advanced constraint: parallel|perpendicular|tangent|equal|coincident|point_on_object|symmetric."""
    p = {"sketch": sketch, "type": type,
         "geo1": geo1, "geo2": geo2,
         "vertex1": vertex1, "vertex2": vertex2, "geo_sym": geo_sym}
    if document: p["document"] = document
    return _call("sketch_add_constraint_advanced", p)


# ==================== GUI SELECTION ====================

@mcp.tool()
def freecad_gui_select(objects: list[str], clear: bool = True,
                       document: str | None = None) -> str:
    """Select objects in viewport. clear=True clears previous selection."""
    p = {"objects": objects, "clear": clear}
    if document: p["document"] = document
    return _call("gui_select", p)


@mcp.tool()
def freecad_gui_clear_selection() -> str:
    """Clear the current selection."""
    return _call("gui_clear_selection")


@mcp.tool()
def freecad_gui_get_selection() -> str:
    """Return currently selected objects."""
    return _call("gui_get_selection")


@mcp.prompt()
def scene_inspection_strategy() -> str:
    """How the agent should inspect the FreeCAD scene with minimal token usage."""
    return """When the user asks to "look at" / "see" / "describe" / "analyze" / "what is in" the FreeCAD scene, ALWAYS start with freecad_get_scene_info().

Token-efficient defaults:
1. Prefer freecad_get_scene_info() over freecad_gui_screenshot().
2. Summarize only relevant objects/features requested by the user.
3. Avoid repeated inspection calls unless geometry changed.

Why:
- The user already sees the FreeCAD viewport locally.
- Screenshot payloads are expensive in tokens.
- freecad_get_scene_info() provides structured geometry/context for precise textual answers.

Use freecad_gui_screenshot() only when the user explicitly requests an image in chat (for example: "send a screenshot", "show me the picture")."""


@mcp.prompt()
def freecad_parametric_modeling_strategy() -> str:
    """Preferred FreeCAD workflow: parametric 2D-to-3D modeling until final part."""
    return """Use a FreeCAD-native parametric workflow by default:

1. Start by understanding current state:
   - Call freecad_get_scene_info() first.
   - Call freecad_get_capabilities() once per session before optional domains.
   - If no document exists, create one.

2. Status-first checks for optional domains:
   - Before FEM/CAM/TechDraw/Mesh/Assembly actions, verify capabilities first.
   - If a domain is not available, explain clearly and use the closest supported fallback.

3. Build parametric geometry in this order:
   - Create/activate Body (freecad_create_body).
   - Create Sketch on explicit plane (freecad_create_sketch).
   - Add sketch geometry (lines/circles/arcs/rectangle).
   - Add constraints and dimensions before 3D features.
   - Recompute when needed.

4. Convert 2D to 3D with PartDesign tools:
   - Use freecad_pad / freecad_pocket as primary operations.
   - Then apply detail operations (fillet/chamfer/patterns/mirror) if requested.
   - Keep model editable and parametric; avoid arbitrary code unless necessary.

5. Validate before declaring done:
   - Recompute document.
   - Verify resulting objects with freecad_list_objects/freecad_get_scene_info.
   - If needed, check key metrics (bbox/volume/area/distance).

6. Export policy:
   - Do NOT export by default.
   - Export (STL/STEP/other) only when user explicitly asks.
   - If format/path is unclear, ask before exporting.

7. Communication policy:
   - Be concise and execution-oriented.
   - Batch logical operations to reduce tool calls.
   - Ask clarifying questions early when critical dimensions/constraints are missing.

8. Hard rules (parametric correctness):
   - To extend an existing solid, select a face of the body before creating the
     sketch (freecad_gui_select), so the sketch attaches to that face.
   - Constrain new sketches against the base solid via External Geometry,
     not absolute coordinates.
   - A sketch must be fully constrained before Pad/Pocket. Treat under- or
     over-constrained sketches as failures and resolve before extruding.
   - Never apply freecad_set_placement to a Pad/Pocket result; move its base
     sketch instead — the feature is permanently bound to the sketch.
   - Prefer freecad_linear_array / freecad_polar_array (Pattern) over duplicating
     features manually; the result stays a single parametric solid.

9. Reference policy:
   - Always reference objects by their internal name (e.g. "Box001"), never by
     user label. Internal names are what every tool resolves against."""


@mcp.prompt()
def workbench_selection_strategy() -> str:
    """Decision tree for choosing the right FreeCAD workbench/domain per task."""
    return """Pick the workbench/domain BEFORE choosing tools. Wrong workbench
is the most common cause of dead-ends.

Decision tree:

- 3D-printable / mechanical / parametric solid part
    -> PartDesign (Body + Sketch + Pad/Pocket/Hole + Fillet/Chamfer/Patterns).
       Always solid, always editable. This is the default for "make a part".

- Free-form CSG (booleans on primitives, no sketch needed)
    -> Part (box/cylinder/sphere + boolean_cut/fuse/common).
       Faster than PartDesign for quick assemblies of primitives.
       Selection order in Cut: base first (kept), tool second (subtracted).

- 2D drawing intended as paper / DXF / SVG output
    -> Draft (line/wire/rectangle with grid + snap + working plane).
       Do NOT use Sketcher for this — Sketcher is only a feed for Pad/Pocket.

- 2D profile that will be extruded/revolved into 3D
    -> Sketcher, inside PartDesign. Never "switch to Sketcher" — stay in
       PartDesign; its toolbar already contains every Sketcher tool.

- Architecture / BIM (walls, windows, slabs)
    -> Arch (it supersets Draft — stay in Arch, do not toggle to Draft).

- 2D engineering drawings of an existing 3D model
    -> TechDraw (page from template + views of the 3D object).
       TechDraw is for documenting a finished model, not for drawing 2D.

- Structural simulation (deformation, stress)
    -> FEM. Precondition: one single fused solid (Part.Fuse multi-bodies first),
       a material, a constraint (Fixed), and a load (Force/Pressure).

- Parametric values driving multiple features
    -> Spreadsheet with aliases. Cells become parameters referenced from any
       property via expressions. A single sheet cannot both write a property
       and read the same property back (no circular dependencies).

- Mesh / STL export for 3D printing
    -> Mesh workbench: shape_to_mesh on the final solid, then export_stl.

- CAM / G-code
    -> CAM workbench: create_job on the solid, then profile/pocket operations.

Always call freecad_get_capabilities() once per session before using FEM, CAM,
TechDraw, Mesh, or Assembly tools — those domains may be disabled in the
runtime."""


@mcp.prompt()
def drafting_2d_strategy() -> str:
    """Canonical 2D drafting workflow with the Draft workbench."""
    return """Use this flow when the deliverable is a 2D drawing (paper, DXF,
SVG), not a 3D part. Tool family: freecad_draft_*.

1. New document. Default working plane is XY (top view). Confirm with the user
   if another plane is needed.

2. Lay guidelines first:
   - Use construction-mode-like lines (Draft lines) for the rough cage of the
     drawing. They are references, not final geometry.

3. Final geometry on top of guidelines:
   - Use Draft lines/wires/rectangles snapped to the guideline intersections.
   - Close wires when they must become a face later.

4. Annotation:
   - freecad_draft_dimension for measurements.
   - freecad_draft_text for labels.

5. Optional 2D -> 3D:
   - A closed Draft wire can be padded/extruded later via Part Extrude.
   - For parametric solids, recreate the profile in Sketcher under a Body
     instead — Draft profiles are not parametric in the PartDesign sense.

6. Export:
   - DXF/SVG via freecad_export. Do NOT export unless the user asks.

Never mix Draft and Sketcher for the same deliverable. Sketcher = 3D feed,
Draft = 2D output."""


@mcp.prompt()
def fem_workflow_strategy() -> str:
    """Canonical FEM analysis order in FreeCAD."""
    return """FEM has strict preconditions. Validate each before moving on or
the analysis silently produces garbage.

0. Capability gate:
   - Call freecad_get_capabilities() and confirm FEM is enabled. If not,
     explain and stop.

1. Geometry preparation:
   - The FEM workbench can analyze ONE single solid at a time. If the model
     has multiple bodies/parts, fuse them first (freecad_boolean_fuse).
   - Hide non-structural decorative objects.

2. Create the analysis container:
   - freecad_fem_create_analysis on the fused solid.

3. Material:
   - freecad_fem_add_material with a realistic material (steel, aluminium,
     concrete) — without material, the solver refuses to run.

4. Boundary conditions, in this order:
   - Fixed support first (freecad_fem_add_fixed) on the face(s) that anchor
     the part.
   - Then loads (freecad_fem_add_force) on the face(s) receiving force.

5. Mesh:
   - Generate the mesh AFTER constraints, not before — mesh quality depends
     on the final geometry state.

6. Solve and inspect:
   - Run the solver, then inspect displacement/stress results.
   - Communicate magnitudes and locations textually; do NOT push screenshots
     unless explicitly requested.

7. Iteration:
   - If results look wrong, the usual root causes are: under-constrained
     fixation, missing material, multi-solid input, or unrealistic load
     magnitude. Re-check in that order."""


if __name__ == "__main__":
    mcp.run()
