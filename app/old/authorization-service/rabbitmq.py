import pika
import json
import os
from supabase import create_client, Client
from supabase_utils import check_authorization
import time

# Define the RabbitMQ host using an environment variable, defaulting to 'rabbitmq'
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RETRY_ATTEMPTS = 10
RETRY_DELAY = 5

# Global connection and channel variables
connection = None
channel = None

def get_connection():
    """Helper function to establish RabbitMQ connection with retries."""
    global connection, channel
    
    if connection and not connection.is_closed:
        return connection
        
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
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Attempt {attempt + 1}/{RETRY_ATTEMPTS}: Failed to connect to RabbitMQ at {RABBITMQ_HOST}: {str(e)}")
            if attempt < RETRY_ATTEMPTS - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Max retry attempts reached. Could not establish initial connection to RabbitMQ.")
                raise
            
def consume_vehicle_detected():
    global connection, channel
    while True:  # Keep trying to reconnect if connection is lost
        try:
            connection = get_connection()
            if not connection:
                print("Authorization service could not start consumer due to connection failure.")
                time.sleep(RETRY_DELAY)
                continue

            channel.queue_declare(queue="vehicle_detected", durable=True)

            def callback(ch, method, properties, body):
                message = json.loads(body)
                plate_number = message["plate_number"]
                print(f" [x] Received {plate_number}")

                try:
                    is_authorized = check_authorization(plate_number)
                    result = {
                        "plate_number": plate_number,
                        "is_authorized": is_authorized,
                        "timestamp": message["timestamp"]
                    }

                    if is_authorized:
                        print(f" [x] Vehicle {plate_number} is authorized.")
                        publish_authorization_result(result)
                    else:
                        print(f" [x] Vehicle {plate_number} is unauthorized. Sending to manual approval.")
                        publish_manual_approval_request(result)

                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    print(f"Error processing vehicle detection message {message}: {str(e)}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # Generate a unique consumer tag
            consumer_tag = f"ctag_{int(time.time())}_{os.getpid()}"
            
            channel.basic_consume(
                queue="vehicle_detected",
                on_message_callback=callback,
                auto_ack=False,
                consumer_tag=consumer_tag
            )
            print(" [*] Authorization service is listening for vehicle detections...")
            
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

def publish_authorization_result(data: dict):
    global connection, channel
    try:
        if not connection or connection.is_closed:
            connection = get_connection()
            channel = connection.channel()

        channel.queue_declare(queue="vehicle.authorization.result", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="vehicle.authorization.result",
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        print(f" [x] Sent authorization result: {data}")
    except Exception as e:
        print(f"Error publishing authorization result message: {str(e)}")
        raise

def publish_manual_approval_request(data: dict):
    global connection, channel
    try:
        if not connection or connection.is_closed:
            connection = get_connection()
            channel = connection.channel()

        channel.queue_declare(queue="manual_approval_requests", durable=True)
        channel.basic_publish(
            exchange="",
            routing_key="manual_approval_requests",
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        print(f" [x] Sent unauthorized vehicle to manual approval queue: {data}")
    except Exception as e:
        print(f"Error publishing manual approval request message: {str(e)}")
        raise