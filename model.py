from pydantic import BaseModel,EmailStr,Field
from abc import ABC,abstractmethod
import json
import os

class User(BaseModel):
    name:str
    password:str
    email:EmailStr
    deleted:int=Field(default=False)

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
    def delete(self,note,path):
        pass

class JSONNote(BaseNote):

    def save(self,note):
        os.makedirs("C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/",exist_ok=True)
        title="C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/"+note["title"]+".json"
        with open(title,"w") as f:
            json.dump(note,f,indent=4)
        return title

    def load(self,title):
        title="C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/"+title+".json"
        with open(title,"r") as f:
            content=json.load(f)
        return content

    def delete(self,title,path):
        full_title=""
        new_title=""
        if path=="delete":
            full_title="C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/"+title+".json"
            os.makedirs("C:/Users/Bharath KA/Documents/Mini-Project/Deleted_Notes/", exist_ok=True)
            new_title = "C:/Users/Bharath KA/Documents/Mini-Project/Deleted_Notes/" + title + ".json"
        elif path=="restore":
            full_title="C:/Users/Bharath KA/Documents/Mini-Project/Deleted_Notes/"+title+".json"
            os.makedirs("C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/", exist_ok=True)
            new_title = "C:/Users/Bharath KA/Documents/Mini-Project/JSON_Notes/" + title + ".json"
        with open(full_title,"r") as f:
            content=json.load(f)
        os.remove(full_title)
        with open(new_title,"w") as f:
            json.dump(content,f,indent=4)
        return f"File removed at {full_title}"

