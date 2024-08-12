#!/bin/bash

# Function to prompt for input with a default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local response

    read -p "${prompt} [${default}]: " response
    echo "${response:-$default}"
}

# Function to find an available port
find_available_port() {
    local port=8000
    while nc -z localhost $port >/dev/null 2>&1; do
        port=$((port+1))
    done
    echo $port
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Nginx configuration
check_nginx() {
    if ! command_exists nginx; then
        echo "Error: Nginx is not installed."
        return 1
    fi

    if ! nginx -t >/dev/null 2>&1; then
        echo "Error: Nginx configuration test failed."
        return 1
    fi

    echo "Nginx is installed and configured correctly."
    return 0
}

# Function to check and setup Gunicorn
setup_gunicorn() {
    local client_name="$1"
    local project_dir="/home/$USER/${client_name}"
    local venv_dir="/opt/venv"  # Using the VIRTUAL_ENV from Dockerfile

    # Check if Gunicorn is installed in the virtual environment
    if ! $venv_dir/bin/pip freeze | grep -q gunicorn; then
        echo "Error: Gunicorn is not installed in the virtual environment."
        return 1
    fi

    # Create Gunicorn socket file
    sudo tee /etc/systemd/system/gunicorn_${client_name}.socket > /dev/null << EOF
[Unit]
Description=gunicorn socket for ${client_name}

[Socket]
ListenStream=/run/gunicorn_${client_name}.sock

[Install]
WantedBy=sockets.target
EOF

    # Create Gunicorn service file
    sudo tee /etc/systemd/system/gunicorn_${client_name}.service > /dev/null << EOF
[Unit]
Description=gunicorn daemon for ${client_name}
Requires=gunicorn_${client_name}.socket
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=${project_dir}
ExecStart=${venv_dir}/bin/gunicorn \\
          --access-logfile - \\
          --workers 3 \\
          --bind unix:/run/gunicorn_${client_name}.sock \\
          ${client_name}.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

    # Start and enable Gunicorn socket
    sudo systemctl start gunicorn_${client_name}.socket
    sudo systemctl enable gunicorn_${client_name}.socket

    # Check if Gunicorn socket file exists
    if [ ! -e /run/gunicorn_${client_name}.sock ]; then
        echo "Error: Gunicorn socket file not created."
        return 1
    fi

    echo "Gunicorn setup completed successfully for ${client_name}."
    return 0
}

# Main script starts here
echo "Welcome to the Enhanced Tenant Creation Wizard!"
echo "-----------------------------------------------"

# Check Nginx configuration
if ! check_nginx; then
    echo "Please fix Nginx configuration before proceeding."
    exit 1
fi

client_name=$(prompt_with_default "Enter client name" "client1")
git_repo=$(prompt_with_default "Enter Git repository URL" "https://github.com/yourusername/your-repo.git")
git_branch=$(prompt_with_default "Enter Git branch" "main")

# Ask if the client wants to deploy locally or remotely
read -p "Deploy locally or remotely? (local/remote): " deploy_type

if [ "$deploy_type" = "remote" ]; then
    echo "Remote deployment is not implemented in this script."
    exit 1
fi

# Continue with local deployment
port=$(find_available_port)

# Database configuration
echo "Database Configuration:"
db_name=$(prompt_with_default "Enter database name" "${client_name}_db")
db_user=$(prompt_with_default "Enter database user" "postgres")
db_password=$(prompt_with_default "Enter database password" "postgres")

# Confirm details
echo -e "\nPlease confirm the following details:"
echo "Client Name: $client_name"
echo "Git Repository: $git_repo"
echo "Git Branch: $git_branch"
echo "Port: $port"
echo "Database Name: $db_name"
echo "Database User: $db_user"
echo "Database Password: $db_password"

read -p "Are these details correct? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Tenant creation cancelled. Please run the script again."
    exit 1
fi

# Create client directory and clone the repository
mkdir -p /home/$USER/${client_name}
git clone -b "$git_branch" "$git_repo" /home/$USER/${client_name}

# Create Docker Compose file for the client
echo "Creating Docker Compose file..."
cat << EOF > /home/$USER/${client_name}/docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: sh -c "
      python manage.py makemigrations &&
      python manage.py migrate &&
      if [ ! -f /code/.initial_data_loaded ]; then
        python manage.py setup_initial_data &&
        touch /code/.initial_data_loaded;
      fi &&
      python manage.py collectstatic --noinput &&
      gunicorn ${client_name}.wsgi:application --bind 0.0.0.0:8000
    "
    volumes:
      - .:/code
      - static_volume:/code/staticfiles
    ports:
      - "${port}:8000"
    environment:
      - DB_NAME=${db_name}
      - DB_USER=${db_user}
      - DB_PASSWORD=${db_password}
    depends_on:
      - db

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${db_name}
      - POSTGRES_USER=${db_user}
      - POSTGRES_PASSWORD=${db_password}

volumes:
  postgres_data:
  static_volume:
EOF

# Setup Gunicorn
if ! setup_gunicorn "$client_name"; then
    echo "Error: Failed to setup Gunicorn."
    exit 1
fi

# Create Nginx configuration file
sudo tee /etc/nginx/sites-available/${client_name} > /dev/null << EOF
server {
    server_name ${client_name}.example.com;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/$USER/${client_name}/staticfiles/;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_${client_name}.sock;
    }
}
EOF

# Enable the Nginx site
sudo ln -s /etc/nginx/sites-available/${client_name} /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

if [ $? -ne 0 ]; then
    echo "Error: Nginx configuration test failed."
    exit 1
fi

# Restart Nginx
sudo systemctl restart nginx

# Start the Docker containers
echo "Starting Docker containers..."
cd /home/$USER/${client_name} && docker-compose up -d --build

# Copy static files from Docker container to host
echo "Copying static files from Docker container to host..."
docker cp $(docker-compose ps -q web):/code/staticfiles /home/$USER/${client_name}/

# Update permissions for the copied static files
echo "Updating permissions for static files..."
sudo chmod -R 755 /home/$USER/${client_name}/staticfiles

echo "Deployment completed successfully!"
echo "You can access the application at http://localhost:${port}"
echo "The client's code is located in /home/$USER/${client_name}"
echo "Static files are located in /home/$USER/${client_name}/staticfiles"
echo "Don't forget to update your DNS settings to point ${client_name}.example.com to your server's IP address."