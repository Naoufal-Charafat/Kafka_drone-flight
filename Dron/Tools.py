from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QSpacerItem

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from heapq import heappop, heappush
from Settings import STX, ETX
import numpy as np
import sys
import socket
import random
import sys
import ssl
import json
from kafka.errors import KafkaError
from time import sleep


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
HOST_KAFKA = config['HOST_KAFKA']
PORT_KAFKA = config['PORT_KAFKA']

# =====================Funciones========================


@staticmethod
def capturar_parametros():
    # Considerando que sys.argv[0] es el nombre del script
    if len(sys.argv) < 4:
        print("Error: Debes proveer exactamente tres argumentos:\n" +
              "- IP y puerto del AD_Engine.\n" +
              "- IP y puerto del Broker/Bootstrap-server del gestor de colas.\n" +
              "- IP y puerto del AD_Registry.")
        sys.exit(1)

    # Descomponer sys.argv[1] que tiene el formato "ip:puerto"
    ip_AD_Engine, puerto_AD_Engine = sys.argv[1].split(':')

    # Descomponer sys.argv[2] que tiene el formato "ip:puerto"
    ip_kafka, puerto_kafka = sys.argv[2].split(':')

    # Descomponer sys.argv[3] que tiene el formato "ip:puerto"
    ip_AD_Registry, puerto_AD_Registry = sys.argv[3].split(':')


@staticmethod
def is_port_in_use(port):
    """Comprueba si un puerto está en uso o no."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False  # El puerto no está en uso
        except socket.error:
            return True   # El puerto está en uso


@staticmethod
def get_port_random():
    """Genera un número de puerto aleatorio entre 49812 y 50000, 
    y verifica si el puerto está en uso. Si está en uso, genera un 
    nuevo número de puerto aleatorio y verifica nuevamente, 
    repitiendo este proceso hasta que encuentre un puerto que no 
    esté en uso. Devuelve el número de puerto."""
    while True:
        port = random.randint(49812, 50000)
        if not is_port_in_use(port):
            return port


@staticmethod
def get_arg():
    """ 
    arg 1: Id dron
    arg 2: Alias dron
    arg 3: habilitar entorno visual
    """
    if len(sys.argv) != 4:
        raise ValueError(
            "Se requieren exactamente 3 argumentos <ID DRON> <ALIAS DRON> <si/no>")

    arg1, arg2, arg3 = sys.argv[1], sys.argv[2], sys.argv[3]

    return arg1, arg2, (True if arg3 == 'si' else False)


@staticmethod
def input_info_dron():
    return input("ID_DRON: "), input("ALIAS_DRON: ")
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
# =====================MyKafka==========================


class MyKafka:

    class AdminKafka:
        def __init__(self):
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=f"{HOST_KAFKA}:{PORT_KAFKA}", client_id='Engine'
            )

        def create_topics(self, topic_names):
            try:
                for topic_name in topic_names:
                    try:
                        self.admin_client.create_topics(new_topics=[NewTopic(
                            name=topic_name, num_partitions=1, replication_factor=1)], validate_only=False)
                        print(f"Creando Topic: {topic_name}")
                    except TopicAlreadyExistsError as e:
                        print(
                            f'create_topics: {topic_name} -> TopicAlreadyExistsError')

                    except Exception as e:
                        print(
                            f'create_topics: {topic_name} -> Exception: {str(e)}')

                self.admin_client.close()
            except KafkaError as ke:
                print(f"KafkaError -> Dron_manager: {ke}")

    @staticmethod
    def fserializer(x):
        """Serializa un objeto a su representación en string JSON y luego lo codifica a bytes."""
        return json.dumps(x).encode("utf-8")

    @staticmethod
    def fdeserializer(x):
        """Deserializa un objeto desde una representación en string JSON decodificada de bytes."""
        return json.loads(x.decode("utf-8"))

    class Producer(KafkaProducer):
        def __init__(self, addr, *args, **kwargs):
            """Constructor de la clase Producer. 
            Inicializa un productor Kafka con la dirección de los servidores y serializadores para las claves y valores."""

            super().__init__(
                bootstrap_servers=addr,
                key_serializer=MyKafka.fserializer,
                value_serializer=MyKafka.fserializer,
                *args, **kwargs
            )

        def send_message_topic(self, message, topic, key=None):
            try:
                self.send(topic, key=key, value=message)
                """print(
                    f"Mensaje enviado al topic {topic}. Key: {key}, Value: {message}")"""
            except KafkaError as ke:
                print(f"KafkaError -> Dron_manager: {ke}")

    class Consumer(KafkaConsumer):
        def __init__(self, addr, topic, group=None, poll_timeout=1000, *args, **kwargs):
            """Constructor de la clase Consumer.
            Inicializa un consumidor Kafka con la dirección de los servidores, deserializadores y otros argumentos."""
            super().__init__(
                topic,
                bootstrap_servers=addr,
                group_id=group,
                key_deserializer=MyKafka.fdeserializer,
                value_deserializer=MyKafka.fdeserializer,
                max_poll_records=1,
                auto_offset_reset="latest",
                *args, **kwargs
            )
            self.poll_timeout = poll_timeout
            self.sync()

        @staticmethod
        def extract_kafka_msg(msg, primitive=True, i=-1):
            """Extrae el mensaje de Kafka de la estructura dada. 
            Si se especifica 'primitive', extraerá el mensaje de una lista o diccionario."""
            if not msg or not primitive:
                return msg
            return list(msg.values())[i]

        def poll_msg(self, *args, **kargs):
            """ como consumir poll_msg --> if message:  for msg in message: if msg: print(msg.value['CordinadaFinal'])"""
            return MyKafka.Consumer.extract_kafka_msg(self.poll(*args, **kargs))

        def sync(self):
            """Sincroniza el consumidor con el servidor."""
            self.poll(self.poll_timeout, update_offsets=True)

        def consume_topic(self):
            """Consume el tópico completo moviendo el offset al final."""
            self.sync()
            self.seek_to_end()

        def consume_tokey_msg(self, stopkey, commit=True):
            try:
                """ Enviar mensajes a cada particion corespondiente por su KEY
                Consume mensajes hasta encontrar un mensaje con la clave dada (stopkey).
                # como consumir consume_tokey_msg -->  print(message['CordinadaFinal'])"""
                while True:
                    message = self.poll_msg(timeout_ms=self.poll_timeout)

                    for msg in message:
                        if not msg:
                            return
                        if commit:
                            self.commit()

                        if msg.key == stopkey:
                            return msg.value
            except KafkaError as ke:
                print(f"KafkaError -> Dron_manager: {ke}")

        def last_kafka_msg(self, commit=False):
            """Obtiene el último mensaje de Kafka en el tópico.
            #como consumir last_kafka_msg -->  for msg in message: if msg:  print(msg.value)"""
            try:
                msg = {}
                while True:
                    newmsg = self.poll_msg(timeout_ms=self.poll_timeout)
                    if not newmsg:
                        break
                    if commit:
                        self.commit()
                    msg = newmsg
                return msg
            except KafkaError as ke:
                print(f"KafkaError -> Dron_manager: {ke}")

    class SecureProducer(Producer):
        def __init__(self, addr, *args, **kwargs):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            super().__init__(
                addr=addr,
                security_protocol="SSL",
                ssl_context=ctx,
                *args, **kwargs
            )

    class SecureConsumer(Consumer):
        def __init__(self, addr, topic, group=None, poll_timeout=1000, *args, **kwargs):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            super().__init__(
                addr=addr,
                topic=topic,
                group=group,
                poll_timeout=poll_timeout,
                security_protocol="SSL",
                ssl_context=ctx,
                *args, **kwargs
            )
