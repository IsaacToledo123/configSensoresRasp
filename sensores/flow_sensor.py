import time
import threading
import RPi.GPIO as GPIO
from config.config import FLOW_SENSOR_PIN, FLOW_QUEUE_NAME
from rabbit.rabbitmq_handler import RabbitMQHandler

class FlowSensor:
    def __init__(self, rabbitmq_host):
        self.rabbitmq_handler = RabbitMQHandler(rabbitmq_host)
        self.lock = threading.Lock()
        self.pulse_count = 0
        self.flow_rate = 0.0
        self.total_liters = 0.0
        self.last_total_liters = 0.0
        self.last_publish_time = time.time()

        GPIO.setup(FLOW_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(FLOW_SENSOR_PIN, GPIO.FALLING, callback=self.increment_pulse_count)

    def increment_pulse_count(self, channel):
        self.pulse_count += 1

    def calculate_flow(self):
        while True:
            current_time = time.time()
            elapsed_time = current_time - self.last_publish_time
            
            if elapsed_time >= 60:
                with self.lock:
                    self.flow_rate = self.pulse_count / elapsed_time * 60.0 / 7.5
                    self.total_liters += self.flow_rate * (elapsed_time / 60.0)
                    self.pulse_count = 0
                    self.last_total_liters = self.total_liters
                    self.last_publish_time = current_time

                    data = {
                        "flow_rate_lpm": self.flow_rate,
                        "total_liters": self.total_liters
                    }
                    self.rabbitmq_handler.send_data(FLOW_QUEUE_NAME, data)
            time.sleep(1)

    def start_flow_monitoring(self):
        thread = threading.Thread(target=self.calculate_flow)
        thread.start()
        return thread