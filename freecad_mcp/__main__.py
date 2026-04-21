# -*- coding: utf-8 -*-
# FreeCAD MCP — __main__.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""MCP server stdio para FreeCAD. Ejecutar: python -m freecad_mcp"""

import json

from mcp.server.fastmcp import FastMCP

from .bridge_client import CLIENT

mcp = FastMCP("freecad")


def _call(action: str, params: dict | None = None) -> str:
    try:
        resp = CLIENT.call(action, params or {})
    except Exception as e:
        return json.dumps({"ok": False, "error": {"code": "NOT_CONNECTED", "message": str(e)}})
    return json.dumps(resp, ensure_ascii=False)


@mcp.tool()
def freecad_ping() -> str:
    """Verifica conexión con FreeCAD. Devuelve versión."""
    return _call("ping")


@mcp.tool()
def freecad_list_documents() -> str:
    """Lista documentos abiertos en FreeCAD y el documento activo."""
    return _call("list_documents")


@mcp.tool()
def freecad_new_document(name: str = "Unnamed") -> str:
    """Crea un nuevo documento FreeCAD con el nombre dado."""
    return _call("new_document", {"name": name})


@mcp.tool()
def freecad_list_objects(document: str | None = None) -> str:
    """Lista objetos de un documento (usa activo si no se especifica)."""
    params = {"document": document} if document else {}
    return _call("list_objects", params)


@mcp.tool()
def freecad_set_active_document(name: str) -> str:
    """Establece el documento activo por nombre."""
    return _call("set_active_document", {"name": name})


@mcp.tool()
def freecad_open_document(path: str) -> str:
    """Abre un archivo .FCStd desde ruta absoluta."""
    return _call("open_document", {"path": path})


@mcp.tool()
def freecad_save_document(path: str | None = None, document: str | None = None) -> str:
    """Guarda documento. Si path se da, hace Save As. Si no, sobreescribe."""
    params = {}
    if path:
        params["path"] = path
    if document:
        params["document"] = document
    return _call("save_document", params)


@mcp.tool()
def freecad_recompute(document: str | None = None) -> str:
    """Fuerza recompute del documento."""
    params = {"document": document} if document else {}
    return _call("recompute", params)


@mcp.tool()
def freecad_create_box(length: float = 10.0, width: float = 10.0, height: float = 10.0,
                       name: str = "Box", document: str | None = None) -> str:
    """Crea caja paramétrica (Part::Box). Unidades: mm."""
    params = {"length": length, "width": width, "height": height, "name": name}
    if document:
        params["document"] = document
    return _call("create_box", params)


@mcp.tool()
def freecad_create_cylinder(radius: float = 5.0, height: float = 10.0,
                            name: str = "Cylinder", document: str | None = None) -> str:
    """Crea cilindro paramétrico (Part::Cylinder). Unidades: mm."""
    params = {"radius": radius, "height": height, "name": name}
    if document:
        params["document"] = document
    return _call("create_cylinder", params)


@mcp.tool()
def freecad_boolean_cut(base: str, tool: str, name: str = "Cut",
                        document: str | None = None) -> str:
    """Booleano: base menos tool. Devuelve nuevo objeto (Part::Cut)."""
    params = {"base": base, "tool": tool, "name": name}
    if document:
        params["document"] = document
    return _call("boolean_cut", params)


@mcp.tool()
def freecad_boolean_fuse(base: str, tool: str, name: str = "Fusion",
                         document: str | None = None) -> str:
    """Booleano: union base+tool (Part::Fuse)."""
    params = {"base": base, "tool": tool, "name": name}
    if document:
        params["document"] = document
    return _call("boolean_fuse", params)


@mcp.tool()
def freecad_boolean_common(base: str, tool: str, name: str = "Common",
                           document: str | None = None) -> str:
    """Booleano: intersección base∩tool (Part::Common)."""
    params = {"base": base, "tool": tool, "name": name}
    if document:
        params["document"] = document
    return _call("boolean_common", params)


@mcp.tool()
def freecad_export(path: str, objects: list[str] | None = None,
                   document: str | None = None) -> str:
    """Exporta objetos a archivo (STEP/STL/IGES/BREP por extensión)."""
    params = {"path": path}
    if objects:
        params["objects"] = objects
    if document:
        params["document"] = document
    return _call("export", params)


