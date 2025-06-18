# 🚁 Art With Drones - Sistema de Control de Enjambre de Drones

## 📝 Descripción

Art With Drones es un sistema distribuido de control de enjambre de drones que permite crear figuras y formaciones artísticas en tiempo real. El proyecto implementa una arquitectura cliente-servidor robusta con comunicación mediante Apache Kafka, permitiendo la coordinación sincronizada de múltiples drones para crear espectáculos visuales aéreos.

## ✨ Características principales

### 🎯 Sistema de Registro y Autenticación
- Registro seguro de drones con tokens SHA256
- Autenticación de drones antes de participar en eventos
- Gestión de límite máximo de drones activos

### 🎨 Creación de Figuras Artísticas
- Carga de figuras desde archivos JSON
- Asignación automática de posiciones a cada dron
- Sincronización en tiempo real entre todos los drones
- Visualización del espacio 2D con interfaz gráfica

### 🌡️ Sistema de Monitoreo Climático
- Integración con servicio meteorológico
- Detención automática del evento en condiciones adversas
- Actualización de temperatura en tiempo real

### 💓 Sistema de Heartbeat
- Monitoreo continuo del estado de cada dron
- Detección automática de drones desconectados
- Reasignación dinámica de tareas

### 🔄 Control de Eventos
- Inicio, parada y reinicio de eventos
- Retorno automático de drones a la base
- Gestión de múltiples figuras en secuencia

## 📸 Capturas de pantalla

### 🖥️ Interfaz del Engine
```
┌────────────────────────┐
│      [ENGINE]          │
│                        │
│   [Start event]        │
│   [Stop event]         │
│   [Restart event]      │
│                        │
│   IP: 169.254.64.2     │
│   Port: 4000           │
│   Max Drones: 50       │
│                        │
│   [Reset parameters]   │
│                        │
│   169.254.64.82:49808  │
└────────────────────────┘
```

### 🎮 Visualización de Drones
```
┌─────────────────────────────┐
│    [Art With Drones]        │
│                             │
│  ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐    │
│  │1│2│3│4│5│...    │20│    │
│  ├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤    │
│ 1│ │ │D│ │ │       │  │    │
│ 2│ │D│ │D│ │       │  │    │
│ 3│D│ │ │ │D│       │  │    │
│  │ │ │ │ │ │       │  │    │
│ ...                         │
│20│ │ │ │ │ │       │  │    │
│  └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘    │
│                             │
│  D = Dron (Verde/Rojo)      │
└─────────────────────────────┘
```

## 🛠️ Tecnologías utilizadas

### 🐍 Backend
- **Python 3.x** - Lenguaje principal
- **Socket Programming** - Comunicación TCP/IP
- **Apache Kafka** - Sistema de mensajería distribuida
- **SQLite3** - Base de datos local
- **Threading** - Procesamiento concurrente

### 🎨 Frontend
- **PyQt5** - Interfaz gráfica de usuario
- **Qt Designer** - Diseño de interfaces

### 📚 Librerías adicionales
- **Faker** - Generación de datos de prueba
- **Hashlib** - Generación de tokens seguros
- **JSON** - Manejo de configuraciones y figuras

## 🚀 Instalación y uso

### 📋 Prerequisitos
```bash
# Python 3.7 o superior
python --version

# Apache Kafka
# Descargar desde https://kafka.apache.org/downloads
```

### 📦 Instalación de dependencias
```bash
pip install PyQt5
pip install kafka-python
pip install faker
```

### ⚙️ Configuración

1. **Configurar Kafka:**
```bash
# Iniciar Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Iniciar Kafka Server
bin/kafka-server-start.sh config/server.properties
```

2. **Configurar archivos de configuración:**
- Editar `config.txt` en cada módulo con las IPs y puertos correspondientes

### 🏃 Ejecución

1. **Iniciar el Registro de Drones:**
```bash
cd Registry_Engine
python AD_Registry.py
```

2. **Iniciar el Engine:**
```bash
cd Registry_Engine
python AD_Engine.py
```

3. **Iniciar el Servicio Meteorológico:**
```bash
cd KAFKA_CLIMA
python AD_Weather.py
```

4. **Iniciar Drones:**
```bash
cd Dron
# Con interfaz gráfica
python AD_Drone.py <ID_DRON> <ALIAS> si

# Sin interfaz gráfica
python AD_Drone.py <ID_DRON> <ALIAS> no
```

## 📁 Estructura del proyecto

```
Art-With-Drones/
│
├── 🚁 Dron/
│   ├── AD_Drone.py         # Lógica principal del dron
│   ├── Tools.py            # Utilidades y clases auxiliares
│   ├── Settings.py         # Configuración de protocolo
│   └── config.txt          # Archivo de configuración
│
├── 🎮 Registry_Engine/
│   ├── AD_Engine.py        # Motor principal del sistema
│   ├── AD_Registry.py      # Servidor de registro
│   ├── Tools.py            # Utilidades compartidas
│   └── config.txt          # Configuración del engine
│
├── 🌡️ KAFKA_CLIMA/
│   ├── AD_Weather.py       # Servicio meteorológico
│   ├── Tools.py            # Utilidades del clima
│   └── config.txt          # Configuración del clima
│
├── 📊 BD/                  # Bases de datos SQLite
│   └── bdTokens.sqlite     # Tokens de autenticación
│
└── 📄 figuras.json         # Definición de figuras
```

## 👥 Autores / Colaboradores

- **Desarrollador Principal** - Sistema de Control de Drones
- **Contribuidores** - Bienvenidos a través de Pull Requests

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para más detalles.

## 📧 Contacto para empresas / Colaboraciones

### 🤝 Oportunidades de colaboración:
- **Eventos y espectáculos** - Creación de shows personalizados con drones
- **Investigación** - Desarrollo de nuevos algoritmos de enjambre
- **Integración empresarial** - Adaptación del sistema a necesidades específicas

### 📬 Contacto:
- **Email empresarial:** business@artwithdrones.com
- **Email técnico:** tech@artwithdrones.com
- **LinkedIn:** [Art With Drones Project](https://linkedin.com/company/artwithdrones)
- **GitHub Issues:** Para reportar bugs o sugerir mejoras

---

💡 **¿Interesado en el proyecto?** ¡No dudes en contactarnos para discutir posibles colaboraciones o implementaciones personalizadas! 
⭐ **Si te gusta el proyecto, no olvides dejar una estrella en GitHub!**
