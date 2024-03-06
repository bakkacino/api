from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException
import jwt
import os


def validate_user_email(email: str):
    try:
        email_valid = validate_email(email)
        email = email_valid.normalized
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail="The provided email address is not in a valid format. Please enter a valid email address.")
    
    
def get_str_bytes(string: str) -> bytes:
    return bytes(string, 'utf-8')


def generate_jwt_token(id: int) -> str:
    token = jwt.encode({"id": id}, os.environ.get("JWT_SECRET"), algorithm="HS256")
    return token
