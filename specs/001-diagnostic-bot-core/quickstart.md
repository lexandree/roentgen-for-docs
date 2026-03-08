# Quickstart: Diagnostic Bot Core

## Prerequisites
- **Local Server**: Linux machine with a CUDA-compatible GPU, Python 3.12+, Conda, and MedGemma 1.5 weights.
- **Cloud Server**: Oracle Cloud Free Tier instance, Python 3.12+.
- **Telegram**: A registered Telegram Bot Token from BotFather.
- **Google Drive**: A Service Account credentials JSON file and the File ID of your whitelist text file.

## 1. Local Server Setup (Backend)

1.  **Clone the repository** on your local machine.

2.  **Create and activate a Conda environment:**
    ```bash
    conda create -n medgemma python=3.12
    conda activate medgemma
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r src/api/requirements.txt
    ```

4.  **Create `gdrive_credentials.json`:**
    In the root of the project, create a file named `gdrive_credentials.json` and paste your full, multi-line Service Account JSON key into it.

5.  **Create `.env` file:**
    In the root of the project, create a file named `.env` with the following content, replacing the placeholder values:
    ```env
    # .env file for the Local API Server
    GOOGLE_DRIVE_CREDENTIALS_FILE_PATH="gdrive_credentials.json"
    WHITELIST_FILE_ID="your_gdrive_file_id_here"
    ```

6.  **Initialize the database and add yourself to the whitelist:**
    From the project root, run:
    ```bash
    python src/api/scripts/init_db.py --add-user YOUR_TELEGRAM_ID --name "Your Name"
    ```

7.  **Start the FastAPI server:**
    From the project root, run:
    ```bash
    uvicorn src.api.main:app --host 127.0.0.1 --port 8000
    ```

## 2. Secure Tunnel Setup

From your local server, initiate a Reverse SSH Tunnel to your Oracle Cloud instance to expose port 8000:
```bash
ssh -R 8000:localhost:8000 user@oracle-cloud-ip -N -f
```

## 3. Cloud Server Setup (Frontend)

1.  **Clone the repository** on your Oracle Cloud instance.

2.  **Create and activate a Conda/Venv environment** (Python 3.12+).

3.  **Install dependencies:**
    ```bash
    pip install -r src/bot/requirements.txt
    ```

4.  **Create `.env` file:**
    In the root of the project on your cloud server, create a file named `.env` with the following content:
    ```env
    # .env file for the Telegram Bot
    TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
    LOCAL_API_URL="http://127.0.0.1:8000/api/v1"

    # The following must be the same as on your local server
    GOOGLE_DRIVE_CREDENTIALS_FILE_PATH="gdrive_credentials.json"
    WHITELIST_FILE_ID="your_gdrive_file_id_here"
    ```
    *Note: You will also need to place a copy of your `gdrive_credentials.json` file in the project root on the cloud server.*

5.  **Start the bot:**
    From the project root, run:
    ```bash
    python src/bot/main.py
    ```

## 4. Usage
Send `/start` to your bot in Telegram. If your ID is whitelisted on both the local DB and the Google Drive file, the bot will accept your messages.