FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y nodejs npm netcat-traditional

COPY . /code/

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN npm install

RUN mkdir -p /code/static/dist/css /code/static/dist/js
RUN echo '@tailwind base;\n@tailwind components;\n@tailwind utilities;' > /code/static/dist/css/input.css

RUN cp -r node_modules/flowbite/dist/*.js /code/static/dist/js/ || true
RUN cp -r node_modules/flowbite/dist/*.css /code/static/dist/css/ || true
RUN cp -r node_modules/flowbite-datepicker/dist/*.js /code/static/dist/js/ || true
RUN cp -r node_modules/flowbite-datepicker/dist/*.css /code/static/dist/css/ || true
RUN cp -r node_modules/leaflet/dist/*.js /code/static/dist/js/ || true
RUN cp -r node_modules/leaflet/dist/*.css /code/static/dist/css/ || true
RUN cp -r node_modules/animejs/lib/*.js /code/static/dist/js/ || true
RUN cp -r node_modules/chart.js/dist/*.js /code/static/dist/js/ || true

RUN npx tailwindcss -i /code/static/dist/css/input.css -o /code/static/dist/css/output.css --minify

RUN find /code

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lms.wsgi:application"]