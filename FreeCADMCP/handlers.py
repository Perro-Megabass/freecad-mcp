# -*- coding: utf-8 -*-
# FreeCAD MCP — handlers.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""Action handlers. Units: mm (FreeCAD default). Coordinate system: global."""

import os

import FreeCAD as App
import Part


def _get_doc(params):
    name = (params or {}).get("document")
    doc = App.getDocument(name) if name else App.ActiveDocument
    if doc is None:
        raise LookupError("No active document")
    return doc


def _obj_info(o):
    info = {"name": o.Name, "label": o.Label, "type": o.TypeId}
    try:
        p = o.Placement
        info["placement"] = {
            "base": {"x": p.Base.x, "y": p.Base.y, "z": p.Base.z},
            "rot": {"qx": p.Rotation.Q[0], "qy": p.Rotation.Q[1],
                    "qz": p.Rotation.Q[2], "qw": p.Rotation.Q[3]},
        }
    except Exception:
        pass
    return info


def h_ping(params):
    return {
        "status": "ok",
        "freecad": {
            "version": ".".join(App.Version()[0:3]),
            "build": App.Version()[3] if len(App.Version()) > 3 else None,
        },
    }


def h_list_documents(params):
    active = App.ActiveDocument.Name if App.ActiveDocument else None
    docs = [{"name": d.Name, "label": d.Label} for d in App.listDocuments().values()]
    return {"active": active, "documents": docs}


def h_new_document(params):
    name = (params or {}).get("name") or "Unnamed"
    doc = App.newDocument(name)
    return {"document": {"name": doc.Name, "label": doc.Label}}


def h_list_objects(params):
    doc = _get_doc(params)
    return {"document": doc.Name, "objects": [_obj_info(o) for o in doc.Objects]}


def h_set_active_document(params):
    name = (params or {}).get("name")
    if not name:
        raise ValueError("Missing 'name'")
    doc = App.getDocument(name)
    if doc is None:
        raise LookupError(f"Document not found: {name}")
    App.setActiveDocument(name)
    return {"active": name}


def h_open_document(params):
    path = (params or {}).get("path")
    if not path:
        raise ValueError("Missing 'path'")
    if not os.path.isfile(path):
        raise LookupError(f"File not found: {path}")
    doc = App.openDocument(path)
    return {"document": {"name": doc.Name, "label": doc.Label, "path": path}}


def h_save_document(params):
    params = params or {}
    doc = _get_doc(params)
    path = params.get("path")
    if path:
        doc.saveAs(path)
    else:
        doc.save()
    return {"document": doc.Name, "path": doc.FileName}


def h_recompute(params):
    doc = _get_doc(params)
    doc.recompute()
    return {"document": doc.Name, "ok": True}


def h_create_box(params):
    params = params or {}
    doc = _get_doc(params)
    length = float(params.get("length", 10.0))
    width = float(params.get("width", 10.0))
    height = float(params.get("height", 10.0))
    name = params.get("name", "Box")
    obj = doc.addObject("Part::Box", name)
    obj.Length = length
    obj.Width = width
    obj.Height = height
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_create_cylinder(params):
    params = params or {}
    doc = _get_doc(params)
    radius = float(params.get("radius", 5.0))
    height = float(params.get("height", 10.0))
    name = params.get("name", "Cylinder")
    obj = doc.addObject("Part::Cylinder", name)
    obj.Radius = radius
    obj.Height = height
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def _boolean(doc, type_id, base_name, tool_name, name):
    base = doc.getObject(base_name)
    tool = doc.getObject(tool_name)
    if base is None or tool is None:
        raise LookupError(f"Base or tool not found: {base_name}, {tool_name}")
    obj = doc.addObject(type_id, name)
    obj.Base = base
    obj.Tool = tool
    doc.recompute()
    return obj


