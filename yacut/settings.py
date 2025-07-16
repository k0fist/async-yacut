import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DISK_TOKEN = os.getenv('DISK_TOKEN')


config = Config()

app = Flask(
    __name__,
    instance_relative_config=True
)
app.config.from_object(config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)