from tokenize import Number # No se utiliza en el código, podría ser removido.
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileSystemModel, QTreeView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSplitter, QMenu, QInputDialog, 
    QMessageBox, QDialog, QLabel, QLineEdit, QComboBox, QDialogButtonBox, QToolBar, QAction
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QIntValidator, QRegExpValidator, QIcon
from PyQt5.QtCore import QRegExp
import time # Módulo para funciones relacionadas con el tiempo.
import ctypes # Módulo para interactuar con tipos de datos C y llamar a funciones en DLLs. Usado aquí para verificación de administrador.
import win32api # Módulo para interactuar con la API de Windows. Usado para obtener letras de unidades.
import os # Módulo para interactuar con el sistema operativo, como rutas de archivos y directorios.
import sys # Módulo para acceder a parámetros y funciones específicos del sistema, como la gestión de la aplicación.
import platform # Módulo para acceder a datos de la plataforma subyacente, como el sistema operativo.
import subprocess # Módulo para ejecutar nuevos procesos y gestionar sus entradas/salidas.
import json # Módulo para codificar y decodificar datos JSON.

# Clase principal de la aplicación, hereda de QMainWindow para crear una ventana de aplicación.
class FileExplorer(QMainWindow):
    def __init__(self):
        # Bandera para ocultar la ventana de consola de los procesos subprocess.
        self.CREATE_NO_WINDOW = 0x08000000
        super().__init__() # Llama al constructor de la clase base QMainWindow.
        self.setWindowTitle("Explorador de Archivos") # Establece el título de la ventana.
        self.setGeometry(100, 100, 1000, 600) # Define la posición y tamaño inicial de la ventana (x, y, ancho, alto).

        # Configura la barra de estado para mostrar mensajes.
        self.statusBar().showMessage("Listo")

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
        self.tree.setMaximumHeight(550) # Limita la altura máxima del árbol.
        self.tree.clicked.connect(self.on_tree_clicked) # Conecta el evento de clic en el árbol a un método.
        
        # Habilitar el menú contextual personalizado en el árbol (clic derecho).
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        # Conecta el evento de clic derecho a un método específico.
        self.tree.customContextMenuRequested.connect(self.on_tree_right_click) 
        
        # Panel derecho: tabla de archivos (QTableWidget). Muestra los archivos del directorio seleccionado.
        self.right_panel = QTableWidget()
        self.right_panel.setColumnCount(2) # Define dos columnas: "Archivo" y "Tamaño (KB)".
        self.right_panel.setHorizontalHeaderLabels(["Archivo", "Tamaño (KB)"]) # Establece los encabezados de las columnas.
        self.right_panel.setColumnWidth(0, 300) # Establece el ancho de la primera columna.
        # Conecta el doble clic en un elemento de la tabla a un método.
        self.right_panel.doubleClicked.connect(self.on_right_panel_item_click) 
        
        # Splitter (QSplitter) para dividir la ventana y permitir redimensionar los paneles.
        splitter = QSplitter(Qt.Horizontal) # Splitter horizontal para dividir la ventana verticalmente.
        splitter.addWidget(self.tree) # Añade el árbol al splitter.
        splitter.addWidget(self.right_panel) # Añade el panel derecho al splitter.
        #splitter.setSizes([300, 700]) # Podría usarse para establecer los tamaños iniciales de los paneles.

        # Widget contenedor para el layout principal de la ventana.
        container = QWidget()
        container.setBaseSize(540,480) # Establece el tamaño base del contenedor.
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
            
            # Obtener la ruta completa del elemento clickeado.
            full_path = self.model.filePath(index)
            # Determinar si es una unidad raíz (ej. "C:/", "D:/") utilizando os.path.ismount.
            is_drive_root = os.path.ismount(full_path) 
            Letra = ""
            if is_drive_root:
                # Extrae la letra de la unidad.
                # Intenta extraer la letra si la ruta está en formato "Nombre (Letra:)", ej. "Disco Local (C:)".
                try:
                    inicio = full_path.index("(")
                    final = full_path.index(")")
                    Letra = full_path[inicio + 1 : final]
                except ValueError:
                    # Si no encuentra el formato esperado, asume que es una ruta de unidad simple como "C:".
                    Letra = full_path[0:2] 
            
            # Crea un menú contextual.
            menu = QMenu()
            # Si es una unidad raíz y NO es "C:", ofrece las opciones de gestión de disco.
            if is_drive_root and Letra.upper() != "C:":
                #menu.addAction("Renombrar") # Opción para renombrar, actualmente comentada.
                menu.addAction("Formatear") # Opción para formatear el disco.
                menu.addAction("Crear Particion") # Opción para crear una nueva partición.
            
            # Ejecuta el menú en la posición del clic derecho y obtiene la acción seleccionada.
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            if action: # Si se seleccionó una acción.
                accion = action.text() # Obtiene el texto de la acción seleccionada.
                print(f"Acción seleccionada: {accion}") # Imprime la acción para depuración.
                
                # Usa una sentencia match para ejecutar la lógica según la acción seleccionada.
                match accion:
                    case "Renombrar": # Lógica para renombrar un disco.
                        if Letra != "C:": # No permite renombrar la unidad C:.
                            # Abre un diálogo de entrada para que el usuario ingrese el nuevo nombre.
                            text, ok = QInputDialog.getText(self, f'Renombrar disco {Letra}', 'Nombre: ')
                            if ok: # Si el usuario hizo clic en OK.
                                nuevo_nombre = text
                                # Comando CMD: label {Letra} {nuevo_nombre}
                                # Renombra la etiqueta de volumen del disco especificado.
                                subprocess.run(["label", Letra, nuevo_nombre], shell=True)
                                # Actualiza el modelo y el TreeView para reflejar el cambio.
                                self.model.setRootPath('') 
                                self.tree.setRootIndex(self.model.index(''))
                        else:
                            QMessageBox.warning(self,"Error","El disco C: no se puede renombrar")
                        
                    case "Formatear": # Lógica para formatear un disco.
                        if Letra != "C:": # No permite formatear la unidad C:.
                            # Abre un diálogo personalizado para obtener los parámetros de formateo.
                            etiqueta, sistema_archivos, seleccion = obtener_valores_formateo()
                            if seleccion == True: # Si el usuario confirmó la selección en el diálogo.
                                # Pide confirmación final antes de formatear.
                                reply = QMessageBox.question(None, 'Desea continuar', f'Desea formatear el disco: {Letra}',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes: # Si el usuario confirma.
                                    self.formatear_disco(Letra, sistema_archivos, etiqueta) # Llama al método para formatear.
                                    # Actualiza el modelo y el TreeView.
                                    self.model.setRootPath('')
                                    self.tree.setRootIndex(self.model.index(''))
                                    self.on_tree_clicked(index) # También actualiza el panel derecho.
                        else:
                            QMessageBox.warning(self,"Error","El disco C: no se puede formatear")
                                                    
                    case "Crear Particion": # Lógica para crear una partición.
                        # Obtiene información del disco físico asociado a la letra de unidad.
                        info = self.obtener_disco_fisico(Letra)
                        # tamano se refiere al espacio restante en el volumen (espacio libre dentro de la partición).
                        tamano = info["SizeRemaining"] 
                        if not info or tamano is None: # Si no se pudo obtener la información o el tamaño.
                            QMessageBox.warning(self, "Error", "No se pudo obtener el tamaño del disco.")
                            return

                        disco_num = info['Number'] # Obtiene el número de disco físico.
                        # Calcula el espacio libre máximo en MB para la nueva partición.
                        # Se usa SizeRemaining que es el espacio libre de la partición actual.
                        max_espacio_libre = round((tamano/1000**2),2) 
                        # Deja un margen de 1500 MB para evitar posibles errores de cálculo o de DiskPart.
                        max_espacio_libre = max_espacio_libre - 1500 

                        # Abre un diálogo para obtener el tamaño deseado y la letra para la nueva partición.
                        tamano_particion, nueva_letra, nombre_particion = obtener_valores_particiones(max_espacio_libre) 

                        if tamano_particion is not None and nueva_letra is not None:
                            # Valida que el tamaño de la partición no exceda el espacio libre disponible.
                            if tamano_particion > max_espacio_libre:
                                QMessageBox.warning(self, "Error", f"El tamaño de la partición ({tamano_particion} MB) excede el espacio libre disponible ({max_espacio_libre} MB).")
                                return

                            # Pide confirmación antes de proceder con la creación de la partición.
                            reply = QMessageBox.question(None, 'Confirmar Creación', f'¿Desea crear una partición de {tamano_particion} MB en el disco {Letra} con la letra {nueva_letra}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                            if reply == QMessageBox.Yes:
                                # Llama al método para crear la partición.
                                self.crear_particion(disco_num, Letra, tamano_particion, nueva_letra, nombre_particion)
                                # Actualiza el modelo y el TreeView para reflejar la nueva partición.
                                self.model.setRootPath('')
                                self.tree.setRootIndex(self.model.index(''))
                                self.on_tree_clicked(index) # Actualiza también el panel derecho.

        except Exception as e:
            # Muestra un mensaje de error si ocurre una excepción durante la operación.
            QMessageBox.warning(self, "Error de operación", f"No se pudo realizar la operación seleccionada. Error: {e}")
            print(e) # Imprime el error en la consola para depuración.

    # Método para formatear un disco.
    def formatear_disco(self, letra, sistema_archivo, nuevo_nombre):
        try:
            # Comando CMD: format {letra} /FS:{sistema_archivo} /Q /V:{nuevo_nombre} /Y
            # {letra}: La letra de la unidad a formatear (ej. D:).
            # /FS:{sistema_archivo}: Especifica el sistema de archivos (ej. NTFS, FAT32).
            # /Q: Realiza un formato rápido.
            # /V:{nuevo_nombre}: Asigna una etiqueta de volumen al disco formateado.
            # /Y: Suprime la solicitud de confirmación del usuario.
            res1 = subprocess.Popen(["format", letra, f"/FS:{sistema_archivo}", "/Q", f"/V:{nuevo_nombre}", "/Y"],
                                    stdout=subprocess.PIPE, # Captura la salida estándar del proceso.
                                    stderr=subprocess.STDOUT, # Redirige la salida de error a la salida estándar.
                                    creationflags=self.CREATE_NO_WINDOW, # Evita que se cree una ventana de consola.
                                    text=True, # Decodifica la salida como texto.
                                    shell=True) # Ejecuta el comando a través del shell de Windows.
            
            # Mostrar salidas en la barra de estado y en la consola.
            output = ""
            for line in res1.stdout:
                output += line
                self.statusBar().showMessage(f"{line.strip()}") # Muestra cada línea en la barra de estado.
                QApplication.processEvents()  # Permite que la GUI se actualice mientras se ejecuta el comando.
                time.sleep(0.05)  # Pequeña pausa para que el usuario pueda leer el mensaje (opcional).
            res1.wait() # Espera a que el proceso de formateo termine.
            QMessageBox.information(self, 'Proceso completado', 'El disco se ha formateado correctamente')
            self.statusBar().showMessage("Operacion realizada con exito", 3000) # Muestra un mensaje de éxito temporal.
            
        except Exception as e:
            # Muestra un mensaje de error si el formateo falla.
            QMessageBox.warning(self, 'Error de formateo', f'Hubo un error al formatear el disco \n Error: {e}')
            # NOTA: Para una actualización más robusta, podrías necesitar llamar a self.model.readDirectory() 
            # en la raíz o la unidad formateada, o incluso reconstruir el QFileSystemModel si los cambios 
            # no se reflejan automáticamente.

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
        ruta = self.model.filePath(index) # Obtiene la ruta de la carpeta seleccionada.
        self.statusBar().showMessage(ruta) # Muestra la ruta actual en la barra de estado.
        archivos = self.obtener_archivos_de_ruta(ruta) # Obtiene la lista de archivos de esa ruta.
        self.lista_archivos = archivos # Almacena la lista de archivos para futuras referencias (ej. doble clic).

        self.right_panel.setRowCount(len(archivos)) # Establece el número de filas en la tabla.
        for row, archivo in enumerate(archivos): # Itera sobre cada archivo.
            nombre = os.path.basename(archivo) # Obtiene solo el nombre del archivo.
            tamaño_kb = round(os.path.getsize(archivo) / 1024, 2) # Obtiene el tamaño en bytes y lo convierte a KB.
            icon = QIcon(self.model.fileIcon(self.model.index(archivo))) # Obtiene el ícono del archivo.
            item = QTableWidgetItem(icon, nombre) # Crea un QTableWidgetItem con el ícono y el nombre.
            self.right_panel.setItem(row, 0, item) # Establece el ítem en la primera columna.

            item_size = QTableWidgetItem(f"{tamaño_kb:.2f}") # Crea un ítem para el tamaño.
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # Alinea el texto a la derecha.
            self.right_panel.setItem(row, 1, item_size) # Establece el ítem en la segunda columna.

        self.right_panel.setAlternatingRowColors(True) # Habilita colores alternos para las filas.
        self.right_panel.setEditTriggers(QTableWidget.NoEditTriggers) # Deshabilita la edición de las celdas.
        self.right_panel.resizeColumnsToContents() # Ajusta automáticamente el ancho de las columnas al contenido.

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
        letra = letra_unidad.strip(":").upper() # Normaliza la letra de la unidad.
        # Comando PowerShell para obtener información del disco y el volumen.
        # $disk = Get-Partition -DriveLetter '{letra}' | Get-Disk: Obtiene el objeto de disco físico asociado a la letra de la partición.
        # $volume = Get-Volume -DriveLetter '{letra}': Obtiene el objeto de volumen asociado a la letra de la unidad.
        # $info = [PSCustomObject]@: Crea un objeto personalizado con la información relevante.
        # Number          = $disk.Number;: Número de disco físico.
        # SizeTotal       = $disk.Size;: Tamaño total del disco físico.
        # SizeRemaining   = $volume.SizeRemaining;: Espacio libre restante en el volumen.
        # $info | ConvertTo-Json -Compress: Convierte el objeto a formato JSON para facilitar el parseo en Python.
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
        salida, error = proceso.communicate() # Espera a que el proceso termine y captura su salida y errores.
        if proceso.returncode == 0: # Si el comando se ejecutó sin errores.
            try:
                datos = json.loads(salida) # Parsea la salida JSON.
                return datos # Retorna los datos del disco.
            except json.JSONDecodeError:
                print("No se pudo decodificar la salida JSON.")
                print("Salida:", salida)
        else:
            print("Error al obtener información del disco:", error) # Imprime el error si lo hubo.
        return None

    # Método para crear una partición en un disco.
    def crear_particion(self, disco_id, letra, tamaño_MB, nueva_letra, nombre_etiqueta): 
        # Asegura que la etiqueta no esté vacía.
        if nombre_etiqueta == "":
            nombre_etiqueta = "Nueva Partición"
        
        # Script DiskPart para reducir el volumen existente.
        # select volume {letra}: Selecciona el volumen por su letra (ej. D:).
        # shrink desired={tamaño_MB}: Reduce el volumen en el tamaño especificado en MB.
        # exit: Sale de DiskPart.
        shrink = f"select volume {letra}\nshrink desired={tamaño_MB}\nexit\n"
        
        # Script DiskPart para crear y formatear la nueva partición.
        # sel disk {disco_id}: Selecciona el disco físico por su número.
        # create partition primary size={tamaño_MB}: Crea una nueva partición primaria del tamaño especificado en MB.
        # format quick fs=ntfs label=\"{nombre_etiqueta}\": Formatea la partición rápidamente con sistema NTFS y la etiqueta dada.
        # assign letter={nueva_letra}: Asigna la letra de unidad especificada a la nueva partición.
        # exit: Sale de DiskPart.
        create = (
            f"sel disk {disco_id}\n"
            f"create partition primary size={tamaño_MB}\n"
            f"format quick fs=ntfs label=\"{nombre_etiqueta}\"\n"
            f"assign letter={nueva_letra}\n"
            f"exit\n"
        )

        # Escribe los scripts en archivos temporales para DiskPart.
        with open("shrink.txt", "w") as f:
            f.write(shrink)
            
        with open("create.txt", "w") as f:
            f.write(create)

        # Ejecuta el script de reducción de volumen con DiskPart.
        resShrink = subprocess.Popen(["diskpart", "/s", "shrink.txt"],
                                     creationflags=self.CREATE_NO_WINDOW, # Evita la ventana de consola.
                                     stdout=subprocess.PIPE, # Captura la salida estándar.
                                     stderr=subprocess.STDOUT, # Redirige errores a la salida estándar.
                                     text=True) # Decodifica la salida como texto.
        
        # Muestra la salida del proceso de reducción en la barra de estado.
        output = ""
        progreso = 0
        for line in resParticion.stdout:
            output += line
            progreso += 1
            self.statusBar().showMessage(f"Progreso: {progreso} - {line.strip()} ")
            print(line.strip()) # Imprime también en la consola.
            QApplication.processEvents()  # Permite que la GUI se actualice.
            time.sleep(0.05)  # Pausa corta.
        resShrink.wait() # Espera a que DiskPart termine.
        
        # Verifica el código de retorno del proceso de reducción.
        if resShrink.returncode != 0:
            QMessageBox.warning(self, "Error", "Error al reducir el volumen. Revisa los permisos o el espacio disponible.")
            os.remove("shrink.txt") # Elimina el archivo temporal.
            return False # Retorna falso indicando un fallo.
        os.remove("shrink.txt") # Elimina el archivo temporal después de un éxito.
        resShrink.stdout.close() # Cierra el pipe de salida.
        time.sleep(1) # Pequeña pausa para que el sistema reconozca los cambios.
        
        # Ejecuta el script de creación de partición con DiskPart.
        resParticion = subprocess.Popen(["diskpart", "/s", "create.txt"],
                                        creationflags=self.CREATE_NO_WINDOW, # Evita la ventana de consola.
                                        stdout=subprocess.PIPE, # Captura la salida estándar.
                                        stderr=subprocess.STDOUT, # Redirige errores a la salida estándar.
                                        text=True) # Decodifica la salida como texto.
        
        # Muestra la salida del proceso de creación en la barra de estado.
        output = ""
        for line in resParticion.stdout:
            output += line
            self.statusBar().showMessage(f"{line.strip()}")
            print(line.strip()) # Imprime también en la consola.
            QApplication.processEvents()  # Permite que la GUI se actualice.
            time.sleep(0.05)  # Pausa corta.
        resParticion.wait() # Espera a que DiskPart termine.
        
        # Verifica el código de retorno del proceso de creación.
        if resParticion.returncode != 0:
            QMessageBox.warning(self, "Error", "Error al crear la partición. Revisa los permisos o el espacio disponible.")
            os.remove("create.txt") # Elimina el archivo temporal.
            return False # Retorna falso indicando un fallo.
        os.remove("create.txt") # Elimina el archivo temporal después de un éxito.
        resParticion.stdout.close() # Cierra el pipe de salida.
        self.statusBar().showMessage("Partición creada con éxito", 3000) # Muestra un mensaje de éxito temporal.
        return resParticion.returncode == 0 # Retorna verdadero si la operación fue exitosa.
        
    def obtener_informacion_particion(self, letra_unidad):
        """
        Obtiene información detallada de una partición específica, incluyendo su tamaño actual
        y el espacio que se puede reducir o extender utilizando PowerShell.
        """
        letra = letra_unidad.strip(":").upper() # Normaliza la letra de la unidad.
        # Comando PowerShell para obtener información de la partición y sus capacidades de redimensionamiento.
        # Get-Partition -DriveLetter {letra}: Obtiene el objeto de partición por su letra de unidad.
        # Get-PartitionSupportedSize -Partition $partition: Obtiene las capacidades de tamaño soportadas (mínimo, máximo de reducción/extensión).
        # [PSCustomObject]@{...}: Crea un objeto personalizado con la información relevante.
        # DriveLetter: Letra de la unidad.
        # Size: Tamaño actual de la partición en bytes.
        # SizeMin: Tamaño mínimo al que la partición puede ser reducida (en bytes).
        # SizeMax: Tamaño máximo al que la partición puede ser extendida (en bytes).
        # ConvertTo-Json -Compress: Convierte el objeto a formato JSON para facilitar el parseo en Python.
        
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
        # Ejecuta el comando PowerShell.
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        if resultado.returncode == 0: # Si el comando se ejecutó sin errores.
            try:
                datos = json.loads(resultado.stdout) # Parsea la salida JSON.
                return datos # Retorna los datos de la partición.
            except json.JSONDecodeError:
                print("No se pudo decodificar la salida JSON al obtener información de partición.")
                print(f"Salida PowerShell: {resultado.stdout}")
        else:
            print("Error al obtener información de la partición:", resultado.stderr) # Imprime el error si lo hubo.
        return None
 
# Clase para el diálogo de entrada de formateo de discos.
class InputFormateo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent) # Llama al constructor de la clase base QDialog.
        self.setWindowTitle("Formateo Discos") # Título del diálogo.
        self.setGeometry(500,400,300,100) # Posición y tamaño del diálogo.

        # Widgets del diálogo.
        self.label = QLabel("Escriba un nombre y elija una opción:") # Etiqueta instructiva.
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

        self.setLayout(layout) # Establece el layout para el diálogo.
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
        return self.line_edit.text(), self.combo_box.currentText(), self.seleccion

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
        super().__init__(parent) # Llama al constructor de la clase base QDialog.
        self.setWindowTitle("Particionar Discos") # Título del diálogo.
        self.setGeometry(500,400,300,100) # Posición y tamaño del diálogo.
        
        self.label_max = QLabel(f"Espacio máximo disponible: {espacio_maximo} MB") # Muestra el espacio máximo.
        maxInt = int(espacio_maximo) # Convierte el espacio máximo a entero para el validador.
        
        # Widgets del diálogo.
        self.label_tamano = QLabel("Indique el tamaño de la partición (MB):") # Etiqueta para el tamaño.
        self.input_tamano = QLineEdit() # Campo para el tamaño de la partición.
        # Validador para asegurar que solo se ingresen números enteros entre 1 y el espacio máximo.
        self.input_tamano.setValidator(QIntValidator(1, maxInt)) 

        self.label_letra = QLabel("Indique la letra de la nueva partición:") # Etiqueta para la letra.
        self.input_letra = QLineEdit() # Campo para la letra de la nueva partición.
        self.input_letra.setMaxLength(1) # Solo permite un carácter.
        # Validador para asegurar que solo se ingresen letras.
        self.input_letra.setValidator(QRegExpValidator(QRegExp("[A-Za-z]"))) 

        self.label_nombre = QLabel("Indique el nombre de la nueva partición:") # Etiqueta para el nombre.
        self.input_nombre = QLineEdit() # Campo para la letra de la nueva partición.

        # Botones de OK y Cancelar.
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.accept) # Conecta el botón OK.
        self.botones.rejected.connect(self.reject) # Conecta el botón Cancelar.

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
        self.setLayout(layout) # Establece el layout para el diálogo.

    # Método para obtener los datos introducidos en el diálogo de partición.
    def obtener_datos(self):
        tamano_texto = self.input_tamano.text().strip() # Obtiene el texto del tamaño, eliminando espacios.
        letra_texto = self.input_letra.text().strip().upper() # Obtiene el texto de la letra, en mayúscula y sin espacios.
        nombre_particion = self.input_nombre.text() # Obtiene el texto del nombre de la partición.

        if not tamano_texto or not letra_texto: # Si algún campo obligatorio está vacío.
            QMessageBox.warning(self, "Error", "Debe completar ambos campos.")
            return None, None, None # Retorna None si hay campos vacíos.

        return int(tamano_texto), letra_texto, nombre_particion # Retorna el tamaño como entero, la letra y el nombre.