def h_boolean_cut(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _boolean(doc, "Part::Cut",
                   params.get("base"), params.get("tool"),
                   params.get("name", "Cut"))
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_boolean_fuse(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _boolean(doc, "Part::Fuse",
                   params.get("base"), params.get("tool"),
                   params.get("name", "Fusion"))
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_boolean_common(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _boolean(doc, "Part::Common",
                   params.get("base"), params.get("tool"),
                   params.get("name", "Common"))
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_export(params):
    params = params or {}
    doc = _get_doc(params)
    path = params.get("path")
    if not path:
        raise ValueError("Missing 'path'")
    obj_names = params.get("objects") or []
    if obj_names:
        objs = [doc.getObject(n) for n in obj_names]
        if any(o is None for o in objs):
            raise LookupError("One or more objects not found")
    else:
        objs = list(doc.Objects)
    Part.export(objs, path)
    return {"path": path, "objects": [o.Name for o in objs]}


def h_delete_object(params):
    params = params or {}
    doc = _get_doc(params)
    name = params.get("name")
    if not name:
        raise ValueError("Missing 'name'")
    if doc.getObject(name) is None:
        raise LookupError(f"Object not found: {name}")
    doc.removeObject(name)
    doc.recompute()
    return {"document": doc.Name, "removed": name}


def _get_obj(doc, name):
    o = doc.getObject(name)
    if o is None:
        raise LookupError(f"Object not found: {name}")
    return o


def _vec(d):
    return App.Vector(float(d.get("x", 0)), float(d.get("y", 0)), float(d.get("z", 0)))


def _rotation(d):
    if d is None:
        return App.Rotation()
    if "axis" in d and "angle_deg" in d:
        return App.Rotation(_vec(d["axis"]), float(d["angle_deg"]))
    if "qw" in d:
        return App.Rotation(float(d.get("qx", 0)), float(d.get("qy", 0)),
                            float(d.get("qz", 0)), float(d.get("qw", 1)))
    return App.Rotation()


def h_create_sphere(params):
    params = params or {}
    doc = _get_doc(params)
    obj = doc.addObject("Part::Sphere", params.get("name", "Sphere"))
    obj.Radius = float(params.get("radius", 5.0))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_create_cone(params):
    params = params or {}
    doc = _get_doc(params)
    obj = doc.addObject("Part::Cone", params.get("name", "Cone"))
    obj.Radius1 = float(params.get("radius1", 5.0))
    obj.Radius2 = float(params.get("radius2", 0.0))
    obj.Height = float(params.get("height", 10.0))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_create_torus(params):
    params = params or {}
    doc = _get_doc(params)
    obj = doc.addObject("Part::Torus", params.get("name", "Torus"))
    obj.Radius1 = float(params.get("radius1", 10.0))
    obj.Radius2 = float(params.get("radius2", 2.0))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_create_polygon_prism(params):
    """Regular N-sided prism. Useful for hex nuts (sides=6), bolts, etc."""
    params = params or {}
    doc = _get_doc(params)
    sides = int(params.get("sides", 6))
    radius = float(params.get("radius", 5.0))  # circunscrito
    height = float(params.get("height", 5.0))
    name = params.get("name", "Prism")
    import math
    poly = Part.makePolygon([
        App.Vector(radius * math.cos(2 * math.pi * i / sides),
                   radius * math.sin(2 * math.pi * i / sides), 0)
        for i in list(range(sides)) + [0]
    ])
    face = Part.Face(poly)
    solid = face.extrude(App.Vector(0, 0, height))
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = solid
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_set_placement(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    base = _vec(params.get("base", {"x": 0, "y": 0, "z": 0}))
    rot = _rotation(params.get("rot"))
    obj.Placement = App.Placement(base, rot)
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_translate(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    d = _vec(params.get("delta", {"x": 0, "y": 0, "z": 0}))
    p = obj.Placement
    obj.Placement = App.Placement(p.Base + d, p.Rotation)
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_rotate(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    axis = _vec(params.get("axis", {"x": 0, "y": 0, "z": 1}))
    angle = float(params.get("angle_deg", 0))
    center = _vec(params.get("center", {"x": 0, "y": 0, "z": 0}))
    rot = App.Rotation(axis, angle)
    p = obj.Placement
    new_base = rot.multVec(p.Base - center) + center
    obj.Placement = App.Placement(new_base, rot.multiply(p.Rotation))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_extrude(params):
    """Extrude a face/shape along a direction vector."""
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    dir_v = _vec(params.get("direction", {"x": 0, "y": 0, "z": 10}))
    name = params.get("name", "Extrude")
    obj = doc.addObject("Part::Extrusion", name)
    obj.Base = src
    obj.Dir = dir_v
    obj.Solid = bool(params.get("solid", True))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_revolve(params):
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    axis = _vec(params.get("axis", {"x": 0, "y": 0, "z": 1}))
    angle = float(params.get("angle_deg", 360.0))
    base = _vec(params.get("base", {"x": 0, "y": 0, "z": 0}))
    name = params.get("name", "Revolve")
    obj = doc.addObject("Part::Revolution", name)
    obj.Source = src
    obj.Axis = axis
    obj.Base = base
    obj.Angle = angle
    obj.Solid = bool(params.get("solid", True))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_fillet(params):
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    radius = float(params.get("radius", 1.0))
    name = params.get("name", "Fillet")
    obj = doc.addObject("Part::Fillet", name)
    obj.Base = src
    edges = []
    if params.get("edges"):
        edges = [(int(i), radius, radius) for i in params["edges"]]
    else:
        edges = [(i + 1, radius, radius) for i in range(len(src.Shape.Edges))]
    obj.Edges = edges
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_chamfer(params):
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    size = float(params.get("size", 1.0))
    name = params.get("name", "Chamfer")
    obj = doc.addObject("Part::Chamfer", name)
    obj.Base = src
    if params.get("edges"):
        edges = [(int(i), size, size) for i in params["edges"]]
    else:
        edges = [(i + 1, size, size) for i in range(len(src.Shape.Edges))]
    obj.Edges = edges
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_mirror(params):
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    normal = _vec(params.get("normal", {"x": 0, "y": 0, "z": 1}))
    base = _vec(params.get("base", {"x": 0, "y": 0, "z": 0}))
    name = params.get("name", "Mirror")
    obj = doc.addObject("Part::Mirroring", name)
    obj.Source = src
    obj.Normal = normal
    obj.Base = base
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_get_object(params):
    doc = _get_doc(params)
    obj = _get_obj(doc, (params or {}).get("name"))
    props = {}
    for p in obj.PropertiesList:
        try:
            v = getattr(obj, p)
            # Serializar solo primitivos
            if isinstance(v, (int, float, bool, str)) or v is None:
                props[p] = v
            elif hasattr(v, "x") and hasattr(v, "y") and hasattr(v, "z"):
                props[p] = {"x": v.x, "y": v.y, "z": v.z}
            else:
                props[p] = str(v)
        except Exception:
            pass
    info = _obj_info(obj)
    info["properties"] = props
    return {"document": doc.Name, "object": info}


def h_set_property(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    prop = params["property"]
    value = params["value"]
    if not hasattr(obj, prop):
        raise LookupError(f"Property not found: {prop}")
    setattr(obj, prop, value)
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj), "property": prop}


def h_set_label(params):
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    obj.Label = params["label"]
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_set_visibility(params):
    """Requiere GUI."""
    import FreeCADGui as Gui
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    vp = Gui.getDocument(doc.Name).getObject(obj.Name)
    vp.Visibility = bool(params.get("visible", True))
    return {"document": doc.Name, "name": obj.Name, "visible": vp.Visibility}


def h_duplicate(params):
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["name"])
    new_name = params.get("new_name", src.Name + "_copy")
    obj = doc.addObject("Part::Feature", new_name)
    obj.Shape = src.Shape.copy()
    obj.Placement = src.Placement
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_import_file(params):
    params = params or {}
    doc = _get_doc(params)
    path = params.get("path")
    if not path or not os.path.isfile(path):
        raise LookupError(f"File not found: {path}")
    before = set(o.Name for o in doc.Objects)
    Part.insert(path, doc.Name)
    imported = [_obj_info(o) for o in doc.Objects if o.Name not in before]
    return {"document": doc.Name, "imported": imported}


def h_run_python(params):
    """Ejecuta Python arbitrario en contexto FreeCAD. Guardrail env var."""
    if os.environ.get("FREECAD_ALLOW_RUN_PYTHON", "false").lower() != "true":
        raise PermissionError("run_python disabled. Set FREECAD_ALLOW_RUN_PYTHON=true to enable.")
    code = (params or {}).get("code")
    if not code:
        raise ValueError("Missing 'code'")
    local_ns = {"App": App, "Part": Part, "doc": App.ActiveDocument}
    try:
        import FreeCADGui as Gui
        local_ns["Gui"] = Gui
    except Exception:
        pass
    exec(compile(code, "<run_python>", "exec"), local_ns, local_ns)
    return {"ok": True, "result": str(local_ns.get("result", None))}


# ==================== SKETCHER ====================

def h_create_sketch(params):
    """Crea sketch en plano base (XY/XZ/YZ)."""
    params = params or {}
    doc = _get_doc(params)
    name = params.get("name", "Sketch")
    plane = params.get("plane", "XY").upper()
    rotations = {
        "XY": App.Rotation(0, 0, 0, 1),
        "XZ": App.Rotation(App.Vector(1, 0, 0), 90),
        "YZ": App.Rotation(App.Vector(0, 1, 0), 90),
    }
    if plane not in rotations:
        raise ValueError(f"plane must be XY|XZ|YZ, got: {plane}")
    sketch = doc.addObject("Sketcher::SketchObject", name)
    sketch.Placement = App.Placement(
        _vec(params.get("base", {"x": 0, "y": 0, "z": 0})),
        rotations[plane])
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(sketch)}


def h_sketch_add_line(params):
    import Sketcher
    params = params or {}
    doc = _get_doc(params)
    sk = _get_obj(doc, params["sketch"])
    x1, y1 = float(params["x1"]), float(params["y1"])
    x2, y2 = float(params["x2"]), float(params["y2"])
    idx = sk.addGeometry(
        Part.LineSegment(App.Vector(x1, y1, 0), App.Vector(x2, y2, 0)), False)
    doc.recompute()
    return {"document": doc.Name, "sketch": sk.Name, "geometry_index": idx}


def h_sketch_add_circle(params):
    import Sketcher
    params = params or {}
    doc = _get_doc(params)
    sk = _get_obj(doc, params["sketch"])
    cx, cy = float(params["cx"]), float(params["cy"])
    r = float(params["radius"])
    idx = sk.addGeometry(
        Part.Circle(App.Vector(cx, cy, 0), App.Vector(0, 0, 1), r), False)
    doc.recompute()
    return {"document": doc.Name, "sketch": sk.Name, "geometry_index": idx}


def h_sketch_add_arc(params):
    params = params or {}
    doc = _get_doc(params)
    sk = _get_obj(doc, params["sketch"])
    import math
    cx, cy = float(params["cx"]), float(params["cy"])
    r = float(params["radius"])
    a1 = math.radians(float(params.get("start_deg", 0)))
    a2 = math.radians(float(params.get("end_deg", 90)))
    arc = Part.ArcOfCircle(
        Part.Circle(App.Vector(cx, cy, 0), App.Vector(0, 0, 1), r), a1, a2)
    idx = sk.addGeometry(arc, False)
    doc.recompute()
    return {"document": doc.Name, "sketch": sk.Name, "geometry_index": idx}


def h_sketch_add_rectangle(params):
    """Add 4 lines forming a closed rectangle to the sketch."""
    params = params or {}
    doc = _get_doc(params)
    sk = _get_obj(doc, params["sketch"])
    x1, y1 = float(params["x1"]), float(params["y1"])
    x2, y2 = float(params["x2"]), float(params["y2"])
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    idxs = []
    for i in range(4):
        a = pts[i]; b = pts[(i + 1) % 4]
        idxs.append(sk.addGeometry(
            Part.LineSegment(App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0)), False))
    doc.recompute()
    return {"document": doc.Name, "sketch": sk.Name, "geometry_indices": idxs}


def h_sketch_add_constraint(params):
    """Basic sketch constraint: 'horizontal'|'vertical'|'distance'|'radius'."""
    import Sketcher
    params = params or {}
    doc = _get_doc(params)
    sk = _get_obj(doc, params["sketch"])
    ctype = params["type"].lower()
    geo = int(params.get("geo_index", -1))
    if ctype == "horizontal":
        idx = sk.addConstraint(Sketcher.Constraint("Horizontal", geo))
    elif ctype == "vertical":
        idx = sk.addConstraint(Sketcher.Constraint("Vertical", geo))
    elif ctype == "distance":
        idx = sk.addConstraint(Sketcher.Constraint("Distance", geo, float(params["value"])))
    elif ctype == "radius":
        idx = sk.addConstraint(Sketcher.Constraint("Radius", geo, float(params["value"])))
    else:
        raise ValueError(f"Unsupported constraint: {ctype}")
    doc.recompute()
    return {"document": doc.Name, "sketch": sk.Name, "constraint_index": idx}


# ==================== PARTDESIGN ====================

def h_create_body(params):
    params = params or {}
    doc = _get_doc(params)
    name = params.get("name", "Body")
    body = doc.addObject("PartDesign::Body", name)
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(body)}


def h_pad(params):
    """Pad (extrude) de un sketch dentro de un Body."""
    params = params or {}
    doc = _get_doc(params)
    body = _get_obj(doc, params["body"])
    sketch = _get_obj(doc, params["sketch"])
    if sketch not in body.Group:
        body.addObject(sketch)
    length = float(params.get("length", 10.0))
    name = params.get("name", "Pad")
    pad = body.newObject("PartDesign::Pad", name)
    pad.Profile = sketch
    pad.Length = length
    pad.Reversed = bool(params.get("reversed", False))
    pad.Midplane = bool(params.get("midplane", False))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(pad)}


