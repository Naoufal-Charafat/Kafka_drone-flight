import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QMenuBar, QAction,
                             QTextEdit, QVBoxLayout, QWidget, QLineEdit, QPushButton,
                             QLabel, QDialog, QVBoxLayout)

# Variables globales para el ID y el alias del dron
drone_id = ""
drone_alias = ""


class ConsoleOutput:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, msg):
        self.textbox.append(msg)

    def flush(self):
        pass


class InitialDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Ingreso de datos del dron")

        layout = QVBoxLayout()

        self.id_label = QLabel("ID Dron:", self)
        self.id_input = QLineEdit(self)

        self.alias_label = QLabel("Alias del Dron:", self)
        self.alias_input = QLineEdit(self)

        self.accept_button = QPushButton("Aceptar", self)
        self.accept_button.clicked.connect(self.accept_data)

        layout.addWidget(self.id_label)
        layout.addWidget(self.id_input)
        layout.addWidget(self.alias_label)
        layout.addWidget(self.alias_input)
        layout.addWidget(self.accept_button)

        self.setLayout(layout)

    def accept_data(self):
        global drone_id
        global drone_alias

        drone_id = self.id_input.text()
        drone_alias = self.alias_input.text()

        if drone_id and drone_alias:
            self.accept()
        else:
            print("Por favor, ingrese el ID y el alias del dron.")


class DronApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.initUI()

        # Establecer el estilo de QTextEdit
        self.console.setStyleSheet(f""" 
            font: 14px;
            color: green;
        """)

        # Redirigir la salida estándar al widget de texto
        sys.stdout = ConsoleOutput(self.console)

    def initUI(self):
        # Crear la barra de menú
        menubar = self.menuBar()

        # ... (resto de acciones y menú) ...

        # Configuración de la ventana principal
        self.setWindowTitle("Interfaz Dron")
        self.setGeometry(300, 300, 400, 250)

        # Widget de texto para mostrar los mensajes
        self.console = QTextEdit(self)
        self.console.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.console)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Crear la barra de menú
        menubar = self.menuBar()

        # Crear las acciones
        alias_action = QAction("Cambiar alias de dron", self)
        alias_action.triggered.connect(self.change_alias)

        delete_action = QAction("Eliminar dron", self)
        delete_action.triggered.connect(self.delete_dron)

        register_action = QAction("Registrar el dron", self)
        register_action.triggered.connect(self.register_dron)

        auth_action = QAction("Autentificar el dron", self)
        auth_action.triggered.connect(self.authenticate_dron)

        # Añadir las acciones al menú
        dron_menu = QMenu("Dron", self)
        dron_menu.addAction(alias_action)
        dron_menu.addAction(delete_action)
        dron_menu.addAction(register_action)
        dron_menu.addAction(auth_action)

        # Añadir el menú a la barra de menú
        menubar.addMenu(dron_menu)

    def change_alias(self):
        print("Cambiar alias del dron")

    def delete_dron(self):
        print("Eliminar dron")

    def register_dron(self):
        print("Registrar el dron")

    def authenticate_dron(self):
        print("Autentificar el dron")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    initial_dialog = InitialDialog()
    response = initial_dialog.exec_()

    if response == QDialog.Accepted:
        ex = DronApp()
        ex.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
