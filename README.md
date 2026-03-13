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
│   ├── api/            # Local FastAPI backend (inference server/dispatcher)
│   ├── bot/            # Cloud-hosted Telegram bot (aiogram)
│   ├── shared/         # Shared services (Google Drive, whitelist)
│   └── workers/        # Cloud batch processing adapters (Colab/Kaggle)
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
    - Create a `.env` file in the project root. You can copy `src/api/dispatcher.env.example` and fill in the values for `GOOGLE_DRIVE_CREDENTIALS_FILE_PATH` and `WHITELIST_FILE_ID`.

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

## Docker Deployment (Recommended for Cloud)

For a streamlined setup on your cloud server (e.g., Oracle Cloud), you can use Docker and Docker Compose. This packages both the Dispatcher API and the Telegram Bot into isolated containers.

### Prerequisites
- Docker and Docker Compose installed on the host.
- A `.env` file and `gdrive_credentials.json` in the project root.

### Steps
1.  **Prepare Configuration**: Ensure your `.env` file contains all necessary tokens and the `WHITELIST_FILE_ID`.
2.  **Start Services**:
    ```bash
    docker-compose up -d --build
    ```
3.  **Logs**: Monitor output using `docker-compose logs -f`.

## Minimalist Deployment (systemd - Alternative for < 1GB RAM)

If you are running on a very limited VM (like Oracle Cloud `Micro` instance with 1GB RAM), it is recommended to use `systemd` to avoid Docker's memory overhead. We strongly recommend using **Ubuntu** instead of Oracle Linux to avoid SELinux and strict user directory permission issues.

See the detailed guide and service files in [deployment/systemd/](deployment/systemd/).

### Summary of Steps
1.  **Setup Virtualenv**: Create a `venv` and install requirements. *Note: Use `src/api/requirements-dispatcher.txt` for the API to avoid compiling heavy ML libraries on the cloud server.*
2.  **Configure Environment**: Create `api.env` and `bot.env` in the root folder with absolute paths to your credentials.
3.  **Install Services**:
    ```bash
    sudo cp deployment/systemd/*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable roentgen-api roentgen-bot
    sudo systemctl start roentgen-api roentgen-bot
    ```

## Worker Infrastructure

The system supports multiple worker types for model inference.

### 1. Local Python Worker
Runs on your local machine with a GPU. Use this for real-time single-image analysis.
```bash
uvicorn src.api.worker:app --host 127.0.0.1 --port 8001
```
The Dispatcher API will route requests here if configured in `INFERENCE_WORKERS` (e.g., `http://127.0.0.1:8080/infer` via SSH tunnel).

### 2. Native C++ Worker (llama-server)
For maximum efficiency and lowest VRAM usage, bypass the Python worker and use the pre-compiled `llama-server`. The Dispatcher automatically detects OpenAI-compatible endpoints.
```bash
./llama-server -m models/medgemma-1.5-4b.gguf --mmproj models/mmproj-model-f16.gguf -c 2048 --port 8001 --host 127.0.0.1
```
Configure `api.env` to point to the completions endpoint: `http://127.0.0.1:8080/v1/chat/completions`.

### 3. Cloud Batch Worker (Colab/Kaggle)
Designed for ephemeral cloud GPUs. It polls Google Drive for batches of images, processes them, and uploads JSON reports.
1.  Upload the project code and models to your notebook.
2.  Set environment variables `GOOGLE_DRIVE_CREDENTIALS_JSON` and `GDRIVE_BATCH_FOLDER_ID`.
3.  Run the adapter:
    ```bash
    python src/workers/cloud_adapter.py
    ```

## Usage

Open Telegram and send the `/start` command to your bot. If your user ID is correctly whitelisted in the Google Drive JSON config, the bot will respond. Use `/analyze` to start a batch upload session for remote cloud workers.

## Whitelist Configuration

The Google Drive JSON file acts as the central source of truth for access control and user preferences. It must be a strictly valid JSON object.

