# Roentgen for Docs - MedGemma Diagnostic Bot

This project provides a secure system for medical image analysis using MedGemma. It consists of a backend dispatcher, scalable inference workers, and a cloud-hosted Telegram bot that acts as the user-facing interface. The components are connected via a secure reverse SSH tunnel, ensuring that sensitive medical data remains private.

## Core Features

- **Secure by Design**: Images and prompts are processed on your dedicated server. The cloud-based bot only handles communication with Telegram.
- **Strict Whitelisting**: Access is controlled via a dual-whitelist system (local database and a centrally-managed Google Drive file).
- **Text and Image Analysis**: Users can engage in text-based medical discussions or upload X-ray/MRI images for diagnostic analysis.
- **Advanced Image Preprocessing**: Built-in interactive Region of Interest (ROI) commands significantly improve analysis quality.
- **Session Management**: Conversations are isolated per user, with automatic session clearing for privacy.
- **Administration & Statistics**: Comprehensive built-in dashboard commands for admins to monitor health and usage.

## Project Structure

```
.
├── specs/              # Feature specifications and planning documents
├── src/
│   ├── api/            # FastAPI backend (dispatcher/routing)
│   ├── bot/            # Cloud-hosted Telegram bot (aiogram)
│   ├── shared/         # Shared services (Google Drive, whitelist)
│   └── workers/        # Cloud batch processing adapters (TODO)
└── tests/              # Unit and integration tests
```

## System Setup

This project fundamentally relies on three logical components:
1. **Cloud Server**: Runs the public-facing Telegram bot.
2. **Dispatcher Server**: Runs the FastAPI backend, manages routing, DB logging, and session state. Does *not* require a GPU.
3. **Inference Worker(s)**: Machines with GPU access running the actual ML model (e.g., `llama-server`).

*Note: The Dispatcher Server and Inference Worker can be hosted on the same physical machine.*

### 1. Dispatcher Server Setup (FastAPI)

This machine routes traffic to the MedGemma model and handles all database logging.

1.  **Prerequisites**:
    - A Linux machine.
    - Python 3.12+ and Conda installed.

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
    python src/api/scripts/init_db.py --add-user YOUR_TELEGRAM_ID --name "Your Name" --role "admin"
    ```

### 2. Cloud Server Setup (Telegram Bot)

This machine runs the Telegram bot and forwards requests to your dispatcher. A free-tier cloud instance is sufficient.

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
    From your **Dispatcher Server**, open a reverse SSH tunnel to your cloud instance. This securely exposes your API to the cloud bot.
    ```bash
    ssh -R 8000:localhost:8000 user@your-cloud-server-ip -N -f
    ```

2.  **Start the Dispatcher API Server**:
    On your **Dispatcher Server**, start the FastAPI application:
    ```bash
    uvicorn src.api.main:app --host 127.0.0.1 --port 8000
    ```

3.  **Start the Telegram Bot**:
    On your **Cloud Server**, start the bot. Remember to use the `-m` flag to run it as a module to ensure correct pathing.
    ```bash
    python -m src.bot.main
    ```

## Worker Infrastructure

The system supports multiple worker types for model inference, allowing flexible deployment options ranging from local GPUs to ephemeral cloud instances.

### 1. llama-server (Primary Worker)
For maximum efficiency and lowest VRAM usage, the pre-compiled `llama-server` is the recommended backend. **It is remote-agnostic**: you can run it on your local hardware, or host it on remote cloud GPU providers. The Dispatcher automatically detects and communicates with any OpenAI-compatible endpoint.
```bash
./llama-server -m models/medgemma-1.5-4b.gguf --mmproj models/mmproj-model-f16.gguf -c 2048 --port 8001 --host 0.0.0.0
```
Configure `api.env` to point `INFERENCE_WORKERS` to its completions endpoint: `http://<WORKER_IP>:8001/v1/chat/completions`.

### 2. Python Worker (Legacy/Custom Pipelines)
While `llama-server` is generally superior for performance, the original Python worker maintains several highly useful qualities:
- **Debugging**: It's much easier to trace tensor shapes and logic in native Python.
- **Custom Architectures**: Useful for bleeding-edge HuggingFace models that are not yet supported by `llama.cpp`.
- **Complex Logic**: Acts as a playground for advanced, custom multi-step pre/post-processing ML pipelines.
```bash
uvicorn src.api.worker:app --host 127.0.0.1 --port 8001
```

### 3. Cloud Batch Worker (TODO)
Designed for ephemeral cloud GPUs. This feature is planned for future implementation and aims to support:
1.  **Manual Execution**: Scripts and notebooks optimized for manual launch on popular cloud notebook providers.
2.  **Automated Serverless Execution**: Full orchestration of cloud instances for automated batch processing without manual intervention.

## Image Preprocessing Features

Image preprocessing is a strong feature of this project, allowing the user to significantly improve the quality of AI analysis using interactive, built-in fast commands. 

Since LLMs often squish non-square images causing spatial distortion, the bot automatically performs intelligent center-cropping (`process_main_image`).

For detailed analysis of specific pathologies, users are prompted with an interactive **Region of Interest (ROI)** keyboard upon upload. The user can select:
- 🔍 **Analyze Full Image**: Processes the standard center-crop.
- ↖️ **Top Left** / ↗️ **Top Right** / ⏺ **Center** / ↙️ **Bottom Left** / ↘️ **Bottom Right**: Instructs the dispatcher to extract a 50% zoomed window at the specified quadrant, re-crop it to a square, and up-res it (`process_roi_image`). This essentially directs the model's visual attention to specific anomalies without losing resolution.

## Administration & Statistics

The platform provides built-in metrics and moderation tools for users with the `"admin"` role defined in the Google Drive whitelist.

Admins can use the following commands directly in the Telegram chat:
- `/admin_status`: Check real-time health, ping latency, and online/offline status for all configured worker endpoints.
- `/admin_stats <daily|weekly|monthly|all>`: View global platform usage statistics, including total token counts and queries over the given period.
- `/admin_user_stats <telegram_id>`: Audit activity metrics for a specific whitelisted user.
- `/admin_worker_stats <period>`: Assess the performance and inference load distributed across specific workers.
- `/refresh_whitelist`: Instantly sync user roles and permissions from Google Drive without needing to restart the bot.

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
    }
  },
  "prompts": {
    "1": {
      "description": "Standard Radiologist",
      "content": "You are an expert radiologist AI assistant..."
    }
  }
}
```

### User Parameters
- `name` *(string)*: Display name for the user.
- `role` *(string)*: User role (`"admin"` or `"user"`).
- `is_active` *(boolean)*: Set to `false` to instantly revoke bot access for the user.
- `system_prompt_type` *(integer)*: Links the user to a specific system prompt.
- `allowed_workers` *(list of strings)*: Restricts which inference routes the user can access.
- `show_thoughts` *(boolean)*: If `true`, the bot will display the AI's internal reasoning.

## Architecture & Performance Optimizations

To run a complex multi-modal model like MedGemma-1.5 on constrained hardware, this project implements:
- **KV Caching & Multi-Slot Architecture**: Maintains multiple parallel context slots in VRAM for instant prompt switching.
- **GBNF Grammar Constraints**: Enforces a physical token-generation grammar (`report.gbnf`) to prevent hallucinations and strictly structure output.
- **Custom Jinja Templating**: Ensures native API compatibility without model crashes.

## Troubleshooting

For solutions to common deployment and SSH tunnel issues, please see [docs/troubleshooting.md](docs/troubleshooting.md).