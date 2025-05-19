import pika
import json
import os # Import the os module

# Define the RabbitMQ host using an environment variable, defaulting to 'rabbitmq'
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')

def get_connection():
    """Helper function to establish RabbitMQ connection with basic error handling."""
    try:
        # Use the defined RABBITMQ_HOST instead of "localhost"
        print(f"Attempting to connect to RabbitMQ at {RABBITMQ_HOST}")
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
        print("Successfully connected to RabbitMQ.")
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Failed to connect to RabbitMQ at {RABBITMQ_HOST}: {str(e)}")
        # Depending on how critical the connection is, you might want to
        # exit, retry, or just return None and handle it in calling functions.
        # For now, we'll print and return None or raise. Let's raise for clarity.
        raise # Re-raise the exception after printing for easier debugging

def publish_vehicle_detected(data: dict):
    connection = None # Initialize connection to None
    try:
        connection = get_connection()
        if not connection:
            # get_connection already prints an error, just return
            print("Could not publish vehicle detected message due to connection failure.")
            return

        channel = connection.channel()

        channel.queue_declare(queue="vehicle_detected", durable=True)

        channel.basic_publish(
            exchange="",
            routing_key="vehicle_detected",
            body=json.dumps(data),
            properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
        )
        print(f" [x] Sent to queue: {data}")
    except pika.exceptions.AMQPConnectionError as e:
         print(f"AMQP Connection Error publishing vehicle detected: {e}")
    except Exception as e:
        print(f"Error publishing vehicle detected message: {str(e)}")
    finally:
        # Ensure connection is closed if it was successfully opened
        if connection and not connection.is_closed:
            try:
                connection.close()
                print("RabbitMQ connection closed after publishing.")
            except Exception as e:
                print(f"Error closing connection after publishing: {str(e)}")