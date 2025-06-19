from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileSystemModel, QTreeView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSplitter, QMenu, QInputDialog, 
    QMessageBox, QDialog, QLabel, QLineEdit, QComboBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp
import win32api
import os
import sys
import platform
import subprocess
import ctypes
import json
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
        #splitter.setSizes([300, 700])

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
        inicio = file.index("(")
        final = file.index(")")
        Letra = file[inicio + 1 : final]

        # Menu al hacer Click Derecho
        menu = QMenu()
        
        # Opciones
        menu.addAction("Renombrar")
        menu.addAction("Formatear")
        menu.addAction("Crear particion")
        
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
                            subprocess.run(["label", Letra, nuevo_nombre], shell=True)
                    else:
                        QMessageBox.warning(self,"Error","El disco C: no se puede renombrar")
                    
                case "Formatear":
                    if Letra != "C:":
                        etiqueta, sistema_archivos = obtener_valores_formateo()
                        if etiqueta is not None and sistema_archivos is not None:
                            reply = QMessageBox.question(None, 'Desea continuar', f'Desea formatear el disco: {Letra}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            if reply == QMessageBox.Yes:
                                self.formatear_disco(Letra, sistema_archivos, etiqueta)
                                    # Aquí puedes poner el código que se ejecuta si el usuario elige Sí
                    else:
                        QMessageBox.warning(self,"Error","El disco C: no se puede formatear")
                                                
                case "Crear particion":                        
                    # Obtiene el disco al que pertenece la particion siesque aplica
                    info = self.obtener_disco_fisico(Letra)
                    disco_num = info['Number']
                    max_espacio = round(info["LargestFreeExtent"] / (1024 ** 2), 2)
                    print(max_espacio)
                    tamano_particion, nueva_letra = obtener_valores_particiones(max_espacio)
                    if tamano_particion is not None and nueva_letra is not None:
                        reply = QMessageBox.question(None, 'Desea continuar', f'Desea particionar el disco: {Letra}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            self.crear_particion(disco_num,tamano_particion,nueva_letra)
       
    def formatear_disco(self, letra, sistema_archivo, nuevo_nombre):
        try:
            subprocess.run(["format", letra, f"/FS:{sistema_archivo}", "/Q", f"/V:{nuevo_nombre}", "/Y"], shell=True)
            QMessageBox.information(self, 'Proceso completado', 'El disco se ha formateado correctamente')
        except Exception as e:
            QMessageBox.warning(self, 'Error de formateo', f'Hubo un error al formatear el disco \n Error: {e}')
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
        except Exception as e:
            QMessageBox.warning(self,"Error",f"Error al abrir el archivo: {e}")
    

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
    
    def obtener_disco_fisico(self,letra_unidad):
        letra = letra_unidad.strip(":").upper()
        cmd = [
            "powershell.exe",
            "-Command",
            f"""
            $disk = Get-Partition -DriveLetter {letra} | Get-Disk;
            $info = [PSCustomObject]@{{
                Number = $disk.Number;
                FriendlyName = $disk.FriendlyName;
                SerialNumber = $disk.SerialNumber;
                Size = $disk.Size;
                LargestFreeExtent = $disk.LargestFreeExtent
            }};
            $info | ConvertTo-Json
            """
        ]
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        if resultado.returncode == 0:
            try:
                datos = json.loads(resultado.stdout)
                return datos  # Devuelve dict con 'Number', 'FriendlyName', etc.
            except json.JSONDecodeError:
                print("No se pudo decodificar la salida JSON.")
        else:
            print("Error al obtener información del disco:", resultado.stderr)
        return None
    
    def crear_particion(self,disco_id, tamaño_MB, letra):
        comando = f'''
            powershell -Command "
                $part = New-Partition -DiskNumber {disco_id} -Size {tamaño_MB}MB -AssignDriveLetter;
                Format-Volume -DriveLetter $part.DriveLetter -FileSystem NTFS -NewFileSystemLabel 'NuevaParticion' -Confirm:$false;
                Set-Partition -DriveLetter $part.DriveLetter -NewDriveLetter {letra}
            "
        '''

        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        if resultado.returncode == 0:
            QMessageBox.information(self,"Particion creada","Partición creada con éxito.")
        else:
            QMessageBox.warning(self,"Error en particion",f"Error al crear partición: \n {resultado.stderr}")
    

class InputFormateo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Formateo Discos")

        # Widgets
        self.label = QLabel("Escriba un nombre y elija una opción:")
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
        if self.line_edit.text() is not None and self.combo_box.currentText() is not None:
            return self.line_edit.text(), self.combo_box.currentText()
        else:
            QMessageBox.warning(self,"Error formateo", "Rellene todos los campos para formatear")
        return None, None

def obtener_valores_formateo():
    dialogo = InputFormateo()
    if dialogo.exec_() == QDialog.Accepted:
        texto, opcion = dialogo.obtener_datos()
        return texto, opcion
    return None, None

class InputParticion(QDialog):
    def __init__(self, espacio_maximo ,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Particionar Discos")
        # Widgets
        self.label_tamano = QLabel("Indique el tamaño de la partición (MB):")
        self.input_tamano = QLineEdit()
        self.input_tamano.setValidator(QIntValidator(1, espacio_maximo))  # Solo números enteros positivos

        self.label_letra = QLabel("Indique la letra de la nueva partición:")
        self.input_letra = QLineEdit()
        self.input_letra.setMaxLength(1)  # Solo un caracter
        self.input_letra.setValidator(QRegExpValidator(QRegExp("[A-Za-z]")))  # Solo letras

        # Botones
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_tamano)
        layout.addWidget(self.input_tamano)
        layout.addWidget(self.label_letra)
        layout.addWidget(self.input_letra)
        layout.addWidget(self.botones)
        self.setLayout(layout)

    def obtener_datos(self):
        tamano_texto = self.input_tamano.text().strip()
        letra_texto = self.input_letra.text().strip().upper()

        if not tamano_texto or not letra_texto:
            QMessageBox.warning(self, "Error", "Debe completar ambos campos.")
            return None, None

        return int(tamano_texto), letra_texto

def obtener_valores_particiones(espacio_maximo):
    dialogo = InputParticion(espacio_maximo)
    if dialogo.exec_() == QDialog.Accepted:
        tam, letra = dialogo.obtener_datos()
        if tam is not None and letra is not None:
            print(f"Tamaño: {tam} MB | Letra: {letra}")
            return tam, letra
    return None, None


    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileExplorer()
    window.show()
    sys.exit(app.exec_())
