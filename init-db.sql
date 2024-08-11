-- Create database
CREATE DATABASE db_name;

-- Create user
CREATE USER db_user WITH PASSWORD 'db_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE db_name TO db_user;

-- Connect to the database
\c db_name

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO db_user;