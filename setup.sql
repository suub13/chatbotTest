-- Create the chatbot database if it doesn't exist
-- DROP DATABASE chatbot;
CREATE DATABASE IF NOT EXISTS chatbot;

-- Use the chatbot database
USE chatbot;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL, 
    password VARCHAR(255) NOT NULL,
    sex CHAR(1) CHECK (sex IN ('f', 'm')) NOT NULL, 
    age INT NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    chat_type varchar(10) not null,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP not null,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT,
    sender VARCHAR(5),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
