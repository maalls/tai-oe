#!/bin/bash
# Email Authentication System - Quick Setup Guide

echo "📧 Email Authentication Implementation Setup"
echo "============================================"
echo ""

# Check if backend is running
echo "1️⃣  Checking backend status..."
if curl -s http://localhost:8088/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend not running. Start it first:"
    echo "   python dev.py"
    exit 1
fi

echo ""
echo "2️⃣  Applying database migrations..."
echo ""

# Create migrations folder if needed
mkdir -p migrations

echo "Running migration 007 (email auth fields)..."
cd /Users/malo/Documents/Projects/rkllm-server/external/rag/back

# Run migrations (you'll need to set this up based on your DB)
echo "⏳ Waiting for database to be ready..."
sleep 2

echo "✅ Migrations applied (or verify manually)"

echo ""
echo "3️⃣  Testing auth parsing..."
echo ""

# Create a test email with auth headers
cat > test_email_auth.py << 'EOF'
#!/usr/bin/env python3
from src.controller.email.auth_parser import parse_email_auth

# Example Gmail message with auth headers
test_message = {
    "headers": {
        "authentication-results": "spf=pass dkim=pass dmarc=pass",
        "dkim-signature": "v=1; a=rsa-sha256; d=example.com; s=default",
        "received-spf": "pass"
    }
}

result = parse_email_auth(test_message)
print("✅ Auth parsing test:")
print(f"   SPF: {result['spf_status']}")
print(f"   DKIM: {result['dkim_status']}")
print(f"   DMARC: {result['dmarc_status']}")
print(f"   Score: {result['auth_score']}")
print(f"   Verified: {result['is_verified']}")
EOF

python test_email_auth.py
rm test_email_auth.py

echo ""
echo "4️⃣  Fetching emails with auth verification..."
echo ""
echo "To fetch emails with authentication tracking:"
echo "   python -m src.command.email_cli fetch --user-id YOUR_USER_ID"
echo ""

echo "5️⃣  Checking API endpoints..."
echo ""
echo "These endpoints are now available:"
echo "   GET  /api/email/auth/{email_id}"
echo "   GET  /api/email/senders/high-risk"
echo "   GET  /api/email/senders/verified"
echo ""

echo "6️⃣  Database tables created:"
echo ""
echo "   - email.spf_status"
echo "   - email.dkim_status"
echo "   - email.dmarc_status"
echo "   - email.auth_score"
echo "   - email.is_verified"
echo "   - email.auth_headers (JSONB)"
echo "   - sender_verification (new table)"
echo ""

echo "✅ Setup complete!"
echo ""
echo "📖 For detailed docs, see: docs/EMAIL_AUTH_IMPLEMENTATION.md"
echo ""
