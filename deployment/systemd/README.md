# systemd setup for RAG stack

This folder contains systemd units to start backend and frontend at boot.

- taioe-backend.service: Python backend (runs src/command/dev_server.py), starts after Ollama and waits for Ollama API readiness.
- taioe-frontend.service: Vite frontend dev server.
- taioe-stack.target: Convenience target to start both services together.

## Install units

```bash
cd /home/malo/tai-oe
sudo cp deployment/systemd/taioe-backend.service /etc/systemd/system/
sudo cp deployment/systemd/taioe-frontend.service /etc/systemd/system/
sudo cp deployment/systemd/taioe-stack.target /etc/systemd/system/
sudo systemctl daemon-reload
```

Important for frontend: Vite 7 requires Node 20.19+ (or 22.12+).
This unit is pinned to Node at:

`/home/malo/.nvm/versions/node/v22.22.2/bin/npm`

If your installed Node path differs, edit `taioe-frontend.service` accordingly before copying.

## Enable on boot

```bash
# Ensure Ollama starts at boot
sudo systemctl enable ollama.service

# Option A: enable both directly
sudo systemctl enable taioe-backend.service taioe-frontend.service

# Option B: enable the target
sudo systemctl enable taioe-stack.target
```

## Start now

```bash
sudo systemctl start taioe-backend.service
sudo systemctl start taioe-frontend.service
# or
sudo systemctl start taioe-stack.target
```

After changing a unit file already installed in `/etc/systemd/system`, run:

```bash
sudo systemctl daemon-reload
sudo systemctl restart taioe-frontend.service
```

## Check status/logs

```bash
systemctl status taioe-backend.service
journalctl -u taioe-frontend.service -f
journalctl -u taioe-backend.service -f
journalctl -u taioe-frontend.service -f
```

## Notes

- Units use `User=malo` and absolute paths from this machine.
- If your username/path differs, edit the unit files before copying.
- Frontend runs `npm run dev` (Vite). For production, prefer a built frontend + static server/reverse proxy.
