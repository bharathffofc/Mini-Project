from pydantic import BaseModel,EmailStr
from abc import ABC,abstractmethod
import json
import os

class User(BaseModel):
    name:str
    password:str
    email:EmailStr

class Note(BaseModel):
    title:str
    tags:list[str]
    content:str

class BaseNote(ABC):
    @abstractmethod
    def save(self,note):
        pass

    @abstractmethod
    def load(self,note):
        pass

    @abstractmethod
    def delete(self,note):
        pass

class JSONNote(BaseNote):

    def save(self,note):
        os.makedirs("C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/",exist_ok=True)
        title="C:/Users/Bharath KA/Documents/Mongo_DB/Practice/mini_project/Notes/"+note["title"]+".json"
        with open(title,"w") as f:
            json.dump(note,f,indent=4)
        return title

    def load(self,title):
        title="C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/"+title+".json"
        with open(title,"r") as f:
            content=json.load(f)
        return content

    def delete(self,title):
        title="C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/"+title+".json"
        os.remove(title)
        return f"File removed at {title}"