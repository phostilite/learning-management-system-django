# Use an official Python runtime as a parent image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y nodejs npm netcat-traditional

# Create and activate virtual environment
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Tailwind CSS
RUN npm install -D tailwindcss@latest postcss@latest autoprefixer@latest

# Copy project
COPY . /code/

# Run Tailwind CSS build
RUN npx tailwindcss -i ./static/dist/css/input.css -o ./static/dist/css/output.css --minify

# Collect static files
RUN python manage.py collectstatic --noinput