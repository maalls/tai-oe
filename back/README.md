# Tai Oe Server - Installation & Setup Guide

## Overview

fetching emails:
`python -m src.command.email_cli loop --interval 10`

## Installation

Create and activate venv:

```bash
cd back
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Prod update

To update venv in another instance:

```bash
cd back
source venv/bin/activate
venv/bin/python -m pip install -r requirements.txt
```

(If venv doesn't exist on the remote, create it with `python3 -m venv venv` first)

Environment/config changes (.env files):
`sudo systemctl restart taioe-backend`

## Systemd Entrypoint

The backend is started by systemd using:

```
python -m src.command.dev_server
```

See deployment/systemd/taioe-backend.service and deployment/systemd/taioe-frontend.service

migration:

```
python -m script.run_migrations
```

The migration runner uses PostgreSQL URLs in this order:

1. `MIGRATION_DATABASE_URL`
2. `ADMIN_DATABASE_URL`
3. `DATABASE_URL`

For schema changes, point `MIGRATION_DATABASE_URL` at a role that can create/alter objects in `public`.
