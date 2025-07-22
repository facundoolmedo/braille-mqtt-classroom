import sys
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QListWidget, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
import paho.mqtt.client as mqtt


def dots_to_unicode_braille(dots):
    val = 0
    for d in dots:
        if 1 <= d <= 8:
            val |= 1 << (d - 1)
    return chr(0x2800 + val)


latex_braille_map = {
    'a': [1],
    'b': [1,2],
    'c': [1,4],
    'd': [1,4,5],
    'e': [1,5],
    'f': [1,2,4],
    'g': [1,2,4,5],
    'h': [1,2,5],
    'i': [2,4],
    'j': [2,4,5],
    'k': [1,3],
    'l': [1,2,3],
    'm': [1,3,4],
    'n': [1,3,4,5],
    'o': [1,3,5],
    'p': [1,2,3,4],
    'q': [1,2,3,4,5],
    'r': [1,2,3,5],
    's': [2,3,4],
    't': [2,3,4,5],
    'u': [1,3,6],
    'v': [1,2,3,6],
    'w': [2,4,5,6],
    'x': [1,3,4,6],
    'y': [1,3,4,5,6],
    'z': [1,3,5,6],
    '1': [1],
    '2': [1,2],
    '3': [1,4],
    '4': [1,4,5],
    '5': [1,5],
    '6': [1,2,4],
    '7': [1,2,4,5],
    '8': [1,2,5],
    '9': [2,4],
    '0': [2,4,5],
    '+': [3,4,6],
    '-': [3,6],
    '=': [2,3,5,6],
    '^': [4,6],
    '(': [2,3,5],
    ')': [2,3,6],
    ' ': [],
    '.': [2,5,6],
    ',': [2],
    ':': [2,5],
    ';/': [2,3],  # corrijo ';' para evitar confusión con '/'
    '!': [2,3,5],
    '?': [2,3,6],
    '/': [3,4],
    '*': [5],
    '\\': [],
    '{': [],
    '}': [],
    '_': [4,5,6],
}


def latex_to_braille_8points(expr):
    result = ""
    for c in expr:
        dots = latex_braille_map.get(c.lower())
        if dots is None:
            result += dots_to_unicode_braille([2, 3, 6])
        else:
            result += dots_to_unicode_braille(dots)
    return result


class ProfessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UTN FRC - CIII - PID Braille - Master App")
        self.setGeometry(100, 100, 600, 550)
        self.devices = set()

        self.layout = QVBoxLayout()

        self.problem_label = QLabel("Expresión matemática (LaTeX):")
        self.layout.addWidget(self.problem_label)

        self.problem_input = QTextEdit()
        self.problem_input.textChanged.connect(self.update_braille_preview)
        self.layout.addWidget(self.problem_input)

        self.braille_preview_label = QLabel("Previsualización en Braille (8 puntos):")
        self.layout.addWidget(self.braille_preview_label)

        self.braille_preview = QLabel("")
        self.braille_preview.setStyleSheet(
            "font-size: 24px; font-family: 'Segoe UI Symbol', 'Arial Unicode MS';"
        )
        self.braille_preview.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.braille_preview)

        self.device_list = QListWidget()
        self.layout.addWidget(self.device_list)

        self.send_selected_btn = QPushButton("Enviar a dispositivo seleccionado")
        self.send_selected_btn.clicked.connect(self.send_to_selected)
        self.layout.addWidget(self.send_selected_btn)

        self.broadcast_btn = QPushButton("Broadcast a todos los dispositivos")
        self.broadcast_btn.clicked.connect(self.send_broadcast)
        self.layout.addWidget(self.broadcast_btn)

        self.history_label = QLabel("Historial de problemas enviados:")
        self.layout.addWidget(self.history_label)

        self.history_box = QTextEdit()
        self.history_box.setReadOnly(True)
        self.history_box.setStyleSheet("background-color: #f0f0f0;")
        self.layout.addWidget(self.history_box)

        self.setLayout(self.layout)

        # MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()
        self.client.subscribe("braille/devices/announce")

    def update_braille_preview(self):
        expr = self.problem_input.toPlainText()
        braille_text = latex_to_braille_8points(expr)
        self.braille_preview.setText(braille_text)

    def on_connect(self, client, userdata, flags, rc):
        print("Conectado al broker MQTT con código:", rc)

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
            device_id = data.get("device_id")
            if device_id and device_id not in self.devices:
                self.devices.add(device_id)
                self.device_list.addItem(device_id)
        except Exception as e:
            print("Error al procesar mensaje:", e)

    def add_to_history(self, target, problem):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] Enviado a {target}:\n{problem}\n\n"
        self.history_box.append(entry)

    def send_to_selected(self):
        selected = self.device_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Seleccioná un dispositivo.")
            return

        expr = self.problem_input.toPlainText()
        topic = f"braille/devices/{selected.text()}/problem"
        self.client.publish(topic, expr)
        self.add_to_history(selected.text(), expr)
        QMessageBox.information(self, "Enviado", f"Problema enviado a {selected.text()}")

    def send_broadcast(self):
        expr = self.problem_input.toPlainText()
        self.client.publish("braille/devices/broadcast", expr)
        self.add_to_history("Todos los dispositivos (broadcast)", expr)
        QMessageBox.information(self, "Enviado", "Problema enviado a todos los dispositivos")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProfessorApp()
    window.show()
    sys.exit(app.exec_())
