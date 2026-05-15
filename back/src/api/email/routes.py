from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional

router = APIRouter()

# Logique migrée depuis mail/handler.py

def handle_gmail_status(user_id: Optional[str] = Query(None)):
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    return {"status": "ok", "user_id": user_id}

@router.get("/api/gmail/status")
async def gmail_status(user_id: Optional[str] = Query(None)):
    return handle_gmail_status(user_id)


def handle_gmail_authorize(redirect_url: Optional[str] = Query(None)):
    if not redirect_url:
        raise HTTPException(status_code=400, detail="Missing redirect_url")
    return {"status": "authorized", "redirect_url": redirect_url}

@router.get("/api/gmail/authorize")
async def gmail_authorize(redirect_url: Optional[str] = Query(None)):
    return handle_gmail_authorize(redirect_url)

# Ajout des autres routes Gmail et IMAP ici...

@router.get("/api/gmail/oauth/start")
async def gmail_oauth_start(redirect_url: Optional[str] = Query(None), user_id: Optional[str] = Query(None)):
    if not redirect_url or not user_id:
        raise HTTPException(status_code=400, detail="Missing redirect_url or user_id")
    return {"status": "oauth_started", "redirect_url": redirect_url, "user_id": user_id}

@router.get("/api/gmail/revoke")
async def gmail_revoke(user_id: Optional[str] = Query(None)):
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    return {"status": "revoked", "user_id": user_id}

@router.get("/api/gmail/profile")
async def gmail_profile(user_id: Optional[str] = Query(None)):
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    return {"status": "profile_fetched", "user_id": user_id}

@router.get("/api/imap/status")
async def imap_status(user_id: Optional[str] = Query(None)):
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    return {"status": "imap_status_ok", "user_id": user_id}

@router.get("/api/imap/config")
async def imap_config(user_id: Optional[str] = Query(None)):
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    return {"status": "imap_config_fetched", "user_id": user_id}

@router.get("/api/gmail/message/{message_id}")
async def gmail_message(message_id: str = Path(...)):
    if not message_id:
        raise HTTPException(status_code=400, detail="Missing message_id")
    return {"status": "message_fetched", "message_id": message_id}

@router.get("/api/email-attachment/{attachment_id}")
async def email_attachment(attachment_id: str = Path(...)):
    if not attachment_id:
        raise HTTPException(status_code=400, detail="Missing attachment_id")
    return {"status": "attachment_fetched", "attachment_id": attachment_id}