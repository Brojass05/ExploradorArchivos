from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileSystemModel, QTreeView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSplitter, QMenu, QInputDialog, 
    QMessageBox, QDialog, QLabel, QLineEdit, QComboBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QModelIndex
import win32api
import os
import sys
import platform
import subprocess
import ctypes
from ctypes import wintypes

class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Explorador de Archivos")
        self.setGeometry(100, 100, 1000, 600)
    
        # Obtener el sistema del equipo
        self.sistema = platform.system() 

        # Modelo del sistema de archivos
        self.model = QFileSystemModel()
        self.model.setRootPath('')

        
        # Lista para guardar archivos
        self.lista_archivos = []

        # Árbol de directorios
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(''))
        self.tree.setColumnWidth(0, 300)
        self.tree.clicked.connect(self.on_tree_clicked)
        
        
        # Habilitar el menú contextual personalizado en el árbol
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_tree_right_click)
        
        
        # Panel derecho: tabla de archivos
        self.right_panel = QTableWidget()
        self.right_panel.setColumnCount(2)
        self.right_panel.setHorizontalHeaderLabels(["Archivo", "Tamaño (KB)"])
        self.right_panel.setColumnWidth(0, 300)
        self.right_panel.doubleClicked.connect(self.on_right_panel_item_click)

        # Splitter para dividir los paneles
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 700])

        # Widget central
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_tree_right_click(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return
        file: str = index.data()
        inicio=file.index("(")
        final=file.index(")")
        Letra = file[inicio + 1 : final]
        
        # Menu al hacer Click Derecho
        menu = QMenu()
        # Opciones
        menu.addAction("Abrir carpeta")
        menu.addAction("Propiedades")
        menu.addAction("Renombrar")
        menu.addAction("Formatear")
        
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        if action:
            accion = action.text()
            print(f"Acción seleccionada: {accion}")
            match accion:
                case "Renombrar":
                    if Letra != "C:":
                        text, ok = QInputDialog.getText(self, f'Renombrar disco{Letra}', 'Nombre: ')
                        if ok:
                            nuevo_nombre = text
                            print(nuevo_nombre)
                            subprocess.run(["label", Letra, nuevo_nombre], shell=True)
                    else:
                        msg = QMessageBox()
                        msg.setWindowTitle("Error")
                        msg.setText("El disco principal no se puede renombrar.")
                        msg.setIcon(QMessageBox.Information)
                        msg.exec_()
                        
                case "Propiedades":
                    if os.name == "nt": print("Windows")
                    
                case "Formatear":
                    etiqueta, sistema_archivos = obtener_valores()
                    self.formatear_disco(Letra, sistema_archivos, etiqueta)
       
    def formatear_disco(self, letra, sistema_archivo, nuevo_nombre):
        subprocess.run(["format", letra, f"/FS:{sistema_archivo}", "/Q", f"/V:{nuevo_nombre}", "/Y"], shell=True)
        # AGREGAR ACTUALIZACION DE TREEVIEW
                
    def on_right_panel_item_click(self, index: QModelIndex):
        try:
            rutaArchivo = self.lista_archivos[index.row()]
            if self.sistema == "Windows":
                os.startfile(rutaArchivo)
            elif self.sistema == "Darwin":  # macOS
                os.system(f"open \"{rutaArchivo}\"")
            elif self.sistema == "Linux":
                os.system(f"xdg-open \"{rutaArchivo}\"")
            else:
                raise Exception(f"Sistema operativo no soportado: {self.sistema}")
            print(rutaArchivo)
        except Exception as e:
            print(f"Error: {e}")
    

    def on_tree_clicked(self, index: QModelIndex):
        """Actualiza el panel derecho con los archivos de la carpeta seleccionada."""
        ruta = self.model.filePath(index)
        archivos = self.obtener_archivos_de_ruta(ruta)
        self.lista_archivos = archivos

        self.right_panel.setRowCount(len(archivos))
        for row, archivo in enumerate(archivos):
            nombre = os.path.basename(archivo)
            tamaño_kb = round(os.path.getsize(archivo) / 1024, 2)

            self.right_panel.setItem(row, 0, QTableWidgetItem(nombre))
            self.right_panel.setItem(row, 1, QTableWidgetItem(f"{tamaño_kb}"))

    def obtener_archivos_de_ruta(self, ruta):
        """Devuelve una lista con los archivos (no carpetas) de una ruta."""
        index = self.model.index(ruta)
        total = self.model.rowCount(index)
        archivos = []

        for i in range(total):
            child_index = self.model.index(i, 0, index)
            if self.model.isDir(child_index):
                continue
            archivos.append(self.model.filePath(child_index))
        return archivos
    

class DialogoEntradaCombo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Entrada con opciones")

        # Widgets
        self.label = QLabel("Escriba un nombre o elija una opción:")
        self.line_edit = QLineEdit()
        self.combo_box = QComboBox()
        self.combo_box.addItems(["NTFS", "FAT32"])

        # Botones
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.combo_box)
        layout.addWidget(self.botones)

        self.setLayout(layout)

    def obtener_datos(self):
        return self.line_edit.text(), self.combo_box.currentText()

def obtener_valores():
    dialogo = DialogoEntradaCombo()
    if dialogo.exec_() == QDialog.Accepted:
        texto, opcion = dialogo.obtener_datos()
        return texto, opcion
    return None, None

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileExplorer()
    window.show()
    sys.exit(app.exec_())
