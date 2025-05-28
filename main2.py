from tkinter import *
from tkinter import filedialog, ttk
import os
import platform

class ExploradorArchivos(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill='both', expand=True)

        self.sistema = platform.system()
        self.master = master
        self.master.title("Explorador de Archivos")
        self.master.config(background="white")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.pagina_inicio = Frame(self.notebook)
        self.notebook.add(self.pagina_inicio, text="Inicio")

        self.lista = Listbox()  # se redefinirá luego en browseFiles

        self.ventanaPrincipal()

    def ventanaPrincipal(self):
        label_file_explorer = Label(self.pagina_inicio, 
                                    text="File Explorer using Tkinter",
                                    width=100, height=4, 
                                    fg="blue")
        
        button_explore = Button(self.pagina_inicio, 
                                text="Browse Files",
                                command=self.browseFiles)
        
        button_exit = Button(self.pagina_inicio, 
                             text="Exit",
                             command=self.master.quit)
        
        label_file_explorer.grid(column=1, row=1)
        button_explore.grid(column=1, row=2)
        button_exit.grid(column=1, row=3)

    def abrir_archivo(self, rutaArchivo: str):
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
            ruta_actual = os.getcwd()
            archivos_en_ruta = os.listdir(ruta_actual)
        except Exception as e:
            print(f"Error al acceder a la ruta: {e}")
            return
        
        self.partes_ruta = [x for x in ruta_actual.split('\\') if x != '']
        self.ruta1: str = ruta_actual.split(self.partes_ruta[-1])[0].rstrip('\\')

        listaRutas: list = []
        nombreArchivos: list = []
        for archivo in archivos_en_ruta:
            listaRutas.append(os.path.join(self.ruta1, archivo))
            nombreArchivos.append(archivo)

        frame_nuevo = Frame(self.notebook)

        for i, carpeta in enumerate(self.partes_ruta): 
            label = Label(frame_nuevo, text=f"Carpeta actual: {carpeta}")
            label.pack(padx=10, pady=5)

        self.lista = Listbox(frame_nuevo, width=50)
        for archivo in archivos_en_ruta:
            self.lista.insert(END, archivo)
        self.lista.pack(padx=10, pady=10)
        self.lista.bind("<Double-Button-1>", self.on_archivo_seleccionado)

        self.notebook.add(frame_nuevo, text=self.partes_ruta[-1])
        self.notebook.select(frame_nuevo)

    def on_archivo_seleccionado(self, event):
        seleccion = self.lista.curselection()
        if seleccion:
            archivo = self.lista.get(seleccion[0])
            ruta_archivo = os.path.join(os.getcwd(), archivo)
            print(f"Archivo seleccionado: {ruta_archivo}")
            self.abrir_archivo(ruta_archivo)

if __name__ == "__main__":
    root = Tk()
    app = ExploradorArchivos(root)
    root.mainloop()
