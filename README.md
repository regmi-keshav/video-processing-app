# Video Processing Application

---

## Overview

The Video Processing Application allows users to upload videos, which are then processed to extract subtitles in multiple languages. Users can search for phrases within the subtitles and retrieve corresponding timestamps to jump directly to that part of the video. The application uses Django for the backend, PostgreSQL for storage, Celery for background tasks, and FFmpeg for subtitle extraction.

## Features

- **Video Upload**: Users can upload videos.
- **Subtitle Extraction**: Extracts English subtitles from uploaded videos using FFmpeg.
- **Search Functionality**: Users can search for a phrase in the subtitles and retrieve timestamps.
- **Multilingual Support**: Designed to support multiple languages
- **List of Uploaded Videos**: View a list of uploaded videos with options to view subtitles and search.

## Technologies Used

- **Backend**: Django
- **Database**: PostgreSQL
- **Task Queue**: Celery
- **Message Broker**: Redis
- **Video Processing**: FFmpeg
- **Containerization**: Docker

## Setup Instructions

### Prerequisites

- Python 3.9 and above
- PostgreSQL
- Docker (optional but recommended)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/regmi-keshav/video-processing-app.git
   cd video-processing-app
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install requirements**:

   Make sure you have the following packages in your `requirements.txt`:

   ```plaintext
   Django
   djangorestframework
   psycopg2-binary
   ffmpeg-python
   celery
   redis
   gunicorn
   eventlet
   ```

   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

1. **Create a PostgreSQL database**:

   ```sql
   CREATE DATABASE video_processing_db;
   ```

2. **Update `settings.py`** to connect to your PostgreSQL database:

   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'video_processing_db',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

### Celery Configuration

- **Broker**: Redis is used as the message broker. Ensure Redis is running.

Add the following configuration to your `settings.py`:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'UTC'
```

### Running the Application

1. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

2. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

3. **Start the Celery worker**:

   In a separate terminal, run:

   ```bash
   celery -A video_processing_app worker --loglevel=info
   ```

### Docker Setup (Optional)

1.  **Create Dockerfile for Django App**

    Create a `Dockerfile` to containerize the Django application. This will install all dependencies, set up the environment, and run the Django development server inside a container.

    **`Dockerfile`**:

    ```dockerfile
    # Base image
    FROM python:3.10-slim

    # Set environment variables
    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1

    # Create a directory for the app
    WORKDIR /app

    # Install dependencies
    COPY requirements.txt /app/
    RUN pip install --upgrade pip && \
        pip install -r requirements.txt

    # Copy project files
    COPY . /app/

    # Expose port 8000 (Django default)
    EXPOSE 8000

    # Command to run the Django app
    CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "video_processing_app.wsgi:application"]
    ```

---

2. **Create `docker-compose.yml`**

   Docker Compose is used to manage multiple containers such as Django (web), PostgreSQL (database), and Redis (for Celery tasks).

**`docker-compose.yml`**:

```yaml
version: "3.8"

services:
  web:
    build: .
    command: gunicorn --workers 3 --bind 0.0.0.0:8000 video_processing_app.wsgi:application
    volumes:
      - .:/app
      - media:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DJANGO_SETTINGS_MODULE=video_processing_app.settings

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: video_db
      POSTGRES_USER: video_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A video_processing_app worker --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - redis
      - db
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

volumes:
  postgres_data:
  media:
```

#### Explanation of Services:

- **`web`**: The Django app container that runs Gunicorn as the WSGI server on port 8000.
- **`db`**: PostgreSQL database container.
- **`redis`**: Redis container that will act as a message broker for Celery.
- **`celery`**: Container that runs the Celery worker.
- **`celery-beat`**: Runs Celery Beat for scheduled tasks (if needed).
- **Volumes**:
  - `media`: This stores uploaded media files.
  - `postgres_data`: Stores PostgreSQL database data.

---

3. **Running the Application with Docker**

To set up and run the application using Docker:

1. **Build the Docker images**:

   ```bash
   docker-compose build
   ```

2. **Run the Docker containers**:
   ```bash
   docker-compose up
   ```

This will start all services: Django, PostgreSQL, Redis, Celery, and Celery Beat. Your Django application will be running on `http://localhost:8000`, and the PostgreSQL and Redis services will also be up.

---

4.  **PostgreSQL Setup**

Inside the `settings.py`, make sure your PostgreSQL settings look like this:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'video_db',
        'USER': 'video_user',
        'PASSWORD': 'password',
        'HOST': 'db',  # 'db' corresponds to the service name in docker-compose
        'PORT': '5432',
    }
}


CELERY_BROKER_URL = 'redis://redis:6379/0' # change localhost to redis
CELERY_RESULT_BACKEND = 'redis://redis:6379/0' # change localhost to redis

