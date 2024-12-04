import time
import threading
import RPi.GPIO as GPIO
from config.config import GPIO_PINS, QUEUE_NAMES, SENSOR_MESSAGES
from rabbit.rabbitmq_handler import RabbitMQHandler

class SensorMonitor:
    def __init__(self, rabbitmq_host):
        self.rabbitmq_handler = RabbitMQHandler(rabbitmq_host)
        self.lock = threading.Lock()
        self.last_sensor_states = {
            'rain_water_level': None,
            'xkc_y26': None
        }

    def get_sensor_state(self, sensor_name, read_count=5, delay=0.1):
        pin = GPIO_PINS[sensor_name]
        readings = []
        for _ in range(read_count):
            readings.append(GPIO.input(pin))
            time.sleep(delay)
        return max(set(readings), key=readings.count)

    def monitor_sensor(self, sensor_name):
        while True:
            sensor_state = self.get_sensor_state(sensor_name)
            with self.lock:
                if sensor_state is not None and sensor_state != self.last_sensor_states[sensor_name]:
                    message = (SENSOR_MESSAGES[sensor_name]['high'] 
                               if sensor_state == GPIO.HIGH 
                               else SENSOR_MESSAGES[sensor_name]['low'])
                    data = {"sensor_state": message}
                    self.rabbitmq_handler.send_data(QUEUE_NAMES[sensor_name], data)
                    self.last_sensor_states[sensor_name] = sensor_state
            time.sleep(10)

    def start_monitoring(self):
        threads = []
        for sensor_name in ['rain_water_level', 'xkc_y26']:
            thread = threading.Thread(target=self.monitor_sensor, args=(sensor_name,))
            thread.start()
            threads.append(thread)
        return threads