@mcp.tool()
def freecad_delete_object(name: str, document: str | None = None) -> str:
    """Elimina objeto por nombre."""
    params = {"name": name}
    if document:
        params["document"] = document
    return _call("delete_object", params)


@mcp.tool()
def freecad_create_sphere(radius: float = 5.0, name: str = "Sphere",
                          document: str | None = None) -> str:
    """Crea esfera (Part::Sphere)."""
    p = {"radius": radius, "name": name}
    if document: p["document"] = document
    return _call("create_sphere", p)


@mcp.tool()
def freecad_create_cone(radius1: float = 5.0, radius2: float = 0.0, height: float = 10.0,
                        name: str = "Cone", document: str | None = None) -> str:
    """Crea cono truncado (radius2=0 → cono puntiagudo)."""
    p = {"radius1": radius1, "radius2": radius2, "height": height, "name": name}
    if document: p["document"] = document
    return _call("create_cone", p)


@mcp.tool()
def freecad_create_torus(radius1: float = 10.0, radius2: float = 2.0,
                         name: str = "Torus", document: str | None = None) -> str:
    """Crea toro. radius1=mayor, radius2=menor."""
    p = {"radius1": radius1, "radius2": radius2, "name": name}
    if document: p["document"] = document
    return _call("create_torus", p)


@mcp.tool()
def freecad_create_polygon_prism(sides: int = 6, radius: float = 5.0, height: float = 5.0,
                                 name: str = "Prism", document: str | None = None) -> str:
    """Prisma poligonal regular (sides=6 para hex, tuerca)."""
    p = {"sides": sides, "radius": radius, "height": height, "name": name}
    if document: p["document"] = document
    return _call("create_polygon_prism", p)


@mcp.tool()
def freecad_set_placement(name: str, base_x: float = 0, base_y: float = 0, base_z: float = 0,
                          axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                          angle_deg: float = 0, document: str | None = None) -> str:
    """Fija posición y rotación (axis-angle) de objeto."""
    p = {"name": name,
         "base": {"x": base_x, "y": base_y, "z": base_z},
         "rot": {"axis": {"x": axis_x, "y": axis_y, "z": axis_z}, "angle_deg": angle_deg}}
    if document: p["document"] = document
    return _call("set_placement", p)


@mcp.tool()
def freecad_translate(name: str, dx: float = 0, dy: float = 0, dz: float = 0,
                      document: str | None = None) -> str:
    """Traslada objeto por delta."""
    p = {"name": name, "delta": {"x": dx, "y": dy, "z": dz}}
    if document: p["document"] = document
    return _call("translate", p)


@mcp.tool()
def freecad_rotate(name: str, axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                   angle_deg: float = 0, cx: float = 0, cy: float = 0, cz: float = 0,
                   document: str | None = None) -> str:
    """Rota objeto alrededor de eje y centro."""
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
    """Extruye objeto fuente en dirección."""
    p = {"source": source, "direction": {"x": dx, "y": dy, "z": dz},
         "solid": solid, "name": name}
    if document: p["document"] = document
    return _call("extrude", p)


@mcp.tool()
def freecad_revolve(source: str, axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                    angle_deg: float = 360.0, bx: float = 0, by: float = 0, bz: float = 0,
                    solid: bool = True, name: str = "Revolve",
                    document: str | None = None) -> str:
    """Revoluciona objeto fuente alrededor de eje."""
    p = {"source": source, "axis": {"x": axis_x, "y": axis_y, "z": axis_z},
         "angle_deg": angle_deg, "base": {"x": bx, "y": by, "z": bz},
         "solid": solid, "name": name}
    if document: p["document"] = document
    return _call("revolve", p)


@mcp.tool()
def freecad_fillet(source: str, radius: float = 1.0, edges: list[int] | None = None,
                   name: str = "Fillet", document: str | None = None) -> str:
    """Redondea aristas. edges=None → todas."""
    p = {"source": source, "radius": radius, "name": name}
    if edges: p["edges"] = edges
    if document: p["document"] = document
    return _call("fillet", p)


