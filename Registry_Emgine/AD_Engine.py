
from Tools import BdDron, MySocket,  MyKafka, UI, load_config,   GetDataJSON, NumDronesRequeridosEvent, GetNamesFiguras, DataDronesPosBase
from time import sleep, time_ns, time
import sys
from PyQt5.QtWidgets import QApplication
from threading import Event, Thread

config = load_config('config.txt')
MY_HOST_ENGINE = config['MY_HOST_ENGINE']
MY_PORT_ENGINE = config['MY_PORT_ENGINE']
HOST_KAFKA = config['HOST_KAFKA']
PORT_KAFKA = config['PORT_KAFKA']
HOST_WEATHER = config['HOST_WEATHER']
PORT_WEATHER = config['PORT_WEATHER']


class EngineServer:
    def __init__(self):
        # crear una instancia de bd
        self.runBDron = BdDron()
        # self.runBDron.Reset_auth_dron()
        self.isEventReady = False
        self.socket_myServer = MySocket(MY_HOST_ENGINE, MY_PORT_ENGINE)
        self.key_start_event = '+'
        self.regresa = False
        self.runBDron.reset_drones_assignment()
        self.matrizSpace = None
        self.stopEvent = False
        self.titulo = ''
        self.DronesAlaBase = False
        self.temperatura = 0.0

        # Inicializar la lista de hilos y la bandera de salida
        self.threads = []
        self.thread_exit_flag = False

    def Engine_manager(self):
        # Funcion main

        try:
            print(
                f"Servidor Engine iniciado en: {MY_HOST_ENGINE}:{MY_PORT_ENGINE}...")

            print(
                f"Servidor Engine conectando a KAFKA en: {HOST_KAFKA}:{PORT_KAFKA}...")

            print(
                f'Conectando con servidor Weather en {HOST_WEATHER}:{PORT_WEATHER}...')

            # conectar con clima
            hilo_clima = Thread(target=self.h_EM_requestWeather).start()
            self.threads.append(hilo_clima)
            # creamos los topics necesartios
            MyKafka.AdminKafka().Create_topics(
                ['isEventCheck', 'PointActualDron', 'SpaceUpdateDron'])

            # hilo para gestionar autentificaciones de los drones
            hilo_autentificacion = Thread(
                target=self.h_EM_gestionSocketDrones).start()
            self.threads.append(hilo_autentificacion)

            def Reset_parametrs():
                print('Parametros restablecidos:')

            def start_action():
                print('Start event...')
                self.isEventReady = True
                self.DronesAlaBase = False
                hilo_engine_manager = Thread(target=self.h_EM).start()
                self.threads.append(hilo_engine_manager)

            def stop_action():
                self.stopEvent = True
                print('Stop event...')

            def restart_action():
                self.stopEvent = False
                P_T_isEventCheck = MyKafka.Producer(
                    f"{HOST_KAFKA}:{PORT_KAFKA}")

                P_T_isEventCheck.send_message_topic(
                    {"isEventCheck": True}, 'isEventCheck', key="event")
                P_T_isEventCheck.flush()
                print('Reundando evento...')

            app = QApplication(sys.argv)
            ventana = UI(on_start=start_action,
                         on_stop=stop_action, on_restart=restart_action, on_reset_parameters=Reset_parametrs)
            ventana.show()
            sys.exit(app.exec_())
        except ValueError as e:
            print(f'{e}')

        except Exception as e:
            print(f'Error fatal en el Engine{e}')

        finally:
            # Indicar a los hilos que terminen
            self.thread_exit_flag = True

            # Esperar a que todos los hilos terminen
            """for t in self.threads:
                t.join()"""

            # Cerrar sockets
            self.socket_ClineteWeather.close_socket()
            self.socket_myServer.close_socket()

    def h_EM(self):
        # ====================Logica evento============================
        """
        #Crearemos hilo por dron que sera tantos drones como hallan autentificados,
            y crearemos hilo para que envia informacion a cierta particion del topic
            y que todos los productores-consumidores esten conectados en timepo real entre si 
            y se envian y reciben datos en funcion de eventos de mensajes recibidos
        """
        if self.isEventReady:
            data = GetDataJSON()
            contadorDeCierre = 0
            NumDronesAsignados = 0
            while contadorDeCierre != 2:
                while data:
                    NumeroDronesNecesarios = NumDronesRequeridosEvent(data)

                    def Get_figuras():
                        """
                        # En esta funcion obtenemos todos los drones autentificados le asignamos sus endpoints de las figuras 
                        # Y devolvemos una lista donde cada elemento son id con los drones 
                        # cada dron agregado a la lista se actualiza su assignacion en la BD a '1'
                        """
                        self.runBDron.reset_drones_assignment()
                        db_dron_ids = self.runBDron.get_available_dron_ids()

                        if len(db_dron_ids) < NumeroDronesNecesarios:
                            raise ValueError(
                                'No hay suficientes Drones para iniciar el evento')
                        # Asignamos los drones disponibles a las posiciones de las figuras
                        figuras_con_drones = []
                        for figure in data["figuras"]:
                            figure_drones = []
                            for i, dron in enumerate(figure["Drones"]):
                                # Convertimos la posición a una tupla de enteros
                                pos_tuple = tuple(
                                    map(int, dron["POS"].split(",")))
                                dron_id = db_dron_ids[i]
                                # Asignamos el dron a esta posición
                                self.runBDron.assign_dron(dron_id)
                                figure_drones.append(
                                    {"ID": dron_id, "POS": pos_tuple})
                            figuras_con_drones.append(figure_drones)

                        return figuras_con_drones

                    def asignar_posiciones_a_drones(figuras):
                        """
                        # Apartir de la funcion Get_figuras generamos una lista mas ordenada donde cada elemento es un dron y cada dron con 
                        # sus posisiones corespondiente a cada figura
                        """
                        dron_ids_asignados = self.runBDron.GetListDronAssigned()
                        asignacion_final = {dron_id: []
                                            for dron_id in dron_ids_asignados}

                        for figura in figuras:
                            for dron in figura:
                                dron_id = dron['ID']
                                if dron_id in asignacion_final:
                                    asignacion_final[dron_id].append(
                                        tuple(dron['POS']))

                        return asignacion_final

                    figuras = Get_figuras()

                    NumDronesAsignados = self.runBDron.count_drones_asignados()

                    # inicializa la matriz space con los drones asignado_dron = '1' y asignando por defecto posisiones [0.0]
                    self.matrizSpace = self.runBDron.GetDictPosDron()
                    if contadorDeCierre < 1:
                        print(
                            f'Total de drones necesarios para llevar acabo todas las figuras : { NumeroDronesNecesarios} drones')

                    # revisar si tenemos suficientes drones autentificados para todas las figuras
                    if NumDronesAsignados < NumeroDronesNecesarios:
                        raise ValueError(
                            f'La figura no puede ser transmitida porque hay {NumDronesAsignados} drones asignados, y se necesita {NumeroDronesNecesarios} drones para evento.')

                    # Gestionamos con eventos los hilos para asegurar que cada hilo halla completado la parte de creacion de productor y consumidor
                    asignaciones = asignar_posiciones_a_drones(figuras)
                    kafka_ready_events = [Event()
                                          for _ in range(len(asignaciones))]

                    # Lista para mantener un registro de todos los hilos
                    threads = []

                    # En tu bucle for cuando creas los hilos
                    for index, (dron_id, pos_figuras) in enumerate(asignaciones.items()):
                        thread = Thread(target=self.h_EM_logicDron,
                                        args=(dron_id, pos_figuras, GetNamesFiguras(data), kafka_ready_events[index]))
                        self.threads.append(thread)
                        threads.append(thread)
                        thread.start()

                    # Esperar a que todos los hilos señalicen que están listos
                    for event in kafka_ready_events:
                        event.wait()  # Esto bloqueará hasta que el hilo correspondiente señale que está listo

                    # damos comienzo a los drones para que empiezan a transmitir pos por kafka
                    P_T_isEventCheck = MyKafka.Producer(
                        f"{HOST_KAFKA}:{PORT_KAFKA}")

                    P_T_isEventCheck.send_message_topic(
                        {"isEventCheck": True, }, 'isEventCheck', key="event")
                    P_T_isEventCheck.flush()

                    # Esperar a que todos los hilos se completen, en otras palabras cunado los drones hallan hecho todas las
                    # figuras del documento json
                    for thread in threads:
                        thread.join()

                    if contadorDeCierre < 1:
                        print(
                            'En 10 segundos se revisara nuevamente el documento para nuevas figuras')
                        sleep(10)
                        print('cargando figuras ..')
                    data = GetDataJSON()

                if contadorDeCierre == 0:
                    print('No hay mas figuras para cargar, terminando evento ...')
                    # una funcion que construye una data json para asignar posisiones de base a los drones
                    data = DataDronesPosBase(NumDronesAsignados)
                    self.DronesAlaBase = True
                contadorDeCierre += 1
                print('Drones a la base...')

            print(f"x Cerrando hilo h_EM.")

    def h_EM_logicDron(self, dron, figurasPosDron, GetNamesFiguras, ready_event: Event):
        """"#creamos el consumidor / productor para dron"""
        C_T_PointActualDron = MyKafka.Consumer(
            addr=f"{HOST_KAFKA}:{PORT_KAFKA}", topic="PointActualDron", group=dron
        )

        t_heart = Thread(target=self.Heartbeats, args=(dron,))
        t_heart.start()

        # Después de que estén configurados, señala el evento para indicar que este hilo está listo
        ready_event.set()

        # sleep(4)
        # if len(GetNamesFiguras) == len(figurasPosDron):
        for Pos_Figura, NameFigura in zip(figurasPosDron, GetNamesFiguras):

            while self.matrizSpace[dron]['beat']:
                event_active = True

                while event_active and not self.thread_exit_flag and self.matrizSpace[dron]['beat']:

                    # Activamos el evento
                    if self.matrizSpace[dron]['beat']:
                        message = C_T_PointActualDron.consume_poll_msg_key(
                            dron)

                        if message:

                            # Si el evento debe detenerse, todos los drones vuelven a la base
                            PosFigura = tuple(
                                (1, 1)) if self.stopEvent else Pos_Figura

                            pos_actual_dron = tuple(message)

                            if pos_actual_dron:

                                self.matrizSpace[dron]['pos'] = pos_actual_dron

                                # Cambiar el color del dron según si llegó a su destino o no
                                self.matrizSpace[dron]['color'] = 'green' if PosFigura == pos_actual_dron else 'red'

                                # revisa si el espacio estan todos los drones en sus posisiones EndPointDron
                                # if all(data_dron['color'] == 'green' for id_dron, data_dron in self.matrizSpace.items()):

                                if self.checkDronStatus(self.matrizSpace):
                                    # if all(data_dron['color'] == 'green' and data_dron['beat'] for id_dron, data_dron in self.matrizSpace.items()):

                                    if self.DronesAlaBase:
                                        self.titulo = 'Evento Terminado...\n !!Todos los drones a la base¡¡'
                                    else:
                                        self.titulo = f'[Figura:{NameFigura}]\n¡¡FIGURA COMPLETADA!!'
                                    event_active = False

                                else:

                                    if self.DronesAlaBase:
                                        self.titulo = 'Evento Terminado...\n !!Todos los drones a la base¡¡'
                                    else:
                                        self.titulo = 'Stop event...\n !!Todos los drones a la base¡¡' if self.stopEvent else f'[Figura:{NameFigura}]\n¡¡CREANDO FIGURA!!'

                                P_T_SpaceUpdateDron = MyKafka.Producer(
                                    addr=f"{HOST_KAFKA}:{PORT_KAFKA}"
                                )

                                # Enviar la actualización de espacio una vez, al final de las comprobaciones
                                P_T_SpaceUpdateDron.send_message_topic(
                                    message={"Space": self.matrizSpace,
                                             "EndPointDron": PosFigura,
                                             "tituloPrincipal": self.titulo},
                                    topic='SpaceUpdateDron',
                                    key=dron
                                )

                                P_T_SpaceUpdateDron.flush()

                                if not event_active:
                                    # Si el evento no está activo, salimos del bucle
                                    break
                            # Retraso para limitar la frecuencia de actualización
                            sleep(1)

                while self.stopEvent:
                    sleep(1)
                break
            sleep(5)
        C_T_PointActualDron.close()
        P_T_SpaceUpdateDron.close()

        print(f"x Cerrando hilo h_EM_logicDron del dron {dron}.")

    def h_EM_gestionSocketDrones(self):

        def h_Socket_Dron(client_socket):
            try:

                data, is_valid = self.socket_myServer.receive_message(
                    client_socket)

                if not is_valid:
                    raise ValueError('Mensaje invalido del cliente Dron')

                action, dron_id, value = data.split("|")

                if action != 'authentication':
                    raise ValueError(
                        'Error de solicitud, accion inccorecta')

                print('=============================================')
                self.runBDron.auth_Dron_DB(dron_id, value)
                self.socket_myServer.send_response(
                    f'El Dron {dron_id} fue autentificado con exito!!', client_socket)

                print(
                    f'-> El dron con ID {dron_id} fue autentificado con exito!!')

                client_socket.close()
                print(f'Cerrando socket para dron: {dron_id} ...')
                print(f'Hilo socket cerrando para dron: {dron_id} ...')
                print('=============================================')

            except ValueError as e:
                print(f"Se ha capturado un error en h_Socket_Dron: {e}")
                self.socket_myServer.send_response(str(e), client_socket)
                client_socket.close()
            except Exception as e:
                print(f"Se ha capturado una excepción en h_Socket_Dron: {e}")
                self.socket_myServer.send_response(str(e), client_socket)
                client_socket.close()

        while not self.thread_exit_flag:
            # en caso de que pulsamos STOP, el engine dejara de accept_connection()
            if not self.stopEvent:
                client_socket, _ = self.socket_myServer.accept_connection()
                if client_socket:
                    Thread(target=h_Socket_Dron,
                           args=(client_socket,)).start()

    def h_EM_requestWeather(self):
        try:
            while not self.thread_exit_flag:
                self.socket_ClineteWeather = MySocket(
                    HOST_WEATHER, PORT_WEATHER, is_server=False)
                # Envía un mensaje al servidor meteorológico usando el socket de cliente
                self.socket_ClineteWeather.send_response(
                    'ENGINE | REQUEST WEATHER')

                # Recibe la respuesta del servidor meteorológico
                temperatura, _ = self.socket_ClineteWeather.receive_message()
                self.socket_ClineteWeather.close_socket()
                self.temperatura = float(temperatura)
                if self.temperatura < 0:
                    self.stopEvent = True
                    print(
                        '[CONDICIONES CLIMATICAS ADVERSAS. ESPECTACULO FINALIZADO]')
                else:
                    self.stopEvent = False
                sleep(1)
                # print(self.temperatura)

        except Exception as e:
            raise ValueError(f"Excepción en h_EM_requestWeather: {e}")

    def Heartbeats(self, dron_id):
        try:
            C_T_heartbeats = MyKafka.Consumer(
                addr=f"{HOST_KAFKA}:{PORT_KAFKA}", topic="Heartbeats", group=dron_id
            )
            DISCONNECTED_TIME_THRESHOLD = 30

            tiempo_actual, tiempo_despues = time(), time()
            while True:
                message = C_T_heartbeats.consume_poll_msg_key(stopkey=dron_id)

                if message:
                    tiempo_despues = time()

                tiempo_actual = time()

                if tiempo_actual - tiempo_despues > DISCONNECTED_TIME_THRESHOLD:
                    # El dron se considera desconectado
                    print(f"Dron {dron_id} desconectado.")
                    self.matrizSpace[dron_id]['beat'] = False
                    self.matrizSpace[dron_id]['color'] = '#D9E1F3'
                    break

                tiempo_actual = time()
                sleep(1)
        except Exception as e:
            print(f'x Cerrando hilo del dron desconectado. ID: {dron_id} .')

    def checkDronStatus(self, matrizSpace):
        # if all(data_dron['color'] == 'green' and data_dron['beat'] for id_dron, data_dron in self.matrizSpace.items()):
        for id_dron, data_dron in matrizSpace.items():
            if data_dron['beat']:
                if data_dron['color'] != 'green':
                    return False
        return True


if __name__ == '__main__':
    while True:
        print('=========EngineServer=========')
        object = EngineServer()
        object.Engine_manager()

        print("Reiniciando el programa en 6 segundos...")
        sleep(6)
