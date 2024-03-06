from fastapi import APIRouter, Depends, HTTPException
from .auth_models import SignInBody, SignUpBody, User
from .auth_lib import validate_user_email, get_str_bytes, generate_jwt_token
import bcrypt
from sqlmodel import Session, select
from lib import get_current_user
from db import engine


auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@auth_router.post("/sign-up")
def sign_up(body: SignUpBody):
    user = User(username=body.username, email=body.email, password=body.password)
    validate_user_email(user.email)

    hashed_password = bcrypt.hashpw(get_str_bytes(user.password), bcrypt.gensalt())
    user.password = hashed_password

    try:
        with Session(engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
    except:
        raise HTTPException(status_code=409, detail="The provided credentials are already associated with an existing account.")


@auth_router.post("/sign-in")
def sign_in(body: SignInBody):
    validate_user_email(body.email)

    with Session(engine) as session:
        result = session.exec(select(User).where(User.email == body.email))
        user = result.first()
        print(user)

    if not user:
        raise HTTPException(status_code=404, detail="No user was found with the provided email address.")

    password_valid = bcrypt.checkpw(get_str_bytes(body.password), get_str_bytes(user.password))

    if not password_valid:
        raise HTTPException(status_code=401, detail="Invalid password. Please check your password and try again.")

    jwt_token = generate_jwt_token(user.id)

    return {"token": jwt_token}


@auth_router.get("/validate", tags=["Authentication"])
def validate_user(current_user: User = Depends(get_current_user)):
    return current_user
