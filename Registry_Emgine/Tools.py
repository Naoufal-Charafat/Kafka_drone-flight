
from Settings import STX, ETX
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from kafka.errors import KafkaError
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import os
import ssl
import json
import sqlite3
import hashlib
import json
import socket
import struct
import pickle
import random


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
Limit_Drones = config['Limit_Drones']
MY_HOST_REGISTRY = config['MY_HOST_REGISTRY']
MY_PORT_REGISTRY = config['MY_PORT_REGISTRY']
MY_HOST_ENGINE = config['MY_HOST_ENGINE']
MY_PORT_ENGINE = config['MY_PORT_ENGINE']
HOST_DRONE = config['HOST_DRONE']
PORT_DRONE = config['PORT_DRONE']
HOST_KAFKA = config['HOST_KAFKA']
PORT_KAFKA = config['PORT_KAFKA']
PATH_FIGURA = config['PATH_FIGURA']


@staticmethod
def Generate_token_SHA256():
    """Genera un token usando SHA256 a partir de un número aleatorio."""
    random_number = str(random.randint(100000, 999999))
    return hashlib.sha256(random_number.encode()).hexdigest()


@staticmethod
def Num_drones_figura(figura):
    return len(figura[1])


@staticmethod
def DataDronesPosBase(num_drones):
    # Crear la estructura básica del JSON con una figura vacía
    data = {
        "figuras": [
            {
                "Nombre": "No hay figura \n !!Drones volviendo a la base¡¡",
                "Drones": []
            }
        ]
    }

    # Añadir drones a la figura
    for i in range(1, num_drones + 1):
        drone = {
            "ID": i,
            "POS": "0,0"
        }
        data["figuras"][0]["Drones"].append(drone)

    # Convertir el diccionario a una cadena JSON para la salida
    return data


def NumDronesRequeridosEvent(data):

    max_drones = 0
    for figura in data["figuras"]:
        num_drones = len(figura["Drones"])
        if num_drones > max_drones:
            max_drones = num_drones
    return max_drones


@staticmethod
def GetDataJSON():
    with open(PATH_FIGURA, 'r') as file:
        data = json.load(file)

    # Sobrescribe el archivo JSON con un objeto vacío
    with open(PATH_FIGURA, 'w') as file:
        json.dump({}, file)

    return data


def GetNamesFiguras(dataJson):
    nombres = []
    for figura in dataJson['figuras']:
        nombres.append(figura['Nombre'])
    return nombres
# ====================BdDron===========================


