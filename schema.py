def serialise_one(doc)->dict:
    doc["_id"]=str(doc["_id"])
    return doc

def serialise_many(docs)->list:
    return [serialise_one(doc) for doc in docs]