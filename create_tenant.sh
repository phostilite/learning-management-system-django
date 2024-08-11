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

# Prompt for tenant details
echo "Welcome to the Tenant Creation Wizard!"
echo "--------------------------------------"

client_name=$(prompt_with_default "Enter client name" "client1")
git_repo=$(prompt_with_default "Enter Git repository URL" "https://github.com/yourusername/your-repo.git")
git_branch=$(prompt_with_default "Enter Git branch" "main")

# Ask if the client wants to deploy locally or remotely
read -p "Deploy locally or remotely? (local/remote): " deploy_type

if [ "$deploy_type" = "remote" ]; then
    # Call the remote deployment script
    ./deploy_to_client_server.sh "$client_name" "$git_repo" "$git_branch"
    exit 0
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
mkdir -p ../${client_name}
git clone -b "$git_branch" "$git_repo" ../${client_name}

# Create Docker Compose file for the tenant
cat << EOF > ../${client_name}/docker-compose.yml
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
      exec python manage.py runserver 0.0.0.0:8000
     "
    volumes:
      - .:/code
      - initial_data_flag:/code
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
  initial_data_flag:
EOF

# Start the tenant's container
cd ../${client_name}
docker-compose up -d

echo "Tenant ${client_name} created successfully!"
echo "You can access the application at http://localhost:${port}"
echo "The tenant's code is located in ../${client_name}"