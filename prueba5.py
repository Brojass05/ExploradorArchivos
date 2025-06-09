import sys  # Importa el módulo sys para acceder a argumentos y funciones del sistema
import os   # Importa el módulo os para operaciones del sistema operativo (no se usa en este código)
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileSystemModel, QTreeView
# Importa los widgets necesarios de PyQt5 para crear la interfaz gráfica

class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()  # Inicializa la clase base QMainWindow
        self.setWindowTitle("Explorador de Archivos")  # Título de la ventana
        self.setGeometry(100, 100, 800, 600)  # Posición y tamaño de la ventana

        model = QFileSystemModel()  # Modelo que representa el sistema de archivos
        model.setRootPath('')  # Establece la raíz del sistema de archivos (vacío para todo el sistema)

        tree = QTreeView()  # Crea un widget de vista en árbol para mostrar archivos y carpetas
        tree.setModel(model)  # Asocia el modelo de archivos al árbol
        
        # Establece el directorio raíz que se mostrará en el árbol (puedes cambiar la ruta)
        tree.setRootIndex(model.index(r'C:\Users\benja\Desktop\Office Universidad\5 Semestre\Sistema Operativo\ExploradorArchivos'))
        tree.setColumnWidth(0, 250)  # Ancho de la columna de nombres de archivos/carpetas

        self.setCentralWidget(tree)  # Coloca el árbol como widget central de la ventana

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Crea la aplicación Qt
    window = FileExplorer()       # Instancia la ventana principal
    window.show()                 # Muestra la ventana
    sys.exit(app.exec_())         # Ejecuta el bucle principal de la aplicación