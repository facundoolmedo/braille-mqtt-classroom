import json
import time
import threading
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion


# Mismo mapeo de puntos braille que en la app del profe (simplificado)
latex_braille_map = {
    'a': [1], 'b': [1,2], 'c': [1,4], 'd': [1,4,5], 'e': [1,5],
    'f': [1,2,4], 'g': [1,2,4,5], 'h': [1,2,5], 'i': [2,4], 'j': [2,4,5],
    'k': [1,3], 'l': [1,2,3], 'm': [1,3,4], 'n': [1,3,4,5], 'o': [1,3,5],
    'p': [1,2,3,4], 'q': [1,2,3,4,5], 'r': [1,2,3,5], 's': [2,3,4],
    't': [2,3,4,5], 'u': [1,3,6], 'v': [1,2,3,6], 'w': [2,4,5,6],
    'x': [1,3,4,6], 'y': [1,3,4,5,6], 'z': [1,3,5,6], '1': [1], '2': [1,2],
    '3': [1,4], '4': [1,4,5], '5': [1,5], '6': [1,2,4], '7': [1,2,4,5],
    '8': [1,2,5], '9': [2,4], '0': [2,4,5], '+': [3,4,6], '-': [3,6],
    '=': [2,3,5,6], '^': [4,6], '(': [2,3,5], ')': [2,3,6], ' ': [],
    '.': [2,5,6], ',': [2], ':': [2,5], ';': [2,3], '!': [2,3,5],
    '?': [2,3,6], '/': [3,4], '*': [5], '\\': [], '{': [], '}': [],
    '_': [4,5,6],
}

def dots_to_unicode_braille(dots):
    val = 0
    for d in dots:
        if 1 <= d <= 8:
            val |= 1 << (d - 1)
    return chr(0x2800 + val)

def latex_to_braille_8points(expr):
    result = ""
    for c in expr:
        dots = latex_braille_map.get(c.lower())
        if dots is None:
            result += dots_to_unicode_braille([2, 3, 6])  # signo pregunta braille
        else:
            result += dots_to_unicode_braille(dots)
    return result


class StudentClient:
    def __init__(self, client_id):
        self.client_id = client_id
        self.client = mqtt.Client(client_id=self.client_id, callback_api_version=CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()

        # Anunciar presencia al tópico de dispositivos
        self.announce()

    def announce(self):
        payload = json.dumps({"device_id": self.client_id})
        self.client.publish("braille/devices/announce", payload)
        print(f"[{self.client_id}] Anunciando presencia...")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[{self.client_id}] Conectado al broker MQTT con código {rc}")
        # Suscribirse a mensajes dirigidos y broadcast
        self.client.subscribe(f"braille/devices/{self.client_id}/problem")
        self.client.subscribe("braille/devices/broadcast")

    def on_message(self, client, userdata, msg):
        expr = msg.payload.decode()
        braille = latex_to_braille_8points(expr)
        print(f"\n[{self.client_id}] Recibido problema:\n{expr}")
        print(f"[{self.client_id}] En Braille:\n{braille}\n")

    def run(self):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"[{self.client_id}] Cerrando cliente...")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    # Podés crear varios clientes para simular varios alumnos:
    student = StudentClient("alumno_02")
    student.run()
