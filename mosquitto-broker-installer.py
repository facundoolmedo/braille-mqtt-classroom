import requests

url = "https://mosquitto.org/files/binary/win64/mosquitto-2.0.22-install-windows-x64.exe"
filename = "mosquitto-installer.exe"

print("Descargando instalador...")
response = requests.get(url)
response.raise_for_status()
with open(filename, "wb") as f:
    f.write(response.content)
print("✅ Descarga completa. Ejecutalo como administrador.")