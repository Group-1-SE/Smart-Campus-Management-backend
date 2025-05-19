import pika
import json
import os
from supabase_utils import log_vehicle, log_surveillance_alert
import threading
import time

# Define the RabbitMQ host using an environment variable, defaulting to 'rabbitmq'
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RETRY_ATTEMPTS = 10
RETRY_DELAY = 5

def get_connection():
    """Helper function to establish RabbitMQ connection with retries."""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            print(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS}: Connecting to RabbitMQ at {RABBITMQ_HOST}")
            
            # Configure connection parameters for Docker networking
            credentials = pika.PlainCredentials('guest', 'guest')
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=5672,
                virtual_host='/',
                credentials=credentials,
                heartbeat=600,  # 10 minutes
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5,
                socket_timeout=5,
                frame_max=131072,  # Maximum allowed frame size for AMQP 0.9.1
                channel_max=65535,  # Maximum allowed channels
                tcp_options={
                    'TCP_KEEPIDLE': 60,
                    'TCP_KEEPINTVL': 10,
                    'TCP_KEEPCNT': 6
                }
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Set QoS prefetch count
            channel.basic_qos(prefetch_count=1)
            
            print("Successfully connected to RabbitMQ.")
            return connection, channel
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS}: Failed to connect to RabbitMQ at {RABBITMQ_HOST}: {str(e)}")
            if attempt < RETRY_ATTEMPTS - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Max retry attempts reached. Could not establish initial connection to RabbitMQ.")
                raise

def consume_vehicle_authorized():
    while True:  # Keep trying to reconnect if connection is lost
        try:
            connection, channel = get_connection()
            if not connection:
                print("Could not start vehicle authorized consumer due to connection failure.")
                time.sleep(RETRY_DELAY)
                continue

            channel.queue_declare(queue="vehicle.authorization.result", durable=True)

            def callback(ch, method, properties, body):
                data = json.loads(body)
                print(f"[x] Received vehicle authorization data: {data}")
                try:
                    log_vehicle(data["plate_number"], "entered", True)  # TODO: Dynamic
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Error processing vehicle authorization message {data}: {str(e)}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # Generate a unique consumer tag
            consumer_tag = f"vehicle_auth_{int(time.time())}_{os.getpid()}"
            
            channel.basic_consume(
                queue="vehicle.authorization.result",
                on_message_callback=callback,
                auto_ack=False,
                consumer_tag=consumer_tag
            )
            print("[*] Waiting for vehicle authorization results...")
            channel.start_consuming()

        except pika.exceptions.ConnectionClosedByBroker:
            print("RabbitMQ connection closed by broker. Attempting to reconnect...")
            time.sleep(RETRY_DELAY)
            continue
        except pika.exceptions.AMQPChannelError as e:
            print(f"AMQP Channel Error: {e}")
            time.sleep(RETRY_DELAY)
            continue
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQP Connection Error: {e}")
            time.sleep(RETRY_DELAY)
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            time.sleep(RETRY_DELAY)
            continue

def consume_surveillance_alerts():
    while True:  # Keep trying to reconnect if connection is lost
        try:
            connection, channel = get_connection()
            if not connection:
                print("Could not start surveillance alerts consumer due to connection failure.")
                time.sleep(RETRY_DELAY)
                continue

            channel.queue_declare(queue="surveillance.alerts", durable=True)

            def callback(ch, method, properties, body):
                data = json.loads(body)
                print(f"[x] Received surveillance alert: {data}")
                try:
                    log_surveillance_alert(data)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Error processing surveillance alert message {data}: {str(e)}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # Generate a unique consumer tag
            consumer_tag = f"surveillance_{int(time.time())}_{os.getpid()}"
            
            channel.basic_consume(
                queue="surveillance.alerts",
                on_message_callback=callback,
                auto_ack=False,
                consumer_tag=consumer_tag
            )
            print("[*] Waiting for surveillance alerts...")
            channel.start_consuming()

        except pika.exceptions.ConnectionClosedByBroker:
            print("RabbitMQ connection closed by broker. Attempting to reconnect...")
            time.sleep(RETRY_DELAY)
            continue
        except pika.exceptions.AMQPChannelError as e:
            print(f"AMQP Channel Error: {e}")
            time.sleep(RETRY_DELAY)
            continue
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQP Connection Error: {e}")
            time.sleep(RETRY_DELAY)
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            time.sleep(RETRY_DELAY)
            continue