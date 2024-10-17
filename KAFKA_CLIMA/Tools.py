
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QLineEdit, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from Settings import STX, ETX
import sqlite3
import socket
import os
import sys
from time import sleep

import hashlib
from threading import Thread, Lock
BUFFER_SIZE = 1024
# =====================Funciones========================


@staticmethod
def load_config(filename):
    config = {}
    with open(filename, 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            # Si el valor es numérico, conviértelo a entero
            if value.isdigit():
                value = int(value)
            # Si el valor parece una dirección IP y puerto, déjalo como cadena
            elif ':' in value:
                pass
            # Si el valor es una secuencia de escape, evalúalo
            elif value.startswith('\\'):
                value = bytes(value, "utf-8").decode("unicode_escape")
            config[key] = value
    return config


config = load_config('config.txt')
TEMPERATURE_DEFAULT = config['TEMPERATURE_DEFAULT']
# ====================BdWeather===========================


class BdWeather:
    def __init__(self):
        self.db_path = 'BD/bd1.sqlite'
        self.create_bd('ALICANTE', TEMPERATURE_DEFAULT)

    def create_bd(self, CITY, TEMPERATURE):

        if not os.path.exists('BD'):
            os.makedirs('BD')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Weather'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Weather (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        city TEXT NOT NULL,
                        temperature REAL NOT NULL
                    )
                ''')

                cursor.execute('''
                INSERT INTO Weather (city, temperature) VALUES (?, ?)
            ''', (CITY, TEMPERATURE))

    def get_temperature(self, CITY):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Consulta para obtener la temperatura de una ciudad específica
            cursor.execute(
                "SELECT temperature FROM Weather WHERE city = ?", (CITY,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                print(
                    f"No se encontró información para la ciudad: {CITY}.")
                return None

    def edit_temperature(self, city='', new_temperature=0):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Actualizar la temperatura de una ciudad específica
            cursor.execute(
                "UPDATE Weather SET temperature = ? WHERE city = ?", (new_temperature, city))

            # Verificar si la operación afectó alguna fila
            if cursor.rowcount == 0:
                print(
                    f"No se encontró la ciudad: {city}. No se realizó ninguna actualización.")
            else:
                print(
                    f"La temperatura de {city} se ha actualizado a {new_temperature}°C.")
# ======================Protocol========================


class Protocol:

    @staticmethod
    def calculate_lrc(data: str) -> str:
        """
        Calcule la verificación de redundancia longitudinal (LRC) para los datos proporcionados.
         Aquí usaremos un XOR simple de todos los caracteres como ejemplo.
        """
        lrc_value = 0
        for char in data:
            lrc_value ^= ord(char)
        return chr(lrc_value)

    def Pack_message(message: str) -> str:
        """
        Empaquete los datos proporcionados en el formato <STX><DATA><ETX><LRC>.
        """
        return STX + message + ETX + Protocol.calculate_lrc(message)

    def Unpack_message(message: str) -> (str):
        """
        Desempaquete un mensaje del formato <STX><DATA><ETX><LRC>.
         Devuelve los datos y un booleano que indica si el mensaje es válido (True) o tiene errores (False).
        """
        if message[0] == STX and message[-2] == ETX:
            data = message[1:-2]
            received_lrc = message[-1]
            calculated_lrc = Protocol.calculate_lrc(data)
            return data, received_lrc == calculated_lrc
        else:
            return None, False

# ======================UI==============================


class UI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.runBWeather = BdWeather()
        self.temperature = self.runBWeather.get_temperature('ALICANTE')
        self.initializeUI()

    def initializeUI(self):
        # Set the size of the window
        self.setGeometry(100, 100, 250, 300)
        self.setWindowTitle('APP WEATHER')

        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a vertical layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create the 'WEATHER' label
        self.label_title = QLabel("[WEATHER]")
        self.label_title.setStyleSheet("color: blue;")
        self.label_title.setFont(QFont('Arial', 18))
        self.label_title.setAlignment(Qt.AlignCenter)

        # Create the 'WEATHER' label
        self.label_temperature = QLabel(f'{self.temperature} Cº')
        self.label_temperature.setStyleSheet("color: green;")
        self.label_temperature.setFont(QFont('Arial', 22))
        self.label_temperature.setAlignment(Qt.AlignCenter)

        # Create the textbox
        self.weather_textbox = QLineEdit()
        self.weather_textbox.setFont(QFont('Arial', 18))
        self.weather_textbox.setAlignment(Qt.AlignCenter)

        # Create the 'Actualizar temperatura' button
        update_button = QPushButton("Actualizar\n Temperatura")
        update_button.setStyleSheet("color: green;")
        update_button.setFont(QFont('Arial', 22))
        update_button.clicked.connect(
            self.update_temperature)  # Connect to the slot

        # Add widgets to the layout
        layout.addWidget(self.label_title)
        layout.addWidget(self.label_temperature)
        layout.addWidget(self.weather_textbox)
        layout.addWidget(update_button)

    def update_temperature(self):
       # Intentar convertir el texto de la caja de texto a un número flotante
        try:
            print('Actualizando temperatura...')

            self.temperature = float(self.weather_textbox.text())
            self.label_temperature.setText(f'{self.temperature} Cº')
            self.runBWeather.edit_temperature('ALICANTE', self.temperature)

        except ValueError:
            # Si la conversión falla, imprimir un mensaje de error y no actualizar self.temperature
            print("Por favor, ingrese un número válido.")

# ======================MySocket==============================


class MySocket:
    def __init__(self, host, port):
        self.server_socket = self.create_server_socket(host, port)
        # pause for 0.5 seconds between each listen
        self.server_socket.settimeout(0.5)

    def create_server_socket(self, host, port):
        s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_socket.bind((host, port))
        s_socket.listen()
        return s_socket

    def accept_connection(self):
        try:
            return self.server_socket.accept()
        except socket.timeout:
            return None, None
        except Exception as e:
            print(f"Error accepting connection: {e}")
            return None, None

    def send_response(self, client_socket, message):
        try:
            client_socket.send(Protocol.Pack_message(message).encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_message(self, client_socket):
        try:
            return Protocol.Unpack_message(client_socket.recv(BUFFER_SIZE).decode('utf-8'))
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None

    def close_server_socket(self):
        self.server_socket.close()

    def close_client_socket(self, client_socket):
        client_socket.close()
# ============================================================


class ConfigManager:
    def __init__(self, filename):
        self.filename = filename
        self.config = {}
        self.file_hash = None
        self.lock = Lock()  # To prevent race conditions
        self.start_reloader()

    def load_config(self):
        """Load the configuration from a file and store a hash to detect changes."""
        with self.lock:
            with open(self.filename, 'r') as file:
                file_content = file.read()
                new_hash = hashlib.md5(
                    file_content.encode('utf-8')).hexdigest()

                # Check if the file has changed by comparing the hash
                if new_hash != self.file_hash:
                    self.file_hash = new_hash
                    # Reset the config dictionary
                    self.config = {}
                    for line in file_content.strip().split('\n'):
                        key, value = line.strip().split('=', 1)
                        # Process the value (convert to int, decode escapes, etc.)
                        self.process_value(key, value)

    def process_value(self, key, value):
        """Process the configuration value before storing it."""
        # Si el valor es numérico, conviértelo a entero
        if value.isdigit():
            value = int(value)
        # Si el valor parece una dirección IP y puerto, déjalo como cadena
        elif ':' in value:
            pass
        # Si el valor es una secuencia de escape, evalúalo
        elif value.startswith('\\'):
            value = bytes(value, "utf-8").decode("unicode_escape")
        self.config[key] = value

    def get_value(self, key):
        """Get a value from the configuration, reloading if necessary."""
        with self.lock:
            # No need to reload the config here, as it's checked periodically
            return self.config.get(key)

    def start_reloader(self, interval=5):
        """#Inicie un hilo en segundo plano que recargue la configuración en el intervalo especificado."""
        def reloader():
            while True:
                self.load_config()
                sleep(interval)

        t = Thread(target=reloader, daemon=True)
        t.start()


def main():
    app = QApplication(sys.argv)
    view = UI()
    view.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
