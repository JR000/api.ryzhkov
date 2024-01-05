# https://blog.authlib.org/2020/fastapi-google-login

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth, OAuthError
from passlib.context import CryptContext
import jwt
from sqlmodel import Session, select, text, update
import re

from .. import env
from ..internal.db import engine
from ..internal.models import User
from ..internal.check import get_current_user
from random import randint
import smtplib
from email.mime.text import MIMEText


if env.ENABLE_AUTH:
    from .. import auth_secrets




    
    # server.quit()

    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")   

    router = APIRouter()
    redirect_response = RedirectResponse(url="/" if env.PROD else env.PREFIX)

    def get_email_token() -> str:
        length = 20
        letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        random_string = ''.join(letters[randint(0, len(letters)-1)] for _ in range(length))
        return random_string

    def send_verification_email(email: str, token: str):
        server = smtplib.SMTP("smtp.yandex.ru", 587)
        server.ehlo()
        server.starttls()
        server.login("iwanryzhkov@yandex.ru", "Phrm8xh0dPzdAGGKMnTdXhE3jHzFHMZSlKk4ZU9RLKmM7yJk0VVWakeCDGSG2E3Vg2kUTh8tNCx14INp3O42hRYi4mTe7va5ziRz")
        msg = "\r\n".join([
            f"From: me blyat",
            f"To: {email}",
            "Subject: ",
            "",
            str(f"Ваша ссылка для подтверждения почты: http://localhost:3000/verify?token={token}")
        ])
        msg = MIMEText('\n {}'.format(msg).encode('utf-8'), _charset='utf-8')
        server.sendmail("iwanryzhkov@ya.ru", email, msg.as_string() )    
    
    @router.post("/register")
    def register(email: str, password: str):
        def check_email(email):
            regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            return re.fullmatch(regex, email) and (email.endswith('.msu.ru') or email.endswith('@msu.ru'))

        # if not check_email(email):
        #     raise HTTPException(status_code=400, detail='Invalid email')
        with Session(engine) as session:
            hashed_password = pwd_context.hash(password)
            token = get_email_token()
            session.add(User(email=email, hashed_password=hashed_password, email_token=token))
            session.commit()
            send_verification_email(email, token)
            
            return {"message": "User registered successfully"}

    @router.post("/verify")
    def register(token: str):
        with Session(engine) as session:
            user = session.exec(select(User).where(User.is_verified == False and User.email_token == token)).all()
            if not len(user):
                raise HTTPException(status_code=401)
            user = user[0]
            session.exec(update(User).where(User.email_token == token).values(email_token="", is_verified=True))
            session.commit()
            
            return {"message": "Email verified successfully"}


    @router.post("/login")
    def login(email: str, password: str):
        # c.execute("SELECT * FROM users WHERE username=?", (username,))
        # user = c.fetchone()
        print('hi')
        with Session(engine) as session:
            user = session.exec(text(f"""
                SELECT * FROM user WHERE email = "{email}"
            """)).mappings().all()[0]
        if user:
            if not user.is_verified:
                raise HTTPException(status_code=403, detail="Not verified")
            if pwd_context.verify(password, user.hashed_password):
                token = jwt.encode({'sub': user.email}, 'secret', algorithm='HS256')
                return {"token": token}
        raise HTTPException(status_code=401, detail="Invalid username or password")


    @router.get("/user")
    async def get_user(user=Depends(get_current_user)):
        print(user)
        return user



    # Приватные роуты, требующие авторизации
    @router.get("/private")
    def private_route(email: str = Depends(get_current_user)):
        if email:
            return f"Добро пожаловать, {email}! Это закрытый роут."