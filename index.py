import time
import json
import pika
import threading
import Adafruit_DHT
import RPi.GPIO as GPIO

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)

# Pines de los sensores
GPIO_PINS = {
    'rain_water_level': 17,
    'xkc_y26': 27,
    'flujo_agua': 22,
    'dht11': 4  # Añadimos el pin del sensor DHT11
}

# URL de RabbitMQ (hardcoded)
RABBITMQ_HOST = 'amqps://vumnphwp:04G37mBLNQfL_i6oM1cfMffWzwOOJifD@shrimp.rmq.cloudamqp.com/vumnphwp'

QUEUE_NAMES = {
    'rain_water_level': 'nivelFertilizante',
    'xkc_y26': 'nivelAgua',
    'flujo_agua': 'flujoAgua',
    'dht11': 'ph'  # Añadimos la cola para el sensor DHT11
}

last_sensor_states = {
    'rain_water_level': None,
    'xkc_y26': None,
    'flujo_agua': None,
    'dht11': {'humidity': None, 'temperature': None, 'conductivity': None}
}

lock = threading.Lock()

FLOW_SENSOR_PIN = 22
FLOW_QUEUE_NAME = 'flujoAgua'
pulse_count = 0
flow_rate = 0.0
total_liters = 0.0
last_total_liters = 0.0
last_publish_time = time.time()

def setup_gpio():
    for pin in GPIO_PINS.values():
        GPIO.setup(pin, GPIO.IN)
    GPIO.setup(FLOW_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(FLOW_SENSOR_PIN, GPIO.FALLING, callback=increment_pulse_count)

def send_data_to_rabbitmq(queue_name, data, retries=5):
    for attempt in range(retries):
        try:
            connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_HOST))
            channel = connection.channel()
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(data),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            print(f"[x] Sent {data} to {queue_name}")
            connection.close()
            break
        except pika.exceptions.AMQPConnectionError as error:
            print(f"Connection error: {error}. Retrying...")
            time.sleep(5)
        except pika.exceptions.AMQPChannelError as error:
            print(f"Channel error: {error}. Retrying...")
            time.sleep(5)
        except Exception as error:
            print(f"General error: {error}. Retrying...")
            time.sleep(5)
    else:
        print(f"Failed to connect to RabbitMQ after {retries} attempts")

def monitor_sensor(sensor_name, message_type, read_count=5, delay=0.1):
    while True:
        sensor_state = get_sensor_state(sensor_name, read_count, delay)
        with lock:
            if sensor_state is not None and sensor_state != last_sensor_states[sensor_name]:
                message = message_type['high'] if sensor_state == GPIO.HIGH else message_type['low']
                data = {
                    "sensor_state": message
                }
                send_data_to_rabbitmq(QUEUE_NAMES[sensor_name], data)
                last_sensor_states[sensor_name] = sensor_state
        time.sleep(10)

def get_sensor_state(sensor_name, read_count, delay):
    pin = GPIO_PINS[sensor_name]
    readings = []
    for _ in range(read_count):
        readings.append(GPIO.input(pin))
        time.sleep(delay)
    return max(set(readings), key=readings.count)

def increment_pulse_count(channel):
    global pulse_count
    pulse_count += 1

def calculate_flow():
    global pulse_count, flow_rate, total_liters, last_total_liters, last_publish_time

    while True:
        current_time = time.time()
        elapsed_time = current_time - last_publish_time
        if elapsed_time >= 60:
            with lock:
                flow_rate = pulse_count / elapsed_time * 60.0 / 7.5
                total_liters += flow_rate * (elapsed_time / 60.0)
                pulse_count = 0
                last_total_liters = total_liters
                last_publish_time = current_time

                data = {
                    "flow_rate_lpm": flow_rate,
                    "total_liters": total_liters
                }
                send_data_to_rabbitmq(FLOW_QUEUE_NAME, data)
        time.sleep(1)

def read_dht11():#corregido
    
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = GPIO_PINS['dht11']
    HUMIDITY_THRESHOLD = 1.0
    TEMPERATURE_THRESHOLD = 0.5

    while True:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            conductivity = 0  # Suponiendo que la conductividad es un valor fijo o calculado de alguna manera
            with lock:
                last_humidity = last_sensor_states['dht11']['humidity']
                last_temperature = last_sensor_states['dht11']['temperature']
                last_conductivity = last_sensor_states['dht11']['conductivity']

                if (last_humidity is None or abs(humidity - last_humidity) >= HUMIDITY_THRESHOLD or
                    last_temperature is None or abs(temperature - last_temperature) >= TEMPERATURE_THRESHOLD or
                    conductivity != last_conductivity):
                    
                    data = {
                        "humidity": humidity,
                        "temperature": temperature,
                        "conductivity": conductivity
                    }
                    send_data_to_rabbitmq(QUEUE_NAMES['dht11'], data)
                    
                    last_sensor_states['dht11']['humidity'] = humidity
                    last_sensor_states['dht11']['temperature'] = temperature
                    last_sensor_states['dht11']['conductivity'] = conductivity
        else:
            print("Failed to retrieve data from DHT11 sensor")
        time.sleep(10)

if __name__ == "__main__":
    setup_gpio()

    sensor_messages = {
        'rain_water_level': {'high': "hay fertilizante", 'low': "no hay fertilizante"},
        'xkc_y26': {'high': "hay agua", 'low': "no hay agua"}
    }

    threads = []
    for sensor_name in ['rain_water_level', 'xkc_y26']:
        thread = threading.Thread(target=monitor_sensor, args=(sensor_name, sensor_messages[sensor_name]))
        thread.start()
        threads.append(thread)

    dht11_thread = threading.Thread(target=read_dht11)
    dht11_thread.start()
    threads.append(dht11_thread)

    flow_thread = threading.Thread(target=calculate_flow)
    flow_thread.start()
    threads.append(flow_thread)

    for thread in threads:
        thread.join()

    GPIO.cleanup()