@mcp.tool()
def freecad_chamfer(source: str, size: float = 1.0, edges: list[int] | None = None,
                    name: str = "Chamfer", document: str | None = None) -> str:
    """Achaflana aristas. edges=None → todas."""
    p = {"source": source, "size": size, "name": name}
    if edges: p["edges"] = edges
    if document: p["document"] = document
    return _call("chamfer", p)


@mcp.tool()
def freecad_mirror(source: str, nx: float = 0, ny: float = 0, nz: float = 1,
                   bx: float = 0, by: float = 0, bz: float = 0,
                   name: str = "Mirror", document: str | None = None) -> str:
    """Espeja objeto respecto a plano (normal + base)."""
    p = {"source": source, "normal": {"x": nx, "y": ny, "z": nz},
         "base": {"x": bx, "y": by, "z": bz}, "name": name}
    if document: p["document"] = document
    return _call("mirror", p)


@mcp.tool()
def freecad_get_object(name: str, document: str | None = None) -> str:
    """Devuelve todas las propiedades del objeto."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_object", p)


@mcp.tool()
def freecad_set_property(name: str, property: str, value, document: str | None = None) -> str:
    """Asigna valor a propiedad del objeto."""
    p = {"name": name, "property": property, "value": value}
    if document: p["document"] = document
    return _call("set_property", p)


@mcp.tool()
def freecad_set_label(name: str, label: str, document: str | None = None) -> str:
    """Cambia Label (nombre visible) del objeto."""
    p = {"name": name, "label": label}
    if document: p["document"] = document
    return _call("set_label", p)


@mcp.tool()
def freecad_set_visibility(name: str, visible: bool = True, document: str | None = None) -> str:
    """Muestra/oculta objeto en viewport (requiere GUI)."""
    p = {"name": name, "visible": visible}
    if document: p["document"] = document
    return _call("set_visibility", p)


@mcp.tool()
def freecad_duplicate(name: str, new_name: str | None = None,
                      document: str | None = None) -> str:
    """Duplica objeto (copia de shape + placement)."""
    p = {"name": name}
    if new_name: p["new_name"] = new_name
    if document: p["document"] = document
    return _call("duplicate", p)


@mcp.tool()
def freecad_import_file(path: str, document: str | None = None) -> str:
    """Importa archivo (STEP/IGES/BREP/STL) al documento."""
    p = {"path": path}
    if document: p["document"] = document
    return _call("import_file", p)


@mcp.tool()
def freecad_run_python(code: str) -> str:
    """Ejecuta código Python arbitrario con App/Part/Gui/doc. Requiere FREECAD_ALLOW_RUN_PYTHON=true."""
    return _call("run_python", {"code": code})


# ==================== SKETCHER ====================

@mcp.tool()
def freecad_create_sketch(name: str = "Sketch", plane: str = "XY",
                          document: str | None = None) -> str:
    """Crea sketch en plano XY|XZ|YZ."""
    p = {"name": name, "plane": plane}
    if document: p["document"] = document
    return _call("create_sketch", p)


@mcp.tool()
def freecad_sketch_add_line(sketch: str, x1: float, y1: float, x2: float, y2: float,
                            document: str | None = None) -> str:
    """Agrega línea al sketch."""
    p = {"sketch": sketch, "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if document: p["document"] = document
    return _call("sketch_add_line", p)


@mcp.tool()
def freecad_sketch_add_circle(sketch: str, cx: float, cy: float, radius: float,
                              document: str | None = None) -> str:
    """Agrega círculo al sketch."""
    p = {"sketch": sketch, "cx": cx, "cy": cy, "radius": radius}
    if document: p["document"] = document
    return _call("sketch_add_circle", p)


@mcp.tool()
def freecad_sketch_add_arc(sketch: str, cx: float, cy: float, radius: float,
                           start_deg: float = 0, end_deg: float = 90,
                           document: str | None = None) -> str:
    """Agrega arco al sketch (grados)."""
    p = {"sketch": sketch, "cx": cx, "cy": cy, "radius": radius,
         "start_deg": start_deg, "end_deg": end_deg}
    if document: p["document"] = document
    return _call("sketch_add_arc", p)


@mcp.tool()
def freecad_sketch_add_rectangle(sketch: str, x1: float, y1: float, x2: float, y2: float,
                                 document: str | None = None) -> str:
    """Agrega rectángulo (4 líneas) al sketch."""
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
    """Crea PartDesign Body."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("create_body", p)


