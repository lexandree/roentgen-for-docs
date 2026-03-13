# Minimalist Deployment (systemd)

This approach is recommended for VMs with < 1GB RAM to avoid Docker overhead.

## Quick Setup

1. **Install Python 3.12+**:
   ```bash
   sudo apt update && sudo apt install -y python3.12 python3.12-venv
   ```

2. **Clone & Prepare Env**:
   ```bash
   git clone <repo_url> && cd roentgen_for_docs
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r src/api/requirements-dispatcher.txt
   pip install -r src/bot/requirements.txt
   ```

3. **Configure Environment**:
   - Create `api.env` and `bot.env` in the project root.
   - Use `src/api/dispatcher.env.example` and `src/bot/.env.example` as templates.

4. **Install Services**:
   - Edit paths in `.service` files to match your project location.
   - Copy files to systemd:
     ```bash
     sudo cp deployment/systemd/*.service /etc/systemd/system/
     sudo systemctl daemon-reload
     sudo systemctl enable roentgen-api roentgen-bot
     sudo systemctl start roentgen-api roentgen-bot
     ```

5. **Logs**:
   ```bash
   journalctl -u roentgen-api -f
   journalctl -u roentgen-bot -f
   ```
