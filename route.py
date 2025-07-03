from fastapi import APIRouter,Depends,HTTPException
from model import Note,JSONNote,User
from connection import collection,user_collection
from schema import serialise_one,serialise_many
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt,JWTError
from datetime import datetime,timedelta

router=APIRouter()

oauth=OAuth2PasswordBearer(tokenUrl="/token")

SECRET_KEY="miniproject"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE=1

@router.post("/create_user",tags=["User"])
async def create_user(user:User):
    res=user_collection.find({},{"name":1})
    for u in res:
        if u["name"]==user.dict()["name"]:
            raise HTTPException(status_code=404,detail="User exists")
    user_collection.insert_one(user.dict())
    return user.dict()

@router.post("/token",tags=["User"])
async def login(form:OAuth2PasswordRequestForm=Depends()):
    user=user_collection.find_one({"name":form.username})
    if not user or user["password"]!=form.password:
        raise HTTPException(status_code=404,detail="Invalid credential or user not exists.")

    data={"sub":form.username,"exp":datetime.utcnow()+timedelta(days=ACCESS_TOKEN_EXPIRE)}
    access=jwt.encode(data,SECRET_KEY,algorithm=ALGORITHM)

    return {"access_token":access,"token_type":"bearer"}

@router.get("/current_user",tags=["User"])
async def current_user(token:str=Depends(oauth)):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        username=payload.get("sub")
        user=user_collection.find_one({"name":username})
        if not user:
            raise HTTPException(status_code=404,detail="Invalid token")
        return serialise_one(user)
    except JWTError:
        raise HTTPException(status_code=404,detail="Invalid token")