Here is an exemplary, fully-documented whitelist:

```json
{
  "users": {
    "123456789": {
      "name": "Dr. House",
      "role": "admin",
      "is_active": true,
      "system_prompt_type": 1,
      "allowed_workers": ["local_python", "cloud_batch"],
      "daily_limit": 50,
      "specialty": "Radiology",
      "show_thoughts": true
    },
    "987654321": {
      "name": "Dr. Watson",
      "role": "user",
      "is_active": true,
      "system_prompt_type": 2,
      "allowed_workers": ["local_python"],
      "show_thoughts": false
    }
  },
  "prompts": {
    "1": {
      "description": "Standard Radiologist",
      "content": "You are an expert radiologist AI assistant. Be highly concise, factual, and direct."
    },
    "2": {
      "description": "Pediatric Radiologist",
      "content": "You are an expert pediatric radiologist. Tailor your language for pediatric cases."
    }
  }
}
```

### User Parameters
- `name` *(string)*: Display name for the user.
- `role` *(string)*: User role (`"admin"` or `"user"`). Admins can use the `/refresh_whitelist` command.
- `is_active` *(boolean)*: Set to `false` to instantly revoke bot access for the user.
- `system_prompt_type` *(integer)*: Links the user to a specific system prompt defined in the `"prompts"` section. Defaults to `1`.
- `allowed_workers` *(list of strings)*: Restricts which inference routes the user can access (e.g., `["local_python"]`). If empty or omitted, all configured routes are allowed.
- `daily_limit` *(integer)*: (Future use) Maximum number of requests allowed per day.
- `specialty` *(string)*: (Future use) Medical specialty of the user for analytics.
- `show_thoughts` *(boolean)*: If `true`, the bot will display the AI's internal reasoning (e.g., `<think>` tags or JSON thought blocks) before the final answer. Defaults to `false`.

## Troubleshooting

### Deployment: Oracle Linux vs Ubuntu
If deploying on Oracle Cloud Free Tier, **always choose the Ubuntu image**. Oracle Linux comes with aggressive SELinux policies that block `systemd` from executing scripts inside user directories (`/home/opc/`), leading to `203/EXEC` and `Permission denied` errors.

### Reverse SSH Tunnel: `Connection refused`
When creating the reverse SSH tunnel from your Local Server, you might encounter a `ssh: connect to host <your-cloud-server-ip> port 22: Connection refused` error. Ensure your cloud firewall (e.g., `ufw`) allows SSH traffic on port 22.

### Reverse SSH Tunnel: `Warning: remote port forwarding failed for listen port 8080`
This happens when an old, disconnected SSH session is still holding port 8080 open on your cloud server. 

#### 1. Automatic Server-Side Cleanup
To ensure the server automatically kills dead tunnel sessions and frees up ports, create a configuration file on your **Cloud Server**:
```bash
sudo tee /etc/ssh/sshd_config.d/tunnel-cleanup.conf <<EOF
ClientAliveInterval 30
ClientAliveCountMax 2
EOF
sudo systemctl restart ssh
```

#### 2. Automatic Client-Side Reconnection
On your **Local Machine**, use a loop script to automatically reconnect if the tunnel drops or the port is temporarily busy. Save this as `start_tunnel.sh`:
```bash
#!/bin/bash
while true; do
    echo "[$(date)] Attempting to open tunnel..."
    ssh -i /path/to/key.key -R 8080:127.0.0.1:8001 ubuntu@<cloud-ip> \
        -N \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=2 \
        -o ExitOnForwardFailure=yes
    echo "[$(date)] Tunnel dropped or port busy. Retrying in 10s..."
    sleep 10
done
```
Make it executable: `chmod +x start_tunnel.sh`. 

The `-o ExitOnForwardFailure=yes` flag is critical: it forces the SSH client to exit if it cannot bind the remote port, allowing the script to retry until the server frees it.
