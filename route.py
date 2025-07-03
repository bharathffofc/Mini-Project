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

@router.post("/create_note",tags=["Notes"])
async def create_note(note:Note,cur:dict=Depends(current_user)):
    temp=note.dict()
    temp_note=collection.find_one({"title":temp["title"]})
    if temp_note:
        raise HTTPException(status_code=404,detail="Note already exists.")
    else:
        j_note=JSONNote()
        path=j_note.save(temp)
        collection.insert_one({"title":temp["title"],"tags":temp["tags"],"path":path})
        return temp


@router.get("/get_all_notes",tags=["Notes"])
async def get_all_notes(cur:dict=Depends(current_user)):
    notes=collection.find()
    notes=serialise_many(notes)
    res={}
    for note in notes:
        j_note=JSONNote()
        content=j_note.load(note["title"])
        res[note["title"]]={"_id":note["_id"],"title":note["title"],"tags":note["tags"],"path":note["path"],"content":content["content"]}
    return res

@router.get("/get_notes/{tags}",tags=["Notes"])
async def get_all_notes_by_tags(tags:str,cur:dict=Depends(current_user)):
    tags=tags.split(",")
    res={}
    notes=[serialise_one(note) for note in collection.find({"tags":{"$in":tags}})]
    for note in notes:
        j_note=JSONNote()
        content=j_note.load(note["title"])
        res[note["title"]]={"_id":note["_id"],"title":note["title"],"tags":note["tags"],"path":note["path"],"content":content["content"]}
    if res=={}:
        raise HTTPException(status_code=404,detail="Invalid tag")
    return res

@router.get("/note/{title}",tags=["Notes"])
async def get_note_by_title(title:str,cur:dict=Depends(current_user)):
    try:
        note=serialise_one(collection.find_one({"title":title}))
        res={}
        j_note=JSONNote()
        content=j_note.load(title)
        res[title]={"_id":note["_id"],"title":note["title"],"tags":note["tags"],"path":note["path"],"content":content["content"]}
        return res
    except TypeError:
        raise HTTPException(status_code=404, detail="Invalid title")

@router.put("/update/{title}",tags=["Notes"])
async def update_by_title(title:str,note:Note,cur:dict=Depends(current_user)):
    try:
        note=note.dict()
        collection.update_one({"title":title},{"$set":{"title":note["title"],"tags":note["tags"]}})
        j_obj=JSONNote()
        content=j_obj.load(title)
        content["title"]=note["title"]
        content["tags"]=note["tags"]
        content["content"]=note["content"]
        path=j_obj.save(content)
        return {f"message":f"content updated in mongoDB and in Path {path}"}
    except FileNotFoundError:
        raise HTTPException(status_code=404,detail="Invalid title")

@router.put("/delete/note/{title}",tags=["Notes"])
async def delete_note_by_title(title:str,cur:dict=Depends(current_user)):
    try:
        collection.delete_one({"title":title})
        j_obj=JSONNote()
        path=j_obj.delete(title)
        return path
    except FileNotFoundError:
        raise HTTPException(status_code=404,detail="Invalid title")