def h_pocket(params):
    params = params or {}
    doc = _get_doc(params)
    body = _get_obj(doc, params["body"])
    sketch = _get_obj(doc, params["sketch"])
    if sketch not in body.Group:
        body.addObject(sketch)
    length = float(params.get("length", 10.0))
    name = params.get("name", "Pocket")
    poc = body.newObject("PartDesign::Pocket", name)
    poc.Profile = sketch
    poc.Length = length
    poc.Reversed = bool(params.get("reversed", False))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(poc)}


# ==================== ARRAYS ====================

def h_linear_array(params):
    """Linear pattern of N copies along XYZ delta."""
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    count = int(params.get("count", 2))
    dx = float(params.get("dx", 10.0))
    dy = float(params.get("dy", 0.0))
    dz = float(params.get("dz", 0.0))
    created = []
    base_name = params.get("name", src.Name + "_arr")
    for i in range(1, count):
        new = doc.addObject("Part::Feature", f"{base_name}_{i}")
        new.Shape = src.Shape.copy()
        p = src.Placement
        new.Placement = App.Placement(
            p.Base + App.Vector(dx * i, dy * i, dz * i), p.Rotation)
        created.append(new.Name)
    doc.recompute()
    return {"document": doc.Name, "source": src.Name, "created": created}


