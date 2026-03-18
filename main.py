import sys
import json
import os
import subprocess
from plyer import notification
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QDialog,
    QLineEdit,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QMenu,
    QSystemTrayIcon,
)
from PySide6.QtCore import (
    Qt,
    QTimer
)
from PySide6.QtGui import (
    QIcon, QAction, QCursor
)
from Sun import gather
from meteo import gather2


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_config_path():
    if sys.platform == "win32":
        base = os.getenv("APPDATA")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/library/Application Support")
    else:
        base = os.path.expanduser("~/.config")
    app_dir = os.path.join(base, "warnW")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "config.json")

CONFIG_FILE = get_config_path()

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("warnW first launch")
        self.setFixedSize(500, 400)

        self.lat_input = QLineEdit()
        self.lon_input = QLineEdit()

        expl = QLabel(
            "Hello! If you want to see your local pressure - enter your latitude and longitude here\n"
            "You can change them at any moment.\nPress NO to skip."
        )
        expl.setWordWrap(True)

        form_layout = QFormLayout()
        form_layout.addRow("Latitude", self.lat_input)
        form_layout.addRow("Longitude", self.lon_input)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttons.button(QDialogButtonBox.Cancel).setText("NO")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(expl)
        layout.addLayout(form_layout)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def get_data(self):
        lat_text = self.lat_input.text().strip()
        lon_text = self.lon_input.text().strip()
        return lat_text, lon_text


