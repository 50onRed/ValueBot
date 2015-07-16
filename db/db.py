import config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

db = create_engine(config.SQLALCHEMY_DATABASE_URI)
Base = declarative_base()