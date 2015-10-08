'''
Created on Sep 12, 2015

@author: Rembrandt
'''
import db_helper

items = db_helper.get_lastest_items_view(2)
for item in items:
    print item[0].title,item[1].name
