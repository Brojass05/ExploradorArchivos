from tkinter import *
from tkinter import filedialog, ttk
import os
import platform

class ExploradorArchivos(ttk.Frame):
    def __init__(self):
        # Crear la ventana principal
        self.window = Tk()
        self.window.title("Explorador de Archivos")
        self.window.config(background="white")
        self.sistema = platform.system()
        self.ruta_principal = os.getcwd()
        self.ventanaPrincipal()

    def ventanaPrincipal(self):
        self.browseFiles()
        
        self.indice_pestana_seleccionada = 0
        self.notebook.bind("<Double-Button-1>", self.obtener_pestana)
        
        self.window.mainloop()


    def obtener_pestana(self, event):
        x, y = event.x, event.y
        try:
            indice = self.notebook.index(f"@{x},{y}")
            self.indice_pestana_seleccionada = indice
            print(f"Pestaña seleccionada: {indice}")
            
            # Ahora puedes hacer algo con self.listas[indice]
            self.listas[indice].bind("<Double-Button-1>", self.on_archivo_seleccionado)
            
        except Exception as e:
            print("No se seleccionó una pestaña válida:", e)

    # Arreglar la seleccion
    def abrir_archivo(self, rutaArchivo: str):
        print("Abriendo")
        # recibe una ruta y dependiendo del tipo de sistema en el que se ejecuta hara una u otra ejecucion
        if self.sistema == "Windows":
            os.startfile(rutaArchivo)
        elif self.sistema == "Darwin":  # macOS
            os.system(f"open \"{rutaArchivo}\"")
        elif self.sistema == "Linux":
            os.system(f"xdg-open \"{rutaArchivo}\"")
        else:
            raise Exception(f"Sistema operativo no soportado: {self.sistema}")
        self.ruta_anterior: str = rutaArchivo.split(rutaArchivo.split('\\')[-1])[0].rstrip('\\')
    
    def on_archivo_seleccionado(self, event, carpeta):
        lista: str = self.listas[carpeta]
        ruta: str = self.ruta_principal.split(carpeta)[0]
        print(f"Ruta: {ruta}")
        print("Lista: ",carpeta,"\n")
        ruta1 = ruta + carpeta
        print(f"Ruta1: {ruta1}")

        selected_indices = lista.curselection()
        if selected_indices:
            for i in selected_indices:
                archivo = lista.get(i)                
                try:
                    ruta_archivo = os.path.join(ruta1, archivo)
                except Exception as e:
                    pass
                self.abrir_archivo(ruta_archivo)


    def browseFiles(self):
        lista_rutas = self.obtener_rutas()
        carpetas: list = str(lista_rutas[0]).split("\\")
        # crea la ventana emergente para la vista del notebook
        self.notebook = ttk.Notebook(self.window)
        lista_rutas.reverse()

        # Recorremos cada carpeta de la ruta actual desglosada
        self.listas = {}  # Diccionario para guardar los Listbox
        for i, carpeta in enumerate(carpetas):
            frame = Frame(self.notebook)
            label = Label(frame, text=f"Contenido de carpeta: {carpeta}")
            label.pack(padx=10, pady=10)

            lista = Listbox(frame, width=50)
            archivos_en_ruta = self.obtener_archivos(lista_rutas[i])
            for archivos in archivos_en_ruta:
                for archivo in archivos:
                    lista.insert(END, archivo)
            lista.pack(padx=10, pady=10)
            lista.bind("<Double-Button-1>", lambda event, c=carpeta: self.on_archivo_seleccionado(event, c))
            # Guardar el Listbox en el diccionario usando la carpeta como clave
            self.listas[carpeta] = lista

            self.notebook.add(frame, text=carpeta)

        # Finalmente, empacamos el notebook para que se muestre en la ventana
        self.notebook.pack(fill='both', expand=True)


            
    def obtener_archivos(self,ruta_actual):
        # Listas que guardarán las rutas completas y los nombres de archivos por ruta
        listaRutas: list = self.obtener_rutas() 
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
    
    def obtener_rutas(self):
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
if __name__ == "__main__":
    explorador = ExploradorArchivos()