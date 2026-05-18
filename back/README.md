# Tai Oe Server - Installation & Setup Guide

## Overview

fetching emails:
`python -m src.command.email_cli loop --interval 10`

## Installation

Create and activate venv:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Prod update

To update venv in another instance:

```bash
cd ~/tai-oe/back
source venv/bin/activate
pip install -r requirements.txt
```

(If venv doesn't exist on the remote, create it with `python3 -m venv venv` first)

Environment/config changes (.env files):
`sudo systemctl restart rag-backend`
