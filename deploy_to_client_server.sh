#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt for input with a default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local response

    read -p "${prompt} [${default}]: " response
    echo "${response:-$default}"
}

# Function to execute SSH command
ssh_execute() {
    if [ "$use_password" = true ]; then
        sshpass -p "$ssh_password" ssh -o StrictHostKeyChecking=no "$ssh_user@$server_ip" "$1"
    else
        ssh -i "$ssh_key" -o StrictHostKeyChecking=no "$ssh_user@$server_ip" "$1"
    fi
}

# Prompt for client details
echo "Welcome to the Remote Client Deployment Wizard!"
echo "-----------------------------------------------"

client_name=$(prompt_with_default "Enter client name" "")
git_repo=$(prompt_with_default "Enter Git repository URL" "")
git_branch=$(prompt_with_default "Enter Git branch" "main")

server_ip=$(prompt_with_default "Enter server IP address" "")
ssh_user=$(prompt_with_default "Enter SSH user" "root")
domain_name=$(prompt_with_default "Enter domain name" "lms.learnknowdigital.com")

# Prompt for authentication method
read -p "Use password authentication? (y/n): " use_password_input
use_password=$([ "$use_password_input" = "y" ] && echo true || echo false)

if [ "$use_password" = true ]; then
    read -s -p "Enter SSH password: " ssh_password
    echo
    if ! command_exists sshpass; then
        echo "Error: sshpass is not installed. Please install it to use password authentication."
        exit 1
    fi
else
    ssh_key=$(prompt_with_default "Enter path to SSH key" "~/.ssh/id_rsa")
fi

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
echo "Server IP: $server_ip"
echo "SSH User: $ssh_user"
echo "Domain Name: $domain_name"
if [ "$use_password" = true ]; then
    echo "Authentication: Password-based"
else
    echo "Authentication: SSH Key-based"
    echo "SSH Key: $ssh_key"
fi
echo "Database Name: $db_name"
echo "Database User: $db_user"
echo "Database Password: $db_password"

read -p "Are these details correct? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Deployment cancelled. Please run the script again."
    exit 1
fi

# Check if the server has Docker and Docker Compose installed
echo "Checking for Docker and Docker Compose on the remote server..."
if ! ssh_execute 'command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1'; then
    echo "Error: Docker and/or Docker Compose are not installed on the remote server."
    echo "Please install them before proceeding with the deployment."
    exit 1
fi

# Clone the repository on the remote server
echo "Cloning the repository on the remote server..."
if ! ssh_execute "git clone -b $git_branch $git_repo ~/${client_name}"; then
    echo "Error: Failed to clone the repository. Please check the repository URL and your access rights."
    exit 1
fi

# Create Docker Compose file for the client
echo "Creating Docker Compose file..."
if ! ssh_execute "cat << EOF > ~/${client_name}/docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: sh -c \"
      python manage.py makemigrations &&
      python manage.py migrate &&
      if [ ! -f /code/.initial_data_loaded ]; then
        python manage.py setup_initial_data &&
        touch /code/.initial_data_loaded;
      fi &&
      python manage.py collectstatic --noinput &&
      gunicorn lms.wsgi:application --bind 0.0.0.0:8000
    \"
    volumes:
      - .:/code
      - static_volume:/code/staticfiles
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
EOF"; then
    echo "Error: Failed to create Docker Compose file."
    exit 1
fi

# Create Gunicorn socket file
echo "Creating Gunicorn socket file..."
if ! ssh_execute "sudo tee /etc/systemd/system/gunicorn_${client_name}.socket > /dev/null << EOF
[Unit]
Description=gunicorn socket for ${client_name}

[Socket]
ListenStream=/run/gunicorn_${client_name}.sock

[Install]
WantedBy=sockets.target
EOF"; then
    echo "Error: Failed to create Gunicorn socket file."
    exit 1
fi

# Create Gunicorn service file
echo "Creating Gunicorn service file..."
if ! ssh_execute "sudo tee /etc/systemd/system/gunicorn_${client_name}.service > /dev/null << EOF
[Unit]
Description=gunicorn daemon for ${client_name}
Requires=gunicorn_${client_name}.socket
After=network.target

[Service]
User=${ssh_user}
Group=www-data
WorkingDirectory=/${ssh_user}/${client_name}
ExecStart=/usr/local/bin/docker-compose -f /${ssh_user}/${client_name}/docker-compose.yml up web

[Install]
WantedBy=multi-user.target
EOF"; then
    echo "Error: Failed to create Gunicorn service file."
    exit 1
fi

# Start and enable Gunicorn socket
echo "Starting and enabling Gunicorn socket..."
if ! ssh_execute "sudo systemctl start gunicorn_${client_name}.socket && sudo systemctl enable gunicorn_${client_name}.socket"; then
    echo "Error: Failed to start and enable Gunicorn socket."
    exit 1
fi

# Create Nginx configuration
echo "Creating Nginx configuration..."
if ! ssh_execute "sudo tee /etc/nginx/sites-available/${client_name} > /dev/null << EOF
server {
    server_name ${domain_name};
    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        alias /var/www/${client_name}/staticfiles/;
    }
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn_${client_name}.sock;
    }
}
EOF"; then
    echo "Error: Failed to create Nginx configuration."
    exit 1
fi

# Enable Nginx configuration
echo "Enabling Nginx configuration..."
if ! ssh_execute "sudo ln -s /etc/nginx/sites-available/${client_name} /etc/nginx/sites-enabled/ && sudo nginx -t"; then
    echo "Error: Failed to enable Nginx configuration."
    exit 1
fi

# Restart Nginx
echo "Restarting Nginx..."
if ! ssh_execute "sudo systemctl restart nginx"; then
    echo "Error: Failed to restart Nginx."
    exit 1
fi

# Configure firewall
echo "Configuring firewall..."
if ! ssh_execute "sudo ufw allow 'Nginx Full'"; then
    echo "Error: Failed to configure firewall."
    exit 1
fi

# Start the Docker containers
echo "Starting Docker containers on the remote server..."
if ! ssh_execute "cd ~/${client_name} && docker-compose up -d --build"; then
    echo "Error: Failed to start Docker containers."
    exit 1
fi

# Restart Gunicorn
echo "Restarting Gunicorn..."
if ! ssh_execute "sudo systemctl daemon-reload && sudo systemctl restart gunicorn_${client_name}"; then
    echo "Error: Failed to restart Gunicorn."
    exit 1
fi

echo "Deployment completed successfully!"
echo "You can access the application at http://${domain_name}"
echo "The client's code is located in ~/${client_name} on the remote server"
echo "Static files are located in /var/www/${client_name}/staticfiles on the remote server"