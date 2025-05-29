# Image Processing Pipeline with RabbitMQ

This project implements an image processing pipeline using a web application, a worker service, and RabbitMQ for message queuing.

## Project Structure

The project consists of the following services:

- **`rabbitmq`**: A RabbitMQ message broker instance.
  - Manages message queues for communication between the `webapp` and `worker` services.
  - Exposes ports `5672` (AMQP) and `15672` (RabbitMQ Management Plugin).
- **`webapp`**: A Flask-based web application.
  - Allows users to upload images.
  - Sends messages to RabbitMQ to request image processing.
  - Exposes port `5000`.
  - Mounts `uploads` and `processed_images` directories as volumes.
- **`worker`**: A worker service.
  - Listens for image processing requests from RabbitMQ.
  - Processes images (e.g., resizing, filtering - _details to be added based on actual worker functionality_).
  - Saves processed images to the `processed_images` directory.
  - Mounts `uploads` (read-only) and `processed_images` directories as volumes.

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Building and Running

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-project-directory>
    ```
2.  **Build and start the services:**

    ```bash
    docker-compose up --build -d
    ```

    This command will build the images for `webapp` and `worker` (if they don't exist) and start all services in detached mode.

3.  **Accessing the services:**
    - **Web Application**: Open your web browser and navigate to `http://localhost:5000`.
    - **RabbitMQ Management**: Open your web browser and navigate to `http://localhost:15672`. You can log in with the default credentials (guest/guest).

## Configuration

- **Timezone**: The timezone for all services is set to `Europe/Kyiv`. You can change this in the `docker-compose.yml` file if needed.
- **Flask Environment**: The `webapp` is configured to run in development mode with debugging enabled. This can be changed in the `docker-compose.yml` for production deployments.
- **RabbitMQ Host**: The `webapp` and `worker` are configured to connect to RabbitMQ at `rabbitmq`.

## Scaling

The `worker` service can be scaled by modifying the `docker-compose.yml` or by using the `--scale` option with `docker-compose up`. For example, to run 3 instances of the worker:

```bash
docker-compose up --build -d --scale worker=3
```

## Volumes

- `rabbitmq_data`: Persists RabbitMQ data.
- `./uploads`:/app/uploads`: Maps the local `uploads`directory to the`webapp`and`worker` containers.
- `./processed_images`:/app/processed_images`: Maps the local `processed_images`directory to the`webapp`and`worker` containers.