# =====================Camino===========================


class Camino:
    class Nodo:
        def __init__(self, posicion, padre=None):
            self.posicion = posicion
            self.padre = padre
            self.g = 0
            self.h = 0
            self.f = 0

        def __eq__(self, otro):
            return self.posicion == otro.posicion

        def __lt__(self, otro):
            return self.f < otro.f

    @staticmethod
    def heuristica(a, b):
        # Distancia de Manhattan
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def AlgA_ruta_camino(matriz, inicio, objetivo):
        nodo_inicio = Camino.Nodo(inicio)
        nodo_objetivo = Camino.Nodo(objetivo)

        abiertos = []
        cerrados = []

        heappush(abiertos, nodo_inicio)

        while abiertos:
            nodo_actual = heappop(abiertos)
            cerrados.append(nodo_actual)

            if nodo_actual == nodo_objetivo:
                ruta = []
                while nodo_actual:
                    ruta.append(nodo_actual.posicion)
                    nodo_actual = nodo_actual.padre
                return ruta[::-1]

            vecinos = []
            # Movimientos en todas las direcciones, incluidas diagonales
            for movimiento in [(0, -1), (-1, 0), (0, 1), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                posicion_vecino = (
                    nodo_actual.posicion[0] + movimiento[0], nodo_actual.posicion[1] + movimiento[1])

                # Verificar que la posición esté dentro de los límites de la matriz
                if posicion_vecino[0] > (len(matriz) - 1) or posicion_vecino[0] < 0 or posicion_vecino[1] > (len(matriz[len(matriz)-1]) - 1) or posicion_vecino[1] < 0:
                    continue

                # Verificar que la posición no sea un obstáculo
                if matriz[posicion_vecino[0]][posicion_vecino[1]] != 0:
                    continue

                vecino = Camino.Nodo(posicion_vecino, nodo_actual)
                vecinos.append(vecino)

            for vecino in vecinos:
                if vecino in cerrados:
                    continue
                vecino.g = nodo_actual.g + 1
                vecino.h = Camino.heuristica(
                    vecino.posicion, nodo_objetivo.posicion)
                vecino.f = vecino.g + vecino.h

                if any(nodo_abierto.posicion == vecino.posicion and vecino.g > nodo_abierto.g for nodo_abierto in abiertos):
                    continue

                heappush(abiertos, vecino)

        return None

    @staticmethod
    def Next_Step_Direct(inicio, objetivo):
        """
        calcula la dirección más directa hacia el objetivo y devuelve el siguiente paso en esa dirección.

        """
        # Cálculo de la diferencia en x y y entre el inicio y el objetivo
        dx = objetivo[0] - inicio[0]
        dy = objetivo[1] - inicio[1]

        move_x = 0
        move_y = 0

        # Si hay movimiento en la dirección x
        if dx != 0:
            move_x = 1 if dx > 0 else -1

        # Si hay movimiento en la dirección y
        if dy != 0:
            move_y = 1 if dy > 0 else -1

        return [(inicio[0] + move_x), (inicio[1] + move_y)]
# ======================UI==============================


class UI(QWidget):
    update_position_signal = pyqtSignal(list, str, str)
    reset_celdas_signal = pyqtSignal()
    setTitulo_signal = pyqtSignal(str)

    def __init__(self, id_dron):
        super().__init__()
        self.dron_id = id_dron
        self.update_position_signal.connect(self.update_position)
        self.reset_celdas_signal.connect(self.reset_celdas)
        self.setTitulo_signal.connect(self.setTitulo)
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 450, 450)
        self.setWindowTitle(f'UI Dron ID: {self.dron_id}')

        # GridLayout
        grid = QGridLayout()
        self.setLayout(grid)

        # Crear el QLabel para el título
        self.titulo = QLabel('[Art With Drones]')
        self.titulo.setAlignment(Qt.AlignCenter)  # Centrar el texto
        self.titulo.setFont(QFont('Arial', 18))   # Tipo de letra y tamaño
        self.titulo.setStyleSheet("color: green;")  # Color del texto

        # Colocamos el título en la fila 1
        grid.addWidget(self.titulo, 1, 0, 1, 21)

        # Usar un QSpacerItem para añadir una separación de 15px
        spacer = QSpacerItem(20, 15)
        grid.addItem(spacer, 2, 0, 1, 21)

        # Añadir enumeración de filas (1 a 20) en el borde superior
        for i in range(1, 21):
            label = QLabel(str(i))
            grid.addWidget(label, 3, i)

        # Añadir enumeración de columnas (1 a 20) en el borde izquierdo
        for j in range(1, 21):
            label = QLabel(str(j))
            grid.addWidget(label, j + 3, 0)

        # Matriz de celdas (QLabels)
        self.celdas = []
        for i in range(1, 21):
            fila = []
            for j in range(1, 21):
                celda = QLabel(self)
                celda.setStyleSheet(
                    "background-color: #D9E1F3; border: 1px solid black;")
                celda.setAlignment(Qt.AlignCenter)
                celda.setFixedSize(30, 30)
                # Incrementamos el índice de fila en 3
                grid.addWidget(celda, i + 3, j)
                fila.append(celda)
            self.celdas.append(fila)

    def reset_celdas(self):
        for fila in self.celdas:
            for celda in fila:
                celda.setStyleSheet(
                    "background-color: #D9E1F3; border: 1px solid black;")  # Changed to blue
                celda.setText('')  # Clear drone label

    def update_position(self, pos, color='green', drone_id='0', msg=''):
        x, y = pos[0], pos[1]  # Adjusted to use 1-indexed position
        # Switch x and y for the celdas list as we want (column, row) referencing

        if ((x-1) >= 0) and ((y-1) >= 0):
            self.celdas[y-1][x-1].setStyleSheet(
                f'background-color: {color}; border: 1px solid black;')
            self.celdas[y-1][x-1].setText(drone_id)

    def setTitulo(self, nuevo_titulo):
        self.titulo.setText(nuevo_titulo)


if __name__ == '__main__':
    # Crear matriz de 20x20
    matriz = np.zeros((20, 20), dtype=int)
    # Probar el algoritmo A* con movimientos diagonales en una matriz de 20x20 sin obstáculos desde (0,0) hasta (3,4)

    """ruta_a_star_diagonal = Camino.AlgA_ruta_camino(matriz, (0, 0), (19, 0))
    ruta_a_star_diagonal += Camino.AlgA_ruta_camino(matriz, (19, 0), (0, 19))
    ruta_a_star_diagonal += Camino.AlgA_ruta_camino(matriz, (0, 19), (19, 19))"""

    app = QApplication(sys.argv)
    ventana = UI('ruta_a_star_diagonal')
    ventana.setTitulo("[Art With Drones]")
    ventana.show()

    app.exec_()