@mcp.tool()
def freecad_pad(body: str, sketch: str, length: float = 10.0,
                reversed: bool = False, midplane: bool = False,
                name: str = "Pad", document: str | None = None) -> str:
    """Pad (extrude) de sketch dentro de Body."""
    p = {"body": body, "sketch": sketch, "length": length,
         "reversed": reversed, "midplane": midplane, "name": name}
    if document: p["document"] = document
    return _call("pad", p)


@mcp.tool()
def freecad_pocket(body: str, sketch: str, length: float = 10.0,
                   reversed: bool = False, name: str = "Pocket",
                   document: str | None = None) -> str:
    """Pocket (cut) de sketch dentro de Body."""
    p = {"body": body, "sketch": sketch, "length": length,
         "reversed": reversed, "name": name}
    if document: p["document"] = document
    return _call("pocket", p)


# ==================== ARRAYS ====================

@mcp.tool()
def freecad_linear_array(source: str, count: int = 2,
                         dx: float = 10.0, dy: float = 0.0, dz: float = 0.0,
                         name: str | None = None, document: str | None = None) -> str:
    """Patrón lineal de copias."""
    p = {"source": source, "count": count, "dx": dx, "dy": dy, "dz": dz}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("linear_array", p)


@mcp.tool()
def freecad_polar_array(source: str, count: int = 4, total_angle_deg: float = 360.0,
                        axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                        cx: float = 0, cy: float = 0, cz: float = 0,
                        name: str | None = None, document: str | None = None) -> str:
    """Patrón polar de copias alrededor de eje."""
    p = {"source": source, "count": count, "total_angle_deg": total_angle_deg,
         "axis": {"x": axis_x, "y": axis_y, "z": axis_z},
         "center": {"x": cx, "y": cy, "z": cz}}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("polar_array", p)


# ==================== GUI ====================

@mcp.tool()
def freecad_gui_screenshot(path: str, width: int = 1280, height: int = 720) -> str:
    """Captura screenshot del viewport activo."""
    return _call("gui_screenshot", {"path": path, "width": width, "height": height})


@mcp.tool()
def freecad_gui_set_view(view: str = "iso") -> str:
    """Vista estándar: iso|top|bottom|front|back|left|right."""
    return _call("gui_set_view", {"view": view})


@mcp.tool()
def freecad_gui_fit_all() -> str:
    """Ajusta vista a todos los objetos."""
    return _call("gui_fit_all")


# ==================== MEASUREMENTS ====================

@mcp.tool()
def freecad_get_bounding_box(name: str, document: str | None = None) -> str:
    """BoundingBox de objeto: min/max/size."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_bounding_box", p)


@mcp.tool()
def freecad_get_volume(name: str, document: str | None = None) -> str:
    """Volumen del shape (mm³)."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_volume", p)


