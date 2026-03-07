# Quickstart: Diagnostic Bot Core

## Prerequisites
- **Local Server**: Linux machine with a CUDA-compatible GPU, Python 3.12+, Conda, and MedGemma 1.5 weights.
- **Cloud Server**: Oracle Cloud Free Tier instance, Python 3.12+.
- **Telegram**: A registered Telegram Bot Token from BotFather.

## 1. Local Server Setup (Backend)

1. Clone the repository on your local machine.
2. Create and activate a Conda environment:
   ```bash
   conda create -n medgemma python=3.12
   conda activate medgemma
   ```
3. Install dependencies:
   ```bash
   pip install -r src/api/requirements.txt
   ```
4. Initialize the SQLite database and add your Telegram ID to the whitelist:
   ```bash
   python src/api/scripts/init_db.py --add-user YOUR_TELEGRAM_ID
   ```
5. Start the FastAPI server:
   ```bash
   uvicorn src.api.main:app --host 127.0.0.1 --port 8000
   ```

## 2. Secure Tunnel Setup

From your local server, initiate a Reverse SSH Tunnel to your Oracle Cloud instance to expose port 8000:
```bash
ssh -R 8000:localhost:8000 user@oracle-cloud-ip -N -f
```

## 3. Cloud Server Setup (Frontend)

1. Clone the repository on your Oracle Cloud instance.
2. Create and activate a Conda/Venv environment (Python 3.12+).
3. Install dependencies:
   ```bash
   pip install -r src/bot/requirements.txt
   ```
4. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export LOCAL_API_URL="http://127.0.0.1:8000/api/v1"
   ```
5. Start the bot:
   ```bash
   python src/bot/main.py
   ```

## 4. Usage
Send `/start` to your bot in Telegram. If your ID is whitelisted, the bot will accept messages and images, forwarding them to your local MedGemma instance.