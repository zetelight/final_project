"""
Just to test database functions,
outside of Flask.

We want to open our MongoDB database,
insert some memos, and read them back
"""

import pymongo
from pymongo import MongoClient
import arrow
import sys
from dateutil import tz  # For interpreting local times
import config

CONFIG = config.configuration()

MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST,
    CONFIG.DB_PORT,
    CONFIG.DB)

print("Using URL '{}'".format(MONGO_CLIENT_URL))

try:
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, CONFIG.DB)
    print("Got database")
    collection = db.dated
    print("Using sample collection")
except Exception as err:
    print("Failed")
    print(err)
    sys.exit(1)

#
# Insertions:  I commented these out after the first
# run successfuly inserted them
#
#

collection.delete_many({})

# record = {"type": "dated_memo",
#           "date": arrow.utcnow().naive,
#           "summary": "This is a sample memo",
#           "description": "what happened?!",
#           "tag": []}

# string = "dated_memo"
# string2 = "what happened?!"
# print("Inserting 1")
# collection.insert_one(record)
# print("Inserted")
# print(record)

# print("try to find it------------")
# right_person = collection.find_one({"type": string})
# wrong_person = collection.find_one({"ha": "ha"})
# if right_person:
#     if string2 == right_person["description"]:
#         print("Your matched!")
#     print(right_person['_id'])
#     print("try to update it")
#     collection.update_one({'type': string}, {'$set': {"events": {"start": 1, "end": 0}}, "$push": {"tag": string2}})
#     collection.update_one({'type': string}, {"$push": {"tag": string2}})
# else:
#     print("You find nothing")

# right_person = collection.find_one({"type": string})
# print(right_person)

# if wrong_person:
#     print("hahahaha")
# else:
#     print("wtf")

# record1 = {"type": "memo",
#           "summary": "This is a sample memo NO1",
#           "tag": ["haha", "heihei"],
#           "event": [{"ds": "ds"}, {"dsadas": "dasdassssssssssssssssssssssssssssdas"}]
#           }
# record2 = {"type": "memo",
#           "date": arrow.utcnow().naive,
#           "summary": "This is a sample memo NO2",
#           "tag": ["haha"],
#           "event": [{"ds": "ds"}, {"dsadas": "dasdasdas"}],
#           "creator": [{"meeting_id": "12345", "start": "2017/01"}]
#           }
# collection.insert_one(record1)
# collection.insert_one(record2)
# list2 = []
# for each in collection.find({"tag": {"$in": ["heihei"]}}):
#     for each_event in each["event"]:
#         list2.append(each_event)

# print(list2)

#person = collection.find_one({"creator.meeting_id" : "12345"})
#print(person['creator'][0]["start"])


#
# Read database --- May be useful to see what is in there,
# even after you have a working 'insert' operation in the flask app,
# but they aren't very readable.  If you have more than a couple records,
# you'll want a loop for printing them in a nicer format.
#


# print("Reading database")

# records = []
# for record in collection.find({"type": "dated_memo"}):
#     records.append(
#         {"type": record['type'],
#          "date": arrow.get(record['date']).to('local').isoformat(),
#          "summary": record['summary'],
#          "description": record['description']})

# print("Records: ")
# print(records)

records = []
for record in collection.find({}):
    print(record)
