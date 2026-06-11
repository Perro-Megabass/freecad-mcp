# -*- coding: utf-8 -*-
# FreeCAD MCP — ui.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""DockWidget with Connect / Disconnect / Status for the FreeCAD MCP Bridge."""

from PySide2 import QtCore, QtWidgets

import handlers
from server import BridgeServer, _ensure_pump_timer


class MCPDock(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super().__init__("FreeCAD MCP Bridge", parent)
        self.setObjectName("FreeCADMCPDock")

        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)

        self.status_label = QtWidgets.QLabel("Disconnected")
        self.status_label.setStyleSheet("font-weight: bold;")

        self.btn_connect = QtWidgets.QPushButton("Connect")
        self.btn_disconnect = QtWidgets.QPushButton("Disconnect")
        self.btn_disconnect.setEnabled(False)

        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_disconnect.clicked.connect(self.on_disconnect)

        self.chk_run_python = QtWidgets.QCheckBox("Allow run_python (arbitrary code)")
        self.chk_run_python.setChecked(handlers.ALLOW_RUN_PYTHON)
        self.chk_run_python.toggled.connect(self.on_toggle_run_python)

        layout.addWidget(QtWidgets.QLabel("Status:"))
        layout.addWidget(self.status_label)
        layout.addWidget(self.btn_connect)
        layout.addWidget(self.btn_disconnect)
        layout.addWidget(self.chk_run_python)
        layout.addStretch(1)

        self.setWidget(w)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

        # The main-thread pump timer is owned by the server module so it
        # survives this dock being closed; ensure it exists anyway.
        _ensure_pump_timer()

    def on_toggle_run_python(self, checked):
        handlers.ALLOW_RUN_PYTHON = bool(checked)

    def on_connect(self):
        srv = BridgeServer.instance()
        srv.start()
        self.refresh()

    def on_disconnect(self):
        srv = BridgeServer.instance()
        srv.stop()
        self.refresh()

    def refresh(self):
        srv = BridgeServer.instance()
        self.status_label.setText(srv.status())
        self.btn_connect.setEnabled(not srv.running)
        self.btn_disconnect.setEnabled(srv.running)
