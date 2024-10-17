@echo off

:: Matar el consumer (asumiendo que es la última ventana cmd abierta relacionada con Kafka)
taskkill /FI "WindowTitle eq C:\WINDOWS\system32\cmd.exe - kafka-console-consumer.bat*" /T /F

:: Esperar unos segundos
timeout /t 5

:: Matar el producer
taskkill /FI "WindowTitle eq C:\WINDOWS\system32\cmd.exe - kafka-console-producer.bat*" /T /F

:: Esperar unos segundos
timeout /t 5

:: Matar el Kafka server
taskkill /FI "WindowTitle eq C:\WINDOWS\system32\cmd.exe - kafka-server-start.bat*" /T /F

:: Esperar unos segundos
timeout /t 5

:: Matar el ZooKeeper server
taskkill /FI "WindowTitle eq C:\WINDOWS\system32\cmd.exe - zookeeper-server-start.bat*" /T /F

exit