def h_polar_array(params):
    """Polar pattern of N copies around an axis."""
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    count = int(params.get("count", 4))
    total_angle = float(params.get("total_angle_deg", 360.0))
    axis = _vec(params.get("axis", {"x": 0, "y": 0, "z": 1}))
    center = _vec(params.get("center", {"x": 0, "y": 0, "z": 0}))
    base_name = params.get("name", src.Name + "_parr")
    step = total_angle / count if total_angle != 360.0 else total_angle / count
    created = []
    for i in range(1, count):
        new = doc.addObject("Part::Feature", f"{base_name}_{i}")
        new.Shape = src.Shape.copy()
        rot = App.Rotation(axis, step * i)
        p = src.Placement
        new_base = rot.multVec(p.Base - center) + center
        new.Placement = App.Placement(new_base, rot.multiply(p.Rotation))
        created.append(new.Name)
    doc.recompute()
    return {"document": doc.Name, "source": src.Name, "created": created}


# ==================== GUI ====================

def h_gui_screenshot(params):
    import FreeCADGui as Gui
    params = params or {}
    path = params.get("path")
    if not path:
        raise ValueError("Missing 'path'")
    w = int(params.get("width", 1280))
    h = int(params.get("height", 720))
    Gui.ActiveDocument.ActiveView.saveImage(path, w, h, "Current")
    return {"path": path, "width": w, "height": h}


