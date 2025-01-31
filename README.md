# Sparkassen Chatbot

A powerful chatbot designed to assist with Sparkassen documents using Redis and Ollama for efficient data retrieval and language processing.

## Features

- **Document Ingestion:** Automatically downloads, converts, and indexes Sparkassen documents.
- **Vector Search:** Utilizes Redis for fast and relevant document retrieval based on user queries.
- **Interactive Chat:** Engages users in natural language conversations, providing precise answers using the indexed documents.
- **Dockerized Setup:** Easily deployable using Docker Compose for seamless environment management.

## Prerequisites

- **Docker:** Ensure Docker is installed on your Linux system. [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose:** Make sure Docker Compose is installed. [Install Docker Compose](https://docs.docker.com/compose/install/)

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/sparkassen-chatbot.git
   cd sparkassen-chatbot
   ```

2. **Start the Chatbot:**

   Simply run the following command to build and start the chatbot:

   ```bash
   docker compose run -it llm_rag
   ```

   This command will:

   - Build the necessary Docker images.
   - Start the Ollama and Redis services.
   - Download the Llama3.2:1b from Ollama
   - Ingest Sparkasse documents
   - Launch the chatbot in interactive mode.

## Usage

Once the chatbot is running, you can interact with it directly in your terminal:

```
============================================================
🏦 Willkommen bei Ihrem Sparkassen-Assistenten!
Ich kann Ihnen Fragen zu Sparkassen-Dokumenten beantworten.
Sie können jederzeit 'exit' eingeben, um zu beenden.
============================================================

➤ Hi

[Chatbot Response...]

➤ exit

Auf Wiedersehen! 👋
```

- **Ask Questions:** Type your queries related to Sparkassen documents.
- **Exit:** Type `exit`, `quit`, or `q` to terminate the session.
