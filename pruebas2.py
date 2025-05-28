
import os
try:
    # obtiene la ruta actual del directorio
    ruta_actual = os.getcwd()
    # obtiene los archivos que estan en la ruta actual
    archivos_en_ruta = os.listdir(ruta_actual)
except Exception as e:
    print(f"Error al acceder a la ruta: {e}")
#  divide la ruta actual en partes para crear pestanas
partes_ruta = [x for x in ruta_actual.split('\\') if x != '']
# obtiene la ruta anterior sacando el ultimo nombre y eliminando el ultimo \
ruta_anterior: str = ruta_actual.split(partes_ruta[-1])[0].rstrip('\\')
print(ruta_anterior)
# crea listas para las rutas y los nombres de los archivos
listaRutas: list = []
nombreArchivos: list = []
# ciclo for para ir agregando las rutas y los nombres a sus listas respectivas
for i in range(0,len(archivos_en_ruta)):
    # agrega la ruta a la lista desde C:, hasta la ruta actual
    listaRutas.append(os.path.join(ruta_anterior, str(archivos_en_ruta[i])))
    # agrega los nombres de los archivos dentro de la ruta actual
    nombreArchivos.append(archivos_en_ruta[i])
listas_rutas_anteriores: list = []    
for n in range(1, len(partes_ruta)):
    ruta = ruta_actual.split(partes_ruta[-n])[0].rstrip('\\')
    listas_rutas_anteriores.append(ruta)
    
for rutas in listas_rutas_anteriores:
    print(rutas)