@mcp.tool()
def freecad_get_area(name: str, document: str | None = None) -> str:
    """Área superficial del shape (mm²)."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("get_area", p)


@mcp.tool()
def freecad_get_distance(name1: str | None = None, name2: str | None = None,
                         ax: float = 0, ay: float = 0, az: float = 0,
                         bx: float = 0, by: float = 0, bz: float = 0,
                         document: str | None = None) -> str:
    """Distancia entre 2 objetos (por nombre) o 2 puntos (a/b)."""
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
    """Convierte shape en mesh (para STL/3D print)."""
    p = {"source": source, "linear_deflection": linear_deflection,
         "angular_deflection": angular_deflection}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("shape_to_mesh", p)


@mcp.tool()
def freecad_export_stl(path: str, objects: list[str] | None = None,
                       document: str | None = None) -> str:
    """Exporta objetos a STL."""
    p = {"path": path}
    if objects: p["objects"] = objects
    if document: p["document"] = document
    return _call("export_stl", p)


# ==================== TECHDRAW ====================

@mcp.tool()
def freecad_techdraw_create_page(name: str = "Page", template: str | None = None,
                                 document: str | None = None) -> str:
    """Crea página TechDraw con template SVG (por defecto A4 landscape)."""
    p = {"name": name}
    if template: p["template"] = template
    if document: p["document"] = document
    return _call("techdraw_create_page", p)


@mcp.tool()
def freecad_techdraw_add_view(page: str, source: str, name: str = "View",
                              dir_x: float = 0, dir_y: float = 0, dir_z: float = 1,
                              scale: float = 1.0, x: float = 100.0, y: float = 100.0,
                              document: str | None = None) -> str:
    """Agrega vista 2D de objeto a página TechDraw."""
    p = {"page": page, "source": source, "name": name,
         "direction": {"x": dir_x, "y": dir_y, "z": dir_z},
         "scale": scale, "x": x, "y": y}
    if document: p["document"] = document
    return _call("techdraw_add_view", p)


# ==================== DRAFT ====================

@mcp.tool()
def freecad_draft_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float,
                       name: str | None = None, document: str | None = None) -> str:
    """Línea Draft (3D)."""
    p = {"p1": {"x": x1, "y": y1, "z": z1}, "p2": {"x": x2, "y": y2, "z": z2}}
    if name: p["name"] = name
    if document: p["document"] = document
    return _call("draft_line", p)


@mcp.tool()
def freecad_draft_dimension(x1: float, y1: float, z1: float,
                            x2: float, y2: float, z2: float,
                            tx: float = 0, ty: float = 0, tz: float = 0,
                            document: str | None = None) -> str:
    """Cota lineal Draft entre 2 puntos (tx,ty,tz = posición texto)."""
    p = {"p1": {"x": x1, "y": y1, "z": z1}, "p2": {"x": x2, "y": y2, "z": z2},
         "p_text": {"x": tx, "y": ty, "z": tz}}
    if document: p["document"] = document
    return _call("draft_dimension", p)


@mcp.tool()
def freecad_draft_text(text: str, x: float = 0, y: float = 0, z: float = 0,
                       document: str | None = None) -> str:
    """Texto Draft en posición 3D."""
    p = {"text": text, "position": {"x": x, "y": y, "z": z}}
    if document: p["document"] = document
    return _call("draft_text", p)


# ==================== ASSEMBLY ====================

@mcp.tool()
def freecad_assembly_attach(name: str, parent: str,
                            offset_x: float = 0, offset_y: float = 0, offset_z: float = 0,
                            axis_x: float = 0, axis_y: float = 0, axis_z: float = 1,
                            angle_deg: float = 0, document: str | None = None) -> str:
    """Fija objeto relativo a padre (placement compuesto)."""
    p = {"name": name, "parent": parent,
         "offset": {"x": offset_x, "y": offset_y, "z": offset_z},
         "rot": {"axis": {"x": axis_x, "y": axis_y, "z": axis_z}, "angle_deg": angle_deg}}
    if document: p["document"] = document
    return _call("assembly_attach", p)


# ==================== FEM ====================

@mcp.tool()
def freecad_fem_create_analysis(name: str = "Analysis", document: str | None = None) -> str:
    """Crea análisis FEM con solver CalculiX."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("fem_create_analysis", p)


@mcp.tool()
def freecad_fem_add_material(analysis: str, material: str = "Steel-Generic",
                             name: str = "Material", document: str | None = None) -> str:
    """Añade material FEM al análisis."""
    p = {"analysis": analysis, "material": material, "name": name}
    if document: p["document"] = document
    return _call("fem_add_material", p)


@mcp.tool()
def freecad_fem_add_fixed(analysis: str, object: str | None = None,
                          faces: list[int] | None = None,
                          name: str = "Fixed", document: str | None = None) -> str:
    """Constraint fijo FEM sobre caras de un objeto."""
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
    """Constraint fuerza FEM sobre caras."""
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
    """Crea Job CAM/Path para objeto fuente."""
    p = {"source": source, "name": name}
    if document: p["document"] = document
    return _call("cam_create_job", p)


@mcp.tool()
def freecad_cam_profile(job: str, name: str = "Profile",
                        document: str | None = None) -> str:
    """Agrega operación Profile (contorno) al Job."""
    p = {"job": job, "name": name}
    if document: p["document"] = document
    return _call("cam_profile", p)


# ==================== SPREADSHEET ====================

@mcp.tool()
def freecad_spreadsheet_create(name: str = "Spreadsheet",
                               document: str | None = None) -> str:
    """Crea hoja de cálculo."""
    p = {"name": name}
    if document: p["document"] = document
    return _call("spreadsheet_create", p)


