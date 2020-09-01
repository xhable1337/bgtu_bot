from pymongo import MongoClient
import os

MONGODB_URI = os.environ['MONGODB_URI']
client = MongoClient(host=MONGODB_URI, retryWrites=False) 
db = client.heroku_38n7vrr9
users = db.users



def get_state(user_id):
    """Позволяет просмотреть state по user_id."""
    return users.find_one({'user_id': user_id})['state']

def set_state(user_id, state):
    """Позволяет изменить state по user_id."""
    users.update_one({'user_id': user_id}, {'$set': {'state': state}})









#users.update_one({'user_id': user_in_reply.id}, {'$inc': {'karma': 1}})