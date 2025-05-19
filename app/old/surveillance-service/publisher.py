import pika
import json

def publish_alert(message: dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='surveillance.alerts', durable=True)
    
    channel.basic_publish(
        exchange='',
        routing_key='surveillance.alerts',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    print("[INFO] Alert published:", message)
    connection.close()
