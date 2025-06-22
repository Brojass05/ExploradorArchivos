from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileSystemModel, QTreeView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSplitter, QMenu, QInputDialog, 
    QMessageBox, QDialog, QLabel, QLineEdit, QComboBox, QDialogButtonBox, QHeaderView, QToolButton, QToolBar
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QIntValidator, QRegExpValidator, QIcon
from PyQt5.QtCore import QRegExp, QFileInfo
import string
import time
import ctypes
import win32api # Se usa para interacciones de bajo nivel con el sistema operativo Windows, aunque no se usa explícitamente en el código proporcionado.
import os # Módulo para interactuar con el sistema operativo, como rutas de archivos y directorios. Es fundamental para operaciones de sistema de archivos.
import sys # Módulo para acceder a parámetros y funciones específicos del sistema, como la gestión de la aplicación (e.g., sys.exit, sys.argv).
import platform # Módulo para acceder a datos de la plataforma subyacente, como el sistema operativo actual (e.g., 'Windows', 'Linux', 'Darwin').
import subprocess # Módulo para ejecutar nuevos procesos y gestionar sus entradas/salidas. Crucial para ejecutar comandos de sistema como 'format' o 'diskpart'.
import json # Módulo para codificar y decodificar datos JSON. Utilizado para procesar la salida de comandos de PowerShell.

