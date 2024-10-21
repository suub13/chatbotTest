-- Create the chatbot database if it doesn't exist
-- DROP DATABASE chatbot;
CREATE DATABASE IF NOT EXISTS chatbot;

-- Use the chatbot database
USE chatbot;


-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    chat_type varchar(10) not null,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP not null
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
