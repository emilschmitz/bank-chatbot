# RAG Bank Chatbot

A chatbot designed to assist with Sparkassen documents using Redis and Ollama for efficient data retrieval and language processing.

## Features

  ⚠️ **Note that this chatbot is a prototype and says a lot of nonsensical things. That's maybe because we use a rather small model, for it to run locally on a laptop.**

Nonetheless, it has all the following features:

- **Document Ingestion:** Automatically downloads, converts, and indexes Sparkassen documents.
- **Vector Search:** Utilizes Redis for fast and relevant document retrieval based on user queries.
- **Interactive Chat:** Engages users in natural language conversations.
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
      ⚠️ **It may take some time for this command to finish, without there being a whole lot of console logging**.

   This command will:

   - Build the necessary Docker images.
   - Start the Ollama and Redis services.
   - Download the Llama3.2:1b from Ollama.
   - Ingest Sparkasse documents into Redis.
   - Launch the chatbot in interactive mode.
  
3. **(Optional) Langsmith tracking**:

   If you want to use Langsmith to track your conversations, add a file named `secrets.env` to the base directory and enter `LANGCHAIN_API_KEY=<your-key>`.

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
