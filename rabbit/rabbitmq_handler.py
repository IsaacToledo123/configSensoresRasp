import json
import time
import pika

class RabbitMQHandler:
    def __init__(self, rabbitmq_host):
        self.rabbitmq_host = rabbitmq_host
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_host))
            self.channel = self.connection.channel()
        except Exception as error:
            print(f"Error conectando a RabbitMQ: {error}")
            raise

    def ensure_queue(self, queue_name):
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
        except Exception as error:
            print(f"Error declarando cola {queue_name}: {error}")
            self.reconnect()

    def reconnect(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.connect()
        except Exception as error:
            print(f"Error reconectando: {error}")

    def send_data(self, queue_name, data, retries=3):
        for attempt in range(retries):
            try:
                self.ensure_queue(queue_name)

                message = json.dumps(data)

                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=message,
                    properties=pika.BasicProperties(
                        delivery_mode=2, 
                        content_type='application/json'
                    )
                )
                print(f"[✓] Enviado {message} a {queue_name}")
                return True

            except (pika.exceptions.AMQPConnectionError, 
                    pika.exceptions.AMQPChannelError) as error:
                print(f"Error de conexión: {error}. Reintentando...")
                self.reconnect()
                time.sleep(3)
            except Exception as error:
                print(f"Error inesperado: {error}")
                break

        print(f"No se pudo enviar mensaje a {queue_name} después de {retries} intentos")
        return False

    def __del__(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()