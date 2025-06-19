import subprocess
import json

def obtener_disco_fisico(letra_unidad):
    letra = letra_unidad.strip(":").upper()
    cmd = [
        "powershell.exe",
        "-Command",
        f"Get-Partition -DriveLetter {letra} | Get-Disk | Select Number, FriendlyName, SerialNumber | ConvertTo-Json"
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    if resultado.returncode == 0:
        try:
            datos = json.loads(resultado.stdout)
            return datos  # Devuelve dict con 'Number', 'FriendlyName', etc.
        except json.JSONDecodeError:
            print("No se pudo decodificar la salida JSON.")
    else:
        print("Error al obtener información del disco:", resultado.stderr)
    return None
info = obtener_disco_fisico("F:")
if info:
    print(f"La unidad D: está en el Disco Físico {info['Number']} ({info['FriendlyName']})")

