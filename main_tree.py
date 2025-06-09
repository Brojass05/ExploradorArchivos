from tkinter import *
from tkinter import ttk
import os
import platform

class ExploradorArchivos:
    def __init__(self):
        self.window = Tk()
        self.window.title("Explorador de Archivos")
        self.window.geometry("800x500")
        self.sistema = platform.system()
        self.ruta_principal = os.getcwd()
        self.tree = None
        self.crear_arbol()
        self.window.mainloop()

    def crear_arbol(self):
        self.tree = ttk.Treeview(self.window)
        self.tree.pack(fill=BOTH, expand=True)

        path_inicial = os.getcwd()
        nodo_root = self.tree.insert('', 'end', text=path_inicial, open=True, values=[path_inicial])
        self.insertar_directorios(nodo_root, path_inicial)

        self.tree.bind("<Double-Button-1>", self.abrir_item)
        self.tree.bind("<Button-1>", self.on_expandir_si_necesario)

    def insertar_directorios(self, padre, ruta):
        try:
            for item in os.listdir(ruta):
                ruta_completa = os.path.join(ruta, item)
                if os.path.isdir(ruta_completa):
                    nodo = self.tree.insert(padre, 'end', text=item, values=[ruta_completa])
                    self.tree.insert(nodo, 'end', text='')  # Nodo temporal para permitir expansión
                else:
                    self.tree.insert(padre, 'end', text=item, values=[ruta_completa])
        except Exception as e:
            print(f"Error accediendo a {ruta}: {e}")

    def on_expandir_si_necesario(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "tree":
            item = self.tree.identify_row(event.y)
            if item:
                hijos = self.tree.get_children(item)
                if len(hijos) == 1 and self.tree.item(hijos[0], 'text') == '':
                    self.tree.delete(hijos[0])
                    ruta = self.tree.item(item, 'values')[0]
                    self.insertar_directorios(item, ruta)

    def abrir_item(self, event):
        item = self.tree.focus()
        ruta = self.tree.item(item, 'values')[0]
        if os.path.isfile(ruta):
            self.abrir_archivo(ruta)

    def abrir_archivo(self, rutaArchivo: str):
        print(f"Abriendo archivo: {rutaArchivo}")
        if self.sistema == "Windows":
            os.startfile(rutaArchivo)
        elif self.sistema == "Darwin":
            os.system(f"open \"{rutaArchivo}\"")
        elif self.sistema == "Linux":
            os.system(f"xdg-open \"{rutaArchivo}\"")
        else:
            raise Exception(f"Sistema operativo no soportado: {self.sistema}")

if __name__ == "__main__":
    ExploradorArchivos()
