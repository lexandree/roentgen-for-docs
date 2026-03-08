# Roentgen for Docs - MedGemma Diagnostic Bot

This project provides a secure, two-part system for medical image analysis using MedGemma. It consists of a local, GPU-powered backend for model inference and a cloud-hosted Telegram bot that acts as the user-facing interface. The two components are connected via a secure reverse SSH tunnel, ensuring that sensitive medical data remains on your local machine.

## Core Features

- **Secure by Design**: Images and prompts are processed on your local server. The cloud-based bot only handles communication with Telegram.
- **Strict Whitelisting**: Access is controlled via a dual-whitelist system (local database and a centrally-managed Google Drive file).
- **Text and Image Analysis**: Users can engage in text-based medical discussions or upload X-ray/MRI images for diagnostic analysis.
- **Session Management**: Conversations are isolated per user, with automatic session clearing for privacy.
- **Multi-Modal Interaction**: Users can upload an image at any point in a conversation to add visual context.

## Project Structure

```
.
├── specs/              # Feature specifications and planning documents
├── src/
│   ├── api/            # Local FastAPI backend (inference server)
│   └── bot/            # Cloud-hosted Telegram bot (aiogram)
└── tests/              # Unit and integration tests
```

## System Setup

This project requires two separate environments: a **Local Server** with GPU access for the model and a **Cloud Server** to run the public-facing Telegram bot.

### 1. Local Server Setup (FastAPI Backend)

This machine runs the MedGemma model and handles all AI processing.

1.  **Prerequisites**:
    - A Linux machine with a CUDA-compatible GPU.
    - Python 3.12+ and Conda installed.
    - MedGemma 1.5 model weights.

2.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd roentgen_for_docs
    ```

3.  **Create Conda Environment**:
    ```bash
    conda create -n medgemma python=3.12
    conda activate medgemma
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r src/api/requirements.txt
    ```

5.  **Configure Credentials**:
    - Create a file named `gdrive_credentials.json` in the project root and paste your Google Drive Service Account JSON key into it.
    - Create a `.env` file in the project root. You can copy `src/api/.env.example` and fill in the values for `GOOGLE_DRIVE_CREDENTIALS_FILE_PATH` and `WHITELIST_FILE_ID`.

6.  **Initialize Database**:
    Run the script to set up the local database and add your Telegram user ID to the whitelist:
    ```bash
    python src/api/scripts/init_db.py --add-user YOUR_TELEGRAM_ID --name "Your Name"
    ```

### 2. Cloud Server Setup (Telegram Bot)

This machine runs the Telegram bot and forwards requests to your local server. A free-tier cloud instance (e.g., Oracle Cloud) is sufficient.

1.  **Prerequisites**:
    - A cloud server with Python 3.12+.
    - A registered Telegram Bot Token from BotFather.

2.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd roentgen_for_docs
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r src/bot/requirements.txt
    ```

4.  **Configure Credentials**:
    - Upload your `gdrive_credentials.json` file to the project root on the cloud server.
    - Create a `.env` file in the project root. You can copy `src/bot/.env.example` and fill in your `TELEGRAM_BOT_TOKEN`, `WHITELIST_FILE_ID`, and other relevant values. Ensure `LOCAL_API_URL` is set to `http://127.0.0.1:8000/api/v1`.

## Running the Application

1.  **Start the Secure Tunnel**:
    From your **Local Server**, open a reverse SSH tunnel to your cloud instance. This securely exposes your local API to the cloud bot.
    ```bash
    ssh -R 8000:localhost:8000 user@your-cloud-server-ip -N -f
    ```

2.  **Start the Local API Server**:
    On your **Local Server**, start the FastAPI application:
    ```bash
    uvicorn src.api.main:app --host 127.0.0.1 --port 8000
    ```

3.  **Start the Telegram Bot**:
    On your **Cloud Server**, start the bot. Remember to use the `-m` flag to run it as a module to ensure correct pathing.
    ```bash
    python -m src.bot.main
    ```

## Usage

Open Telegram and send the `/start` command to your bot. If your user ID is correctly whitelisted, the bot will respond, and you can begin sending text queries or uncompressed images for analysis.