class FurinaApp(QWidget):
    def __init__(self):
        super().__init__()

        self.time = QTimer(self)
        self.time.timeout.connect(self.bg)
        self.time.start(1800000)

        self.setWindowTitle("warnW")
        self.setFixedSize(800, 600)

        self.xray_button = QPushButton("X-ray activity")
        self.xray_button.clicked.connect(self.xray)

        self.pressure_button = QPushButton("Local pressure")
        self.pressure_button.clicked.connect(self.pressure)

        self.config_button = QPushButton("Change coordinates")
        self.config_button.clicked.connect(self.jason)

        self.output_label = QLabel("")
        self.output_label.setWordWrap(True)
        self.output_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.xray_button)
        button_layout.addWidget(self.pressure_button)
        button_layout.addWidget(self.config_button)
        button_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.output_label)

        self.setLayout(main_layout)

        self.check_config()

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("wayland_icon.png")))
        self.tray_icon.setToolTip("warnW running in background")

        tray_menu = QMenu(self)
        show_action = QAction("Show Window",self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        exit_action = QAction("Exit",self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.on_tray_icon_activated)
    def check_config(self):
        if not os.path.exists(CONFIG_FILE):
            dialog = ConfigDialog(self)
            config_data = {}

            if dialog.exec() == QDialog.Accepted:
                lat_text, lon_text = dialog.get_data()

                if lat_text and lon_text:
                    try:
                        number1 = float(lat_text)
                        number2 = float(lon_text)

                        if not (-90 <= number1 <= 90):
                            self.output_label.setText("Latitude must be between -90 and 90.")
                            return
                        if not (-180 <= number2 <= 180):
                            self.output_label.setText("Longitude must be between -180 and 180.")
                            return

                        config_data = {"user_data1": number1, "user_data2": number2}

                    except ValueError:
                        self.output_label.setText("Invalid input: please enter valid numbers.")
                        return

            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=4)

            self.output_label.setText("Config saved.")

    def xray(self):
        try:
            data = gather()

            if not data:
                self.output_label.setText("No data found.")
                return

            text = (
                "X-ray data\n\n"
                f"Current activity: {data['seichas']}\n"
            )

            if data['bilo'] and data["bilo"][0] == "M":
                text += (
                    f"The recent maximum was {data['bilo']}, happened at {data['v']}, it may affect you"
                )
            elif data['bilo'] and data["bilo"][0] == "X":
                text += (
                    f"Major flare! {data['bilo']}, happened at {data['v']}, "
                    f"consider taking medicine if needed"
                )

            self.output_label.setText(text)

        except Exception as e:
            self.output_label.setText(f"Error:\n{e}")

    def pressure(self):
        try:
            date = gather2()
            code = 0
            if not date:
                self.output_label.setText("Couldn`t get meteodata!")
                return
            if date["cr"] <= 988:
                output = f"The current pressure is really low! {date['cr'] *0.75 // 1}"
                code = -1
            if date["cr"] >= 1027:
                output = f"The current pressure is really high!{date['cr'] *0.75 // 1}"
                code = 1
            if code != -1:
                if 0 <= date["1h"] <= 998:
                    output = f"Soon the pressure will be low - {date['1h'] *0.75 // 1}, keep it in mind"
                    code = -2
                if 0 <= date["2h"] <= 998:
                    output = f"Soon the pressure will be low - {date['2h'] *0.75 // 1}, keep it in mind"
                    code = -2
                if 0 <= date["3h"] <= 998:
                    output = f"Soon the pressure will be low - {date['3h'] *0.75 // 1}, keep it in mind"
                    code = -2
            if code != 1:
                if date["1h"] >= 1027:
                    output = f"Soon the pressure will be high - {date['1h'] *0.75 // 1}, keep it in mind"
                    code = 2
                if date["2h"] >= 1027:
                    output = f"Soon the pressure will be high - {date['2h'] *0.75 // 1}, keep it in mind"
                    code = 2
                if date["3h"] >= 1027:
                    output = f"Soon the pressure will be high - {date['3h'] *0.75 // 1}, keep it in mind"
                    code = 2
            if code == 0:
                output = "Everything is fine"

            self.output_label.setText(output)
        except Exception as d:
            self.output_label.setText("Is your config empty?")

    def jason(self):
        try:
            if os.path.exists(CONFIG_FILE):
                if sys.platform == "win32":
                    os.startfile(CONFIG_FILE)
                elif sys.platform == "darwin":
                    subprocess.call(("open", CONFIG_FILE))
                else:
                    subprocess.call(("xdg-open", CONFIG_FILE))
        except Exception as f:
            self.output_label.setText("Error finding config")

    def bg(self):
        try:
            xray = gather()
            mt = gather2()
            code = 0
            z = 0
            output = None

            if mt["cr"] <= 988:
                output = f"The current pressure is really low! {mt['cr'] * 0.75 // 1}"
                code = -1

            elif mt["cr"] >= 1027:
                output = f"The current pressure is really high! {mt['cr'] * 0.75 // 1}"
                code = 1

            if code != -1:
                for key in ["1h", "2h", "3h"]:
                    if 0 <= mt[key] <= 998:
                        output = f"Soon the pressure will be low - {mt[key] * 0.75 // 1}, keep it in mind"
                        code = -2
                        break

            if code != 1:
                for key in ["1h", "2h", "3h"]:
                    if mt[key] >= 1027:
                        output = f"Soon the pressure will be high - {mt[key] * 0.75 // 1}, keep it in mind"
                        code = 2
                        break

            if output:
                self.send_notification(output)

            if xray:
                if xray['seichas'] != "M" and xray['seichas'] != "X":
                    if xray['bilo'] and (xray['bilo'] == "M" or xray["bilo"] == "X"):
                        output = "Major recent solar activity!"
                        z = 1
                if xray["seichas"] == "M" or xray["seichas"] == "X":
                    output = "New flare alert"
                    z = 1
            if output and z == 1:
                self.send_notification(output)
        except Exception as gf:
            print(gf)
    def send_notification(self, output):
        try:
            notification.notify(
                title= "warnW",
                message= output,
                timeout = 6
            )
        except Exception as g:
            print(g)
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "warnW",
            "App is still running in background.",
            QSystemTrayIcon.Information,
            3000
        )

    def on_tray_icon_activated(self, reason):
        from PySide6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.Trigger:
            self.show()
            self.raise_()
            self.activateWindow()
        elif reason == QSystemTrayIcon.Context:
            self.tray_icon.contextMenu().exec(QCursor.pos())
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = FurinaApp()
    window.show()
    sys.exit(app.exec())