```

---

5. **Testing and Using Celery**

- Celery automatically handles background tasks like subtitle extraction. When a video is uploaded through the `/api/upload/` endpoint, the subtitle extraction task is queued and processed in the background.
- You can monitor Celery tasks by checking the logs of the `celery` container:
  ```bash
  docker-compose logs -f celery
  ```

---

### API Endpoints

The application provides several API endpoints to manage video uploads, subtitle extraction, and searching. Below is a detailed list of all available endpoints.

#### 1. Upload Video

- **Method**: `POST`
- **URL**: `/api/upload/`
- **Description**: Uploads a video file and triggers the subtitle extraction process.
- **Request Body**:
  - `video_file`: (file, required) The video file to upload.
- **Response**:
  - **201 Created**:
    ```json
    {
      "message": "Video uploaded successfully. Subtitles will be processed shortly."
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "message": "Video uploaded, but an error occurred during subtitle extraction."
    }
    ```
    or validation errors:
    ```json
    {
      "video_file": ["This field is required."]
    }
    ```

#### 2. List Videos

- **Method**: `GET`
- **URL**: `/api/videos/`
- **Description**: Retrieves a list of all uploaded videos.
- **Response**:

  - **200 OK**:

    ```json
        [
            {
                "id": 1,
                "title": "Sample Video 1",
                "video_file": "http://127.0.0.1:8000/media/videos/test1.mkv",
                "uploaded_at": "2024-09-20T14:36:47.577811Z",
                "subtitles": [
                    {
                        "id": 1,
                        "language":
                         {
                            "id": 1,
                            "code": "en",
                            "name": "English"
                        },
                        "content": "Popeye the Sailor",
                        "video_id": 1,
                        "timestamp_start": "00:02.391",
                        "timestamp_end": "00:14.575"
                    },
                    {
                        ...
                    }
                ]

            },
            {
                "id": 2,
                "title": "Sample Video 2",
                "video_file": "http://127.0.0.1:8000/media/videos/test2.mkv",
                "uploaded_at":  "2024-09-20T14:40:47.475849Z",
                "subtitles": [
                    {
                        "id": 127,
                        "language": {
                            "id": 1,
                            "code": "en",
                            "name": "English"
                        },
                        "content": "and there's an extra cigar for each and every vote you give me, yes sir!",
                        "video_id": 2,
                        "timestamp_start": "00:00.990",
                        "timestamp_end": "00:05.820"
                }
            ]
        }
    ]
    ```

#### 3. Get Video Details

- **Method**: `GET`
- **URL**: `/api/videos/<video_id>/`
- **Description**: Retrieves detailed information about a specific video by its ID.
- **Response**:
  - **200 OK**:
    ```json
    {
      "id": 1,
      "title": "Sample Video 1",
      "video_file": "http://127.0.0.1:8000/media/videos/test1.mkv",
      "uploaded_at": "2024-09-20T14:36:47.577811Z",
      "subtitles": [
        ...
      ]
    }
    ```

#### 4. Get Subtitles for a Video

- **Method**: `GET`
- **URL**: `/api/videos/<video_id>/subtitles/`
- **Description**: Retrieves all subtitles associated with a specific video.
- **Response**:
  - **200 OK**:
    ```json
    [
      {
        "id": 1,
        "language": {
          "id": 1,
          "code": "en",
          "name": "English"
        },
        "content": "Popeye the Sailor",
        "video_id": 1,
        "timestamp_start": "00:02.391",
        "timestamp_end": "00:14.575"
      },
      {
        "id": 2,
        "language": {
          "id": 1,
          "code": "en",
          "name": "English"
        },
        "content": "Popeye for President",
        "video_id": 1,
        "timestamp_start": "00:17.658",
        "timestamp_end": "00:23.177"
      },
      {
        "id": 43,
        "language": {
          "id": 2,
          "code": "ru",
          "name": "Russian"
        },
        "content": "Моряк Попай",
        "video_id": 1,
        "timestamp_start": "00:02.391",
        "timestamp_end": "00:14.575"
      },
      {
        "id": 85,
        "language": {
          "id": 3,
          "code": "ja",
          "name": "Japanese"
        },
        "content": "ポパイ・ザ・セーラーマン",
        "video_id": 1,
        "timestamp_start": "00:02.391",
        "timestamp_end": "00:14.575"
      }
    ]
    ```

#### 5. Search Subtitles

- **Method**: `GET`
- **URL**: `/api/videos/<video_id>/subtitles/search/?q=<query>&lang=<language>`
- **Description**: Searches for subtitles containing a specific phrase and returns matching subtitles with timestamps.
- **Query Parameters**:
  - `q`: (string, required) The search query.
  - `lang`: (string, optional) The language code (this example shows for English but you can test for other languages also).
- **Response**:
  - **200 OK**:
    ```json
    [
      {
        "id": 1,
        "language": {
          "id": 1,
          "code": "en",
          "name": "English"
        },
        "content": "Popeye the Sailor",
        "video_id": 1,
        "timestamp_start": "00:02.391",
        "timestamp_end": "00:14.575"
      },
      {
        "id": 2,
        "language": {
          "id": 1,
          "code": "en",
          "name": "English"
        },
        "content": "Popeye for President",
        "video_id": 1,
        "timestamp_start": "00:17.658",
        "timestamp_end": "00:23.177"
      },
      {
        "id": 4,
        "language": {
          "id": 1,
          "code": "en",
          "name": "English"
        },
        "content": "a vote for Popeye means free ice cream for all the kiddies!",
        "video_id": 1,
        "timestamp_start": "00:28.514",
        "timestamp_end": "00:33.442"
      },
      {
        "id": 35,
        "language": {
          "id": 1,
          "code": "en",
          "name": "English"
        },
        "content": "Popeye, I'm casting my vote for you!",
        "video_id": 1,
        "timestamp_start": "04:33.427",
        "timestamp_end": "04:37.599"
      },
      {
        "id": 40,
        "language": {
          "id": 1,
          "code": "en",
          "name": "English"
        },
        "content": "Get in there babe and vote for ... Popeye!",
        "video_id": 1,
        "timestamp_start": "05:29.661",
        "timestamp_end": "05:32.294"
      }
    ]
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "No subtitles found for the query."
    }
    ```

### Error Handling

The API will return appropriate error responses for invalid requests or internal server errors. Common error responses include:

- **400 Bad Request**: Returned for validation errors or bad input.
- **404 Not Found**: Returned when a requested resource cannot be found.

---

### Screenshots

Included a folder named `/screenshots` in the project directory with screenshots of the application in use.
