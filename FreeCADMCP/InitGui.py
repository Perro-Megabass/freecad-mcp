# -*- coding: utf-8 -*-
# FreeCAD MCP — InitGui.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""Registro del Workbench en FreeCAD GUI."""

import FreeCADGui as Gui


class FreeCADMCPWorkbench(Gui.Workbench):
    MenuText = "MCP Bridge"
    ToolTip = "FreeCAD MCP Bridge (Claude)"
    Icon = ""

    def Initialize(self):
        pass

    def Activated(self):
        import os, sys
        import FreeCAD as App
        from PySide2 import QtCore
        _here = os.path.join(App.getUserAppDataDir(), "Mod", "FreeCADMCP")
        if _here not in sys.path:
            sys.path.insert(0, _here)
        from ui import MCPDock
        mw = Gui.getMainWindow()
        if not hasattr(self, "_dock") or self._dock is None:
            self._dock = MCPDock(mw)
            mw.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock)
        self._dock.show()

    def Deactivated(self):
        if hasattr(self, "_dock") and self._dock is not None:
            self._dock.hide()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(FreeCADMCPWorkbench())
