from typing import Annotated
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from .. import env
from fastapi import APIRouter, Request, HTTPException, Depends, Header
import jwt
from sqlmodel import Session, select, text
from ..internal.db import engine
from ..internal.models import User

async def get_token(
    Authorization: str = Header(default="Bearer "),
) -> str:
    _, token = Authorization.split(" ")
    print(token)
    return token

async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        email = payload.get('sub')
        if email is None:
            raise jwt.DecodeError()
        with Session(engine) as session:
            user = session.exec(select(User).where(User.email == email)).one()
            if not user:
                raise jwt.DecodeError()
            return user
    # except jwt.ExpiredSignatureError:
    #     raise HTTPException(status_code=401, detail="Token has expired")
    # except jwt.DecodeError:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    except:
        raise HTTPException(status_code=403, detail="Not allowed")
        # return RedirectResponse(url="/login")
    
def check_session(request: Request):
    # if env.ENABLE_AUTH and not request.session.get("user"):
    #     return RedirectResponse(url="/login")
    
    return None


check = Depends(get_current_user)

MaybeRedirect = Annotated[RedirectResponse | None, check]