def h_gui_set_view(params):
    """Set standard view: iso|top|bottom|front|back|left|right."""
    import FreeCADGui as Gui
    params = params or {}
    view = (params.get("view") or "iso").lower()
    v = Gui.ActiveDocument.ActiveView
    mapping = {
        "iso": v.viewIsometric,
        "axometric": v.viewIsometric,
        "top": v.viewTop,
        "bottom": v.viewBottom,
        "front": v.viewFront,
        "back": v.viewRear,
        "left": v.viewLeft,
        "right": v.viewRight,
    }
    if view not in mapping:
        raise ValueError(f"Unknown view: {view}")
    mapping[view]()
    return {"view": view}


def h_gui_fit_all(params):
    import FreeCADGui as Gui
    Gui.SendMsgToActiveView("ViewFit")
    return {"ok": True}


# ==================== MEASUREMENTS ====================

def h_get_bounding_box(params):
    doc = _get_doc(params)
    obj = _get_obj(doc, (params or {}).get("name"))
    bb = obj.Shape.BoundBox
    return {"name": obj.Name,
            "min": {"x": bb.XMin, "y": bb.YMin, "z": bb.ZMin},
            "max": {"x": bb.XMax, "y": bb.YMax, "z": bb.ZMax},
            "size": {"x": bb.XLength, "y": bb.YLength, "z": bb.ZLength}}


def h_get_volume(params):
    doc = _get_doc(params)
    obj = _get_obj(doc, (params or {}).get("name"))
    return {"name": obj.Name, "volume": obj.Shape.Volume}


def h_get_area(params):
    doc = _get_doc(params)
    obj = _get_obj(doc, (params or {}).get("name"))
    return {"name": obj.Name, "area": obj.Shape.Area}


def h_get_distance(params):
    """Distancia entre dos puntos o dos objetos (centros)."""
    params = params or {}
    if "a" in params and "b" in params:
        a = _vec(params["a"]); b = _vec(params["b"])
        return {"distance": (b - a).Length}
    doc = _get_doc(params)
    o1 = _get_obj(doc, params["name1"])
    o2 = _get_obj(doc, params["name2"])
    d, _, _ = o1.Shape.distToShape(o2.Shape)
    return {"name1": o1.Name, "name2": o2.Name, "distance": d}


# ==================== MESH ====================

def h_shape_to_mesh(params):
    import Mesh
    import MeshPart
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    linear_def = float(params.get("linear_deflection", 0.1))
    angular_def = float(params.get("angular_deflection", 0.523599))  # 30°
    name = params.get("name", src.Name + "_mesh")
    mesh = MeshPart.meshFromShape(
        Shape=src.Shape,
        LinearDeflection=linear_def,
        AngularDeflection=angular_def,
        Relative=False,
    )
    obj = doc.addObject("Mesh::Feature", name)
    obj.Mesh = mesh
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_export_stl(params):
    import Mesh
    params = params or {}
    doc = _get_doc(params)
    path = params.get("path")
    if not path:
        raise ValueError("Missing 'path'")
    names = params.get("objects") or []
    objs = [_get_obj(doc, n) for n in names] if names else list(doc.Objects)
    Mesh.export(objs, path)
    return {"path": path, "objects": [o.Name for o in objs]}


# ==================== TECHDRAW ====================

def h_techdraw_create_page(params):
    params = params or {}
    doc = _get_doc(params)
    name = params.get("name", "Page")
    template_path = params.get("template")
    page = doc.addObject("TechDraw::DrawPage", name)
    tmpl = doc.addObject("TechDraw::DrawSVGTemplate", name + "_Tmpl")
    if template_path and os.path.isfile(template_path):
        tmpl.Template = template_path
    else:
        # Intenta template por defecto
        import FreeCAD as _App
        default_tmpl = os.path.join(_App.getResourceDir(), "Mod", "TechDraw",
                                    "Templates", "A4_LandscapeTD.svg")
        if os.path.isfile(default_tmpl):
            tmpl.Template = default_tmpl
    page.Template = tmpl
    doc.recompute()
    return {"document": doc.Name, "page": page.Name, "template": tmpl.Name}


