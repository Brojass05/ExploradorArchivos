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
        self.lista = Listbox()
    

    def ventanaPrincipal(self):
        label_file_explorer = Label(self.window, 
                                    text="File Explorer using Tkinter",
                                    width=100, height=4, 
                                    fg="blue")
        
        button_explore = Button(self.window, 
                                text="Browse Files",
                                command=self.browseFiles)
        
        button_exit = Button(self.window, 
                             text="Exit",
                             command=self.window.quit)
        
        label_file_explorer.grid(column=1, row=1)
        button_explore.grid(column=1, row=2)
        button_exit.grid(column=1, row=3)
        
        self.lista.bind("<Double-Button-1>", lambda event: self.on_archivo_seleccionado(event))


        self.window.mainloop()
        
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
        print(self.ruta_anterior)
    
    def on_archivo_seleccionado(self, event):
        seleccion = self.lista.curselection()
        print("Seleccion: ",seleccion)
        if seleccion:
            archivo = self.lista.get(seleccion[0])

            # Usa la ruta asociada al listbox, no os.getcwd()
            ruta_base = getattr(self.lista, 'ruta_base', os.getcwd())
            ruta_archivo = os.path.join(ruta_base, archivo)

            print(f"Archivo seleccionado: {ruta_archivo}")
            self.abrir_archivo(ruta_archivo)

        
    def browseFiles(self):
        lista_rutas = self.obtener_rutas() 
        carpetas: list = str(lista_rutas[0]).split("\\")
        # crea la ventana emergente para la vista del notebook
        ventana_carpetas = Toplevel(self.window)
        ventana_carpetas.title("Archivos")
        notebook = ttk.Notebook(ventana_carpetas)
        lista_rutas.reverse()

        # Recorremos cada carpeta de la ruta actual desglosada
        for i, carpeta in enumerate(carpetas):
            # Creamos un nuevo frame (pestaña) para agregar al notebook
            frame = Frame(notebook)
            
            # Agregamos un label que muestra qué carpeta representa esta pestaña
            label = Label(frame, text=f"Contenido de carpeta: {carpeta}")
            label.pack(padx=10, pady=10)

            # Creamos un Listbox para mostrar los archivos
            self.lista = Listbox(frame, width=50)
            # Insertamos cada archivo dentro del Listbox
            ruta = lista_rutas[i]
            archivos_en_ruta = self.obtener_archivos(ruta)
            for archivos in archivos_en_ruta:
                for archivo in archivos:
                    self.lista.insert(END, archivo)
            # Empaquetamos el Listbox en el frame
            self.lista.pack(padx=10, pady=10)

            # Agregamos el frame al notebook como una nueva pestaña con el nombre de la carpeta
            notebook.add(frame, text=carpeta)

        # Finalmente, empacamos el notebook para que se muestre en la ventana
        notebook.pack(fill='both', expand=True)


            
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
    explorador.ventanaPrincipal()