# Función auxiliar para mostrar el diálogo de partición y obtener sus valores.
def obtener_valores_particiones(espacio_maximo):
    dialogo = InputParticion(espacio_maximo) # Crea una instancia del diálogo, pasando el espacio máximo.
    if dialogo.exec_() == QDialog.Accepted: # Si el usuario hace clic en OK.
        tam, letra, nombre_particion = dialogo.obtener_datos() # Obtiene los datos del diálogo.
        if tam is not None and letra is not None: # Si se obtuvieron valores válidos.
            print(f"Tamaño: {tam} MB | Letra: {letra}") # Imprime para depuración.
            return tam, letra, nombre_particion # Retorna los valores.
    return None, None, None # Retorna None si se canceló o hubo un error en la obtención de datos.

# Función para verificar si el usuario tiene privilegios de administrador.
def es_admin():
    try:
        # Llama a la función IsUserAnAdmin de la API de shell32 de Windows.
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Bloque principal de ejecución cuando el script se ejecuta directamente.
if __name__ == "__main__":
    # Si la aplicación no se está ejecutando como administrador, la eleva a administrador.
    if not es_admin():
        print("Elevando privilegios a administrador...")
        # Ejecuta el mismo script (sys.executable) con la opción "runas" (ejecutar como administrador).
        # sys.argv contiene los argumentos de línea de comandos.
        # El último parámetro '1' es SW_SHOWNORMAL, para mostrar la ventana normalmente.
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit() # Sale de la instancia actual, ya que se iniciará una nueva con privilegios elevados.
    app = QApplication(sys.argv) # Crea una instancia de QApplication (necesaria para cualquier aplicación PyQt).
    window = FileExplorer() # Crea una instancia de la ventana principal de la aplicación.
    window.show() # Muestra la ventana.
    sys.exit(app.exec_()) # Inicia el bucle de eventos de la aplicación y espera a que la aplicación finalice.