class BdDron:
    def __init__(self):
        self.db_path = 'BD/bd1.sqlite'
        self.create_bd()

    def create_bd(self):

        if not os.path.exists('BD'):
            os.makedirs('BD')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='Drones'")
            if not cursor.fetchone():

                cursor.execute('''
                    CREATE TABLE Drones (
                        dron_id TEXT PRIMARY KEY,
                        dron_alias TEXT NOT NULL,
                        auth_token TEXT NOT NULL,
                        auth_dron TEXT NOT NULL,
                        asignado_dron TEXT NOT NULL
                    )
                ''')

    def Registry_Dron_DB(self, dron_id, dron_alias, token):

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Drones (dron_id, dron_alias, auth_token,auth_dron,asignado_dron) VALUES (?, ?, ?,?,?)", (dron_id, dron_alias, token, 0, 0))

            if cursor.rowcount <= 0:
                raise ValueError(f'Ya existe el dron con id: {dron_id}.')

    def Delete_Dron_DB(self, dron_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM Drones WHERE dron_id = ?", (dron_id,))

                if cursor.rowcount <= 0:
                    raise ValueError(
                        f'No se encontró el dron con id: {dron_id}.')

        except ValueError as e:
            print(f'Error en Delete_Dron_DB ->')
            raise ValueError(e)

        except sqlite3.IntegrityError as e:
            print(f'Excepcion SQLITE en Delete_Dron_DB ->')
            raise ValueError(e)

        except Exception as e:
            print(f'Exception en Delete_Dron_DB ->')
            # Manejo de otras excepciones no especificadas anteriormente
            raise ValueError(e)

    def auth_Dron_DB(self, dron_id, token):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Llamar a las funciones para ver si el dron está autenticado o si se puede autenticar.
                self.is_dron_auth(dron_id)
                self.is_auth_enable()

                cursor.execute(
                    "SELECT auth_token, auth_dron FROM Drones WHERE dron_id = ?", (dron_id,))
                result = cursor.fetchone()

                if not result:
                    raise ValueError(
                        f'No se encontró el dron con id: {dron_id}.')

                stored_token, auth_dron = result

                if auth_dron == '1':
                    raise ValueError(
                        f'Dron con id: {dron_id} ya está autentificado.')

                if stored_token != token:
                    raise ValueError(
                        f'El token proporcionado no coincide para el dron con id: {dron_id}.')

                cursor.execute(
                    "UPDATE Drones SET auth_dron = 1 WHERE dron_id = ?", (dron_id,))

                if cursor.rowcount <= 0:
                    raise ValueError(
                        f'Dron: {dron_id} no ha sido autenticado con éxito.')

        except ValueError as e:
            print(f'Error en auth_Dron_DB -> {e}')
            raise e

        except sqlite3.IntegrityError as e:
            print(f'Excepcion SQLITE en auth_Dron_DB -> {e}')
            raise e

        except Exception as e:
            print(f'Excepcion en auth_Dron_DB -> {e}')
            raise e

    def is_dron_auth(self, dron_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT auth_dron FROM Drones WHERE dron_id = ?", (dron_id,))
            result = cursor.fetchone()

            if result[0] == '1':
                raise ValueError(
                    f'Dron con id: {dron_id} ya fue autentificado')

    def is_auth_enable(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Drones WHERE auth_dron = 1")
            authenticated_drones_count = cursor.fetchone()[0]

            if authenticated_drones_count >= Limit_Drones:
                raise ValueError(
                    f'Ya se ha alcanzado el límite de {Limit_Drones} drones autenticados.')

    def Edit_auth_dron_BD(self, dron_id, new_auth_dron):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE Drones SET auth_dron = ? WHERE dron_id = ?", (new_auth_dron, dron_id))

                if cursor.rowcount > 0:
                    print(f'Dron: {dron_id} fue actualizado con éxito !!')
                    return True
                else:
                    print(f'No se encontró el dron con id: {dron_id}.')
                    return False
            except sqlite3.Error as e:
                return False

    def count_drones_asignados(self):
        """#Numero total de drones autentificaods"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM Drones WHERE asignado_dron = '1'")
            return cursor.fetchone()[0]

    def get_available_dron_ids(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT dron_id FROM Drones WHERE auth_dron	='1' and asignado_dron = '0'")
            return [row[0] for row in cursor.fetchall()]

    def GetDictPosDron(self):
        """Retrieve a dictionary where keys are dron_id (with asignado_dron = 1) and values are another dictionary with default values"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT dron_id FROM Drones WHERE asignado_dron = '1'")
            dron_ids = [row[0] for row in cursor.fetchall()]

            # Default dictionary for each dron_id
            default_dron_data = {
                'pos': [0, 0],
                'color': '#D9E1F3',
                'id': '',
                'beat': True  # This will be replaced by the actual dron_id
            }

            return {dron_id: {**default_dron_data, 'id': str(dron_id)} for dron_id in dron_ids}

    def GetListDronAssigned(self):
        """Retrieve a list of dron_id where asignado_dron = '1'."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Ejecutamos la consulta para obtener los IDs de los drones asignados
            cursor.execute(
                "SELECT dron_id FROM Drones WHERE asignado_dron = '1'")
            # Recopilamos los resultados en una lista
            assigned_dron_ids = [row[0] for row in cursor.fetchall()]

        return assigned_dron_ids

    def assign_dron(self, dron_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Drones SET asignado_dron = '1' WHERE dron_id = ?", (dron_id,))

    def Reset_auth_dron(self):
        """# resetea todos los drones a no autentificados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE Drones SET auth_dron = '0'")

            if cursor.rowcount > 0:
                print(f'Drones registrados ({cursor.rowcount})')
                print('Reset drones...')
                return True
            else:
                print('No hubo drones para reset.')
                return False

    def reset_drones_assignment(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("UPDATE Drones SET asignado_dron = '0'")

                if cursor.rowcount > 0:
                    print(
                        f'Todos los drones han sido desasignados reseteados a asignado_dron = 0')
                else:
                    print('No hubo drones para resetear.')

        except sqlite3.Error as e:
            print(f'Error al resetear la asignación de drones en la BD: {e}')

# ==================================================


BUFFER_SIZE = 1024


class MySocket:
    def __init__(self, host, port, is_server=True):
        if is_server:
            self.socket = self.create_server_socket(host, port)
            self.socket.settimeout(0.5)
        else:
            self.socket = self.create_client_socket(host, port)

    def create_server_socket(self, host, port):
        s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_socket.bind((host, port))
        s_socket.listen()
        return s_socket

    def create_client_socket(self, host, port):
        try:
            c_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c_socket.connect((host, port))
            return c_socket
        except Exception as e:
            error = f'Error al create_client_socket con {host}:{port}'
            raise ValueError(error)

    def accept_connection(self):
        try:
            return self.socket.accept()
        except socket.timeout:
            return None, None
        except Exception as e:
            print(f"Error accepting connection: {e}")
            return None, None

    def send_response(self, message, h_client_socket=None):
        try:
            if h_client_socket == None:
                self.socket.send(Protocol.Pack_message(
                    message).encode('utf-8'))
            else:
                h_client_socket.send(
                    Protocol.Pack_message(message).encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_message(self, h_client_socket=None):
        try:
            if h_client_socket == None:
                return Protocol.Unpack_message(self.socket.recv(BUFFER_SIZE).decode('utf-8'))
            else:
                return Protocol.Unpack_message(h_client_socket.recv(BUFFER_SIZE).decode('utf-8'))

        except Exception as e:
            print(f"Error receiving message: {e}")
            return None

    def close_socket(self, h_client_socket=None):
        if h_client_socket == None:
            self.socket.close()
        else:
            h_client_socket.close()

# ==================================================


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

    def Unpack_message(message: str) -> (str, bool):
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
# ==================================================


class MyKafka:

    class AdminKafka:
        def __init__(self):
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=f"{HOST_KAFKA}:{PORT_KAFKA}", client_id='Engine'
            )

        def Create_topics(self, topic_names, op_timeout=5000):
            try:
                for topic_name in topic_names:
                    try:
                        self.admin_client.create_topics(new_topics=[NewTopic(
                            name=topic_name, num_partitions=1, replication_factor=1)], validate_only=False, timeout_ms=op_timeout)
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
                # print(f"Mensaje enviado al tópico 'Destination'. Key: {key}, Value: {message}")
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

        def consume_poll_msg_key(self, stopkey, commit=True):
            try:
                """para no esperar bloqueado y va con key"""

                message = self.poll_msg(timeout_ms=2000)

                for msg in message:
                    if not msg:
                        return None
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
# ==================================================


class MySocketAUX(socket.socket):
    def __init__(self, type, addr):
        # Inicializa la instancia de socket con el tipo dado (UDP o TCP)
        super().__init__(socket.AF_INET,
                         socket.SOCK_DGRAM if type == "UDP" else socket.SOCK_STREAM)

        # Determina si la instancia actúa como servidor o cliente
        self.is_server = not len(addr[0])

        if self.is_server:
            self.bind(addr)
            self.listen()
            self.conn = {}
        else:
            self.connect(addr)
            self.conn = {"None": self}

    def accept(self):
        # Acepta una conexión entrante y la almacena en el diccionario conn
        conn, client = super().accept()
        self.conn["None"] = conn
        self.conn[client] = conn
        return conn, client

    def close(self):
        # Cierra todas las conexiones y el propio socket
        for conn in self.conn.values():
            if conn != self:
                conn.close()
        self.conn = None
        super().close()

    @staticmethod
    def pack(data):
        # Empaqueta los datos con su longitud para enviar
        packet_len = struct.pack("!I", len(data))
        return packet_len + data

    def send_msg(self, msg, client="None"):
        # Envía un mensaje de texto al cliente especificado
        self.conn[client].sendall(MySocket.pack(msg.encode("utf-8")))

    def send_obj(self, obj, client="None"):
        # Envía un objeto (serializado) al cliente especificado
        self.conn[client].sendall(MySocket.pack(pickle.dumps(obj)))

    @staticmethod
    def recv_confirmed(conn, buf_len):
        # Recibe datos del socket hasta que se ha recibido la cantidad especificada
        buf = b""
        while len(buf) < buf_len:
            buf += conn.recv(buf_len - len(buf))
            if not buf:
                raise socket.error
        return buf

    @staticmethod
    def recvall(conn):
        # Recibe todos los datos de un paquete, incluida su longitud
        buf_len = struct.unpack("!I", MySocket.recv_confirmed(conn, 4))[0]
        return MySocket.recv_confirmed(conn, buf_len)

    def recv_msg(self, client="None"):
        # Recibe un mensaje de texto del cliente especificado
        return MySocket.recvall(self.conn[client]).decode("utf-8")

    def recv_obj(self, client="None"):
        # Recibe y deserializa un objeto del cliente especificado
        return pickle.loads(MySocket.recvall(self.conn[client]))

# ==================================================


class UI(QWidget):

    def __init__(self, on_start=None, on_stop=None, on_restart=None, on_reset_parameters=None):
        super().__init__()
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_restart = on_restart
        self.on_reset_parameters = on_reset_parameters
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 350, 450)
        self.setWindowTitle('APP ENGINE')

        # organiza los widgets en una sola columna QVBoxLayout
        GeneralLayoutV = QVBoxLayout()

        # label superior
        top_label = QLabel('[ENGINE]')
        top_label.setAlignment(Qt.AlignCenter)
        top_label.setFont(QFont('Arial', 18))
        top_label.setStyleSheet("color: green;")
        GeneralLayoutV.addWidget(top_label)

        # Generar buton start
        start_event_button = QPushButton('Start event')
        start_event_button.setFont(QFont('Arial', 18))
        start_event_button.setStyleSheet("color: green;")
        if self.on_start:
            start_event_button.clicked.connect(self.on_start)

        GeneralLayoutV.addWidget(start_event_button)

        # Generar buton stop
        stop_event_button = QPushButton('Stop event')
        stop_event_button.setFont(QFont('Arial', 18))
        stop_event_button.setStyleSheet("color: red;")
        if self.on_stop:
            stop_event_button.clicked.connect(self.on_stop)
        GeneralLayoutV.addWidget(stop_event_button)

        # Generar buton restart
        restart_event_button = QPushButton('Restart event')
        restart_event_button.setFont(QFont('Arial', 18))
        restart_event_button.setStyleSheet("color: orange;")
        if self.on_restart:
            restart_event_button.clicked.connect(self.on_restart)
        GeneralLayoutV.addWidget(restart_event_button)

        # QHBoxLayout para el label y el textbox de IP
        ip_layoutLayoutH = QHBoxLayout()
        # Para "ip" label-textbox
        ip_label = QLabel('IP')
        ip_label.setFont(QFont('Arial', 14))
        ip_layoutLayoutH.addWidget(ip_label)
        ip_textbox = QLineEdit('169.254.64.2')
        ip_textbox.setFont(QFont('Arial', 14))
        ip_layoutLayoutH.setAlignment(Qt.AlignCenter)
        ip_layoutLayoutH.addWidget(ip_textbox)

        # Para "port" label-textbox
        port_layoutLayoutH = QHBoxLayout()
        port_label = QLabel('Port')
        port_label.setFont(QFont('Arial', 14))
        port_layoutLayoutH.addWidget(port_label)
        port_textbox = QLineEdit('4000')
        port_textbox.setFont(QFont('Arial', 14))
        port_layoutLayoutH.addWidget(port_textbox)

        # QHBoxLayout para el label y el textbox de Limit_Drones
        Limit_DronesLayoutH = QHBoxLayout()
        # Para "ip" label-textbox
        Limit_Drones_label = QLabel('Maximo Drones:')
        Limit_Drones_label.setFont(QFont('Arial', 14))
        Limit_DronesLayoutH.addWidget(Limit_Drones_label)
        Limit_Drones_textbox = QLineEdit(str(Limit_Drones))
        Limit_Drones_textbox.setFont(QFont('Arial', 14))
        Limit_DronesLayoutH.addWidget(Limit_Drones_textbox)

        # Agregar el QHBoxLayout al QVBoxLayout principal
        GeneralLayoutV.addLayout(ip_layoutLayoutH)
        GeneralLayoutV.addLayout(port_layoutLayoutH)
        GeneralLayoutV.addLayout(Limit_DronesLayoutH)

        # Botón para "Reset parameters"
        reset_parameters_button = QPushButton('Reset\nparameters')
        reset_parameters_button.setFont(QFont('Arial', 14))
        if self.on_reset_parameters:
            reset_parameters_button.clicked.connect(self.on_reset_parameters)

        GeneralLayoutV.addWidget(reset_parameters_button)

        # label inferior IP:PUERTO
        bottom_label = QLabel(f'{MY_HOST_ENGINE}:{MY_PORT_ENGINE}')
        bottom_label.setAlignment(Qt.AlignCenter)
        bottom_label.setFont(QFont('Arial', 14))
        bottom_label.setStyleSheet("color: green;")
        GeneralLayoutV.addWidget(bottom_label)

        # Establece un espaciado de 10 píxeles entre widgets
        GeneralLayoutV.setSpacing(10)

        # Establecer la disposición (layout) en el QWidget
        self.setLayout(GeneralLayoutV)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = UI()
    ventana.show()
    sys.exit(app.exec_())
