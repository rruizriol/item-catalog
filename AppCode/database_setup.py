'''
Created on Sep 7, 2015

@author: Rembrandt
'''
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# Database definition
 
Base = declarative_base()
 
class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name'       : self.name,
           'id'         : self.id,
        }
 
class Item(Base):
    __tablename__ = 'item'

    id   = Column(Integer, primary_key = True)
    title = Column(String(100), nullable = False)
    description = Column(String(250))
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category) 

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'id'          : self.id,
           'title'       : self.title,
           'description' : self.description,
           'category_id' : self.category_id,
        }
 

engine = create_engine('sqlite:///itemcatalog.db')
 

Base.metadata.create_all(engine)