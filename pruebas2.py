import os
def obtener_archivos(ruta_actual):
    # Listas que guardarán las rutas completas y los nombres de archivos por ruta
    listaRutas: list = obtener_rutas() 
    nombreArchivos: list = []
    # Ciclo que recorre cada ruta guardada y obtiene sus archivos
    try:
        archivos = os.listdir(ruta_actual)  # Intenta listar los archivos en esa ruta
    except Exception as e:
        print(f"No se pudo acceder a {ruta_actual}: {e}")
        archivos = []  # Si hay error (por permisos o inexistencia), agrega lista vacía
    # Guarda los resultados como una tupla (ruta, lista de archivos)
    nombreArchivos.append(archivos)
    return nombreArchivos

def obtener_rutas():
    try:
        # Obtiene la ruta actual del directorio desde donde se ejecuta el script
        ruta_actual = os.getcwd()
    except Exception as e:
        print(f"Error al acceder a la ruta: {e}")
        return []
    # Divide la ruta actual en partes usando el separador del sistema operativo
    # Esto sirve para ir construyendo rutas anteriores paso a paso
    
    partes_ruta = [x for x in ruta_actual.split(os.sep) if x != '']
    partes_ruta.append(ruta_actual)

    # Crea una lista para almacenar las rutas anteriores desde el root hasta el directorio actual
    listas_rutas_anteriores: list = []
    for n in range(1, len(partes_ruta)):
        ruta_partes = partes_ruta[:len(partes_ruta) - n]
        
        # Si solo queda "C:", lo convertimos a "C:\\"
        if len(ruta_partes) == 1 and ':' in ruta_partes[0]:
            ruta = ruta_partes[0] + os.sep
        else:
            # Construye rutas anteriores de forma progresiva
            ruta = os.sep.join(ruta_partes)
        
        listas_rutas_anteriores.append(ruta)

        
    listaRutas: list = []
    # Agrega cada ruta previa construida a la lista
    for ruta in listas_rutas_anteriores:
        listaRutas.append(ruta)
        
    return listaRutas

listaRutas = obtener_rutas()



for ruta in listaRutas:
    archivos = obtener_archivos(ruta)
    for archivo in archivos:
        print(f"Ruta({ruta}): ",archivo,"\n")

    

    