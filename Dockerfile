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

# Add debug commands
RUN echo "Contents of /code/static/dist:" && ls -R /code/static/dist

RUN cp -r node_modules/flowbite/dist/*.js /code/static/dist/js/ || true && \
    echo "Copied Flowbite JS to:" && ls -l /code/static/dist/js/*.js
RUN cp -r node_modules/flowbite/dist/*.css /code/static/dist/css/ || true && \
    echo "Copied Flowbite CSS to:" && ls -l /code/static/dist/css/*.css
RUN cp -r node_modules/flowbite-datepicker/dist/*.js /code/static/dist/js/ || true && \
    echo "Copied Flowbite Datepicker JS to:" && ls -l /code/static/dist/js/*datepicker*.js
RUN cp -r node_modules/flowbite-datepicker/dist/*.css /code/static/dist/css/ || true && \
    echo "Copied Flowbite Datepicker CSS to:" && ls -l /code/static/dist/css/*datepicker*.css
RUN cp -r node_modules/leaflet/dist/*.js /code/static/dist/js/ || true && \
    echo "Copied Leaflet JS to:" && ls -l /code/static/dist/js/*leaflet*.js
RUN cp -r node_modules/leaflet/dist/*.css /code/static/dist/css/ || true && \
    echo "Copied Leaflet CSS to:" && ls -l /code/static/dist/css/*leaflet*.css
RUN cp -r node_modules/animejs/lib/*.js /code/static/dist/js/ || true && \
    echo "Copied Anime.js to:" && ls -l /code/static/dist/js/*anime*.js
RUN cp -r node_modules/chart.js/dist/*.js /code/static/dist/js/ || true && \
    echo "Copied Chart.js to:" && ls -l /code/static/dist/js/*chart*.js

RUN npx tailwindcss -i /code/static/dist/css/input.css -o /code/static/dist/css/output.css --minify && \
    echo "Generated Tailwind CSS at:" && ls -l /code/static/dist/css/output.css

# Final debug command
RUN echo "Final contents of /code/static/dist:" && ls -R /code/static/dist

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lms.wsgi:application"]