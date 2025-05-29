import pika
import time
import json
import os
from PIL import Image, UnidentifiedImageError

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
UPLOAD_FOLDER = '/app/uploads'
PROCESSED_FOLDER = '/app/processed_images'

if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def process_image_task(task_details):
    image_id = task_details.get('image_id')
    image_path_in_task = task_details.get('image_path')
    action = task_details.get('action')
    params = task_details.get('params', {})

    if not image_id or not image_path_in_task:
        print(f" [!] Error: Missing image_id or image_path in task: {task_details}")
        return False

    source_image_path = image_path_in_task 

    if not os.path.exists(source_image_path):
        print(f" [!] Error: Source image {source_image_path} not found for task ID {image_id}.")
        return False

    base_name, ext = os.path.splitext(image_id)
    if action in base_name:
        processed_image_filename = f"{base_name}{ext}"
    else:
        processed_image_filename = f"{base_name}_{action}{ext}"
    output_path = os.path.join(PROCESSED_FOLDER, processed_image_filename)

    try:
        print(f" [>] Attempting to open image: {source_image_path}")
        img = Image.open(source_image_path)

        if action == 'resize':
            new_size = (params.get('width', 300), params.get('height', 300))
            img = img.resize(new_size)
            print(f" [>] Resized {image_id} to {new_size}")
        elif action == 'grayscale':
            if img.mode == 'RGBA': 
                img = img.convert('RGB') 
            img = img.convert('L')
            print(f" [>] Converted {image_id} to grayscale")
        elif action == 'thumbnail':
            thumb_size = (params.get('width', 100), params.get('height', 100))
            img.thumbnail(thumb_size) 
            print(f" [>] Created thumbnail for {image_id} with max size {thumb_size}")
        else:
            print(f" [!] Unknown action: {action} for task ID {image_id}")
            return False

        img.save(output_path)
        print(f" [>] Processed image saved to {output_path}")
        return True
    except UnidentifiedImageError:
        print(f" [!] Error: Cannot identify image file {source_image_path} for task ID {image_id}. It might be corrupted or not an image.")
        return False
    except FileNotFoundError:
         print(f" [!] Error: File not found at {source_image_path} during PIL processing for task ID {image_id}.")
         return False
    except Exception as e:
        print(f" [!] Error processing image {image_id} for action {action}: {e}")
        return False

def callback(ch, method, properties, body):
    print(f" [x] Received message, processing...")
    try:
        task_details = json.loads(body.decode())
    except json.JSONDecodeError:
        print(f" [!] Error: Could not decode JSON from message body: {body}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    task_id_for_log = task_details.get('image_id', 'UNKNOWN_ID')
    if process_image_task(task_details):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f" [x] Task {task_id_for_log} acknowledged.")
    else:
        print(f" [!] Task {task_id_for_log} failed. Nacking message (requeue=False).")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    print(' [*] Worker starting...')
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST, 
                    heartbeat=600, 
                    blocked_connection_timeout=300
                )
            )
            channel = connection.channel()
            queue_name = 'image_tasks_queue'
            channel.queue_declare(queue=queue_name, durable=True)
            print(f" [*] Connected to RabbitMQ on '{RABBITMQ_HOST}'. Waiting for messages in '{queue_name}'.")

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=callback)

            print(" [*] Starting consumption. To exit press CTRL+C (won't work easily inside Docker logs, stop container instead).")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f" [!] AMQP Connection Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt: 
            print(" [*] Worker stopping due to KeyboardInterrupt.")
            if 'channel' in locals() and channel.is_open:
                channel.close()
            if 'connection' in locals() and connection.is_open:
                connection.close()
            break
        except Exception as e:
            print(f" [!] An unexpected error occurred in main loop: {e}. Retrying in 10 seconds...")
            time.sleep(10)

if __name__ == '__main__':
    main()