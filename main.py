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
        self.lista.bind("<Key>", self.on_archivo_seleccionado)

        self.window.mainloop()
        
    def abrir_archivo(self, rutaArchivo: str):
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
        
    def browseFiles(self):
        try:
            # obtiene la ruta actual del directorio
            ruta_actual = os.getcwd()
            # obtiene los archivos que estan en la ruta actual
            archivos_en_ruta = os.listdir(ruta_actual)
        except Exception as e:
            print(f"Error al acceder a la ruta: {e}")
            return
        #  divide la ruta actual en partes para crear pestanas
        self.partes_ruta = [x for x in ruta_actual.split('\\') if x != '']
        # obtiene la ruta anterior sacando el ultimo nombre y eliminando el ultimo \
        self.ruta_anterior: str = ruta_actual.split(self.partes_ruta[-1])[0].rstrip('\\')
        # crea listas para las rutas y los nombres de los archivos
        lista_rutas_archivos: list = []
        nombreArchivos: list = []
        listas_rutas_anteriores: list = []
        
        for n in range(1, len(self.partes_ruta)):
            ruta = ruta_actual.split(self.partes_ruta[-n])[0].rstrip('\\')
            listas_rutas_anteriores.append(ruta)
        
        
        # ciclo for para ir agregando las rutas y los nombres a sus listas respectivas
        for i in range(0,len(archivos_en_ruta)):
            # agrega la ruta a la lista desde C:, hasta la ruta actual
            lista_rutas_archivos.append(os.path.join(self.ruta_anterior, str(archivos_en_ruta[i])))
            # agrega los nombres de los archivos dentro de la ruta actual
            nombreArchivos.append(archivos_en_ruta[i])
        
        
        # crea la ventana emergente para la vista del notebook
        ventana_carpetas = Toplevel(self.window)
        ventana_carpetas.title("Archivos")
        notebook = ttk.Notebook(ventana_carpetas)

        # Recorremos cada carpeta de la ruta actual desglosada
        for i, carpeta in enumerate(self.partes_ruta): 
            # Creamos un nuevo frame (pestaña) para agregar al notebook
            frame = Frame(notebook)

            # Agregamos un label que muestra qué carpeta representa esta pestaña
            label = Label(frame, text=f"Contenido de carpeta: {carpeta}")
            label.pack(padx=10, pady=10)

            # Creamos un Listbox para mostrar los archivos
            self.lista = Listbox(frame, width=50)
            nuevos_archivos_en_ruta: list = os.listdir(lista_rutas_archivos[i])
            # Insertamos cada archivo dentro del Listbox
            for archivo in nuevos_archivos_en_ruta:
                self.lista.insert(END, archivo)

            # Empaquetamos el Listbox en el frame
            self.lista.pack(padx=10, pady=10)


            # Solo agregamos los archivos visibles en la última pestaña,
            # que representa la carpeta final (la ruta actual completa)
            '''if i == len(self.partes_ruta) - 1:
                # Creamos un Listbox para mostrar los archivos
                self.lista = Listbox(frame, width=50)
                
                # Insertamos cada archivo dentro del Listbox
                for archivo in archivos_en_ruta:
                    self.lista.insert(END, archivo)

                # Empaquetamos el Listbox en el frame
                self.lista.pack(padx=10, pady=10)'''

            # Agregamos el frame al notebook como una nueva pestaña con el nombre de la carpeta
            notebook.add(frame, text=carpeta)

        # Finalmente, empacamos el notebook para que se muestre en la ventana
        notebook.pack(fill='both', expand=True)

    def on_archivo_seleccionado(self,event):
        seleccion = self.lista.curselection()
        if seleccion:
            archivo = self.lista.get(seleccion[0])
            ruta_archivo = os.path.join(os.getcwd(), archivo)
            print(f"Archivo seleccionado: {ruta_archivo}")
            self.abrir_archivo(ruta_archivo)
if __name__ == "__main__":
    explorador = ExploradorArchivos()
    explorador.ventanaPrincipal()
