from flask import Flask, request, render_template, redirect, url_for, flash
import pika
import json
import os
import uuid

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here' 

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
UPLOAD_FOLDER = '/app/uploads' 

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            original_filename = file.filename
            filename_prefix = uuid.uuid4().hex
            filename = f"{filename_prefix}_{original_filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            try:
                file.save(filepath)
            except Exception as e:
                flash(f'Error saving file: {e}')
                return redirect(request.url)

            action = request.form.get('action', 'resize')
            params = {}
            if action == 'resize' or action == 'thumbnail':
                params = {'width': 300, 'height': 300} 
                if action == 'thumbnail':
                     params = {'width': 100, 'height': 100}

            task_details = {
                'image_id': filename, 
                'image_path': filepath, 
                'action': action,
                'params': params
            }
            message_body = json.dumps(task_details)

            try:
                connection = get_rabbitmq_connection()
                channel = connection.channel()
                queue_name = 'image_tasks_queue'
                channel.queue_declare(queue=queue_name, durable=True)
                channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=message_body,
                    properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                )
                connection.close()
                flash(f"Task for image {original_filename} (as {filename}) sent to queue for action: {action}!")
            except pika.exceptions.AMQPConnectionError as e:
                flash(f"Error connecting to RabbitMQ: {e}")
            except Exception as e:
                flash(f"An error occurred while sending task: {e}")

            return redirect(url_for('upload_file'))

    processed_files_list = []
    processed_folder_host = 'processed_images' 

    if os.path.exists(processed_folder_host):
         processed_files_list = [f for f in os.listdir(processed_folder_host) if os.path.isfile(os.path.join(processed_folder_host, f))]


    return render_template('upload.html', processed_files=processed_files_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)