import os

def obtener_rutas_y_archivos(self):
    try:
        # Obtiene la ruta actual del directorio desde donde se ejecuta el script
        ruta_actual = os.getcwd()

        # Obtiene la lista de archivos y carpetas dentro de la ruta actual
        archivos_en_ruta = os.listdir(ruta_actual)
    except Exception as e:
        print(f"Error al acceder a la ruta: {e}")
        return [], []

    # Divide la ruta actual en partes usando el separador del sistema operativo
    # Esto sirve para ir construyendo rutas anteriores paso a paso
    partes_ruta = [x for x in ruta_actual.split(os.sep) if x != '']

    # Crea una lista para almacenar las rutas anteriores desde el root hasta el directorio actual
    listas_rutas_anteriores: list = []
    for n in range(1, len(partes_ruta)):
        # Construye rutas anteriores de forma progresiva (sin incluir la carpeta final)
        ruta = os.sep.join(partes_ruta[:len(partes_ruta) - n])
        listas_rutas_anteriores.append(ruta)

    # Listas que guardarán las rutas completas y los nombres de archivos por ruta
    listaRutas: list = []
    nombreArchivos: list = []

    # Agrega cada ruta previa construida a la lista
    for ruta in listas_rutas_anteriores:
        listaRutas.append(ruta)

    # Ciclo que recorre cada ruta guardada y obtiene sus archivos
    for rutas in listaRutas:
        print("Accediendo a:", rutas)
        try:
            archivos = os.listdir(rutas)  # Intenta listar los archivos en esa ruta
        except Exception as e:
            print(f"No se pudo acceder a {rutas}: {e}")
            archivos = []  # Si hay error (por permisos o inexistencia), agrega lista vacía

        # Guarda los resultados como una tupla (ruta, lista de archivos)
        nombreArchivos.append((rutas, archivos))



    return listaRutas, nombreArchivos

# Llamada de prueba fuera de una clase (self se ignora)
lista_rutas, nombre_archivos = obtener_rutas_y_archivos(None)
# Mostramos los archivos encontrados por ruta (ignorando rutas vacías)
for ruta, archivos in nombre_archivos:
    for archivo in archivos:
        if archivo:  # Filtra strings vacíos
            print("Ruta:", ruta, "Archivo:", archivo)

