import RPi.GPIO as GPIO

# RabbitMQ Configuration
RABBITMQ_HOST = 'amqps://vumnphwp:04G37mBLNQfL_i6oM1cfMffWzwOOJifD@shrimp.rmq.cloudamqp.com/vumnphwp'

# GPIO Configuration
GPIO.setmode(GPIO.BCM)

# Sensor Pins
GPIO_PINS = {
    'rain_water_level': 17,
    'xkc_y26': 27,
    'flujo_agua': 22,
    'dht11': 4
}

# Queue Names
QUEUE_NAMES = {
    'rain_water_level': 'nivelFertilizante',
    'xkc_y26': 'nivelAgua',
    'flujo_agua': 'flujoAgua',
    'dht11': 'ph'
}

# Sensor Message Definitions
SENSOR_MESSAGES = {
    'rain_water_level': {'high': "hay fertilizante", 'low': "no hay fertilizante"},
    'xkc_y26': {'high': "hay agua", 'low': "no hay agua"}
}

# Flow Sensor Configuration
FLOW_SENSOR_PIN = 22
FLOW_QUEUE_NAME = 'flujoAgua'

# DHT11 Sensor Thresholds
HUMIDITY_THRESHOLD = 1.0
TEMPERATURE_THRESHOLD = 0.5