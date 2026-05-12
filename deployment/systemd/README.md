# systemd setup for RAG stack

This folder contains systemd units to start backend and frontend at boot.

- rag-backend.service: Python backend, starts after Ollama and waits for Ollama API readiness.
- rag-frontend.service: Vite frontend dev server.
- rag-stack.target: Convenience target to start both services together.

## Install units

```bash
cd /home/malo/tai-oe
sudo cp deployment/systemd/rag-backend.service /etc/systemd/system/
sudo cp deployment/systemd/rag-frontend.service /etc/systemd/system/
sudo cp deployment/systemd/rag-stack.target /etc/systemd/system/
sudo systemctl daemon-reload
```

Important for frontend: Vite 7 requires Node 20.19+ (or 22.12+).
This unit is pinned to Node at:

`/home/malo/.nvm/versions/node/v22.22.2/bin/npm`

If your installed Node path differs, edit `rag-frontend.service` accordingly before copying.

## Enable on boot

```bash
# Ensure Ollama starts at boot
sudo systemctl enable ollama.service

# Option A: enable both directly
sudo systemctl enable rag-backend.service rag-frontend.service

# Option B: enable the target
sudo systemctl enable rag-stack.target
```

## Start now

```bash
sudo systemctl start rag-backend.service
sudo systemctl start rag-frontend.service
# or
sudo systemctl start rag-stack.target
```

After changing a unit file already installed in `/etc/systemd/system`, run:

```bash
sudo systemctl daemon-reload
sudo systemctl restart rag-frontend.service
```

## Check status/logs

```bash
systemctl status rag-backend.service
systemctl status rag-frontend.service
journalctl -u rag-backend.service -f
journalctl -u rag-frontend.service -f
```

## Notes

- Units use `User=malo` and absolute paths from this machine.
- If your username/path differs, edit the unit files before copying.
- Frontend runs `npm run dev` (Vite). For production, prefer a built frontend + static server/reverse proxy.
