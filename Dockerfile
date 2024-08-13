FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y nodejs npm netcat-traditional

COPY . /code/

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lms.wsgi:application"]