def h_techdraw_add_view(params):
    params = params or {}
    doc = _get_doc(params)
    page = _get_obj(doc, params["page"])
    src = _get_obj(doc, params["source"])
    name = params.get("name", "View")
    view = doc.addObject("TechDraw::DrawViewPart", name)
    view.Source = [src]
    view.Direction = _vec(params.get("direction", {"x": 0, "y": 0, "z": 1}))
    view.Scale = float(params.get("scale", 1.0))
    view.X = float(params.get("x", 100.0))
    view.Y = float(params.get("y", 100.0))
    page.addView(view)
    doc.recompute()
    return {"document": doc.Name, "view": view.Name}


# ==================== DRAFT ====================

def h_draft_line(params):
    import Draft
    params = params or {}
    doc = _get_doc(params)
    p1 = _vec(params["p1"]); p2 = _vec(params["p2"])
    obj = Draft.make_line(p1, p2)
    if params.get("name"):
        obj.Label = params["name"]
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_draft_dimension(params):
    import Draft
    params = params or {}
    doc = _get_doc(params)
    p1 = _vec(params["p1"]); p2 = _vec(params["p2"])
    p3 = _vec(params.get("p_text", params["p2"]))
    dim = Draft.make_linear_dimension(p1, p2, p3)
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(dim)}


def h_draft_text(params):
    import Draft
    params = params or {}
    doc = _get_doc(params)
    pos = _vec(params.get("position", {"x": 0, "y": 0, "z": 0}))
    text = params.get("text", "Text")
    obj = Draft.make_text([text], point=pos)
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


# ==================== ASSEMBLY (basic attach) ====================

def h_assembly_attach(params):
    """Fix object placement relative to a parent object (basic attach)."""
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    parent = _get_obj(doc, params["parent"])
    offset = _vec(params.get("offset", {"x": 0, "y": 0, "z": 0}))
    rot = _rotation(params.get("rot"))
    obj.Placement = parent.Placement.multiply(App.Placement(offset, rot))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj), "parent": parent.Name}


# ==================== FEM ====================

def h_fem_create_analysis(params):
    from femtools import ccxtools  # noqa: F401
    import ObjectsFem
    params = params or {}
    doc = _get_doc(params)
    name = params.get("name", "Analysis")
    analysis = ObjectsFem.makeAnalysis(doc, name)
    solver = ObjectsFem.makeSolverCalculixCcxTools(doc, "CalculiX")
    analysis.addObject(solver)
    doc.recompute()
    return {"document": doc.Name, "analysis": analysis.Name, "solver": solver.Name}


def h_fem_add_material(params):
    import ObjectsFem
    params = params or {}
    doc = _get_doc(params)
    analysis = _get_obj(doc, params["analysis"])
    preset = params.get("material", "Steel-Generic")
    mat = ObjectsFem.makeMaterialSolid(doc, params.get("name", "Material"))
    mat_dict = mat.Material
    mat_dict["Name"] = preset
    mat.Material = mat_dict
    analysis.addObject(mat)
    doc.recompute()
    return {"document": doc.Name, "material": mat.Name}


def h_fem_add_fixed(params):
    import ObjectsFem
    params = params or {}
    doc = _get_doc(params)
    analysis = _get_obj(doc, params["analysis"])
    c = ObjectsFem.makeConstraintFixed(doc, params.get("name", "Fixed"))
    if params.get("references"):
        src = _get_obj(doc, params["references"]["object"])
        faces = params["references"].get("faces", [])
        c.References = [(src, tuple(f"Face{i}" for i in faces))]
    analysis.addObject(c)
    doc.recompute()
    return {"document": doc.Name, "constraint": c.Name}


def h_fem_add_force(params):
    import ObjectsFem
    params = params or {}
    doc = _get_doc(params)
    analysis = _get_obj(doc, params["analysis"])
    c = ObjectsFem.makeConstraintForce(doc, params.get("name", "Force"))
    c.Force = float(params.get("force", 1.0))
    d = _vec(params.get("direction", {"x": 0, "y": 0, "z": -1}))
    # Assigning direction requires a geometric reference; magnitude only here.
    if params.get("references"):
        src = _get_obj(doc, params["references"]["object"])
        faces = params["references"].get("faces", [])
        c.References = [(src, tuple(f"Face{i}" for i in faces))]
    analysis.addObject(c)
    doc.recompute()
    return {"document": doc.Name, "constraint": c.Name, "force": c.Force}


# ==================== CAM / PATH ====================

def h_cam_create_job(params):
    from Path.Main import Job as PathJob
    params = params or {}
    doc = _get_doc(params)
    src = _get_obj(doc, params["source"])
    job = PathJob.Create(params.get("name", "Job"), [src])
    doc.recompute()
    return {"document": doc.Name, "job": job.Name}


