import pika
import json
import os
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

def publish_vehicle_detected(data: dict):
    try:
        connection, channel = get_connection()
        if not connection:
            raise Exception("Failed to establish RabbitMQ connection")

        channel.queue_declare(queue="vehicle_detected", durable=True)

        channel.basic_publish(
            exchange="",
            routing_key="vehicle_detected",
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        print(f" [x] Sent to queue: {data}")
    except Exception as e:
        print(f"Error publishing vehicle detection message: {str(e)}")
        raise