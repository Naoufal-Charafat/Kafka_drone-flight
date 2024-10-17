
from Tools import load_config, BdWeather,  MySocket, UI
import socket
from threading import Event, Thread
import sys
from PyQt5.QtWidgets import QApplication

config = load_config('config.txt')
MY_HOST_WEATHER = config['MY_HOST_WEATHER']
MY_PORT_WEATHER = config['MY_PORT_WEATHER']


class WeatherServer:

    def __init__(self):
        # Iniciamos la BD : crear BD+tabla drones  en caso de que no exista
        self.runBWeather = BdWeather()

        # construimos el socket
        self.socket_server = MySocket(MY_HOST_WEATHER, MY_PORT_WEATHER)

    def Weather_manager(self):
        try:
            print(
                f"Servidor Weather iniciado en: {MY_HOST_WEATHER}:{MY_PORT_WEATHER}...")
            # hilo para gestionar autentificaciones de los drones
            Thread(target=self.h_WM_gestionSocketEngine).start()

            app = QApplication(sys.argv)
            view = UI()
            view.show()
            sys.exit(app.exec_())
        except ValueError as e:
            print(f'{e}')

    def h_WM_gestionSocketEngine(self):

        def h_Socket_Engine(client_socket):
            try:

                data, is_valid = self.socket_server.receive_message(
                    client_socket)

                if not is_valid:
                    raise ValueError('Mensaje invalido del cliente Engine')

                print(f'Data recibida: {data}')
                print('=============================================')
                self.socket_server.send_response(
                    client_socket, str(self.runBWeather.get_temperature('ALICANTE')))
                client_socket.close()
                print(f'Cerrando socket')
                print(f'Cerrando hilo socket')
                print('=============================================')

            except Exception as e:
                print(f"Se ha capturado una excepción en h_Socket_Engine: {e}")
                client_socket.close()

        while True:
            client_socket, _ = self.socket_server.accept_connection()
            if client_socket:
                Thread(target=h_Socket_Engine,
                       args=(client_socket,)).start()


if __name__ == '__main__':

    # Creamos una instancia de la clase y la iniciamos
    Weather_server = WeatherServer()
    Weather_server.Weather_manager()
