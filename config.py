from flask import Flask
import re	# the regex module
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# create a regular expression object that we'll use later   
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

app=Flask(__name__)

app.secret_key="shush, no telling"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///photobomb.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

bcrypt=Bcrypt(app)
db=SQLAlchemy(app)
migrate = Migrate(app, db)


