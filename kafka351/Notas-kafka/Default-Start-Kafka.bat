@echo off

:: Inicia ZooKeeper
start cmd /k "cd C:\SD-Practica\kafka351\bin\windows && zookeeper-server-start.bat C:\SD-Practica\kafka351\config\zookeeper.properties"

:: Espera unos segundos para asegurarse de que ZooKeeper haya iniciado
timeout /t 15

:: Inicia el broker de Kafka
start cmd /k "cd C:\SD-Practica\kafka351\bin\windows && kafka-server-start.bat C:\SD-Practica\kafka351\config\server.properties"

:: Espera unos segundos para asegurarse de que Kafka haya iniciado
timeout /t 15

:: Inicia el producer
start cmd /k "cd C:\SD-Practica\kafka351\bin\windows && kafka-console-producer.bat --broker-list localhost:9092 --topic test1"

:: Espera unos segundos
timeout /t 5

:: Inicia el consumer podemos agregar el --from-beginning para que el consumidor arranque obteniendo todos los mensajes que hay en ese topic
start cmd /k "cd C:\SD-Practica\kafka351\bin\windows && kafka-console-consumer.bat --bootstrap-server localhost:9092 --topic test1 "

:: Abre un cmd en la ubicación especificada
start cmd /k "cd C:\SD-Practica\kafka351\bin\windows"

exit
