from fastapi import APIRouter,Depends,HTTPException,Request,status
from model import Note,JSONNote,User
from connection import collection,user_collection,delete
from schema import serialise_one,serialise_many
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt,JWTError
from datetime import datetime,timedelta,UTC
import os

oauth=OAuth2PasswordBearer(tokenUrl="/token")

router=APIRouter()

auth_router=APIRouter(dependencies=[Depends(oauth)])

SECRET_KEY="mini_project"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE=1

@router.post("/create_user",tags=["User"])
async def create_user(user:User):
    res=serialise_many(user_collection.find({},{"name":1,"email":1}))
    user=user.dict()
    user["name"]=user["name"].lower()
    user["email"]=user["email"].lower()
    for u in res:
        if u["name"].lower()==user["name"].lower():
            raise HTTPException(status_code=400,detail="User exists")
        if u["email"].lower()==user["email"].lower():
            raise HTTPException(status_code=400, detail="Two different users cant have same email.")
        if user["deleted"]!=0:
            raise HTTPException(status_code=400,detail="Invalid user data")
    user_collection.insert_one(user)
    return serialise_one(user)

@router.post("/token",tags=["User"])
async def login(form:OAuth2PasswordRequestForm=Depends()):
    user=user_collection.find_one({"name":form.username})
    if  not user or user["password"]!=form.password or user["deleted"]==1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid credential or user not exists.")

    data={"sub":form.username,"exp":datetime.now(UTC)+timedelta(days=ACCESS_TOKEN_EXPIRE)}
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
    user_collection.update_one({"name":cur["name"]},{"$set":{"deleted":1}})
    return serialise_one(user_collection.find_one({"name":cur["name"]}))

@router.put("/update_user",tags=["User"])
async def update_user(user:User,cur:dict=Depends(current_user)):
    user=user.dict()
    user["name"]=user["name"].lower()
    user["email"]=user["email"].lower()
    exist=user_collection.find_one({"name":user["name"]})
    if exist:
        raise HTTPException(status_code=400,detail="User exists")
    if user["deleted"]!=0:
        raise HTTPException(status_code=400,detail="Invalid data")
    user_collection.update_one({"name":cur["name"]},{"$set":user})
    return serialise_one(user_collection.find_one({"name":user["name"]}))

@router.put("/restore/user/{name}",tags=["User"])
async def restore_user(name:str):
    name=name.lower()
    res=user_collection.find_one_and_update({"name":name},{"$set":{"deleted":0}})
    if res is None:
        raise HTTPException(status_code=400,detail="Invalid title")
    return serialise_one(user_collection.find_one({"name":name}))

@auth_router.get("/get_users",tags=["User"])
async def get_users():
    res=[serialise_one(user) for user in user_collection.find({"deleted":0},{"name":1})]
    if not res:
        raise HTTPException(status_code=404,detail="Users db is empty")
    return res

@auth_router.post("/create_note",tags=["Notes"])
async def create_note(note:Note):
    temp=note.model_dump()
    temp["title"]=temp["title"].lower()
    temp["tags"]=[var.lower() for var in temp["tags"]]
    temp["content"]=temp["content"].lower()
    temp_note=collection.find_one({"title":temp["title"]})
    if temp_note:
        raise HTTPException(status_code=400,detail="Note already exists.")
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
    tags=tags.lower()
    tags=tags.split(",")
    res={}
    notes=[serialise_one(note) for note in collection.find({"tags":{"$in":tags}})]
    if not notes:
        raise HTTPException(status_code=400, detail="Invalid tag")
    for note in notes:
        j_note=JSONNote()
        content=j_note.load(note["title"])
        res[note["title"]]={"_id":note["_id"],"title":note["title"],"tags":note["tags"],"path":note["path"],"content":content["content"]}
    return res

@auth_router.get("/note/{title}",tags=["Notes"])
async def get_note_by_title(title:str):
    title=title.lower()
    note=collection.find_one({"title":title})
    if note is None:
        raise HTTPException(status_code=400,detail="Invalid title")
    note=serialise_one(note)
    res={}
    j_note=JSONNote()
    content=j_note.load(title)
    res[title]={"_id":note["_id"],"title":note["title"],"tags":note["tags"],"path":note["path"],"content":content["content"]}
    return res


@auth_router.put("/update/{title}",tags=["Notes"])
async def update_by_title(title:str,note:Note):
    note=note.model_dump()
    title=title.lower()
    res=collection.find_one({"title":title})
    if res is None:
        raise HTTPException(status_code=400, detail="Invalid title")
    ans=collection.find_one({"title":note["title"].lower()})
    if ans:
        raise HTTPException(status_code=400,detail="Note already exists.")
    note["title"] = note["title"].lower()
    note["tags"] = [var.lower() for var in note["tags"]]
    note["content"]=note["content"].lower()
    r="C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/"+title+".json"
    os.remove(r)
    j_obj=JSONNote()
    path=j_obj.save(note)
    collection.update_one({"title": title}, {"$set": {"title": note["title"], "tags": note["tags"],"path":path}})
    return {f"message":f"content updated in mongoDB and in Path {path}"}

@auth_router.delete("/delete/note/{title}",tags=["Notes"])
async def delete_note_by_title(title:str,request:Request):
    title=title.lower()
    res=collection.find_one_and_delete({"title":title})
    if res is None:
        raise HTTPException(status_code=400,detail="Invalid title")
    res=serialise_one(res)
    res.pop("_id")
    delete.insert_one(res)
    j_obj=JSONNote()
    path="document deleted from the collection and "+j_obj.delete(title,request.url.path.split("/")[1])
    return {"message":path}

@auth_router.put("/restore/{title}",tags=["Notes"])
async def restore_note(title:str,request:Request):
    title=title.lower()
    res=delete.find_one_and_delete({"title":title})
    if res is None:
        raise HTTPException(status_code=400, detail="Invalid title")
    res=serialise_one(res)
    res.pop("_id")
    collection.insert_one(res)
    j_obj=JSONNote()
    path="document deleted from the collection and "+j_obj.delete(title,request.url.path.split("/")[1])
    return {"message":path}





