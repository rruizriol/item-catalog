'''
Created on Sep 7, 2015

@author: Rembrandt
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Database helpers function

def get_categories():
    """Return a list of category
    
    Returns:
       A list of Category objects
    """
    categories = session.query(Category).all()
    return categories

def get_category(category_id):
    """
    Return a category

    Args:
      category_id: the category's id.
      
    Returns:
       A Category object
    """
    category = session.query(Category).filter_by(id=category_id).first()
    return category

def get_category_by_name(name):
    """
    Return a category

    Args:
      category_name: the category's name.
      
    Returns:
       A Category object
    """
    category = session.query(Category).filter(Category.name.like(name)).first()
    return category

def get_items(category_id):
    """
    Return the items related to a category

    Args:
      category_id: the category's id.
      
    Returns:
       A list of Item objects
    """
    items = session.query(Item).filter_by(category_id=category_id).all()
    return items

def get_items_by_name(category_name):
    """
    Return the items related to a category

    Args:
      category_name: the category's name.
      
    Returns:
       A list of Item objects
    """
    category = get_category_by_name(category_name)
    return get_items(category.id)

def get_item(item_id):
    """
    Return an item

    Args:
      item_id: the item's id.
      
    Returns:
       An Item object
    """
    item = session.query(Item).filter_by(id = item_id).first()
    return item

def get_item_by_title(title, category_id):
    """
    Return an item

    Args:
      title: the item's title.
      category_id: category's id
    
    Returns:
       An Item object
    """
    item = session.query(Item).filter(Item.title.like(title), category_id == category_id).first()
    return item

def get_item_by_title_category(title, category_name):
    """
    Return an item

    Args:
      title: the item's title.
      category_name: category's name
    
    Returns:
       An Item object
    """
    category = get_category_by_name(category_name)
    return get_item_by_title(title, category.id)

def get_lastest_items(number):
    """
    Return the lastest items

    Args:
      number: the number of items.
   
    Returns:
       A list of Item objects
    """
    items = session.query(Item).order_by(Item.id.desc())[0:number]
    return items

# item View functions
def get_items_view(category_id):
    """
    Return the items related to a category

    Args:
      category_id: the category's id.
      
    Returns:
       A list of tuples, each of which contains (item, category):
         item: an Item object
         category: an Category object       
    """
    items_view = session.query(Item,Category).filter(Item.category_id == Category.id, 
                                                     Item.category_id == category_id).all()
    return items_view

def get_items_by_name_view(category_name):
    """
    Return the items related to a category

    Args:
      category_name: the category's name.
      
    Returns:
       A list of tuples, each of which contains (item, category):
         item: an Item object
         category: an Category object       
    """
    category = get_category_by_name(category_name)
    return get_items_view(category.id)

def get_item_view(item_id):
    """
    Return an item

    Args:
      item_id: the item's id.
      
    Returns:
       A tuple, that contains (item, category):
         item: an Item object
         category: an Category object
    """
    items_view = session.query(Item,Category).filter(Item.category_id == Category.id, 
                                                     Item.id == item_id).first()
    return items_view

def get_item_by_title_view(title, category_id):
    """
    Return an item

    Args:
      title: the item's title.
      category_id: category's id
    
    Returns:
       A tuple, that contains (item, category):
         item: an Item object
         category: an Category object
    """
    items_view = session.query(Item,Category).filter(Item.category_id == Category.id, 
                                                     Item.title.like(title), 
                                                     Item.category_id == category_id).first()
    return items_view

def get_item_by_title_category_view(title, category_name):
    """
    Return an item

    Args:
      title: the item's title.
      category_name: category's name
    
    Returns:
       A tuple, that contains (item, category):
         item: an Item object
         category: an Category object
    """
    category = get_category_by_name(category_name)
    return get_item_by_title_view(title, category.id)

def get_lastest_items_view(number):
    """
    Return the lastest items

    Args:
      number: the number of items
   
    Returns:
       A list of tuples, each of which contains (item, category):
         item: an Item object
         category: an Category object       
    """
    items_view = session.query(Item,Category).filter(
                               Item.category_id == Category.id).order_by(Item.id.desc())[0:number]
    return items_view

# Items operations
def add_item(item):
    """
    Add an item to the database

    Args:
      item: an item object
    """
    session.add(item)
    session.commit()

def update_item(item_id, item):
    """
    Update an item in the database

    Args:
      item_id: item's id
      item: an item object
    """
    current_item = get_item(item_id)
    
    current_item.title = item.title
    current_item.description = item.description
    current_item.category_id = item.category_id
    
    session.add(current_item)
    session.commit()

def delete_item(item_id):
    """
    Delete an item in the database

    Args:
      item_id: item's id
    """
    item = get_item(item_id)
    session.delete(item)
    session.commit()
    
def build_item(title, description, category_id):
    """
    Return an item

    Args:
      title: the item's title
      description: the item's description
      category_id: the item's category id
   
    Returns:
       A list of tuples, each of which contains (item, category):
         item: an Item object
         category: an Category object       
    """
    return Item(title = title, description = description, category_id = category_id)


                                        