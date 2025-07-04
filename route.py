from fastapi import APIRouter,Depends,HTTPException
from model import Note,JSONNote,User
from connection import collection,user_collection
from schema import serialise_one,serialise_many
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt,JWTError
from datetime import datetime,timedelta

oauth=OAuth2PasswordBearer(tokenUrl="/token")

router=APIRouter()
auth_router=APIRouter(dependencies=[Depends(oauth)])

SECRET_KEY="miniproject"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE=1

@router.post("/create_user",tags=["User"])
async def create_user(user:User):
    res=user_collection.find({},{"name":1,"email":1})
    for u in res:
        if u["name"]==user.dict()["name"]:
            raise HTTPException(status_code=404,detail="User exists")
        if u["email"]==user.dict()["email"]:
            raise HTTPException(status_code=404, detail="Two different users cant have same email.")
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


@router.delete("/delete_user",tags=["User"])
async def delete_user(cur:dict=Depends(current_user)):
    user=user_collection.find_one_and_delete({"name":cur["name"]})
    return serialise_one(user)

@router.put("/update_user",tags=["User"])
async def update_user(user:User,cur:dict=Depends(current_user)):
    user=user_collection.find_one_and_update({"name":cur["name"]},{"$set":user.dict()})
    return serialise_one(user)

@auth_router.get("/get_users",tags=["User"])
async def get_users():
    res=[serialise_one(user) for user in user_collection.find({},{"name":1})]
    if not res:
        raise HTTPException(status_code=404,detail="Users db is empty")
    return res

@auth_router.post("/create_note",tags=["Notes"])
async def create_note(note:Note):
    temp=note.dict()
    temp_note=collection.find_one({"title":temp["title"]})
    if temp_note:
        raise HTTPException(status_code=404,detail="Note already exists.")
    else:
        j_note=JSONNote()
        path=j_note.save(temp)
        collection.insert_one({"title":temp["title"],"tags":temp["tags"],"path":path})
        return temp


@auth_router.get("/get_all_notes",tags=["Notes"])
async def get_all_notes():
    notes=collection.find()
    notes=serialise_many(notes)
    res={}
    for note in notes:
        j_note=JSONNote()
        content=j_note.load(note["title"])
        res[note["title"]]={"_id":note["_id"],"title":note["title"],"tags":note["tags"],"path":note["path"],"content":content["content"]}
    return res

@auth_router.get("/get_notes/{tags}",tags=["Notes"])
async def get_all_notes_by_tags(tags:str):
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

@auth_router.get("/note/{title}",tags=["Notes"])
async def get_note_by_title(title:str):
    try:
        note=serialise_one(collection.find_one({"title":title}))
        res={}
        j_note=JSONNote()
        content=j_note.load(title)
        res[title]={"_id":note["_id"],"title":note["title"],"tags":note["tags"],"path":note["path"],"content":content["content"]}
        return res
    except TypeError:
        raise HTTPException(status_code=404, detail="Invalid title")

@auth_router.put("/update/{title}",tags=["Notes"])
async def update_by_title(title:str,note:Note):
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

@auth_router.delete("/delete/note/{title}",tags=["Notes"])
async def delete_note_by_title(title:str):
    try:
        collection.delete_one({"title":title})
        j_obj=JSONNote()
        path=j_obj.delete(title)
        return path
    except FileNotFoundError:
        raise HTTPException(status_code=404,detail="Invalid title")