@mcp.tool()
def freecad_spreadsheet_set(sheet: str, cell: str, value, alias: str | None = None,
                            document: str | None = None) -> str:
    """Asigna valor a celda (p.ej. 'A1'). Alias opcional para referenciar."""
    p = {"sheet": sheet, "cell": cell, "value": value}
    if alias: p["alias"] = alias
    if document: p["document"] = document
    return _call("spreadsheet_set", p)


@mcp.tool()
def freecad_spreadsheet_get(sheet: str, cell: str, document: str | None = None) -> str:
    """Lee contenido y valor de celda."""
    p = {"sheet": sheet, "cell": cell}
    if document: p["document"] = document
    return _call("spreadsheet_get", p)


# ==================== COLOR ====================

@mcp.tool()
def freecad_set_color(name: str, r: float = 0.8, g: float = 0.8, b: float = 0.8,
                      document: str | None = None) -> str:
    """Color RGB 0-1 del objeto (GUI)."""
    p = {"name": name, "r": r, "g": g, "b": b}
    if document: p["document"] = document
    return _call("set_color", p)


@mcp.tool()
def freecad_set_transparency(name: str, transparency: int = 50,
                             document: str | None = None) -> str:
    """Transparencia 0-100 (GUI)."""
    p = {"name": name, "transparency": transparency}
    if document: p["document"] = document
    return _call("set_transparency", p)


# ==================== LOFT / SWEEP ====================

@mcp.tool()
def freecad_loft(sections: list[str], solid: bool = True, ruled: bool = False,
                 name: str = "Loft", document: str | None = None) -> str:
    """Loft entre secciones (>=2 objetos con Shape)."""
    p = {"sections": sections, "solid": solid, "ruled": ruled, "name": name}
    if document: p["document"] = document
    return _call("loft", p)


@mcp.tool()
def freecad_sweep(profile: str, path: str, solid: bool = True, frenet: bool = False,
                  name: str = "Sweep", document: str | None = None) -> str:
    """Sweep de profile a lo largo de path."""
    p = {"profile": profile, "path": path, "solid": solid, "frenet": frenet, "name": name}
    if document: p["document"] = document
    return _call("sweep", p)


# ==================== HOLE ====================

@mcp.tool()
def freecad_hole(body: str, sketch: str, diameter: float = 6.0, depth: float = 10.0,
                 threaded: bool = False, thread_type: str | None = None,
                 name: str = "Hole", document: str | None = None) -> str:
    """Hole PartDesign en Body usando sketch con círculos."""
    p = {"body": body, "sketch": sketch, "diameter": diameter, "depth": depth,
         "threaded": threaded, "name": name}
    if thread_type: p["thread_type"] = thread_type
    if document: p["document"] = document
    return _call("hole", p)


# ==================== SKETCH CONSTRAINTS AVANZADOS ====================

@mcp.tool()
def freecad_sketch_add_constraint_advanced(sketch: str, type: str,
                                           geo1: int = -1, geo2: int = -1,
                                           vertex1: int = 1, vertex2: int = 1,
                                           geo_sym: int = -1,
                                           document: str | None = None) -> str:
    """Constraint avanzado: parallel|perpendicular|tangent|equal|coincident|point_on_object|symmetric."""
    p = {"sketch": sketch, "type": type,
         "geo1": geo1, "geo2": geo2,
         "vertex1": vertex1, "vertex2": vertex2, "geo_sym": geo_sym}
    if document: p["document"] = document
    return _call("sketch_add_constraint_advanced", p)


# ==================== GUI SELECTION ====================

@mcp.tool()
def freecad_gui_select(objects: list[str], clear: bool = True,
                       document: str | None = None) -> str:
    """Selecciona objetos en viewport. clear=True limpia antes."""
    p = {"objects": objects, "clear": clear}
    if document: p["document"] = document
    return _call("gui_select", p)


@mcp.tool()
def freecad_gui_clear_selection() -> str:
    """Limpia la selección actual."""
    return _call("gui_clear_selection")


@mcp.tool()
def freecad_gui_get_selection() -> str:
    """Devuelve objetos seleccionados actualmente."""
    return _call("gui_get_selection")


if __name__ == "__main__":
    mcp.run()