def h_cam_profile(params):
    import PathScripts.PathProfile as PathProfile
    params = params or {}
    doc = _get_doc(params)
    job = _get_obj(doc, params["job"])
    op = PathProfile.Create(params.get("name", "Profile"))
    job.Proxy.addOperation(op, job)
    doc.recompute()
    return {"document": doc.Name, "operation": op.Name}


# ==================== SPREADSHEET ====================

def h_spreadsheet_create(params):
    params = params or {}
    doc = _get_doc(params)
    sheet = doc.addObject("Spreadsheet::Sheet", params.get("name", "Spreadsheet"))
    doc.recompute()
    return {"document": doc.Name, "sheet": sheet.Name}


def h_spreadsheet_set(params):
    params = params or {}
    doc = _get_doc(params)
    sheet = _get_obj(doc, params["sheet"])
    cell = params["cell"]
    sheet.set(cell, str(params["value"]))
    if params.get("alias"):
        sheet.setAlias(cell, params["alias"])
    doc.recompute()
    return {"document": doc.Name, "sheet": sheet.Name, "cell": cell}


def h_spreadsheet_get(params):
    params = params or {}
    doc = _get_doc(params)
    sheet = _get_obj(doc, params["sheet"])
    cell = params["cell"]
    return {"sheet": sheet.Name, "cell": cell,
            "contents": sheet.getContents(cell),
            "value": str(sheet.get(cell))}


# ==================== MATERIAL / COLOR ====================

def h_set_color(params):
    import FreeCADGui as Gui
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    r = float(params.get("r", 0.8))
    g = float(params.get("g", 0.8))
    b = float(params.get("b", 0.8))
    vp = Gui.getDocument(doc.Name).getObject(obj.Name)
    vp.ShapeColor = (r, g, b)
    return {"document": doc.Name, "name": obj.Name, "color": [r, g, b]}


def h_set_transparency(params):
    import FreeCADGui as Gui
    params = params or {}
    doc = _get_doc(params)
    obj = _get_obj(doc, params["name"])
    t = int(params.get("transparency", 0))
    vp = Gui.getDocument(doc.Name).getObject(obj.Name)
    vp.Transparency = max(0, min(100, t))
    return {"document": doc.Name, "name": obj.Name, "transparency": vp.Transparency}


# ==================== LOFT / SWEEP ====================

def h_loft(params):
    params = params or {}
    doc = _get_doc(params)
    sections = params.get("sections", [])
    if len(sections) < 2:
        raise ValueError("Loft requires >=2 sections")
    objs = [_get_obj(doc, n) for n in sections]
    obj = doc.addObject("Part::Loft", params.get("name", "Loft"))
    obj.Sections = objs
    obj.Solid = bool(params.get("solid", True))
    obj.Ruled = bool(params.get("ruled", False))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


def h_sweep(params):
    params = params or {}
    doc = _get_doc(params)
    profile = _get_obj(doc, params["profile"])
    path = _get_obj(doc, params["path"])
    obj = doc.addObject("Part::Sweep", params.get("name", "Sweep"))
    obj.Sections = [profile]
    obj.Spine = path
    obj.Solid = bool(params.get("solid", True))
    obj.Frenet = bool(params.get("frenet", False))
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(obj)}


# ==================== HOLE (PartDesign) ====================

def h_hole(params):
    """PartDesign Hole in a Body. Requires a sketch with circle(s) as the profile."""
    params = params or {}
    doc = _get_doc(params)
    body = _get_obj(doc, params["body"])
    sketch = _get_obj(doc, params["sketch"])
    if sketch not in body.Group:
        body.addObject(sketch)
    hole = body.newObject("PartDesign::Hole", params.get("name", "Hole"))
    hole.Profile = sketch
    hole.Diameter = float(params.get("diameter", 6.0))
    hole.Depth = float(params.get("depth", 10.0))
    if params.get("threaded"):
        hole.Threaded = True
        if params.get("thread_type"):
            hole.ThreadType = params["thread_type"]  # p.ej. 'ISOMetricProfile'
    doc.recompute()
    return {"document": doc.Name, "object": _obj_info(hole)}


# ==================== SKETCH CONSTRAINTS AVANZADOS ====================

def h_sketch_add_constraint_advanced(params):
    """parallel|perpendicular|tangent|equal|symmetric|coincident|point_on_object."""
    import Sketcher
    params = params or {}
    doc = _get_doc(params)
    sk = _get_obj(doc, params["sketch"])
    ctype = params["type"].lower()
    g1 = int(params.get("geo1", -1))
    g2 = int(params.get("geo2", -1))
    v1 = int(params.get("vertex1", 1))
    v2 = int(params.get("vertex2", 1))
    mapping = {
        "parallel": lambda: Sketcher.Constraint("Parallel", g1, g2),
        "perpendicular": lambda: Sketcher.Constraint("Perpendicular", g1, g2),
        "tangent": lambda: Sketcher.Constraint("Tangent", g1, g2),
        "equal": lambda: Sketcher.Constraint("Equal", g1, g2),
        "coincident": lambda: Sketcher.Constraint("Coincident", g1, v1, g2, v2),
        "point_on_object": lambda: Sketcher.Constraint("PointOnObject", g1, v1, g2),
        "symmetric": lambda: Sketcher.Constraint("Symmetric", g1, v1, g2, v2,
                                                 int(params.get("geo_sym", -1))),
    }
    if ctype not in mapping:
        raise ValueError(f"Unsupported constraint: {ctype}")
    idx = sk.addConstraint(mapping[ctype]())
    doc.recompute()
    return {"document": doc.Name, "sketch": sk.Name, "constraint_index": idx}


