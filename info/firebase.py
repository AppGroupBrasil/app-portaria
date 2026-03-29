import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate('../static/json/firebase-key.json')
firebase_admin.initialize_app(cred)
