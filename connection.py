from pymongo import MongoClient

client=MongoClient("mongodb://localhost:27017/")

db=client.Notes
collection=db["Notes_info"]
user_collection=db["User_info"]
delete=db["Deleted_Notes"]


