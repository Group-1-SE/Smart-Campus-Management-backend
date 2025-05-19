import pika
import json
import os
from manual_approvals import add_vehicle
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
                socket_timeout=5
            )
            
            connection = pika.BlockingConnection(parameters)
            print("Successfully connected to RabbitMQ.")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS}: Failed to connect to RabbitMQ at {RABBITMQ_HOST}: {str(e)}")
            if attempt < RETRY_ATTEMPTS - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Max retry attempts reached. Could not establish initial connection to RabbitMQ.")
                raise

def consume_manual_approvals():
    while True:  # Keep trying to reconnect if connection is lost
        connection = None
        try:
            connection = get_connection()
            if not connection:
                print("Could not start manual approvals consumer due to connection failure.")
                time.sleep(RETRY_DELAY)
                continue

            channel = connection.channel()
            channel.queue_declare(queue="manual_approval_requests", durable=True)

            def callback(ch, method, properties, body):
                message = json.loads(body)
                print(f"[x] Received manual approval request: {message}")
                try:
                    add_vehicle(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"Error processing message {message}: {str(e)}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_consume(queue="manual_approval_requests", on_message_callback=callback)
            print(" [*] Waiting for manual approval requests...")
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

def send_manual_approval(vehicle):
    connection = None
    try:
        connection = get_connection()
        if not connection:
            print("Could not send manual approval due to connection failure.")
            return

        channel = connection.channel()
        channel.queue_declare(queue="vehicle.authorization.result", durable=True)

        message = {
            "plate_number": vehicle["plate_number"],
            "status": "manually approved",
            "security_clear": True,
            "timestamp": vehicle["timestamp"]
        }

        channel.basic_publish(
            exchange="",
            routing_key="vehicle.authorization.result",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        print(f" [x] Sent manual approval result: {message}")
    except Exception as e:
        print(f"Error sending manual approval message: {str(e)}")
        raise