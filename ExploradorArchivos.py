from tokenize import Number
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileSystemModel, QTreeView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSplitter, QMenu, QInputDialog, 
    QMessageBox, QDialog, QLabel, QLineEdit, QComboBox, QDialogButtonBox, QHeaderView, QToolButton, QToolBar
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QIntValidator, QRegExpValidator, QIcon
from PyQt5.QtCore import QRegExp
import string
import time
import ctypes
import win32api
import os # Módulo para interactuar con el sistema operativo, como rutas de archivos y directorios.
import sys # Módulo para acceder a parámetros y funciones específicos del sistema, como la gestión de la aplicación.
import platform # Módulo para acceder a datos de la plataforma subyacente, como el sistema operativo.
import subprocess # Módulo para ejecutar nuevos procesos y gestionar sus entradas/salidas.
import json # Módulo para codificar y decodificar datos JSON.

# Clase principal de la aplicación, hereda de QMainWindow para crear una ventana de aplicación.
class FileExplorer(QMainWindow):
    def __init__(self):
        self.CREATE_NO_WINDOW = 0x08000000
        super().__init__() # Llama al constructor de la clase base QMainWindow.
        self.setWindowTitle("Explorador de Archivos") # Establece el título de la ventana.
        self.setGeometry(100, 100, 1000, 600) # Define la posición y tamaño inicial de la ventana (x, y, ancho, alto).

        self.statusBar().showMessage("Listo")

        # Obtener el sistema operativo del equipo (ej. 'Windows', 'Darwin' para macOS, 'Linux').
        self.sistema = platform.system() 

        # Modelo del sistema de archivos. QFileSystemModel proporciona un modelo de datos para el sistema de archivos local.
        self.model = QFileSystemModel()
        self.model.setRootPath('') # Establece la raíz del modelo al directorio principal del sistema.
        #self.model.removeRow(1, QModelIndex()) # Elimina la primera fila del modelo, que suele ser el directorio raíz (C:/ en Windows).
        # Lista para almacenar las rutas completas de los archivos mostrados en el panel derecho.
        self.lista_archivos = []

        # Árbol de directorios (QTreeView). Muestra la jerarquía del sistema de archivos.
        self.tree = QTreeView()
        self.tree.setModel(self.model) # Asocia el modelo de sistema de archivos al QTreeView.
        self.tree.setRootIndex(self.model.index('')) # Muestra el contenido del directorio raíz.
        self.tree.setColumnWidth(0, 150) # Establece el ancho de la primera columna (nombre del archivo/directorio).
        self.tree.clicked.connect(self.click_en_arbol) # Conecta el evento de clic en el árbol a un método.
        self.tree.expanded.connect(lambda index: self.tree.resizeColumnToContents(0))
        self.tree.collapsed.connect(lambda index: self.tree.resizeColumnToContents(0))
        self.tree.setMaximumHeight(400) # Establece una altura máxima para el árbol de directorios.
        header = self.tree.header()
        # Ajustes del comportamiento de las columnas
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)       # Columna 0 ocupa el espacio sobrante
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)

        # Crear barra de herramientas
        self.toolbar = QToolBar("Barra principal")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Crear botón de herramienta
        self.boton_formateo = QToolButton()
        self.boton_formateo.setText("Formatear Unidad")
        self.boton_formateo.clicked.connect(self.formateo_boton)
        # Agregar el botón a la barra de herramientas
        self.toolbar.addWidget(self.boton_formateo)
        # Crear botón de herramienta
        self.boton_particion = QToolButton()
        self.boton_particion.setText("Particionar Unidad")
        self.boton_particion.clicked.connect(self.particion_boton)
        # Agregar el botón a la barra de herramientas
        self.toolbar.addWidget(self.boton_particion)

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
        #splitter.setSizes([300, 700]) # Podría usarse para establecer los tamaños iniciales de los paneles.
        # Widget contenedor para el layout principal de la ventana.
        container = QWidget()
        container.setBaseSize(540,480)
        layout = QVBoxLayout() # Layout vertical para organizar los widgets.
        layout.addWidget(splitter) # Añade el splitter al layout.
        container.setLayout(layout) # Establece el layout para el contenedor.
        self.setCentralWidget(container) # Establece el contenedor como el widget central de la ventana principal.
    
        
    def formateo_boton(self):
        """Muestra un diálogo para formatear discos."""
        try:
            disco,etiqueta, sistema_archivos, seleccion = obtener_valores_formateo(combobox=True)
        except Exception as e:
            return
        if seleccion == True: # Si el usuario confirmó la selección en el diálogo.
            # Pide confirmación antes de formatear.
            reply = QMessageBox.question(None, 'Desea continuar', f'Desea formatear el disco: {disco}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes: # Si el usuario confirma.
                self.formatear_disco(disco, sistema_archivos, etiqueta) # Llama al método para formatear.
    
    def particion_boton(self):
        unidades = obtener_unidades()
        unidades = [unidad for unidad in unidades if unidad != "C:"] # Excluye la unidad C: de la lista de unidades.
        letra, ok = QInputDialog.getItem(
            self,
            "Seleccionar unidad",
            "Elige la unidad que deseas particionar:",
            unidades,
            current=0,          # Opción seleccionada por defecto
            editable=False      # Para que sea sólo selección (no texto libre)
        )

        if ok and letra:
            info = self.obtener_disco_fisico(letra)
            tamano = info["SizeRemaining"]
            if not info or tamano is None:
                QMessageBox.warning(self, "Error", "No se pudo obtener el tamaño del disco.")
                return

            disco_num = info['Number']
            max_espacio_libre = round((tamano/1000**2),2) # Convierte el tamaño a MB.
            max_espacio_libre = max_espacio_libre - 100 # Deja un margen de 100 MB para evitar errores al crear la partición.

            tamano_particion, nueva_letra, nombre_particion = obtener_valores_particiones(max_espacio_libre) # Pasar solo el espacio libre

            if tamano_particion is not None and nueva_letra is not None:
                if tamano_particion > max_espacio_libre:
                    QMessageBox.warning(self, "Error", f"El tamaño de la partición ({tamano_particion} MB) excede el espacio libre disponible ({max_espacio_libre} MB).")
                    return

                reply = QMessageBox.question(None, 'Confirmar Creación', f'¿Desea crear una partición de {tamano_particion} MB en el disco {letra} con la letra {nueva_letra}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.crear_particion(disco_num, letra, tamano_particion, nueva_letra, nombre_particion)




    # Método para manejar el clic derecho en el QTreeView (menú contextual).
    def on_tree_right_click(self, position):
        try:
            # Obtiene el índice del elemento sobre el que se hizo clic.
            index = self.tree.indexAt(position)
            if not index.isValid(): # Si el índice no es válido (se hizo clic en un espacio vacío), no hacer nada.
                return
         
            # Obtener la ruta completa del elemento clickeado
            full_path = self.model.filePath(index)
            # Determinar si es una unidad raíz (ej. "C:/", "D:/")
            is_drive_root = os.path.ismount(full_path) # Verifica si la ruta es un punto de montaje (unidad)
            Letra = ""
            if is_drive_root:
                # Extrae la letra de la unidad si es una raíz de disco
                # Asume que las unidades son mostradas como "Nombre (Letra:)"
                try:
                    inicio = full_path.index("(")
                    final = full_path.index(")")
                    Letra = full_path[inicio + 1 : final]
                except ValueError:
                    # Si no encuentra el formato esperado, puede ser solo la letra (ej. "C:")
                    Letra = full_path[0:2] # Ej: "C:"
            # Crea un menú contextual.
            menu = QMenu()
            if is_drive_root and Letra.upper() != "C:":
                #menu.addAction("Renombrar")
                menu.addAction("Formatear")
                menu.addAction("Crear Particion") # Nueva opción
            
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
                                self.model.setRootPath('')  # Esto fuerza a QFileSystemModel a recargar el sistema de archivos
                                self.tree.setRootIndex(self.model.index(''))
                        else:
                            QMessageBox.warning(self,"Error","El disco C: no se puede renombrar")
                        
                    case "Formatear":
                        if Letra != "C:": # No permite formatear la unidad C:.
                            # Abre un diálogo para obtener los parámetros de formateo (etiqueta y sistema de archivos).
                            etiqueta, sistema_archivos, seleccion = obtener_valores_formateo(combobox=False)
                            if seleccion == True: # Si el usuario confirmó la selección en el diálogo.
                                # Pide confirmación antes de formatear.
                                reply = QMessageBox.question(None, 'Desea continuar', f'Desea formatear el disco: {Letra}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes: # Si el usuario confirma.
                                    self.formatear_disco(Letra, sistema_archivos, etiqueta) # Llama al método para formatear.
                                    self.model.setRootPath('')
                                    self.tree.setRootIndex(self.model.index(''))
                                    self.click_en_arbol(index)
                                    self.update() # Actualiza el modelo y el árbol.
                        else:
                            QMessageBox.warning(self,"Error","El disco C: no se puede formatear")
                                                    
                    case "Crear Particion":
                        # Nueva lógica para crear partición
                            info = self.obtener_disco_fisico(Letra)
                            tamano = info["SizeRemaining"]
                            if not info or tamano is None:
                                QMessageBox.warning(self, "Error", "No se pudo obtener el tamaño del disco.")
                                return

                            disco_num = info['Number']
                            max_espacio_libre = (tamano/1024**2) # Convierte el tamaño a MB.
                            #max_espacio_libre = max_espacio_libre - 1500 # Deja un margen de 1500 MB para evitar errores al crear la partición.

                            tamano_particion, nueva_letra, nombre_particion = obtener_valores_particiones(max_espacio_libre) # Pasar solo el espacio libre

                            if tamano_particion is not None and nueva_letra is not None:
                                if tamano_particion > max_espacio_libre:
                                    QMessageBox.warning(self, "Error", f"El tamaño de la partición ({tamano_particion} MB) excede el espacio libre disponible ({max_espacio_libre} MB).")
                                    return

                                reply = QMessageBox.question(None, 'Confirmar Creación', f'¿Desea crear una partición de {tamano_particion} MB en el disco {Letra} con la letra {nueva_letra}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes:
                                    self.crear_particion(disco_num, Letra, tamano_particion, nueva_letra, nombre_particion)
                                    self.model.setRootPath('')
                                    self.tree.setRootIndex(self.model.index(''))
                                    self.click_en_arbol(index)
                                    self.update() # Actualiza el modelo y el árbol.

        except Exception as e:
            QMessageBox.warning(self, "Error de operación", f"No se pudo realizar la operación seleccionada. Error: {e}")
            print(e)
    # Método para formatear un disco.
    def formatear_disco(self, letra, sistema_archivo, nuevo_nombre):
        try:
            # Ejecuta el comando 'format' de Windows.
            # /FS:{sistema_archivo}: especifica el sistema de archivos (NTFS/FAT32).
            # /Q: formateo rápido.
            # /V:{nuevo_nombre}: establece la etiqueta de volumen.
            # /Y: suprime la solicitud de confirmación.
            res1 = subprocess.Popen(["format", letra, f"/FS:{sistema_archivo}", "/Q", f"/V:{nuevo_nombre}", "/Y"],stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,creationflags=self.CREATE_NO_WINDOW,
            text=True, shell=True)
            # Mostrar salidas
            output = ""
            progreso = 0
            for line in res1.stdout:
                output += line
                progreso += 1
                self.statusBar().showMessage(f"Linea: {progreso} - {line.strip()} ")
                QApplication.processEvents()  # Permite que la GUI se actualice
                time.sleep(0.05)  # Pequeña pausa para que se vea el cambio (opcional)
            res1.wait()
            QMessageBox.information(self, 'Proceso completado', 'El disco se ha formateado correctamente')
            self.statusBar().showMessage("Operacion realizada con exito", 3000)
            
        except Exception as e:
            QMessageBox.warning(self, 'Error de formateo', f'Hubo un error al formatear el disco \n Error: {e}')
            # AGREGAR ACTUALIZACION DE TREEVIEW: Para una actualización más robusta,
            # podrías necesitar llamar a self.model.readDirectory() en la raíz o la unidad formateada,
            # o incluso reconstruir el QFileSystemModel si los cambios no se reflejan automáticamente.
                
    # Método para manejar el doble clic en un elemento del panel derecho (abrir archivo).
    def doble_click_archivo_panel_derecho(self, index: QModelIndex):
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
    def click_en_arbol(self, index: QModelIndex):
        """Actualiza el panel derecho con los archivos de la carpeta seleccionada."""
        ruta = self.model.filePath(index)
        self.statusBar().showMessage(ruta)
        archivos = self.obtener_archivos_de_ruta(ruta)
        self.lista_archivos = archivos

        self.right_panel.setRowCount(len(archivos))
        for row, archivo in enumerate(archivos):
            nombre = os.path.basename(archivo)
            tamaño_kb = round(os.path.getsize(archivo) / 1024, 2)
            icon = QIcon(self.model.fileIcon(self.model.index(archivo)))
            item = QTableWidgetItem(icon, nombre)
            self.right_panel.setItem(row, 0, item)

            item_size = QTableWidgetItem(f"{tamaño_kb:.2f}")
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.right_panel.setItem(row, 1, item_size)

        self.right_panel.setAlternatingRowColors(True)
        self.right_panel.setEditTriggers(QTableWidget.NoEditTriggers)
        self.right_panel.resizeColumnsToContents()

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
    def obtener_disco_fisico(self, letra_unidad):
        letra = letra_unidad.strip(":").upper()
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

        proceso = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=self.CREATE_NO_WINDOW)
        salida, error = proceso.communicate()
        if proceso.returncode == 0:
            try:
                datos = json.loads(salida)
                return datos
            except json.JSONDecodeError:
                print("No se pudo decodificar la salida JSON.")
                print("Salida:", salida)
        else:
            print("Error al obtener información del disco:", error)
        return None

    # Método para crear una partición en un disco.
    
    def crear_particion(self, disco_id, letra, tamaño_MB, nueva_letra, nombre_etiqueta):                
        # Generar scripts
        if nombre_etiqueta == "":
            nombre_etiqueta = "Nueva Particion"
        shrink = f"select volume {letra}\nshrink desired={tamaño_MB}\nexit\n"
        create = (
            f"sel disk {disco_id}\n"
            f"create partition primary size={tamaño_MB}\n"
            f"format quick fs=ntfs label=\"{nombre_etiqueta}\"\n"
            f"assign letter={nueva_letra}\n"
            f"exit\n"
        )

        with open("shrink.txt", "w") as f:
            f.write(shrink)
            
        with open("create.txt", "w") as f:
            f.write(create)

        # Ejecutar scripts
        resShrink = subprocess.Popen(["diskpart", "/s", "shrink.txt"],creationflags=self.CREATE_NO_WINDOW,stdout=subprocess.PIPE,stderr=subprocess.STDOUT, text=True)
        output = ""
        for line in resShrink.stdout:
            output += line
            self.statusBar().showMessage(f"{line.strip()}")
            print(line.strip())
            QApplication.processEvents()  # Permite que la GUI se actualice
            time.sleep(0.05)  # Pequeña pausa para que se vea el cambio (opcional)
        resShrink.wait()
        if resShrink.returncode != 0:
            QMessageBox.warning(self, "Error", "Error al reducir el volumen. Revisa los permisos o el espacio disponible.")
            os.remove("shrink.txt")
            return False
        os.remove("shrink.txt")
        resShrink.stdout.close()  # Cierra el pipe de salida del proceso
        time.sleep(1)
        resParticion = subprocess.Popen(["diskpart", "/s", "create.txt"],creationflags=self.CREATE_NO_WINDOW,stdout=subprocess.PIPE,stderr=subprocess.STDOUT, text=True)
        output = ""
        progreso = 0
        for line in resParticion.stdout:
            output += line
            progreso += 1
            self.statusBar().showMessage(f"Linea: {progreso} - {line.strip()} ")
            print(line.strip())
            QApplication.processEvents()  # Permite que la GUI se actualice
            time.sleep(0.05)  # Pequeña pausa para que se vea el cambio (opcional)
        resParticion.wait()
        if resParticion.returncode != 0:
            QMessageBox.warning(self, "Error", "Error al crear la partición. Revisa los permisos o el espacio disponible.")
            os.remove("create.txt")
            return False
        os.remove("create.txt")
        resParticion.stdout.close()
        self.statusBar().showMessage("Partición creada con éxito", 3000)
        return resParticion.returncode == 0   
        
    def obtener_informacion_particion(self, letra_unidad):
        """
        Obtiene información detallada de una partición específica, incluyendo su tamaño actual
        y el espacio que se puede reducir o extender.
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
        resultado = subprocess.run(cmd, capture_output=True, text=True)
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
  
# Clase para el diálogo de entrada de formateo de discos.
class InputFormateo(QDialog):
    
    def __init__(self, combobox,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Formateo Discos") # Título del diálogo.
        self.setGeometry(500,400,300,100)
        unidades = obtener_unidades()
        unidades = [unidad for unidad in unidades if unidad != "C:"] # Excluye la unidad C: de la lista de unidades.
        self.combobox = combobox
        
        self.label_disco = QLabel("Seleccione el disco a formatear:")
        self.combo_discos = QComboBox()
        self.combo_discos.addItems(unidades)
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
        if combobox:
            layout.addWidget(self.label_disco)
            layout.addWidget(self.combo_discos)

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
        if self.combobox:
            return self.combo_discos.currentText(),self.line_edit.text(), self.combo_box.currentText(), self.seleccion
        else:
            return self.line_edit.text(), self.combo_box.currentText(), self.seleccion

def obtener_unidades():
    letras = string.ascii_uppercase
    unidades = [f"{letra}:" for letra in letras if os.path.exists(f"{letra}:\\")]
    return unidades
    

# Función auxiliar para mostrar el diálogo de formateo y obtener sus valores.
def obtener_valores_formateo(combobox):
    dialogo = InputFormateo(combobox) # Crea una instancia del diálogo.
    if dialogo.exec_() == QDialog.Accepted: # Si el usuario hace clic en OK.
        if combobox:
            disco, texto, opcion, seleccion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
            return disco,texto, opcion, seleccion # Retorna los valores.
        else:
            texto, opcion, seleccion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
            return texto, opcion, seleccion # Retorna los valores.
    return None, None, False # Retorna None si se canceló.


# Clase para el diálogo de entrada para la creación de particiones.
class InputParticion(QDialog):
    def __init__(self, espacio_maximo ,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Particionar Discos") # Título del diálogo.
        self.setGeometry(500,400,300,100)
        
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

        self.label_nombre = QLabel("Indique el nombre de la nueva partición:")
        self.input_nombre = QLineEdit() # Campo para la letra de la nueva partición.



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
        layout.addWidget(self.label_nombre)
        layout.addWidget(self.input_nombre)
        layout.addWidget(self.botones)
        layout.addWidget(self.label_max) # Añade la etiqueta de espacio máximo al layout.
        self.setLayout(layout)

    # Método para obtener los datos introducidos en el diálogo de partición.
    def obtener_datos(self):
        tamano_texto = self.input_tamano.text().strip() # Obtiene el texto del tamaño.
        letra_texto = self.input_letra.text().strip().upper() # Obtiene el texto de la letra, en mayúscula.
        nombre_particion = self.input_nombre.text() # Obtiene el texto de la letra, en mayúscula.

        if not tamano_texto or not letra_texto: # Si algún campo está vacío.
            QMessageBox.warning(self, "Error", "Debe completar ambos campos.")
            return None, None, None # Retorna None si hay campos vacíos.

        return int(tamano_texto), letra_texto, nombre_particion # Retorna el tamaño como entero y la letra.

# Función auxiliar para mostrar el diálogo de partición y obtener sus valores.
def obtener_valores_particiones(espacio_maximo):
    dialogo = InputParticion(espacio_maximo) # Crea una instancia del diálogo, pasando el espacio máximo.
    if dialogo.exec_() == QDialog.Accepted: # Si el usuario hace clic en OK.
        tam, letra, nombre_particion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
        if tam is not None and letra is not None: # Si se obtuvieron valores válidos.
            print(f"Tamaño: {tam} MB | Letra: {letra}") # Imprime para depuración.
            return tam, letra,nombre_particion  # Retorna los valores.
    return None, None, None # Retorna None si se canceló o hubo un error.


def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Bloque principal de ejecución cuando el script se ejecuta directamente.
if __name__ == "__main__":
    # Si no es administrador, vuelve a ejecutar el mismo script con permisos elevados
    if not es_admin():
        print("Elevando privilegios a administrador...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    app = QApplication(sys.argv) # Crea una instancia de QApplication (necesaria para cualquier aplicación PyQt).
    window = FileExplorer() # Crea una instancia de la ventana principal de la aplicación.
    window.show() # Muestra la ventana.
    sys.exit(app.exec_()) # Inicia el bucle de eventos de la aplicación y espera a que la aplicación finalice.