# Clase principal de la aplicación, hereda de QMainWindow para crear una ventana de aplicación.
class FileExplorer(QMainWindow):
    """
    FileExplorer es una aplicación de escritorio que simula un explorador de archivos
    básico, permitiendo la navegación, gestión y manipulación de unidades, directorios y archivos.
    Ofrece funcionalidades como la visualización del árbol de directorios, listado de archivos,
    creación de carpetas, renombrado, borrado, formateo de unidades y creación de particiones.
    Utiliza PyQt5 para la interfaz gráfica y se integra con las funcionalidades
    nativas del sistema operativo (principalmente Windows) para operaciones de bajo nivel.
    """
    def __init__(self):
        """
        Constructor de la clase FileExplorer. Inicializa la interfaz de usuario,
        los modelos de datos y las conexiones de señales.
        """
        # Flag para subprocess que evita la creación de una ventana de consola.
        self.CREATE_NO_WINDOW = 0x08000000 
        super().__init__() # Llama al constructor de la clase base QMainWindow.
        self.setWindowTitle("Explorador de Archivos") # Establece el título de la ventana.
        self.setGeometry(100, 100, 1000, 600) # Define la posición y tamaño inicial de la ventana (x, y, ancho, alto).

        self.statusBar().showMessage("Listo") # Inicializa la barra de estado con un mensaje.

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
        self.tree.setColumnWidth(0, 150) # Establece el ancho de la primera columna (nombre del archivo/directorio).
        self.tree.clicked.connect(self.click_en_arbol) # Conecta el evento de clic en el árbol a un método para actualizar el panel derecho.
        self.tree.expanded.connect(lambda index: self.tree.resizeColumnToContents(0)) # Ajusta el ancho de la columna al expandir.
        self.tree.collapsed.connect(lambda index: self.tree.resizeColumnToContents(0)) # Ajusta el ancho de la columna al colapsar.
        
        header = self.tree.header() # Obtiene la cabecera del QTreeView.
        # Ajustes del comportamiento de las columnas para que la primera columna (nombre) se estire.
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)       # Columna 0 ocupa el espacio sobrante
        header.setSectionResizeMode(1, QHeaderView.Fixed)         # El resto de columnas tienen tamaño fijo
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)

        # Crear barra de herramientas para acciones rápidas.
        self.toolbar = QToolBar("Barra principal")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Crear y añadir botón para la función de formateo.
        self.boton_formateo = QToolButton()
        self.boton_formateo.setText("Formatear Unidad")
        self.boton_formateo.clicked.connect(self.formateo_boton)
        self.toolbar.addWidget(self.boton_formateo)

        # Crear y añadir botón para la función de particionado.
        self.boton_particion = QToolButton()
        self.boton_particion.setText("Particionar Unidad")
        self.boton_particion.clicked.connect(self.particion_boton)
        self.toolbar.addWidget(self.boton_particion)

        # Crear y añadir botón para crear una nueva carpeta.
        self.boton_carpeta = QToolButton()
        self.boton_carpeta.setText("Crear Carpeta")
        self.boton_carpeta.clicked.connect(self.carpeta_boton)
        self.toolbar.addWidget(self.boton_carpeta)

        # Habilitar el menú contextual personalizado en el árbol (clic derecho).
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_tree_right_click) # Conecta el evento de clic derecho a un método.
        
        # Panel derecho: tabla de archivos (QTableWidget). Muestra los archivos del directorio seleccionado.
        self.right_panel = QTableWidget()
        self.right_panel.setColumnCount(2) # Define dos columnas: "Archivo" y "Tamaño (KB)".
        self.right_panel.setHorizontalHeaderLabels(["Archivo", "Tamaño (KB)"]) # Establece los encabezados de las columnas.
        self.right_panel.setColumnWidth(0, 300) # Establece el ancho de la primera columna.
        self.right_panel.doubleClicked.connect(self.doble_click_archivo_panel_derecho) # Conecta el doble clic en un elemento a un método.
        
        # Splitter (QSplitter) para dividir la ventana y permitir redimensionar los paneles.
        splitter = QSplitter(Qt.Horizontal) # Splitter horizontal para dividir la ventana verticalmente.
        splitter.addWidget(self.tree) # Añade el árbol al splitter.
        splitter.addWidget(self.right_panel) # Añade el panel derecho al splitter.
        
        # Widget contenedor para el layout principal de la ventana.
        container = QWidget()
        container.setBaseSize(540,480) # Establece un tamaño base para el contenedor.
        layout = QVBoxLayout() # Layout vertical para organizar los widgets.
        layout.addWidget(splitter) # Añade el splitter al layout.
        container.setLayout(layout) # Establece el layout para el contenedor.
        self.setCentralWidget(container) # Establece el contenedor como el widget central de la ventana principal.
    

    def carpeta_boton(self):
        """
        Maneja la acción de crear una carpeta desde el botón de la barra de herramientas.
        Obtiene el índice actual del árbol y llama al método crear_carpeta.
        """
        try:
            index = self.tree.currentIndex()
            if not index.isValid():
                QMessageBox.warning(self, "Error", "Por favor, seleccione una ubicación para crear la carpeta.")
                return
            self.crear_carpeta(index) # Llama al método para crear una carpeta en la unidad/carpeta seleccionada.
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo iniciar la creación de carpeta. Error: {e}")
            return
        
    def formateo_boton(self):
        """
        Muestra un diálogo para que el usuario seleccione una unidad a formatear
        y sus parámetros (etiqueta, sistema de archivos). Confirma la acción y
        llama al método para formatear el disco.
        """
        try:
            disco,etiqueta, sistema_archivos, seleccion = obtener_valores_formateo(combobox=True)
        except Exception as e:
            
            return
            
        if seleccion == True: # Si el usuario confirmó la selección en el diálogo.
            # Pide confirmación antes de formatear para evitar pérdidas de datos accidentales.
            reply = QMessageBox.question(None, 'Desea continuar', f'Desea formatear el disco: {disco}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes: # Si el usuario confirma.
                self.formatear_disco(disco, sistema_archivos, etiqueta) # Llama al método para formatear.
    
    def particion_boton(self):
        """
        Maneja la acción de particionar una unidad desde el botón de la barra de herramientas.
        Muestra un diálogo para seleccionar la unidad y luego llama a auxiliar_particion.
        """
        unidades = obtener_unidades()
        unidades = [unidad for unidad in unidades if unidad != "C:"] # Excluye la unidad C: de la lista de unidades por seguridad.
        if not unidades:
            QMessageBox.information(self, "Información", "No hay unidades disponibles para particionar (excluyendo C:).")
            return

        letra, ok = QInputDialog.getItem(
            self,
            "Seleccionar unidad",
            "Elige la unidad que deseas particionar:",
            unidades,
            current=0,          # Opción seleccionada por defecto
            editable=False      # Para que sea sólo selección (no texto libre)
        )

        if ok and letra:
            self.auxiliar_particion(letra) # Llama al método auxiliar para manejar la partición de la unidad seleccionada.        
            
    def auxiliar_particion(self, letra):
        """
        Función auxiliar para manejar la lógica de particionamiento.
        Obtiene información del disco, solicita el tamaño de la nueva partición
        y la letra, y luego llama a crear_particion.
        
        Args:
            letra (str): La letra de la unidad a particionar (ej. "D:").
        """
        info = self.obtener_disco_fisico(letra)
        if not info or info.get("SizeRemaining") is None:
            QMessageBox.warning(self, "Error", "No se pudo obtener el tamaño del disco o el espacio libre.")
            return

        tamano = info["SizeRemaining"]
        # Convertir el tamaño a MB para la interfaz de usuario.
        max_espacio_libre = round((tamano / 1024**2), 0) # Convertir bytes a MB.

        tamano_particion, nueva_letra, nombre_particion = obtener_valores_particiones(max_espacio_libre) # Pasar solo el espacio libre en MB.

        if tamano_particion is not None and nueva_letra is not None:
            if tamano_particion > max_espacio_libre:
                QMessageBox.warning(self, "Error", f"El tamaño de la partición ({tamano_particion} MB) excede el espacio libre disponible ({max_espacio_libre} MB).")
                return

            reply = QMessageBox.question(None, 'Confirmar Creación', f'¿Desea crear una partición de {tamano_particion} MB en el disco {letra} con la letra {nueva_letra}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # El 'Number' es el índice del disco físico en DiskPart.
                self.crear_particion(info['Number'], letra, tamano_particion, nueva_letra, nombre_particion)


    # Método para manejar el clic derecho en el QTreeView (menú contextual).
    def on_tree_right_click(self, position):
        """
        Muestra un menú contextual personalizado cuando se hace clic derecho en un elemento del QTreeView.
        Las opciones del menú varían si el elemento es una unidad de disco o una carpeta/archivo,
        y si la unidad es la unidad del sistema (C:).
        
        Args:
            position (QPoint): La posición del clic dentro del viewport del QTreeView.
        """
        try:
            # Obtiene el índice del elemento sobre el que se hizo clic.
            index = self.tree.indexAt(position)
            if not index.isValid(): # Si el índice no es válido (se hizo clic en un espacio vacío), no hacer nada.
                return
         
            # Obtener la ruta completa del elemento clickeado.
            full_path = self.model.filePath(index)
            # Determinar si es una unidad raíz (ej. "C:/", "D:/").
            is_drive_root = os.path.ismount(full_path) # Verifica si la ruta es un punto de montaje (unidad).
            Letra = ""
            if is_drive_root:
                # Extrae la letra de la unidad si es una raíz de disco.
                # Asume que las unidades son mostradas como "Nombre (Letra:)" o "Letra:".
                try:
                    # Intenta parsear el formato "Nombre (Letra:)"
                    inicio = full_path.rfind("(") # Busca la última ocurrencia de '('
                    final = full_path.rfind(")")  # Busca la última ocurrencia de ')'
                    if inicio != -1 and final != -1 and inicio < final:
                        Letra = full_path[inicio + 1 : final]
                    else:
                        # Si no encuentra el formato esperado, asume que es solo la letra (ej. "C:")
                        Letra = full_path[0:2] 
                except Exception:
                    # En caso de cualquier error, intenta la forma simple.
                    Letra = full_path[0:2] # Ej: "C:"

            # Crea un menú contextual.
            menu = QMenu()
            # Opciones específicas para unidades de disco (excluyendo C:).
            if is_drive_root and Letra.upper() != "C:":
                menu.addAction("Formatear")
                menu.addAction("Crear Particion") # Nueva opción para particionar.
            
            # Opción común para crear carpeta.
            menu.addAction("Crear carpeta")
            
            # Opciones para archivos y carpetas que no son la raíz de una unidad.
            if not is_drive_root:
                menu.addAction("Renombrar")
                menu.addAction("Borrar")
                
            
            # Ejecuta el menú en la posición del clic derecho y obtiene la acción seleccionada.
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            if action: # Si se seleccionó una acción.
                accion = action.text() # Obtiene el texto de la acción seleccionada.
                
                # Usa una sentencia match para ejecutar la lógica según la acción seleccionada.
                match accion:
                    case "Renombrar":
                        nuevo_nombre, ok = QInputDialog.getText(self, "Renombrar", "Nuevo nombre:")
                        if ok and nuevo_nombre:
                            info = QFileInfo(full_path)
                            nueva_ruta = os.path.join(info.path(), nuevo_nombre)
                            try:
                                os.rename(full_path, nueva_ruta)
                                self.model.setRootPath('') # Forzar una actualización completa para reflejar el cambio.
                                self.tree.setRootIndex(self.model.index(''))
                                self.click_en_arbol(self.model.index(info.path())) # Refrescar la vista de la carpeta padre.
                                self.statusBar().showMessage(f"Elemento renombrado a '{nuevo_nombre}'", 3000)
                            except Exception as e:
                                QMessageBox.warning(self, "Error de Renombrado", f"No se pudo renombrar {full_path}. Error: {e}")
                    case "Crear carpeta":
                        self.crear_carpeta(index)
                        
                    case "Formatear":
                        if Letra != "C:": # No permite formatear la unidad C: por seguridad del sistema operativo.
                            # Abre un diálogo para obtener los parámetros de formateo (etiqueta y sistema de archivos).
                            etiqueta, sistema_archivos, seleccion = obtener_valores_formateo(combobox=False)
                            if seleccion == True: # Si el usuario confirmó la selección en el diálogo.
                                # Pide confirmación antes de formatear.
                                reply = QMessageBox.question(None, 'Desea continuar', f'Desea formatear el disco: {Letra}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes: # Si el usuario confirma.
                                    self.formatear_disco(Letra, sistema_archivos, etiqueta) # Llama al método para formatear.
                                    # Forzar actualización del modelo y del árbol después de formatear.
                                    self.model.setRootPath('')
                                    self.tree.setRootIndex(self.model.index(''))
                                    self.click_en_arbol(index) # Intenta refrescar el contenido de la unidad.
                                    self.update() # Actualiza el widget.
                        else:
                            QMessageBox.warning(self,"Error","El disco C: (unidad del sistema) no se puede formatear por seguridad.")
                                                    
                    case "Crear Particion":
                        # Nueva lógica para crear partición.
                        self.auxiliar_particion(Letra) # Llama al método auxiliar para manejar la partición de la unidad seleccionada.   
                    case "Borrar":
                        # Pide confirmación antes de borrar.
                        reply = QMessageBox.question(self, 'Confirmar Borrado', f'¿Estás seguro de que deseas eliminar {full_path}? Esta acción no se puede deshacer.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            try:
                                if os.path.isdir(full_path):
                                    os.rmdir(full_path) # Elimina un directorio vacío.
                                    # Para directorios no vacíos se necesitaría shutil.rmtree.
                                else:
                                    os.remove(full_path) # Elimina un archivo.
                                self.model.setRootPath('') # Forzar una actualización completa para reflejar el cambio.
                                self.tree.setRootIndex(self.model.index(''))
                                self.click_en_arbol(self.model.parent(index)) # Refrescar la vista de la carpeta padre.
                                self.statusBar().showMessage(f"'{os.path.basename(full_path)}' eliminado", 3000)

                            except OSError as e:
                                # Captura errores específicos de operación de sistema de archivos.
                                QMessageBox.warning(self, "Error de borrado", f"No se pudo eliminar {full_path}. Verifique si la carpeta está vacía o si tiene permisos suficientes. Error: {e}")
                            except Exception as e:
                                # Captura otros errores inesperados.
                                QMessageBox.warning(self, "Error de borrado", f"Ocurrió un error inesperado al intentar eliminar {full_path}. Error: {e}")

        except Exception as e:
            QMessageBox.warning(self, "Error de operación", f"No se pudo realizar la operación seleccionada. Error: {e}")
            
    def formatear_disco(self, letra, sistema_archivo, nuevo_nombre):
        """
        Ejecuta el comando 'format' de Windows para formatear una unidad.
        Muestra el progreso en la barra de estado. Requiere privilegios de administrador.

        Args:
            letra (str): La letra de la unidad a formatear (ej. "D:").
            sistema_archivo (str): El sistema de archivos a aplicar (ej. "NTFS", "FAT32").
            nuevo_nombre (str): La nueva etiqueta de volumen para la unidad.
        """
        try:
            # Ejecuta el comando 'format' de Windows a través de subprocess.
            # /FS:{sistema_archivo}: especifica el sistema de archivos (NTFS/FAT32).
            # /Q: formateo rápido.
            # /V:{nuevo_nombre}: establece la etiqueta de volumen.
            # /Y: suprime la solicitud de confirmación.
            # creationflags=self.CREATE_NO_WINDOW: evita que aparezca una ventana de consola.
            # text=True: decodifica la salida como texto.
            # shell=True: necesario para que el comando 'format' funcione directamente sin especificar su ruta completa.
            res1 = subprocess.Popen(["format", letra, f"/FS:{sistema_archivo}", "/Q", f"/V:{nuevo_nombre}", "/Y"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    creationflags=self.CREATE_NO_WINDOW,
                                    text=True, 
                                    shell=True)
            # Mostrar salidas en la barra de estado para feedback al usuario.
            output = ""
            progreso = 0
            for line in res1.stdout:
                output += line
                progreso += 1
                self.statusBar().showMessage(f"Línea: {progreso} - {line.strip()} ")
                QApplication.processEvents()  # Permite que la GUI se actualice y no se congele.
                time.sleep(0.05)  # Pequeña pausa para que el progreso sea visible (opcional).
            res1.wait() # Espera a que el proceso termine.
            if res1.returncode == 0:
                QMessageBox.information(self, 'Proceso completado', 'El disco se ha formateado correctamente.')
                self.statusBar().showMessage("Operación realizada con éxito", 3000)
                # Refrescar el modelo de archivos para reflejar los cambios en el árbol y panel derecho.
                self.model.setRootPath('') 
                self.tree.setRootIndex(self.model.index(''))
            else:
                # Si el comando format devuelve un error.
                QMessageBox.warning(self, 'Error de formateo', f'Hubo un error al formatear el disco. Código de error: {res1.returncode}\nSalida: {output}')

        except FileNotFoundError:
            QMessageBox.warning(self, 'Error', 'El comando "format" no se encontró. Asegúrese de que Windows lo tiene en su PATH o de que tiene permisos de administrador.')
        except Exception as e:
            QMessageBox.warning(self, 'Error de formateo', f'Hubo un error al formatear el disco. Error: {e}')
            
                
    def doble_click_archivo_panel_derecho(self, index: QModelIndex):
        """
        Maneja el doble clic en un elemento del panel derecho (QTableWidget).
        Abre el archivo seleccionado utilizando el programa predeterminado del sistema operativo.

        Args:
            index (QModelIndex): El índice del elemento en la tabla que fue doble clickeado.
        """
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
                raise Exception(f"Sistema operativo no soportado para abrir archivos: {self.sistema}")
            self.statusBar().showMessage(f"Abriendo archivo: {os.path.basename(rutaArchivo)}", 3000)
        except IndexError:
            QMessageBox.warning(self, "Error", "Índice de archivo no válido. El archivo puede haber sido movido o eliminado.")
        except Exception as e:
            QMessageBox.warning(self,"Error",f"Error al abrir el archivo: {e}")
    
    def click_en_arbol(self, index: QModelIndex):
        """
        Actualiza el panel derecho (QTableWidget) con los archivos de la carpeta
        seleccionada en el árbol (QTreeView).
        
        Args:
            index (QModelIndex): El índice del elemento en el árbol que fue clickeado.
        """
        ruta = self.model.filePath(index)
        self.statusBar().showMessage(f"Ruta actual: {ruta}") # Muestra la ruta actual en la barra de estado.
        archivos = self.obtener_archivos_de_ruta(ruta)
        self.lista_archivos = archivos # Almacena las rutas completas de los archivos mostrados.

        self.right_panel.setRowCount(len(archivos)) # Establece el número de filas en la tabla.
        for row, archivo in enumerate(archivos):
            nombre = os.path.basename(archivo) # Obtiene solo el nombre del archivo.
            tamaño_kb = round(os.path.getsize(archivo) / 1024, 2) # Obtiene el tamaño en KB.
            icon = QIcon(self.model.fileIcon(self.model.index(archivo))) # Obtiene el ícono del archivo.
            item = QTableWidgetItem(icon, nombre) # Crea un QTableWidgetItem con ícono y nombre.
            self.right_panel.setItem(row, 0, item) # Establece el ítem en la primera columna.

            item_size = QTableWidgetItem(f"{tamaño_kb:.2f}") # Crea un ítem para el tamaño.
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # Alinea el texto a la derecha.
            self.right_panel.setItem(row, 1, item_size) # Establece el ítem en la segunda columna.

        self.right_panel.setAlternatingRowColors(True) # Habilita colores alternos para las filas.
        self.right_panel.setEditTriggers(QTableWidget.NoEditTriggers) # Deshabilita la edición de celdas.
        self.right_panel.resizeColumnsToContents() # Ajusta automáticamente el ancho de las columnas.

    def obtener_archivos_de_ruta(self, ruta):
        """
        Devuelve una lista con las rutas completas de los archivos (excluyendo carpetas)
        en una ruta de directorio dada.

        Args:
            ruta (str): La ruta del directorio a explorar.

        Returns:
            list: Una lista de strings, donde cada string es la ruta completa de un archivo.
        """
        index = self.model.index(ruta) # Obtiene el índice del modelo para la ruta dada.
        total = self.model.rowCount(index) # Obtiene el número total de elementos (archivos y carpetas) en la ruta.
        archivos = []

        for i in range(total):
            child_index = self.model.index(i, 0, index) # Obtiene el índice de un hijo.
            if self.model.isDir(child_index): # Si es un directorio, lo salta.
                continue
            archivos.append(self.model.filePath(child_index)) # Si es un archivo, añade su ruta.
        return archivos
    
    def obtener_disco_fisico(self, letra_unidad):
        """
        Obtiene información detallada de un disco físico (como su número de disco,
        tamaño total y espacio restante) utilizando comandos de PowerShell.
        Esta función está diseñada para Windows.

        Args:
            letra_unidad (str): La letra de la unidad (ej. "D:").

        Returns:
            dict or None: Un diccionario con la información del disco si la operación fue exitosa,
                          None en caso de error.
        """
        letra = letra_unidad.strip(":").upper() # Asegura que la letra esté en mayúsculas y sin dos puntos.
        cmd = [
            "powershell.exe",
            "-Command",
            f"""
            $disk = Get-Partition -DriveLetter '{letra}' | Get-Disk
            $volume = Get-Volume -DriveLetter '{letra}'

            $info = [PSCustomObject]@{{
                Number         = $disk.Number
                SizeTotal      = $disk.Size
                SizeRemaining  = $volume.SizeRemaining
            }}

            $info | ConvertTo-Json -Compress
            """
        ]
        # Ejecuta el comando PowerShell.
        proceso = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=self.CREATE_NO_WINDOW)
        salida, error = proceso.communicate() # Espera a que el proceso termine y obtiene la salida y el error.
        if proceso.returncode == 0:
            try:
                datos = json.loads(salida) # Parsea la salida JSON.
                return datos
            except json.JSONDecodeError:
                print("No se pudo decodificar la salida JSON de PowerShell.")
                print("Salida:", salida)
                QMessageBox.warning(self, "Error de Datos", "No se pudo interpretar la información del disco.")
        else:
            print("Error al obtener información del disco (PowerShell):", error)
            QMessageBox.warning(self, "Error de PowerShell", f"Error al obtener información del disco {letra_unidad}: {error.strip()}")
        return None

    def crear_particion(self, disco_id, letra_original, tamaño_MB, nueva_letra, nombre_etiqueta):                
        """
        Crea una nueva partición en un disco físico utilizando DiskPart (requiere Windows y admin).
        Primero reduce el volumen existente y luego crea una nueva partición en el espacio no asignado.

        Args:
            disco_id (int): El número de disco físico (ej. 0, 1) obtenido de PowerShell.
            letra_original (str): La letra de la unidad existente a reducir (ej. "D:").
            tamaño_MB (int): El tamaño de la nueva partición en megabytes.
            nueva_letra (str): La letra que se asignará a la nueva partición.
            nombre_etiqueta (str): La etiqueta de volumen para la nueva partición.

        Returns:
            bool: True si la partición se creó con éxito, False en caso contrario.
        """
        if not nombre_etiqueta: # Si la etiqueta está vacía, se asigna un nombre por defecto.
            nombre_etiqueta = "Nueva Particion"
        
        # Script DiskPart para reducir un volumen existente.
        shrink_script = f"select volume {letra_original}\nshrink desired={tamaño_MB}\nexit\n"
        # Script DiskPart para crear una partición primaria en el espacio no asignado.
        create_script = (
            f"sel disk {disco_id}\n"
            f"create partition primary size={tamaño_MB}\n"
            f"format quick fs=ntfs label=\"{nombre_etiqueta}\"\n" # Formatea la nueva partición.
            f"assign letter={nueva_letra}\n" # Asigna la letra a la nueva partición.
            f"exit\n"
        )

        # Escribe los scripts a archivos temporales para DiskPart.
        shrink_file = "shrink.txt"
        create_file = "create.txt"
        with open(shrink_file, "w") as f:
            f.write(shrink_script)
            
        with open(create_file, "w") as f:
            f.write(create_script)

        self.statusBar().showMessage("Reduciendo volumen existente...", 0)
        QApplication.processEvents()
        # Ejecuta el script de reducción con DiskPart.
        resShrink = subprocess.Popen(["diskpart", "/s", shrink_file],
                                     creationflags=self.CREATE_NO_WINDOW,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, 
                                     text=True)
        # Monitorea y muestra la salida del proceso de reducción.
        for line in resShrink.stdout:
            self.statusBar().showMessage(f"DiskPart (Reducir): {line.strip()}")
            QApplication.processEvents() 
            time.sleep(0.05)
        resShrink.wait() # Espera a que el proceso de reducción termine.
        
        # Manejo de errores para la reducción.
        if resShrink.returncode != 0:
            QMessageBox.warning(self, "Error", f"Error al reducir el volumen {letra_original}. Código: {resShrink.returncode}. Revise los permisos o el espacio disponible.")
            os.remove(shrink_file)
            return False
        os.remove(shrink_file) # Elimina el archivo de script temporal.
        resShrink.stdout.close() 
        time.sleep(1) # Pequeña pausa para asegurar que el sistema actualice el espacio no asignado.

        self.statusBar().showMessage("Creando nueva partición...", 0)
        QApplication.processEvents()
        # Ejecuta el script de creación de partición con DiskPart.
        resParticion = subprocess.Popen(["diskpart", "/s", create_file],
                                        creationflags=self.CREATE_NO_WINDOW,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, 
                                        text=True)
        # Monitorea y muestra la salida del proceso de creación.
        progreso = 0
        for line in resParticion.stdout:
            progreso += 1
            self.statusBar().showMessage(f"DiskPart (Crear): Línea {progreso} - {line.strip()} ")
            QApplication.processEvents() 
            time.sleep(0.05)
        resParticion.wait() # Espera a que el proceso de creación termine.

        # Manejo de errores para la creación de partición.
        if resParticion.returncode != 0:
            QMessageBox.warning(self, "Error", f"Error al crear la partición. Código: {resParticion.returncode}. Revise los permisos o si la letra ya está en uso.")
            os.remove(create_file)
            return False
        os.remove(create_file) # Elimina el archivo de script temporal.
        resParticion.stdout.close()
        
        self.statusBar().showMessage("Partición creada con éxito", 3000)
        # Forzar una actualización completa del modelo para reflejar la nueva partición.
        self.model.setRootPath('')
        self.tree.setRootIndex(self.model.index(''))
        return True   
        
    def obtener_informacion_particion(self, letra_unidad):
        """
        Obtiene información detallada de una partición específica (tamaño actual,
        espacio mínimo y máximo para reducir/extender) utilizando PowerShell.
        (Este método fue proporcionado pero no es usado directamente en el flujo de creación de particiones actual,
        que usa 'obtener_disco_fisico' para el espacio libre).
        
        Args:
            letra_unidad (str): La letra de la unidad a consultar (ej. "D:").
            
        Returns:
            dict or None: Un diccionario con la información de la partición si la operación fue exitosa,
                          None en caso de error.
        """
        letra = letra_unidad.strip(":").upper()
        cmd = [
            "powershell.exe",
            "-Command",
            f"""
            $partition = Get-Partition -DriveLetter {letra}
            if ($partition) {{
                $supportedSize = Get-PartitionSupportedSize -Partition $partition
                $info = [PSCustomObject]@{{
                    DriveLetter = '{letra}'
                    Size        = $partition.Size
                    SizeMin     = $supportedSize.SizeMin
                    SizeMax     = $supportedSize.SizeMax
                }}
                $info | ConvertTo-Json -Compress
            }} else {{
                Write-Error "Partición {letra} no encontrada."
            }}
            """
        ]
        resultado = subprocess.run(cmd, capture_output=True, text=True, creationflags=self.CREATE_NO_WINDOW)
        if resultado.returncode == 0:
            try:
                datos = json.loads(resultado.stdout)
                return datos
            except json.JSONDecodeError:
                print("No se pudo decodificar la salida JSON al obtener información de partición.")
                print(f"Salida PowerShell: {resultado.stdout}")
        else:
            print("Error al obtener información de la partición:", resultado.stderr)
        return None
    
    def crear_carpeta(self, index: QModelIndex):
        """
        Crea una nueva carpeta en la ruta seleccionada en el QTreeView.
        Pide al usuario el nombre de la carpeta y maneja la creación en el sistema de archivos.

        Args:
            index (QModelIndex): El índice de la carpeta padre donde se creará la nueva carpeta.
        """
        name = self.nombre_carpeta() # Pide al usuario un nombre para la nueva carpeta.
        if name: # Si el usuario proporcionó un nombre.
            ruta = self.model.filePath(index) # Obtiene la ruta del directorio seleccionado.
            nueva_ruta = os.path.join(ruta, name) # Crea la ruta completa para la nueva carpeta.
            try:
                os.makedirs(nueva_ruta) # Crea la nueva carpeta (incluyendo directorios intermedios si no existen).
                QMessageBox.information(self, "Carpeta Creada", f"Carpeta '{name}' creada en {ruta}")
                # Refrescar el modelo para que la nueva carpeta aparezca.
                self.model.setRootPath('') 
                self.tree.setRootIndex(self.model.index(''))
                self.click_en_arbol(index) # Refrescar la vista de la carpeta actual.
                self.statusBar().showMessage(f"Carpeta '{name}' creada", 3000)
            except FileExistsError:
                QMessageBox.warning(self, "Error al crear carpeta", f"La carpeta '{name}' ya existe en esta ubicación.")
            except Exception as e:
                QMessageBox.warning(self, "Error al crear carpeta", f"No se pudo crear la carpeta: {e}")

    
    def nombre_carpeta(self):
        """
        Muestra un diálogo de entrada para que el usuario ingrese el nombre de la nueva carpeta.

        Returns:
            str or None: El nombre de la carpeta si el usuario lo ingresa y confirma,
                         None si cancela o no ingresa un nombre válido.
        """
        text, ok = QInputDialog.getText(self, f'Crear Carpeta', 'Nombre de la carpeta:')
        if ok and text:
            return text.strip()
        else:            
            # El mensaje de error se maneja en el método que llama a esta función (`crear_carpeta`).
            return None
        
  
# Clase para el diálogo de entrada de formateo de discos.
class InputFormateo(QDialog):
    """
    Diálogo para solicitar al usuario la unidad a formatear, una etiqueta de volumen
    y el sistema de archivos (NTFS/FAT32).
    """
    def __init__(self, combobox_enabled, parent=None):
        """
        Constructor del diálogo InputFormateo.

        Args:
            combobox_enabled (bool): Si es True, muestra un QComboBox para seleccionar la unidad.
                                     Si es False, se asume que la unidad ya está preseleccionada.
            parent (QWidget, optional): El widget padre de este diálogo. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Opciones de Formateo") # Título del diálogo.
        self.setGeometry(500,400,300,100) # Define la posición y tamaño inicial.

        unidades = obtener_unidades()
        unidades = [unidad for unidad in unidades if unidad != "C:"] # Excluye la unidad C: de la lista por seguridad.
        self.combobox_enabled = combobox_enabled # Guarda el estado del combobox.
        
        layout = QVBoxLayout() # Layout vertical para organizar los widgets.

        if self.combobox_enabled:
            self.label_disco = QLabel("Seleccione el disco a formatear:")
            self.combo_discos = QComboBox()
            self.combo_discos.addItems(unidades)
            layout.addWidget(self.label_disco)
            layout.addWidget(self.combo_discos)

        self.label = QLabel("Escriba un nombre para la etiqueta de volumen y elija el sistema de archivos:")
        self.line_edit = QLineEdit() # Campo para el nombre de la etiqueta de volumen.
        self.line_edit.setPlaceholderText("Nueva Etiqueta") # Placeholder para guiar al usuario.
        self.combo_box = QComboBox() # ComboBox para seleccionar el sistema de archivos.
        self.combo_box.addItems(["NTFS", "FAT32"]) # Opciones de sistemas de archivos.

        # Botones de OK y Cancelar.
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept) # Conecta el botón OK al método accept del diálogo.
        self.botones.rejected.connect(self.reject) # Conecta el botón Cancelar al método reject del diálogo.
        self.botones.clicked.connect(self.on_boton_clickeado) # Conecta cualquier clic de botón a un método.

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.combo_box)
        layout.addWidget(self.botones)

        self.setLayout(layout)
        self.seleccion = False # Inicializa una bandera para saber si se aceptó o canceló el diálogo.
        
    def on_boton_clickeado(self, button):
        """
        Maneja los clics en los botones del diálogo para establecer la bandera 'seleccion'.
        
        Args:
            button (QPushButton): El botón que fue clickeado.
        """
        role = self.botones.buttonRole(button) # Obtiene el rol del botón presionado.
        if role == QDialogButtonBox.AcceptRole: # Si es el botón OK (o un rol de aceptación).
            self.seleccion = True
        elif role == QDialogButtonBox.RejectRole: # Si es el botón Cancelar (o un rol de rechazo).
            self.seleccion = False
    
    def obtener_datos(self):
        """
        Obtiene los datos ingresados en el diálogo de formateo.

        Returns:
            tuple: (disco, etiqueta, sistema_archivos, seleccion) si combobox_enabled es True.
                   (etiqueta, sistema_archivos, seleccion) si combobox_enabled es False.
        """
        if self.combobox_enabled:
            return self.combo_discos.currentText(), self.line_edit.text(), self.combo_box.currentText(), self.seleccion
        else:
            return self.line_edit.text(), self.combo_box.currentText(), self.seleccion

def obtener_unidades():
    """
    Detecta las letras de las unidades de disco presentes en el sistema.
    Asume un sistema operativo tipo Windows.

    Returns:
        list: Una lista de strings, donde cada string es una letra de unidad seguida de ":" (ej. "C:", "D:").
    """
    letras = string.ascii_uppercase # Obtiene todas las letras del alfabeto en mayúsculas.
    unidades = [f"{letra}:" for letra in letras if os.path.exists(f"{letra}:\\")] # Comprueba si la ruta existe.
    return unidades
    

def obtener_valores_formateo(combobox):
    """
    Función auxiliar para mostrar el diálogo de formateo y obtener sus valores.

    Args:
        combobox (bool): Determina si el diálogo debe mostrar el combobox de selección de disco.

    Returns:
        tuple: Los valores ingresados por el usuario (disco, etiqueta, sistema_archivos, seleccion)
               o (None, None, False) si el diálogo fue cancelado.
    """
    dialogo = InputFormateo(combobox) # Crea una instancia del diálogo.
    if dialogo.exec_() == QDialog.Accepted: # Si el usuario hace clic en OK.
        if combobox:
            disco, texto, opcion, seleccion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
            return disco, texto, opcion, seleccion # Retorna los valores.
        else:
            texto, opcion, seleccion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
            return texto, opcion, seleccion # Retorna los valores.
    return None, None, False # Retorna None si se canceló.


# Clase para el diálogo de entrada para la creación de particiones.
class InputParticion(QDialog):
    """
    Diálogo para solicitar al usuario el tamaño de la nueva partición en MB,
    la letra de la unidad y una etiqueta de volumen.
    """
    def __init__(self, espacio_maximo ,parent=None):
        """
        Constructor del diálogo InputParticion.

        Args:
            espacio_maximo (float): El espacio libre máximo disponible para la partición en MB.
            parent (QWidget, optional): El widget padre de este diálogo. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Crear Partición") # Título del diálogo.
        self.setGeometry(500,400,300,100) # Define la posición y tamaño inicial.
        
        self.label_max = QLabel(f"Espacio máximo disponible: {espacio_maximo:.0f} MB") # Muestra el espacio máximo.
        maxInt = int(espacio_maximo) # Convierte el espacio máximo a entero para el validador.
        
        # Widgets del diálogo.
        self.label_tamano = QLabel("Indique el tamaño de la partición (MB):")
        self.input_tamano = QLineEdit() # Campo para el tamaño de la partición.
        self.input_tamano.setPlaceholderText("Ej: 1024")
        # Validador para asegurar que solo se ingresen números enteros entre 1 y el espacio máximo.
        self.input_tamano.setValidator(QIntValidator(1, maxInt)) 

        self.label_letra = QLabel("Indique la letra de la nueva partición:")
        self.input_letra = QLineEdit() # Campo para la letra de la nueva partición.
        self.input_letra.setMaxLength(1) # Solo permite un carácter.
        self.input_letra.setPlaceholderText("Ej: X")
        # Validador para asegurar que solo se ingresen letras mayúsculas o minúsculas.
        self.input_letra.setValidator(QRegExpValidator(QRegExp("[A-Za-z]"))) 

        self.label_nombre = QLabel("Indique el nombre de la nueva partición (opcional):")
        self.input_nombre = QLineEdit() # Campo para la etiqueta de la nueva partición.
        self.input_nombre.setPlaceholderText("Nueva Partición")


        # Botones de OK y Cancelar.
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept)
        self.botones.rejected.connect(self.reject)

        # Layout del diálogo.
        layout = QVBoxLayout()
        layout.addWidget(self.label_max) # Añade la etiqueta de espacio máximo al layout.
        layout.addWidget(self.label_tamano)
        layout.addWidget(self.input_tamano)
        layout.addWidget(self.label_letra)
        layout.addWidget(self.input_letra)
        layout.addWidget(self.label_nombre)
        layout.addWidget(self.input_nombre)
        layout.addWidget(self.botones)
        
        self.setLayout(layout)

    def obtener_datos(self):
        """
        Obtiene los datos introducidos en el diálogo de partición.
        Realiza validación básica de campos.

        Returns:
            tuple: (tamaño_MB (int), nueva_letra (str), nombre_particion (str))
                   o (None, None, None) si hay campos vacíos.
        """
        tamano_texto = self.input_tamano.text().strip() # Obtiene el texto del tamaño.
        letra_texto = self.input_letra.text().strip().upper() # Obtiene el texto de la letra, en mayúscula.
        nombre_particion = self.input_nombre.text().strip() # Obtiene el texto del nombre.

        if not tamano_texto or not letra_texto: # Si algún campo obligatorio está vacío.
            QMessageBox.warning(self, "Error de Entrada", "Debe proporcionar el tamaño y la letra para la nueva partición.")
            return None, None, None # Retorna None si hay campos vacíos.
        
        if len(letra_texto) != 1 or not letra_texto.isalpha():
             QMessageBox.warning(self, "Error de Entrada", "La letra de la partición debe ser un único carácter alfabético.")
             return None, None, None

        return int(tamano_texto), letra_texto, nombre_particion # Retorna el tamaño como entero, la letra y el nombre.

def obtener_valores_particiones(espacio_maximo):
    """
    Función auxiliar para mostrar el diálogo de creación de particiones y obtener sus valores.

    Args:
        espacio_maximo (float): El espacio libre máximo disponible para la partición en MB.

    Returns:
        tuple: Los valores ingresados por el usuario (tamaño_MB, nueva_letra, nombre_particion)
               o (None, None, None) si el diálogo fue cancelado o hubo un error de validación.
    """
    dialogo = InputParticion(espacio_maximo) # Crea una instancia del diálogo, pasando el espacio máximo.
    if dialogo.exec_() == QDialog.Accepted: # Si el usuario hace clic en OK.
        tam, letra, nombre_particion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
        if tam is not None and letra is not None: # Si se obtuvieron valores válidos.
            return tam, letra, nombre_particion  # Retorna los valores.
    return None, None, None # Retorna None si se canceló o hubo un error.


def es_admin():
    """
    Verifica si el script se está ejecutando con privilegios de administrador en Windows.
    Esta función es específica para sistemas Windows.

    Returns:
        bool: True si el usuario es administrador, False en caso contrario o si no es Windows.
    """
    try:
        # ctypes.windll.shell32.IsUserAnAdmin() es una función de la API de Windows.
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        # Retorna False si no es Windows o si hay un error al verificar los permisos.
        return False

# Bloque principal de ejecución cuando el script se ejecuta directamente.
if __name__ == "__main__":
    # Si no es administrador, vuelve a ejecutar el mismo script con permisos elevados
    '''PARA PROBAR EL PROGRAMA SIN CREAR EL EJECUTABLE COMENTA EL IF COMPLETO DE ABAJO'''
    # Este bloque es crucial para que las operaciones de formateo y particionado funcionen,
    # ya que requieren permisos elevados en Windows.
    '''
    if not es_admin():
        # Ejecuta el script de nuevo con el verbo 'runas', que solicita permisos de administrador.
        # sys.executable: la ruta al ejecutable de Python.
        # " ".join(sys.argv): pasa los argumentos originales al nuevo proceso.
        # 1: SHOW_NORMAL (muestra la ventana normalmente).
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit() # Sale de la aplicación actual, esperando que la nueva instancia con privilegios se inicie.
    '''
    app = QApplication(sys.argv) # Crea una instancia de QApplication (necesaria para cualquier aplicación PyQt).
    window = FileExplorer() # Crea una instancia de la ventana principal de la aplicación.
    window.show() # Muestra la ventana.
    sys.exit(app.exec_()) # Inicia el bucle de eventos de la aplicación y espera a que la aplicación finalice.