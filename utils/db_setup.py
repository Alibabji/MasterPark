import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Load environment variables
load_dotenv()
DB_PASSWORD = os.getenv('DB_PASSWORD')

# MongoDB connection URI
uri = f"mongodb+srv://alibabji:{DB_PASSWORD}@cluster0.vu34v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
warns_db = client.warns
warns_coll = warns_db.serverwarns

bans_db = client.bans
bans_coll = bans_db.serverbans

alerts_db = client.alerts
alerts_coll = alerts_db.serveralerts

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
