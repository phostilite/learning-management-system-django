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

client_name="$1"
git_repo="$2"
git_branch="$3"

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

# Clone the repository on the remote server
echo "Cloning the repository on the remote server..."
ssh_execute "git clone -b $git_branch $git_repo ~/${client_name}"

# Copy Docker Compose file
echo "Creating Docker Compose file..."
ssh_execute "cat << EOF > ~/${client_name}/docker-compose.yml
services:
  web:
    build: .
    volumes:
      - .:/code
      - static_volume:/code/staticfiles
    environment:
      - DB_NAME=${db_name}
      - DB_USER=${db_user}
      - DB_PASSWORD=${db_password}
    depends_on:
      - db
    command: >
      sh -c \"
        python manage.py makemigrations &&
        python manage.py migrate &&
        if [ ! -f /code/.initial_data_loaded ]; then
          python manage.py setup_initial_data &&
          touch /code/.initial_data_loaded;
        fi &&
        python manage.py collectstatic --noinput &&
        gunicorn lms.wsgi:application --bind 0.0.0.0:8000
      \"

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${db_name}
      - POSTGRES_USER=${db_user}
      - POSTGRES_PASSWORD=${db_password}

  nginx:
    image: nginx:latest
    ports:
      - \"80:80\"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/code/staticfiles
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
EOF"

# Create Nginx configuration
echo "Creating Nginx configuration..."
ssh_execute "cat << EOF > ~/${client_name}/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream django {
        server web:8000;
    }

    server {
        listen 80;
        server_name ${domain_name};

        location / {
            proxy_pass http://django;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header Host \$host;
            proxy_redirect off;
        }

        location /static/ {
            alias /code/staticfiles/;
        }
    }
}
EOF"

# Set up environment variables
echo "Setting up environment variables..."
ssh_execute "cat << EOF > ~/${client_name}/.env
DB_NAME=${db_name}
DB_USER=${db_user}
DB_PASSWORD=${db_password}
EOF"

# Install Docker and Docker Compose if not already installed
echo "Ensuring Docker and Docker Compose are installed..."
ssh_execute '
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi
'

# Start the Docker containers
echo "Starting Docker containers on the remote server..."
ssh_execute "cd ~/${client_name} && docker-compose up -d --build"

# Configure firewall
echo "Configuring firewall..."
ssh_execute '
if command -v ufw > /dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
    else
        echo "UFW is installed but not active. Skipping firewall configuration."
    fi
else
    echo "UFW is not installed. Skipping firewall configuration."
fi
'

echo "Deployment completed successfully!"
echo "You can access the application at http://${domain_name}"
echo "The client's code is located in ~/${client_name} on the remote server"