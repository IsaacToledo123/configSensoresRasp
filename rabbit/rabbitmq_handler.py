import json
import time
import pika

class RabbitMQHandler:
    def __init__(self, rabbitmq_host):
        self.rabbitmq_host = rabbitmq_host

    def send_data(self, queue_name, data, retries=5):
        for attempt in range(retries):
            try:
                connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_host))
                channel = connection.channel()
                channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(data),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print(f"[x] Sent {data} to {queue_name}")
                connection.close()
                return True
            except (pika.exceptions.AMQPConnectionError, 
                    pika.exceptions.AMQPChannelError, 
                    Exception) as error:
                print(f"Error: {error}. Retrying...")
                time.sleep(5)
        
        print(f"Failed to connect to RabbitMQ after {retries} attempts")
        return False