# ==================== GUI SELECTION ====================

def h_gui_select(params):
    import FreeCADGui as Gui
    params = params or {}
    doc = _get_doc(params)
    names = params.get("objects", [])
    clear = bool(params.get("clear", True))
    if clear:
        Gui.Selection.clearSelection()
    for n in names:
        Gui.Selection.addSelection(doc, n)
    return {"document": doc.Name, "selected": names}


def h_gui_clear_selection(params):
    import FreeCADGui as Gui
    Gui.Selection.clearSelection()
    return {"ok": True}


def h_gui_get_selection(params):
    import FreeCADGui as Gui
    sel = [{"document": o.Document.Name, "name": o.Name, "label": o.Label}
           for o in Gui.Selection.getSelection()]
    return {"selection": sel}


HANDLERS = {
    "ping": h_ping,
    "list_documents": h_list_documents,
    "new_document": h_new_document,
    "list_objects": h_list_objects,
    "set_active_document": h_set_active_document,
    "open_document": h_open_document,
    "save_document": h_save_document,
    "recompute": h_recompute,
    "create_box": h_create_box,
    "create_cylinder": h_create_cylinder,
    "boolean_cut": h_boolean_cut,
    "boolean_fuse": h_boolean_fuse,
    "boolean_common": h_boolean_common,
    "export": h_export,
    "delete_object": h_delete_object,
    "create_sphere": h_create_sphere,
    "create_cone": h_create_cone,
    "create_torus": h_create_torus,
    "create_polygon_prism": h_create_polygon_prism,
    "set_placement": h_set_placement,
    "translate": h_translate,
    "rotate": h_rotate,
    "extrude": h_extrude,
    "revolve": h_revolve,
    "fillet": h_fillet,
    "chamfer": h_chamfer,
    "mirror": h_mirror,
    "get_object": h_get_object,
    "set_property": h_set_property,
    "set_label": h_set_label,
    "set_visibility": h_set_visibility,
    "duplicate": h_duplicate,
    "import_file": h_import_file,
    "run_python": h_run_python,
    # Sketcher
    "create_sketch": h_create_sketch,
    "sketch_add_line": h_sketch_add_line,
    "sketch_add_circle": h_sketch_add_circle,
    "sketch_add_arc": h_sketch_add_arc,
    "sketch_add_rectangle": h_sketch_add_rectangle,
    "sketch_add_constraint": h_sketch_add_constraint,
    # PartDesign
    "create_body": h_create_body,
    "pad": h_pad,
    "pocket": h_pocket,
    # Arrays
    "linear_array": h_linear_array,
    "polar_array": h_polar_array,
    # GUI
    "gui_screenshot": h_gui_screenshot,
    "gui_set_view": h_gui_set_view,
    "gui_fit_all": h_gui_fit_all,
    # Measurements
    "get_bounding_box": h_get_bounding_box,
    "get_volume": h_get_volume,
    "get_area": h_get_area,
    "get_distance": h_get_distance,
    # Mesh
    "shape_to_mesh": h_shape_to_mesh,
    "export_stl": h_export_stl,
    # TechDraw
    "techdraw_create_page": h_techdraw_create_page,
    "techdraw_add_view": h_techdraw_add_view,
    # Draft
    "draft_line": h_draft_line,
    "draft_dimension": h_draft_dimension,
    "draft_text": h_draft_text,
    # Assembly
    "assembly_attach": h_assembly_attach,
    # FEM
    "fem_create_analysis": h_fem_create_analysis,
    "fem_add_material": h_fem_add_material,
    "fem_add_fixed": h_fem_add_fixed,
    "fem_add_force": h_fem_add_force,
    # CAM
    "cam_create_job": h_cam_create_job,
    "cam_profile": h_cam_profile,
    # Spreadsheet
    "spreadsheet_create": h_spreadsheet_create,
    "spreadsheet_set": h_spreadsheet_set,
    "spreadsheet_get": h_spreadsheet_get,
    # Color
    "set_color": h_set_color,
    "set_transparency": h_set_transparency,
    # Loft/Sweep
    "loft": h_loft,
    "sweep": h_sweep,
    # Hole
    "hole": h_hole,
    # Sketch constraints avanzados
    "sketch_add_constraint_advanced": h_sketch_add_constraint_advanced,
    # GUI selection
    "gui_select": h_gui_select,
    "gui_clear_selection": h_gui_clear_selection,
    "gui_get_selection": h_gui_get_selection,
}
