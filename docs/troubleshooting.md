# Troubleshooting Guide

## Deployment: Oracle Linux vs Ubuntu
If deploying on Oracle Cloud Free Tier, **always choose the Ubuntu image**. Oracle Linux comes with aggressive SELinux policies that block `systemd` from executing scripts inside user directories (`/home/opc/`), leading to `203/EXEC` and `Permission denied` errors.

## Reverse SSH Tunnel: `Connection refused`
When creating the reverse SSH tunnel from your Dispatcher Server, you might encounter a `ssh: connect to host <your-cloud-server-ip> port 22: Connection refused` error. Ensure your cloud firewall (e.g., `ufw`) allows SSH traffic on port 22.

## Reverse SSH Tunnel: `Warning: remote port forwarding failed for listen port 8080`
This happens when an old, disconnected SSH session is still holding port 8080 open on your cloud server. 

### 1. Automatic Server-Side Cleanup
To ensure the server automatically kills dead tunnel sessions and frees up ports, create a configuration file on your **Cloud Server**:
```bash
sudo tee /etc/ssh/sshd_config.d/tunnel-cleanup.conf <<EOF
ClientAliveInterval 30
ClientAliveCountMax 2
EOF
sudo systemctl restart ssh
```

### 2. Automatic Client-Side Reconnection
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