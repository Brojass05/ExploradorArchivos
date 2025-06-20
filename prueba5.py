from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QFileSystemModel, QTreeView, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QSplitter, QMenu, QInputDialog, 
    QMessageBox, QDialog, QLabel, QLineEdit, QComboBox, QDialogButtonBox, QToolBar
)
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp
import win32api
import os # Módulo para interactuar con el sistema operativo, como rutas de archivos y directorios.
import sys # Módulo para acceder a parámetros y funciones específicos del sistema, como la gestión de la aplicación.
import platform # Módulo para acceder a datos de la plataforma subyacente, como el sistema operativo.
import subprocess # Módulo para ejecutar nuevos procesos y gestionar sus entradas/salidas.
import json # Módulo para codificar y decodificar datos JSON.

# Clase principal de la aplicación, hereda de QMainWindow para crear una ventana de aplicación.
class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__() # Llama al constructor de la clase base QMainWindow.
        self.setWindowTitle("Explorador de Archivos") # Establece el título de la ventana.
        self.setGeometry(100, 100, 1000, 600) # Define la posición y tamaño inicial de la ventana (x, y, ancho, alto).

        self.statusBar().showMessage("Listo")

        # Obtener el sistema operativo del equipo (ej. 'Windows', 'Darwin' para macOS, 'Linux').
        self.sistema = platform.system() 

        # Modelo del sistema de archivos. QFileSystemModel proporciona un modelo de datos para el sistema de archivos local.
        self.model = QFileSystemModel()
        self.model.setRootPath('') # Establece la raíz del modelo al directorio principal del sistema.
        
        
        # Lista para almacenar las rutas completas de los archivos mostrados en el panel derecho.
        self.lista_archivos = []

        self.tollBar = QToolBar(self)

        # Árbol de directorios (QTreeView). Muestra la jerarquía del sistema de archivos.
        self.tree = QTreeView()
        self.tree.setModel(self.model) # Asocia el modelo de sistema de archivos al QTreeView.
        self.tree.setRootIndex(self.model.index('')) # Muestra el contenido del directorio raíz.
        self.tree.setColumnWidth(0, 150) # Establece el ancho de la primera columna (nombre del archivo/directorio).
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
        #splitter.setSizes([300, 700]) # Podría usarse para establecer los tamaños iniciales de los paneles.

        # Widget contenedor para el layout principal de la ventana.
        container = QWidget()
        container.setBaseSize(540,480)
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
                menu.addAction("Renombrar")
                menu.addAction("Formatear")
                menu.addAction("Reducir y Crear Partición") # Nueva opción
            
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
                            info = self.obtener_disco_fisico(Letra)
                            if info is None: # Asegúrate de que se obtuvo información del disco
                                QMessageBox.warning(self, "Error", "No se pudo obtener información del disco físico.")
                                return

                            disco_num = info['Number']
                            # Aseguramos que el espacio disponible sea solo el LargestFreeExtent para crear particiones.
                            # Si se muestra el tamaño total del disco, podría confundir al usuario.
                            max_espacio_libre = round(info.get("LargestFreeExtent", 0) / (1024 ** 2), 2)
                            
                            # Solo si el disco tiene espacio libre significativo
                            if max_espacio_libre <= 0.1: # Considerando un margen muy pequeño
                                QMessageBox.warning(self, "Error", f"No hay espacio libre significativo en el disco {Letra} para crear una nueva partición. Espacio libre: {max_espacio_libre} MB.")
                                return

                            tamano_particion, nueva_letra = obtener_valores_particiones(max_espacio_libre) # Pasar solo el espacio libre
                            
                            if tamano_particion is not None and nueva_letra is not None:
                                if tamano_particion > max_espacio_libre:
                                    QMessageBox.warning(self, "Error", f"El tamaño de la partición ({tamano_particion} MB) excede el espacio libre disponible ({max_espacio_libre} MB).")
                                    return

                                reply = QMessageBox.question(None, 'Confirmar Creación', f'¿Desea crear una partición de {tamano_particion} MB en el disco {Letra} con la letra {nueva_letra}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes:
                                    self.crear_particion(disco_num, tamano_particion, nueva_letra)
                    case "Reducir y Crear Partición":
                        # Nueva lógica para reducir y crear
                        if Letra and Letra.upper() != "C:":
                            # Obtener la información de la partición
                            partition_info = self.obtener_informacion_particion(Letra)
                            if not partition_info:
                                QMessageBox.warning(self, "Error", f"No se pudo obtener información para la partición {Letra}.")
                                return

                            min_size_mb = round(partition_info['SizeMin'] / (1024 ** 2), 2)
                            max_shrink_mb = round((partition_info['Size'] - partition_info['SizeMin']) / (1024 ** 2), 2)
                            
                            if max_shrink_mb <= 0.1: # Margen pequeño
                                QMessageBox.warning(self, "Error", f"La partición {Letra} no tiene espacio significativo para reducir. Espacio máximo a reducir: {max_shrink_mb} MB.")
                                return

                            # Diálogo para pedir el tamaño a reducir y la nueva letra
                            shrink_size_mb, new_part_letter, ok = self.get_shrink_and_new_partition_values(max_shrink_mb, min_size_mb)
                            if ok and shrink_size_mb is not None and new_part_letter is not None:
                                if shrink_size_mb > max_shrink_mb:
                                    QMessageBox.warning(self, "Error", f"El tamaño a reducir ({shrink_size_mb} MB) excede el máximo disponible ({max_shrink_mb} MB).")
                                    return

                                reply = QMessageBox.question(self, 'Confirmar Operación',
                                                             f'¿Desea reducir {Letra} en {shrink_size_mb} MB y crear una nueva partición con letra {new_part_letter}?',
                                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                if reply == QMessageBox.Yes:
                                    self.shrink_and_create_partition(Letra, shrink_size_mb, new_part_letter)
                        else:
                            QMessageBox.warning(self, "Error", "La partición C: no se puede reducir de esta manera o la unidad no es válida.")

        except Exception as e:
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
            self.model.setRootPath('') 
            self.tree.setRootIndex(self.model.index(''))
            QMessageBox.information(self, 'Proceso completado', 'El disco se ha formateado correctamente')
            self.statusBar().showMessage("Operacion realizada con exito", 3000)
            
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
        self.statusBar().showMessage(ruta)
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

    # Método para crear una partición en un disco.
    # Método para crear una partición en un disco.
    def crear_particion(self, disco_id, tamaño_MB, letra_propuesta):
        # Asegura que la letra esté en mayúscula y sea solo un carácter, y que no sea 'C'.
        letra_propuesta = str(letra_propuesta).upper()[0]
        if letra_propuesta == 'C':
            QMessageBox.warning(self, "Error de Partición", "No se puede asignar 'C:' a una nueva partición. Por favor, elija otra letra.")
            return

        print(f"Intentando crear partición en Disco: {disco_id}, Tamaño: {tamaño_MB}MB, Letra propuesta: {letra_propuesta}")

        # Comando PowerShell para crear y formatear la partición, y luego asignar la letra.
        # Es importante que el formateo se haga en la misma secuencia.
        comando = [
            "powershell",
            "-Command",
            (
                f"$part = New-Partition -DiskNumber {disco_id} -Size {tamaño_MB}MB -AssignDriveLetter;" # Crea la partición y asigna una letra temporal
                f"if ($part) {{" # Verifica si la partición se creó con éxito
                f"    Format-Volume -DriveLetter $part.DriveLetter -FileSystem NTFS -NewFileSystemLabel 'NuevaParticion' -Confirm:$false;" # Formatea la partición con su letra temporal
                f"    Set-Partition -DriveLetter $part.DriveLetter -NewDriveLetter {letra_propuesta};" # Re-asigna a la letra deseada
                f"    Write-Host \"Partición creada y formateada con éxito en $($part.DriveLetter) y reasignada a {letra_propuesta}\";"
                f"}} else {{"
                f"    Write-Error \"No se pudo crear la partición.\";"
                f"}}"
            )
        ]
        
        # Ejecuta el comando PowerShell.
        resultado = subprocess.run(comando, capture_output=True, text=True, shell=True, check=False) # Agregamos shell=True por si acaso

        if resultado.returncode == 0:
            # Puedes verificar si la letra asignada es realmente la que querías.
            # Esto podría requerir una llamada adicional a PowerShell o a win32api
            # para listar las unidades después de un breve retraso.
            QMessageBox.information(self, "Partición Creada", "Partición creada y formateada con éxito.")
            # **Importante:** Actualizar el TreeView después de la operación.
            # Esto forza al modelo a reescanear el sistema de archivos.
            self.model.setRootPath('')
            self.tree.setRootIndex(self.model.index(''))
            self.statusBar().showMessage("Operacion realizada con exito", 3000)
        else:
            error_message = resultado.stderr.strip()
            if not error_message: # Si stderr está vacío, a veces el error está en stdout
                error_message = resultado.stdout.strip()
            QMessageBox.warning(self, "Error en Partición", f"Error al crear partición:\n{error_message}\nCódigo de salida: {resultado.returncode}")
            print(f"Error stdout: {resultado.stdout}")
            print(f"Error stderr: {resultado.stderr}")
        
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

    
    
    def shrink_and_create_partition(self, original_drive_letter, shrink_size_mb, new_part_letter):
        """
        Reduce una partición existente y crea una nueva partición con el espacio liberado.
        """
        original_drive_letter = original_drive_letter.strip(":").upper()
        new_part_letter = new_part_letter.strip().upper()[0]

        # Convertir MB a Bytes para PowerShell cmdlets
        shrink_size_bytes = int(shrink_size_mb * (1024 ** 2))

        # Script PowerShell para reducir, y luego crear y formatear la nueva partición
        # Este script busca el "LargestFreeExtent" después de la reducción.
        comando = [
            "powershell",
            "-Command",
            (
                f"Resize-Partition -DriveLetter {original_drive_letter} -Size ({original_drive_letter}.Size - {shrink_size_bytes}); " # Reduce la partición
                f"$disk = Get-Partition -DriveLetter {original_drive_letter} | Get-Disk; "
                f"if ($disk) {{ "
                f"   $unallocatedSize = $disk.LargestFreeExtent; "
                f"   if ($unallocatedSize -gt 0) {{ "
                f"       $newPart = New-Partition -DiskNumber $disk.Number -Size $unallocatedSize -AssignDriveLetter; " # Crea una nueva partición con todo el espacio sin asignar
                f"       if ($newPart) {{ "
                f"           Format-Volume -DriveLetter $newPart.DriveLetter -FileSystem NTFS -NewFileSystemLabel 'NuevaParticion' -Confirm:$false; "
                f"           Set-Partition -DriveLetter $newPart.DriveLetter -NewDriveLetter {new_part_letter}; "
                f"           Write-Host \"Operación completada: {original_drive_letter} reducida y nueva partición creada con letra {new_part_letter}.\"; "
                f"       }} else {{ Write-Error \"No se pudo crear la nueva partición.\"; }} "
                f"   }} else {{ Write-Error \"No se generó espacio sin asignar suficiente después de la reducción.\"; }} "
                f"}} else {{ Write-Error \"No se pudo encontrar el disco físico.\"; }}"
            )
        ]

        resultado = subprocess.run(comando, capture_output=True, text=True, shell=True, check=False)

        if resultado.returncode == 0:
            QMessageBox.information(self, "Operación Exitosa", "Partición reducida y nueva partición creada con éxito.")
            self.model.setRootPath('') 
            self.tree.setRootIndex(self.model.index(''))
        else:
            error_message = resultado.stderr.strip()
            if not error_message:
                error_message = resultado.stdout.strip()
            QMessageBox.warning(self, "Error en Operación", f"Error al reducir o crear partición:\n{error_message}\nCódigo de salida: {resultado.returncode}")
            print(f"Error stdout: {resultado.stdout}")
            print(f"Error stderr: {resultado.stderr}")

    
    def get_shrink_and_new_partition_values(self, max_shrink_mb, min_partition_size_mb):
        """
        Diálogo para obtener el tamaño a reducir y la nueva letra de partición.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Reducir y Crear Partición")
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Espacio máximo a reducir: {max_shrink_mb} MB"))
        layout.addWidget(QLabel(f"La partición existente mantendrá al menos: {min_partition_size_mb} MB"))
        
        layout.addWidget(QLabel("Tamaño a reducir (MB):"))
        shrink_input = QLineEdit()
        shrink_input.setValidator(QIntValidator(1, int(max_shrink_mb))) # Validar hasta el máximo a reducir
        layout.addWidget(shrink_input)

        layout.addWidget(QLabel("Letra para la nueva partición:"))
        letter_input = QLineEdit()
        letter_input.setMaxLength(1)
        letter_input.setValidator(QRegExpValidator(QRegExp("[A-Za-z]")))
        layout.addWidget(letter_input)
        
        # Validar letra de unidad en tiempo real
        existing_letters = self.get_existing_drive_letters() # Asegúrate de que esta función exista
        def validate_letter(text):
            if text.upper() in existing_letters or text.upper() == 'C':
                letter_input.setStyleSheet("background-color: yellow;")
            else:
                letter_input.setStyleSheet("")
        letter_input.textChanged.connect(validate_letter)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            shrink_size = int(shrink_input.text()) if shrink_input.text().isdigit() else None
            new_letter = letter_input.text().strip().upper() if letter_input.text() else None
            
            # Validación final de la letra
            if new_letter in existing_letters or new_letter == 'C':
                QMessageBox.warning(dialog, "Error", f"La letra '{new_letter}:' ya está en uso o no es válida (C:). Elija otra.")
                return None, None, False

            return shrink_size, new_letter, True
        return None, None, False
    
    
    def get_existing_drive_letters(self):
        """
        Obtiene un conjunto de letras de unidades lógicas existentes en el sistema (Windows).
        Necesitarías import `win32api` para esto.
        """
        letters = set()
        # win32api.GetLogicalDriveStrings() devuelve una cadena como "C:\0D:\0E:\0\0"
        for drive in win32api.GetLogicalDriveStrings().split('\000'):
            if drive and len(drive) >= 2 and drive[1] == ':':
                letters.add(drive[0].upper())
        return letters
    
    
# Clase para el diálogo de entrada de formateo de discos.
class InputFormateo(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Formateo Discos") # Título del diálogo.
        self.setGeometry(500,400,300,100)

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