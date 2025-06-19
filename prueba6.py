from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileSystemModel, QTreeView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSplitter, QMenu, QInputDialog, 
    QMessageBox, QDialog, QLabel, QLineEdit, QComboBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp
import win32api # Usado para interacciones específicas de Windows (no directamente en el código proporcionado, pero importado).
import os # Módulo para interactuar con el sistema operativo, como rutas de archivos y directorios.
import sys # Módulo para acceder a parámetros y funciones específicos del sistema, como la gestión de la aplicación.
import platform # Módulo para acceder a datos de la plataforma subyacente, como el sistema operativo.
import subprocess # Módulo para ejecutar nuevos procesos y gestionar sus entradas/salidas.
import ctypes # Módulo para interactuar con tipos de datos de C y llamar a funciones en DLLs/bibliotecas compartidas (no directamente usado, pero importado).
import json # Módulo para codificar y decodificar datos JSON.
from ctypes import wintypes # Tipos de datos específicos de Windows para ctypes (no directamente usado, pero importado).

# Clase principal de la aplicación, hereda de QMainWindow para crear una ventana de aplicación.
class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__() # Llama al constructor de la clase base QMainWindow.
        self.setWindowTitle("Explorador de Archivos") # Establece el título de la ventana.
        self.setGeometry(100, 100, 1000, 600) # Define la posición y tamaño inicial de la ventana (x, y, ancho, alto).
    
        # Obtener el sistema operativo del equipo (ej. 'Windows', 'Darwin' para macOS, 'Linux').
        self.sistema = platform.system() 

        # Modelo del sistema de archivos. QFileSystemModel proporciona un modelo de datos para el sistema de archivos local.
        self.model = QFileSystemModel()
        self.model.setRootPath('') # Establece la raíz del modelo al directorio principal del sistema.
        
        # Lista para almacenar las rutas completas de los archivos mostrados en el panel derecho.
        self.lista_archivos = []

        # Árbol de directorios (QTreeView). Muestra la jerarquía del sistema de archivos.
        self.tree = QTreeView()
        self.tree.setModel(self.model) # Asocia el modelo de sistema de archivos al QTreeView.
        self.tree.setRootIndex(self.model.index('')) # Muestra el contenido del directorio raíz.
        self.tree.setColumnWidth(0, 300) # Establece el ancho de la primera columna (nombre del archivo/directorio).
        self.tree.clicked.connect(self.on_tree_clicked) # Conecta el evento de clic en el árbol a un método.
        
        # Habilitar el menú contextual personalizado en el árbol (clic derecho).
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_tree_right_click) # Conecta el evento de clic derecho a un método.
        
        # Panel derecho: tabla de archivos (QTableWidget). Muestra los archivos del directorio seleccionado.
        self.right_panel = QTableWidget()
        self.right_panel.setColumnCount(2) # Define dos columnas: "Archivo" y "Tamaño (KB)".
        self.right_panel.setHorizontalHeaderLabels(["Archivo", "Tamaño (KB)"]) # Establece los encabezados de las columnas.
        self.right_panel.setColumnWidth(0, 300) # Establece el ancho de la primera columna.
        self.right_panel.doubleClicked.connect(self.on_right_panel_item_click) # Conecta el doble clic en un elemento a un método.

        # Splitter (QSplitter) para dividir la ventana y permitir redimensionar los paneles.
        splitter = QSplitter(Qt.Horizontal) # Splitter horizontal para dividir la ventana verticalmente.
        splitter.addWidget(self.tree) # Añade el árbol al splitter.
        splitter.addWidget(self.right_panel) # Añade el panel derecho al splitter.
        # splitter.setSizes([300, 700]) # Podría usarse para establecer los tamaños iniciales de los paneles.

        # Widget contenedor para el layout principal de la ventana.
        container = QWidget()
        layout = QVBoxLayout() # Layout vertical para organizar los widgets.
        layout.addWidget(splitter) # Añade el splitter al layout.
        container.setLayout(layout) # Establece el layout para el contenedor.
        self.setCentralWidget(container) # Establece el contenedor como el widget central de la ventana principal.

    # Método para manejar el clic derecho en el QTreeView (menú contextual).
    def on_tree_right_click(self, position):
        try:
            # Obtiene el índice del elemento sobre el que se hizo clic.
            index = self.tree.indexAt(position)
            if not index.isValid(): # Si el índice no es válido (se hizo clic en un espacio vacío), no hacer nada.
                return
            
            # Obtiene el nombre del archivo/directorio seleccionado.
            file: str = index.data()
            
            # Intenta extraer la letra de la unidad de la cadena del archivo (ej. "(C:)").
            # Esto asume que solo se hará clic derecho en las unidades raíz para las acciones de disco.
            inicio = file.index("(")
            final = file.index(")")
            Letra = file[inicio + 1 : final] # Extrae la letra de la unidad (ej. "C:").

            # Crea un menú contextual.
            menu = QMenu()
            
            # Añade acciones al menú.
            menu.addAction("Renombrar")
            menu.addAction("Formatear")
            menu.addAction("Crear particion")
            
            # Ejecuta el menú en la posición del clic derecho y obtiene la acción seleccionada.
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            if action: # Si se seleccionó una acción.
                accion = action.text() # Obtiene el texto de la acción seleccionada.
                print(f"Acción seleccionada: {accion}") # Imprime la acción para depuración.
                
                # Usa una sentencia match para ejecutar la lógica según la acción seleccionada.
                match accion:
                    case "Renombrar":
                        if Letra != "C:": # No permite renombrar la unidad C:.
                            # Pide al usuario un nuevo nombre para la unidad.
                            text, ok = QInputDialog.getText(self, f'Renombrar disco {Letra}', 'Nombre: ')
                            if ok: # Si el usuario hizo clic en OK.
                                nuevo_nombre = text
                                # Ejecuta el comando 'label' de Windows para renombrar la unidad.
                                subprocess.run(["label", Letra, nuevo_nombre], shell=True)
                        else:
                            QMessageBox.warning(self,"Error","El disco C: no se puede renombrar")
                        
                    case "Formatear":
                        if Letra != "C:": # No permite formatear la unidad C:.
                            # Abre un diálogo para obtener los parámetros de formateo (etiqueta y sistema de archivos).
                            etiqueta, sistema_archivos, seleccion = obtener_valores_formateo()
                            print(seleccion) # Imprime la selección para depuración.
                            if seleccion == True: # Si el usuario confirmó la selección en el diálogo.
                                # Pide confirmación antes de formatear.
                                reply = QMessageBox.question(None, 'Desea continuar', f'Desea formatear el disco: {Letra}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes: # Si el usuario confirma.
                                    self.formatear_disco(Letra, sistema_archivos, etiqueta) # Llama al método para formatear.
                        else:
                            QMessageBox.warning(self,"Error","El disco C: no se puede formatear")
                                                    
                    case "Crear particion": 
                        # Obtiene información del disco físico al que pertenece la unidad seleccionada.
                        info = self.obtener_disco_fisico(Letra)
                        disco_num = info['Number'] # Número de disco.
                        max_espacio = round(info["Size"] / (1024 ** 2), 2) # Espacio libre más grande en MB.
                        print(max_espacio) # Imprime el espacio máximo para depuración.
                        # Abre un diálogo para obtener el tamaño y la letra de la nueva partición.
                        tamano_particion, nueva_letra = obtener_valores_particiones(max_espacio)
                        if tamano_particion is not None and nueva_letra is not None: # Si se obtuvieron valores válidos.
                            # Pide confirmación antes de crear la partición.
                            reply = QMessageBox.question(None, 'Desea continuar', f'Desea particionar el disco: {Letra}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            if reply == QMessageBox.Yes: # Si el usuario confirma.
                                self.crear_particion(disco_num,tamano_particion,nueva_letra) # Llama al método para crear partición.
                                
        except Exception as e:
            # Captura cualquier excepción durante el clic derecho (ej. si no es una unidad).
            # pass # Ignora la excepción. Podrías añadir un QMessageBox.warning aquí si prefieres.
            QMessageBox.warning(self, "Error de operación", f"No se pudo realizar la operación seleccionada. Error: {e}")
        
    # Método para formatear un disco.
    def formatear_disco(self, letra, sistema_archivo, nuevo_nombre):
        try:
            # Ejecuta el comando 'format' de Windows.
            # /FS:{sistema_archivo}: especifica el sistema de archivos (NTFS/FAT32).
            # /Q: formateo rápido.
            # /V:{nuevo_nombre}: establece la etiqueta de volumen.
            # /Y: suprime la solicitud de confirmación.
            subprocess.run(["format", letra, f"/FS:{sistema_archivo}", "/Q", f"/V:{nuevo_nombre}", "/Y"], shell=True)
            self.tree.update() # Intenta actualizar la vista del árbol (aunque QFileSystemModel podría necesitar un refresh más explícito).
            QMessageBox.information(self, 'Proceso completado', 'El disco se ha formateado correctamente')
            
        except Exception as e:
            QMessageBox.warning(self, 'Error de formateo', f'Hubo un error al formatear el disco \n Error: {e}')
            # AGREGAR ACTUALIZACION DE TREEVIEW: Para una actualización más robusta,
            # podrías necesitar llamar a self.model.readDirectory() en la raíz o la unidad formateada,
            # o incluso reconstruir el QFileSystemModel si los cambios no se reflejan automáticamente.
                
    # Método para manejar el doble clic en un elemento del panel derecho (abrir archivo).
    def on_right_panel_item_click(self, index: QModelIndex):
        try:
            # Obtiene la ruta completa del archivo de la lista almacenada.
            rutaArchivo = self.lista_archivos[index.row()]
            
            # Abre el archivo según el sistema operativo.
            if self.sistema == "Windows":
                os.startfile(rutaArchivo) # Función específica de Windows para abrir archivos.
            elif self.sistema == "Darwin":  # macOS
                os.system(f"open \"{rutaArchivo}\"") # Comando 'open' en macOS.
            elif self.sistema == "Linux":
                os.system(f"xdg-open \"{rutaArchivo}\"") # Comando 'xdg-open' en Linux para abrir archivos con la aplicación predeterminada.
            else:
                raise Exception(f"Sistema operativo no soportado: {self.sistema}")
        except Exception as e:
            QMessageBox.warning(self,"Error",f"Error al abrir el archivo: {e}")
    
    # Método para actualizar el panel derecho con los archivos de la carpeta seleccionada en el árbol.
    def on_tree_clicked(self, index: QModelIndex):
        """Actualiza el panel derecho con los archivos de la carpeta seleccionada."""
        ruta = self.model.filePath(index) # Obtiene la ruta del elemento seleccionado en el árbol.
        archivos = self.obtener_archivos_de_ruta(ruta) # Obtiene la lista de archivos en esa ruta.
        self.lista_archivos = archivos # Almacena la lista de archivos para su posterior uso (ej. abrir).

        self.right_panel.setRowCount(len(archivos)) # Establece el número de filas en la tabla.
        # Itera sobre los archivos y los añade a la tabla.
        for row, archivo in enumerate(archivos):
            nombre = os.path.basename(archivo) # Obtiene solo el nombre del archivo.
            tamaño_kb = round(os.path.getsize(archivo) / 1024, 2) # Obtiene el tamaño en KB.

            self.right_panel.setItem(row, 0, QTableWidgetItem(nombre)) # Añade el nombre a la primera columna.
            self.right_panel.setItem(row, 1, QTableWidgetItem(f"{tamaño_kb}")) # Añade el tamaño a la segunda columna.

    # Método auxiliar para obtener solo los archivos (no directorios) de una ruta.
    def obtener_archivos_de_ruta(self, ruta):
        """Devuelve una lista con los archivos (no carpetas) de una ruta."""
        index = self.model.index(ruta) # Obtiene el índice del modelo para la ruta dada.
        total = self.model.rowCount(index) # Obtiene el número total de elementos (archivos y carpetas) en la ruta.
        archivos = []

        for i in range(total):
            child_index = self.model.index(i, 0, index) # Obtiene el índice de un hijo.
            if self.model.isDir(child_index): # Si es un directorio, lo salta.
                continue
            archivos.append(self.model.filePath(child_index)) # Si es un archivo, añade su ruta.
        return archivos
    
    # Método para obtener información del disco físico utilizando PowerShell.
    def obtener_disco_fisico(self,letra_unidad):
        letra = letra_unidad.strip(":").upper() # Normaliza la letra de la unidad.
        cmd = [
            "powershell.exe", # Comando para ejecutar PowerShell.
            "-Command", # Indica que el siguiente argumento es un comando.
            f"""
            $disk = Get-Partition -DriveLetter {letra} | Get-Disk; # Obtiene la partición por letra y luego el disco.
            $info = [PSCustomObject]@{{" # Crea un objeto personalizado con la información relevante.
                Number = $disk.Number;
                FriendlyName = $disk.FriendlyName;
                SerialNumber = $disk.SerialNumber;
                Size = $disk.Size;
                LargestFreeExtent = $disk.LargestFreeExtent # Espacio libre más grande en el disco.
            }};
            $info | ConvertTo-Json # Convierte el objeto a JSON para facilitar el parseo en Python.
            """
        ]
        # Ejecuta el comando PowerShell y captura la salida.
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        if resultado.returncode == 0: # Si el comando se ejecutó sin errores.
            try:
                datos = json.loads(resultado.stdout) # Parsea la salida JSON a un diccionario Python.
                return datos # Devuelve el diccionario con la información del disco.
            except json.JSONDecodeError:
                print("No se pudo decodificar la salida JSON.")
        else:
            print("Error al obtener información del disco:", resultado.stderr)
        return None # Retorna None si hubo un error.
    
    # Método para crear una partición en un disco.
    def crear_particion(self, disco_id, tamaño_MB, letra):
        # Asegura que la letra esté en mayúscula y sea solo un carácter.
        letra = str(letra).upper()[0]
        print("Letra: ", letra, " Disco: ",disco_id," tamano: ",tamaño_MB) # Imprime parámetros para depuración.
        comando = [
            "powershell",
            "-Command",
            (
                f"$part = New-Partition -DiskNumber {disco_id} -Size {tamaño_MB}MB -AssignDriveLetter;" # Crea una nueva partición.
                f"Format-Volume -DriveLetter $part.DriveLetter -FileSystem NTFS -NewFileSystemLabel 'NuevaParticion' -Confirm:$false;" # Formatea la nueva partición.
                f"Set-Partition -DriveLetter $part.DriveLetter -NewDriveLetter {letra}" # Asigna la letra deseada a la partición.
            )
        ]
        # Ejecuta el comando PowerShell.
        resultado = subprocess.run(comando, capture_output=True, text=True)
        if resultado.returncode == 0:
            QMessageBox.information(self, "Partición creada", "Partición creada con éxito.")
            # Similar al formateo, podrías necesitar una actualización explícita del QFileSystemModel aquí.
        else:
            QMessageBox.warning(self, "Error en partición", f"Error al crear partición:\n{resultado.stderr}")
    
# Clase para el diálogo de entrada de formateo de discos.
class InputFormateo(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Formateo Discos") # Título del diálogo.

        # Widgets del diálogo.
        self.label = QLabel("Escriba un nombre y elija una opción:")
        self.line_edit = QLineEdit() # Campo para el nombre de la etiqueta de volumen.
        self.combo_box = QComboBox() # ComboBox para seleccionar el sistema de archivos.
        self.combo_box.addItems(["NTFS", "FAT32"]) # Opciones de sistemas de archivos.

        # Botones de OK y Cancelar.
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept) # Conecta el botón OK al método accept del diálogo.
        self.botones.rejected.connect(self.reject) # Conecta el botón Cancelar al método reject del diálogo.
        self.botones.clicked.connect(self.on_boton_clickeado) # Conecta cualquier clic de botón a un método.

        # Layout del diálogo.
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.combo_box)
        layout.addWidget(self.botones)

        self.setLayout(layout)
        self.seleccion = False # Inicializa una bandera para saber si se aceptó o canceló el diálogo.
        
    # Método para manejar clics en los botones del diálogo (específicamente para rastrear la selección).
    def on_boton_clickeado(self, button):
        role = self.botones.buttonRole(button) # Obtiene el rol del botón presionado.
        if role == QDialogButtonBox.AcceptRole: # Si es el botón OK (o un rol de aceptación).
            self.seleccion = True
        elif role == QDialogButtonBox.RejectRole: # Si es el botón Cancelar (o un rol de rechazo).
            self.seleccion = False
    
    # Método para obtener los datos introducidos en el diálogo.
    def obtener_datos(self):
        # Verifica que los campos no estén vacíos.
        if self.line_edit.text() and self.combo_box.currentText():
            return self.line_edit.text(), self.combo_box.currentText(), self.seleccion
        else:
            QMessageBox.warning(self,"Error formateo", "Rellene todos los campos para formatear")
            return None, None, self.seleccion # Retorna None si hay campos vacíos.

# Función auxiliar para mostrar el diálogo de formateo y obtener sus valores.
def obtener_valores_formateo():
    dialogo = InputFormateo() # Crea una instancia del diálogo.
    if dialogo.exec_() == QDialog.Accepted: # Si el usuario hace clic en OK.
        texto, opcion, seleccion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
        return texto, opcion, seleccion # Retorna los valores.
    return None, None, False # Retorna None si se canceló.

# Clase para el diálogo de entrada para la creación de particiones.
class InputParticion(QDialog):
    def __init__(self, espacio_maximo ,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Particionar Discos") # Título del diálogo.
        
        self.label_max = QLabel(f"Espacio máximo disponible: {espacio_maximo} MB") # Muestra el espacio máximo.
        maxInt = int(espacio_maximo) # Convierte el espacio máximo a entero para el validador.
        
        # Widgets del diálogo.
        self.label_tamano = QLabel("Indique el tamaño de la partición (MB):")
        self.input_tamano = QLineEdit() # Campo para el tamaño de la partición.
        # Validador para asegurar que solo se ingresen números enteros entre 1 y el espacio máximo.
        self.input_tamano.setValidator(QIntValidator(1, maxInt)) 

        self.label_letra = QLabel("Indique la letra de la nueva partición:")
        self.input_letra = QLineEdit() # Campo para la letra de la nueva partición.
        self.input_letra.setMaxLength(1) # Solo permite un carácter.
        # Validador para asegurar que solo se ingresen letras.
        self.input_letra.setValidator(QRegExpValidator(QRegExp("[A-Za-z]"))) 

        # Botones de OK y Cancelar.
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)

        # Layout del diálogo.
        layout = QVBoxLayout()
        layout.addWidget(self.label_tamano)
        layout.addWidget(self.input_tamano)
        layout.addWidget(self.label_letra)
        layout.addWidget(self.input_letra)
        layout.addWidget(self.botones)
        layout.addWidget(self.label_max) # Añade la etiqueta de espacio máximo al layout.
        self.setLayout(layout)

    # Método para obtener los datos introducidos en el diálogo de partición.
    def obtener_datos(self):
        tamano_texto = self.input_tamano.text().strip() # Obtiene el texto del tamaño.
        letra_texto = self.input_letra.text().strip().upper() # Obtiene el texto de la letra, en mayúscula.

        if not tamano_texto or not letra_texto: # Si algún campo está vacío.
            QMessageBox.warning(self, "Error", "Debe completar ambos campos.")
            return None, None # Retorna None si hay campos vacíos.

        return int(tamano_texto), letra_texto # Retorna el tamaño como entero y la letra.

# Función auxiliar para mostrar el diálogo de partición y obtener sus valores.
def obtener_valores_particiones(espacio_maximo):
    dialogo = InputParticion(espacio_maximo) # Crea una instancia del diálogo, pasando el espacio máximo.
    if dialogo.exec_() == QDialog.Accepted: # Si el usuario hace clic en OK.
        tam, letra = dialogo.obtener_datos() # Obtiene los datos del diálogo.
        if tam is not None and letra is not None: # Si se obtuvieron valores válidos.
            print(f"Tamaño: {tam} MB | Letra: {letra}") # Imprime para depuración.
            return tam, letra # Retorna los valores.
    return None, None # Retorna None si se canceló o hubo un error.

# Bloque principal de ejecución cuando el script se ejecuta directamente.
if __name__ == "__main__":
    app = QApplication(sys.argv) # Crea una instancia de QApplication (necesaria para cualquier aplicación PyQt).
    window = FileExplorer() # Crea una instancia de la ventana principal de la aplicación.
    window.show() # Muestra la ventana.
    sys.exit(app.exec_()) # Inicia el bucle de eventos de la aplicación y espera a que la aplicación finalice.