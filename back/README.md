# RAG Server - Installation & Setup Guide

## Overview

The RAG (Retrieval-Augmented Generation) server provides email classification, PDF extraction, vector search, and business document processing capabilities.

## Installation

### Prerequisites

- Python 3.9 or higher
- pip and setuptools
- Virtual environment (recommended)

### Quick Start

1. **Clone and navigate to the project:**

   ```bash
   cd back
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode:**

   ```bash
   pip install -e .
   ```

   This installs the `rag-server` package with all dependencies defined in `pyproject.toml`:
   - Google Auth packages (Gmail/Drive integration)
   - Supabase client (database operations)
   - Sentence-transformers (embeddings)
   - And all other required dependencies

4. **Install development dependencies (optional):**

   ```bash
   pip install -e ".[dev]"
   ```

   This adds testing and code quality tools:
   - pytest, pytest-cov, pytest-timeout
   - black, flake8

### Environment Variables

Create a `.env` file in the `back/` directory with the following variables:

```env
# LLM Configuration
LLM_URL=http://127.0.0.1:1234/v1/chat/completions
LLM_MODEL=Qwen2.5-7B-Instruct
LLM_TIMEOUT=30

# Optional: Enable live LLM tests
RUN_LLM_LIVE=1
USER_ID=74378-324-232 # the user id managed by supabase
# Supabase Configuration
SUPABASE_URL=http://localhost:8003
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# Google OAuth2 (for Gmail/Drive integration)
# Place credentials.json in var/credentials.json

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
```

## Project Structure

```
back/
├── pyproject.toml          # Package configuration & dependencies
├── src/                    # Source code
│   ├── llm/               # LLM client and JSON parsing
│   ├── pdf/               # PDF text extraction
│   ├── google_auth/       # Google OAuth2 authentication
│   ├── supabase/          # Supabase client wrappers
│   ├── embeddings/        # Embedding generation
│   ├── email/             # Email classification
│   ├── auth/              # Authentication routes & middleware
│   └── rag/               # Core RAG functionality
├── script/                # Standalone scripts & utilities
├── var/                   # Data storage
│   ├── attachments/       # Email attachments
│   ├── storage/           # Data files
│   ├── credentials.json   # Google OAuth credentials
│   └── token.pickle       # Google OAuth token
├── schema/                # Database schema
└── tests/                 # Integration tests
```

## Running the Server

### Development Server

```bash
python dev.py
```

The server runs on `http://localhost:5000` by default.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run only fast tests (skip slow LLM tests)
pytest -m "not slow"

# Run with live LLM tests
RUN_LLM_LIVE=1 pytest
```

## Key Features

### Email Classification

- Gmail integration with OAuth2 authentication
- Automatic email classification using LLM
- Attachment handling (stored in `var/attachments/`)

### PDF Processing

- PDF text extraction using pdfplumber
- RFP (Request for Proposal) parsing

### Vector Search

- Qdrant integration for semantic search
- Sentence-transformer embeddings

### Business Document Processing

- XLSX/CSV file handling
- Data denormalization

## Configuration Files

- `config.yml` - Application configuration (LLM, database, vendor settings)
- `pyproject.toml` - Package metadata and dependencies
- `.env` - Environment variables (not tracked in git)

## Dependencies

All dependencies are defined in `pyproject.toml`. The key packages include:

- **Flask 3.0+** - Web framework
- **Google APIs** - Gmail and Drive integration
- **Supabase** - Database and authentication
- **Sentence-transformers** - NLP embeddings
- **Qdrant-client** - Vector database
- **pdfplumber** - PDF text extraction
- **pytest** - Testing framework

## Troubleshooting

### Import Errors

If you see import errors, ensure the package is installed in development mode:

```bash
pip install -e .
```

### Missing Dependencies

Install development dependencies:

```bash
pip install -e ".[dev]"
```

### LLM Connection Issues

Verify your `LLM_URL` and `LLM_MODEL` in `.env`:

```bash
curl http://your-llm-url/v1/models
```

### Database Connection

Ensure Supabase environment variables are set:

```bash
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
```

## ETIM Reference

FEATURETYPE in ETIM tables:

- **A**: Alphanumeric — free text value
- **N**: Numeric — single numeric value; unit from UNITOFMEASID if present
- **R**: Range — numeric "from–to" range; unit via UNITOFMEASID
- **L**: List — coded/enumerated value from predefined list

## Import from Google Drive

See [Google Drive Integration Guide](docs/GMAIL_INTEGRATION.md) for detailed setup instructions.

# backup restoration

cd /Users/malo/Documents/Projects/rkllm-server/external/rag/back
PGPASSWORD='g7+bXoS1sE7TJ8nmsO5TnvBNm3WRDQmO' psql -h localhost -p 5432 -U supabase_admin -d postgres < var/backup/nego.sql

if vendor issues:
ALTER TABLE brand DROP CONSTRAINT IF EXISTS brand_vendor_id_fkey1;
ALTER TABLE family DROP CONSTRAINT IF EXISTS family_brand_id_fkey1;
NOTIFY pgrst, 'reload schema';
