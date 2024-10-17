
import socket
import sqlite3
from Tools import get_arg, load_config, Protocol, MyKafka, Camino, UI
import threading
from time import sleep
import sys
import os
from faker import Faker
from PyQt5.QtWidgets import QApplication

config = load_config('config.txt')

HOST_REGISTRY = config['HOST_REGISTRY']
PORT_REGISTRY = config['PORT_REGISTRY']
HOST_ENGINE = config['HOST_ENGINE']
PORT_ENGINE = config['PORT_ENGINE']
HOST_KAFKA = config['HOST_KAFKA']
PORT_KAFKA = config['PORT_KAFKA']


class DronManager:
    def __init__(self):
        # en caso de agregar argumentos
        self.dron_id, self.dron_alias, self.isUIenable = get_arg()

        if self.isUIenable:
            # iniciamos la app para el entorno UIñ
            self.app = QApplication(sys.argv)
            self.space = UI(self.dron_id)

        self.isEventCheck = False
        self.db_path = 'BD/bdTokens.sqlite'
        self.nextPOS = [0, 0]
        self.create_bd()

        # self.test_Generator_dron(20)

    def create_server_socket(self, host, port):
        s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_socket.bind((host, port))
        s_socket.listen()
        return s_socket

    def create_bd(self):
        if not os.path.exists('BD'):
            os.makedirs('BD')

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS DB_TOKENS (
                    dron_id TEXT PRIMARY KEY,
                    auth_token TEXT NOT NULL
                )
            ''')

    def send_message_to_server(self, host, port, action, value=''):
        """Envia una solicitud al servidor """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client_socket.connect((host, port))
        message = f"{action}|{self.dron_id}|{value}"
        packed_message = Protocol.Pack_message(message)
        client_socket.send(packed_message.encode('utf-8'))
        response_packed = client_socket.recv(1024).decode('utf-8')
        client_socket.close()
        return Protocol.Unpack_message(response_packed)

    def Edit_Perfil_Dron(self, acction, value):
        print('\nIniciando edicion del dron: ')
        response, is_valid = self.send_message_to_server(
            HOST_ENGINE, PORT_ENGINE, acction, value)
        return response if is_valid else "ERROR: Respuesta invalida del servidor"

    def Registry_Dron(self):
        try:
            print(f'\nIniciando registro del dron: {self.dron_id}...')
            # ver si dron tiene o no token
            if not self.has_dron_token():

                response, is_valid = self.send_message_to_server(
                    HOST_REGISTRY, PORT_REGISTRY, 'registry', self.dron_alias)

                token, message = response.split("|")

                if not is_valid:
                    raise ValueError(
                        'Respuesta invalida del servidor Registry')

                if token == 'None':
                    raise ValueError(message)

                # Si el registro tuvo exito entonces guardamos el token
                self.Save_token(token)

                print(f'{message}')
        except ValueError as e:
            raise ValueError(print(f"Excepción en Registry_Dron: {e}"))

    def Delete_Dron(self):
        try:
            print('\nIniciando borrado del dron: ')
            response, is_valid = self.send_message_to_server(
                HOST_REGISTRY, PORT_REGISTRY, 'delete', None)

            if not is_valid:
                raise ValueError('Respuesta invalida del servidor Registry')

            print(f'{response}')

        except ValueError as e:
            print(f"Excepción en Delete_Dron: {e}")

    def has_dron_token(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT auth_token FROM DB_TOKENS WHERE dron_id = ?", (self.dron_id,))

                if cursor.fetchone():
                    print(
                        f'El Dron con id {self.dron_id} ya fue registrado anteriormente')
                    return True

                return False
        except sqlite3.Error as e:
            return False

        except ValueError as e:
            raise ValueError(f'{e}')

    def Save_token(self, token):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if token for given dron_id exists
                cursor.execute(
                    "SELECT auth_token FROM DB_TOKENS WHERE dron_id = ?", (self.dron_id,))
                existing_token = cursor.fetchone()

                if existing_token:
                    # If a token already exists for the given dron_id
                    return False
                else:
                    # Insert the token for the dron_id
                    cursor.execute('''
                        INSERT INTO DB_TOKENS (dron_id, auth_token)
                        VALUES (?, ?)
                    ''', (self.dron_id, token))
                    conn.commit()
                    return True

        except sqlite3.Error as e:
            print(f"DB Tokens error: {e}")
            return False

    def Delete_token(self, id_dron):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT auth_token FROM DB_TOKENS WHERE dron_id = ?", (id_dron,))
                existing_token = cursor.fetchone()

                if not existing_token:
                    return False
                else:
                    cursor.execute('''
                        DELETE FROM DB_TOKENS WHERE dron_id = ?
                    ''', (id_dron,))
                    conn.commit()
                    return True

        except sqlite3.Error as e:
            print(f"DB Tokens error: {e}")
            return False

    def Autentication_Dron(self):
        """Obtenemos el token desde bdTokens y nos autentificamos
        para que engine nos asigna un puerto ya que cada dron debe de tener su propio 
        puerto para escuchar """
        try:
            print(f'\nIniciando la autentication del dron: {self.dron_id}...')
            # Use LoadToken to get the associated token
            token = self.LoadToken()

            response, is_valid = self.send_message_to_server(
                HOST_ENGINE, PORT_ENGINE, 'authentication', token)

            if not is_valid:
                raise ValueError('Respuesta invalida del servidor Engine')

            print(f'{response}')

        except ValueError as e:
            raise ValueError(f"Excepción en Autenticacion_Dron: {e}")

    def LoadToken(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Query to get the token for the given dron_id
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT auth_token FROM DB_TOKENS WHERE dron_id = ?", (self.dron_id,))
                token = cursor.fetchone()

                if token is None:
                    raise ValueError(
                        f"Dron con id {self.dron_id} no esta registrado -> [Registre el Dron antes de autentificar]")

                return token[0]

        except sqlite3.Error as e:
            raise ValueError(
                f"{e}")
        except ValueError as ve:
            raise ValueError(
                f"Dron con id {self.dron_id} no esta registrado -> [Registre el Dron antes de autentificar]")

    def Dron_manager(self):
        try:

            threading.Thread(target=self.h_DM_Update_isEventCheck).start()
            threading.Thread(target=self.h_drone_heartbeats).start()
            # threading.Thread(target=self.h_DM_Efect_loader).start()

            self.Registry_Dron()

            self.Autentication_Dron()

            print('Esperando inicio del evento...')

            threading.Thread(
                target=self.h_DM_logicDron).start()

            if self.isUIenable:
                print('Iniciando interfaz UI..')
                while True:
                    if self.isEventCheck:
                        self.space.show()
                        self.app.exec_()
                        break

        except ValueError as e:
            print(f"Se ha capturado una excepción en AD_Manager: {e}")

    def h_DM_Update_isEventCheck(self):
        """
        Esta funcion se va a ejecutar en un hilo generado por el main donde 
        estara modificando en tiempo real la variable self.isEventCheck
        """
        C_T_isEventCheck = MyKafka.Consumer(
            addr=f"{HOST_KAFKA}:{PORT_KAFKA}", topic="isEventCheck", group=self.dron_id)

        while True:
            message = C_T_isEventCheck.consume_tokey_msg('event')
            if message and (message['isEventCheck'] == True):
                self.isEventCheck = True

        C_T_isEventCheck.close()
        print('Hilo C_T_isEventCheck cerrado.')

    def h_DM_logicDron(self):
        """
                Poner a escuchar los Consumidores necesaros del dron por particion del dron: 
                ['isEventCheck', 'PointActualDron', 'SpaceUpdateDron']
                Isevenreadt==True
                - hilo2: Consumidor updateSpace que recibira una data: 
                Data=situacionSpace+EndPointDron

                +Productor point-actual-dron 
                Data=PointActualDron+color(grean/red)(esta linea fuerza a que empiece la transmision) 
                """

        while True:
            if self.isEventCheck:

                P_PointActualDron = MyKafka.Producer(
                    addr=f"{HOST_KAFKA}:{PORT_KAFKA}"
                )

                C_T_SpaceUpdateDron = MyKafka.Consumer(
                    addr=f"{HOST_KAFKA}:{PORT_KAFKA}", topic="SpaceUpdateDron", group=self.dron_id
                )

                while True:

                    P_PointActualDron.send_message_topic(
                        self.nextPOS, topic='PointActualDron', key=self.dron_id)

                    message = C_T_SpaceUpdateDron.consume_tokey_msg(
                        self.dron_id)

                    if message:

                        matrizSpace = message['Space']
                        EndPointDron = message["EndPointDron"]
                        tituloPrincipal = message['tituloPrincipal']

                        if self.isUIenable:
                            self.space.reset_celdas_signal.emit()
                            for celda in matrizSpace.values():
                                if celda['color'] != '#D9E1F3':
                                    self.space.update_position_signal.emit(
                                        celda['pos'], celda['color'],  celda['id'])

                            self.space.setTitulo_signal.emit(tituloPrincipal)

                        # calculamos siguiente pos
                        self.nextPOS = Camino.Next_Step_Direct(
                            matrizSpace[self.dron_id]['pos'], EndPointDron)

    def h_drone_heartbeats(self):
        """"
        #esta funcion simula latido de corazon del dron , su se cierra el terminal de un dron este topic dara la señal al engine
        """
        P_heartbeats = MyKafka.Producer(
            addr=f"{HOST_KAFKA}:{PORT_KAFKA}"
        )
        while True:
            P_heartbeats.send_message_topic(
                self.dron_id, topic='Heartbeats', key=self.dron_id)
            sleep(1)

    def h_DM_Efect_loader(self):
        if not self.isEventCheck:
            spin_chars = ['|', '/', '-', '\\']
            while not self.isEventCheck:
                for char in spin_chars:
                    sys.stdout.write('\r' + char)
                    sys.stdout.flush()  # Asegura que el carácter se imprima inmediatamente
                    sleep(0.1)

        print('Hilo h_DM_Efect_loader cerrado.')

    def test_Generator_dron(self, numero_max_drones):
        fake = Faker()
        for i in range(1, numero_max_drones+1):
            self.dron_id = str(i)
            self.dron_alias = str(fake.name())
            self.Registry_Dron()
            sleep(1)
            self.Autentication_Dron()
            sleep(1)


if __name__ == '__main__':

    object_dron = DronManager()
    object_dron.Dron_manager()
