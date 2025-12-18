"""
Email verification endpoints

Handles:
- Email verification token generation
- Email verification
- Resending verification emails
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models.db_models import User
from app.services.email_service import EmailService, get_email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Email Verification"])

# In-memory token storage (use Redis or database in production)
_verification_tokens = {}


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class VerificationStatusResponse(BaseModel):
    email: str
    is_verified: bool


def generate_verification_token(email: str) -> str:
    """Generate secure verification token"""
    random_string = secrets.token_urlsafe(32)
    token_data = f"{email}:{random_string}:{datetime.utcnow().isoformat()}"
    token = hashlib.sha256(token_data.encode()).hexdigest()

    # Store token with expiration (24 hours)
    _verification_tokens[token] = {
        "email": email,
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }

    return token


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address using token

    Args:
        token: Verification token from email

    Returns:
        Success message

    Raises:
        400: Invalid or expired token
        404: User not found
    """
    token = request.token

    # Check if token exists
    if token not in _verification_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )

    token_data = _verification_tokens[token]

    # Check if token is expired
    if datetime.utcnow() > token_data["expires_at"]:
        del _verification_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one."
        )

    email = token_data["email"]

    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Mark user as verified
    user.is_verified = True
    db.commit()

    # Delete token after use
    del _verification_tokens[token]

    logger.info(f"Email verified successfully: {email}")

    return {
        "message": "Email verified successfully",
        "email": email,
        "is_verified": True
    }


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    """
    Resend verification email

    Args:
        email: User email address

    Returns:
        Success message

    Raises:
        404: User not found
        400: User already verified
    """
    email = request.email

    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal that user doesn't exist (security)
        return {"message": "If the email exists, a verification email has been sent"}

    # Check if already verified
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    # Generate new token
    token = generate_verification_token(email)

    # Send verification email
    user_name = user.first_name or user.full_name.split()[0] if user.full_name else "User"
    success = await email_service.send_verification_email(
        to=email,
        user_name=user_name,
        verification_token=token
    )

    if not success:
        logger.error(f"Failed to send verification email to {email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

    logger.info(f"Verification email resent to {email}")

    return {"message": "Verification email sent"}


@router.get("/verify-status", response_model=VerificationStatusResponse)
async def check_verification_status(
    email: EmailStr,
    db: Session = Depends(get_db)
):
    """
    Check email verification status

    Args:
        email: User email address

    Returns:
        Verification status

    Raises:
        404: User not found
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return VerificationStatusResponse(
        email=email,
        is_verified=user.is_verified
    )
