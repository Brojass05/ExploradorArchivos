import os
import platform
try:
    ruta_actual = os.getcwd()
    archivos_en_ruta = os.listdir(ruta_actual)
except Exception as e:
    print(f"Error al acceder a la ruta: {e}")


partes_ruta = [x for x in ruta_actual.split('\\') if x != '']
ruta1: str = ruta_actual.split(partes_ruta[-1])[0].rstrip('\\')
archivos = os.listdir(ruta1)
listaRutas = []
nombreArchivos: list = []
for i in range(0,len(archivos)):
    listaRutas.append(os.path.join(ruta1, str(archivos[i])))
    nombreArchivos.append(archivos[i])
    
for j in range(0,len(archivos)):
    print("Rutas: ",listaRutas[j])
    print("Archivos: ",nombreArchivos[j])




rutaArchivo: str = os.path.join(ruta1, str(archivos[1]))


sistema = platform.system()

def abrir_archivo(rutaArchivo: str):
    if sistema == "Windows":
        os.startfile(rutaArchivo)
    elif sistema == "Darwin":  # macOS
        os.system(f"open \"{rutaArchivo}\"")
    elif sistema == "Linux":
        os.system(f"xdg-open \"{rutaArchivo}\"")
    else:
        raise Exception(f"Sistema operativo no soportado: {sistema}")