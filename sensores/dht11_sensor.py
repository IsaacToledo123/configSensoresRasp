import time
import threading
import Adafruit_DHT
import RPi.GPIO as GPIO
from config.config import (GPIO_PINS, QUEUE_NAMES, 
                    HUMIDITY_THRESHOLD, TEMPERATURE_THRESHOLD)
from rabbit.rabbitmq_handler import RabbitMQHandler

class DHT11Sensor:
    def __init__(self, rabbitmq_host):
        self.rabbitmq_handler = RabbitMQHandler(rabbitmq_host)
        self.lock = threading.Lock()
        self.last_sensor_states = {
            'humidity': None, 
            'temperature': None, 
            'conductivity': None
        }
        self.DHT_SENSOR = Adafruit_DHT.DHT11
        self.DHT_PIN = GPIO_PINS['dht11']

    def read_dht11(self):
        while True:
            humidity, temperature = Adafruit_DHT.read_retry(self.DHT_SENSOR, self.DHT_PIN)
            
            if humidity is not None and temperature is not None:
                conductivity = 0  # Placeholder for actual conductivity calculation

                with self.lock:
                    last_humidity = self.last_sensor_states['humidity']
                    last_temperature = self.last_sensor_states['temperature']
                    last_conductivity = self.last_sensor_states['conductivity']

                    if (last_humidity is None or 
                        abs(humidity - last_humidity) >= HUMIDITY_THRESHOLD or
                        last_temperature is None or 
                        abs(temperature - last_temperature) >= TEMPERATURE_THRESHOLD or
                        conductivity != last_conductivity):
                        
                        data = {
                            "humidity": humidity,
                            "temperature": temperature,
                            "conductivity": conductivity
                        }
                        self.rabbitmq_handler.send_data(QUEUE_NAMES['dht11'], data)
                        
                        self.last_sensor_states.update(data)
            else:
                print("Failed to retrieve data from DHT11 sensor")
            time.sleep(10)

    def start_dht11_monitoring(self):
        thread = threading.Thread(target=self.read_dht11)
        thread.start()
        return thread