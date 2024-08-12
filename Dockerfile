# Use an official Python runtime as a parent image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv

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

# Install npm packages including Tailwind CSS and Flowbite
COPY package.json package-lock.json* /code/
RUN npm install

# Copy project
COPY . /code/

# Create dist, css, and js folders
RUN mkdir -p /code/static/dist/css /code/static/dist/js

# Create input.css file with Tailwind directives
RUN echo '@tailwind base;@tailwind components;@tailwind utilities;' > /code/static/dist/css/input.css

# Copy Flowbite files (adjust paths if necessary)
RUN cp -r node_modules/flowbite/dist/*.js /code/static/dist/js/ || true
RUN cp -r node_modules/flowbite/dist/*.css /code/static/dist/css/ || true

# Run Tailwind CSS build
RUN npx tailwindcss -i /code/static/dist/css/input.css -o /code/static/dist/css/output.css --minify

# Install Gunicorn
RUN pip install gunicorn

# Expose port 8000
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lms.wsgi:application"]