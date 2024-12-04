import RPi.GPIO as GPIO

RABBITMQ_HOST = 'amqps://huejwzha:2wQ8OaBYpNCXyJJhQW6r0mw3kCWEPOaL@shrimp.rmq.cloudamqp.com/huejwzha'

GPIO.setmode(GPIO.BCM)

GPIO_PINS = {
    'rain_water_level': 17,
    'xkc_y26': 27,
    'flujo_agua': 22,
    'dht11': 4
}

QUEUE_NAMES = {
    'rain_water_level': 'nivelFertilizante',
    'xkc_y26': 'nivelAgua',
    'flujo_agua': 'flujoAgua',
    'dht11': 'ph'
}

SENSOR_MESSAGES = {
    'rain_water_level': {'high': "hay fertilizante", 'low': "no hay fertilizante"},
    'xkc_y26': {'high': "hay agua", 'low': "no hay agua"}
}

FLOW_SENSOR_PIN = 22
FLOW_QUEUE_NAME = 'flujoAgua'

HUMIDITY_THRESHOLD = 1.0
TEMPERATURE_THRESHOLD = 0.5