import RPi.GPIO as GPIO
from config.config import RABBITMQ_HOST
from sensores.sensor_monitor import SensorMonitor
from sensores.flow_sensor import FlowSensor
from sensores.dht11_sensor import DHT11Sensor

def main():
    try:
        # Initialize sensors
        sensor_monitor = SensorMonitor(RABBITMQ_HOST)
        flow_sensor = FlowSensor(RABBITMQ_HOST)
        dht11_sensor = DHT11Sensor(RABBITMQ_HOST)

        # Start monitoring threads
        sensor_threads = sensor_monitor.start_monitoring()
        flow_thread = flow_sensor.start_flow_monitoring()
        dht11_thread = dht11_sensor.start_dht11_monitoring()

        # Combine all threads
        threads = sensor_threads + [flow_thread, dht11_thread]

        # Wait for threads to complete (which they won't in normal operation)
        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()