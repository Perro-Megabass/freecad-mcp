# -*- coding: utf-8 -*-
# FreeCAD MCP — ui.py
# Author : Perro Megabass
# GitHub : https://github.com/Perro-Megabass
# Instagram: https://www.instagram.com/perromods/
# License : MIT
"""DockWidget con Connect/Disconnect/Status."""

from PySide2 import QtCore, QtWidgets

from server import BridgeServer, _pump_main_queue


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

        layout.addWidget(QtWidgets.QLabel("Status:"))
        layout.addWidget(self.status_label)
        layout.addWidget(self.btn_connect)
        layout.addWidget(self.btn_disconnect)
        layout.addStretch(1)

        self.setWidget(w)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

        # Pump cola principal (ejecuta handlers en hilo GUI)
        self._pump_timer = QtCore.QTimer(self)
        self._pump_timer.setInterval(50)
        self._pump_timer.timeout.connect(_pump_main_queue)
        self._pump_timer.start()

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
