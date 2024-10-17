import threading
from Tools import Generate_token_SHA256, BdDron, MySocket, load_config

config = load_config('config.txt')
MY_HOST_REGISTRY = config['MY_HOST_REGISTRY']
MY_PORT_REGISTRY = config['MY_PORT_REGISTRY']


class RegistryServer:
    def __init__(self):
        self.runBDron = BdDron()
        self.socket_server = MySocket(MY_HOST_REGISTRY, MY_PORT_REGISTRY)

    def Registry_manager(self):
        print(
            f"Servidor de registros iniciado en: {MY_HOST_REGISTRY}:{MY_PORT_REGISTRY}...")
        while True:
            client_socket, _ = self.socket_server.accept_connection()
            if client_socket:
                threading.Thread(target=self.handle_dron,
                                 args=(client_socket,)).start()

    def handle_dron(self, client_socket):
        """Funcion hilo para cada Dron"""
        print('=============================================')
        try:
            data, is_valid = self.socket_server.receive_message(client_socket)

            if not is_valid:
                raise ValueError('Mensaje invalido del cliente Dron')

            action, dron_id, value = data.split("|")

            action_map = {
                'registry': self.h_registry_dron,
                'delete': self.h_delete_dron,
            }

            if action not in action_map:
                raise ValueError('Error de solicitud, accion inccorecta')

            action_map[action](client_socket, dron_id, value)

            client_socket.close()
        except ValueError as e:
            print(f"Se ha capturado un error en handle_dron: {e}")
            self.socket_server.send_response(str(e), client_socket)
            client_socket.close()

        except Exception as e:
            print(f"Se ha capturado una excepción en handle_dron_E: {e}")
            self.socket_server.send_response(str(e), client_socket)
            client_socket.close()
        print('=============================================\n')

    def h_registry_dron(self, client_socket, dron_id, dron_alias):
        try:
            token = Generate_token_SHA256()
            self.runBDron.Registry_Dron_DB(dron_id, dron_alias, token)
            self.socket_server.send_response(
                f'{token}|El dron con ID {dron_id} fue registrado con exito!!', client_socket)
            print(f'-> El dron con ID {dron_id} fue registrado con exito!!')

        except ValueError as e:
            print(f'Excepcion en h_registry_dron ->')
            raise ValueError(
                f'No fue posible registrar dron con id {dron_id}')

    def h_delete_dron(self, client_socket, dron_id, value=''):
        try:
            self.runBDron.Delete_Dron_DB(dron_id)
            self.socket_server.send_response(
                f'El Dron {dron_id} fue borrado exitosamente!!', client_socket)

            print(f'-> El dron con ID {dron_id} fue borrado con exito!!')

        except ValueError as e:
            print(f'Excepcion en h_delete_dron ->')
            raise ValueError(
                f'No fue posible borrar Dron con id {dron_id}')


if __name__ == '__main__':

    # Creamos una instancia de la clase y la iniciamos
    registry_server = RegistryServer()
    registry_server.Registry_manager()
