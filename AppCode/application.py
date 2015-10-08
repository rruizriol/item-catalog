'''
Created on Sep 7, 2015

@author: Rembrandt
'''
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import dicttoxml

import db_helper

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

@app.route('/login')
def show_login():
    """Render the login page."""
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """User authentication using facebook credentials."""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token
    
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    
    url_graph = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token'
    url_graph += '&client_id=%s&client_secret=%s&fb_exchange_token=%s'
    
    url = url_graph % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    
    # Use token to get user info from API
    # strip expire tag from access token
    token = result.split("&")[0]
    
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    
    url = userinfo_url + '?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['facebook_id'] = data["id"]
    
    if 'email' in data:
        login_session['email'] = data["email"]
    else:
        login_session['email'] = ''   
        
    # The token must be stored in the login_session in order to properly logout, let's 
    # strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = userinfo_url + '/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]
    login_session['user_id'] = 0

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    """User logout if the user was authenticated using the facebook credentials."""
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']  
    
    del login_session['facebook_id'] 
    del login_session['access_token']    
    
    return "you have been logged out"

@app.route('/gconnect', methods=['POST'])
def gconnect():
    """User authentication using google credentials."""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Obtain authorization code, now compatible with Python3
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'
        
    if not login_session['username']:
        login_session['username'] = login_session['email'] 
    
    # user id    
    login_session['user_id']  = 0

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output

@app.route('/gdisconnect')
def gdisconnect():
    """User logout if the user was authenticated using the google credentials."""
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']     

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response
    
# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    """Logout process using the different authnetication providers used by the application."""  
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        elif login_session['provider'] == 'facebook':
            fbdisconnect()
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('catalog_page'))
    else:
        flash("You were not logged in")
        return redirect(url_for('catalog_page'))

@app.route('/')
@app.route('/catalog/')
def catalog_page():
    """Render the catalog page."""
    categories = db_helper.get_categories()
    lastest_items_view = db_helper.get_lastest_items_view(10)
    return render_template('catalog.html', items_view=lastest_items_view, 
                           categories=categories, category_name = None) 

@app.route('/catalog/<string:category_name>/')
def category_page(category_name):
    """Render a page with items associated to a category.

    Args:
      category_name: the category's name.
    """
    categories = db_helper.get_categories()
    category   = db_helper.get_category_by_name(category_name)
    items_view = db_helper.get_items_view(category.id)
    return render_template('category.html', items_view=items_view,
                           categories=categories, category_name = category_name) 
    
    
@app.route('/catalog/<string:category_name>/<string:item_title>/view')
@app.route('/catalog/<string:category_name>/<string:item_title>')
def view_item(category_name, item_title):
    """Render a page with the item information.

    Args:
      category_name: the category's name.
      item_title: the category's name.
    """
    categories = db_helper.get_categories()
    item_view = db_helper.get_item_by_title_category_view(item_title, category_name)
    return render_template('viewItem.html', item_view=item_view, categories = categories) 

@app.route('/catalog/add', methods=['GET', 'POST'])
def add_item():
    """Handle the logic related to add an item to the catalog"""
    if 'username' not in login_session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            # build an item object
            item = db_helper.build_item(request.form['title'], request.form['description']
                                        , request.form['category_id']);
            
            # check if the item exists (the item must by unique by category)
            item_view_db = db_helper.get_item_by_title(item.title, item.category_id)
            
            if not item_view_db:
                db_helper.add_item(item)
                return redirect(url_for('catalog_page'))
            else:
                categories = db_helper.get_categories()
                return render_template('addItem.html', categories=categories,
                                        message = 'An item with the same name exists')  
        else:
            categories = db_helper.get_categories()
            return render_template('addItem.html', categories=categories, message = '') 

@app.route('/catalog/<string:category_name>/<string:item_title>/edit', methods=['GET', 'POST'])
def edit_item(category_name, item_title):
    """Handle the logic related to edit an item to the catalog"""
    if 'username' not in login_session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            item_id = request.form['item_id']
            
            # build an item object
            item = db_helper.build_item(request.form['title'], request.form['description'], 
                                        request.form['category_id']);                                        
            
            # check if the item exists (the item must by unique by category)
            item_view_db = db_helper.get_item_by_title(item.title, item.category_id)
            
            # update the record if the item doesn't exists ot if exists is the sane
            # item that we are updating
            if not item_view_db or (item_view_db and item_view_db.id == item_id):
                db_helper.update_item(item_id, item)
                return redirect(url_for('category_page', category_name = category_name))
            else:
                categories = db_helper.get_categories()
                return render_template('editItem.html', item_view=item_view_db, 
                                       categories=categories, message = 'An item with the same name exists')
        else:
            categories = db_helper.get_categories()
            item_view = db_helper.get_item_by_title_category_view(item_title, category_name)
            return render_template('editItem.html', item_view=item_view,
                                    categories=categories, message = '') 

@app.route('/catalog/<string:category_name>/<string:item_title>/delete', methods=['GET', 'POST'])
def delete_item(category_name, item_title):
    """Handle the logic related to delete an item to the catalog"""
    if 'username' not in login_session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            item_id = request.form['item_id']
            db_helper.delete_item(item_id)
            return redirect(url_for('category_page', category_name = category_name))
        else:
            categories = db_helper.get_categories()
            item_view = db_helper.get_item_by_title_category_view(item_title, category_name)
            return render_template('deleteItem.html', item_view=item_view, categories=categories)     

# Json data
@app.route('/catalog.json')
def catalog_json():
    """Return the catalog data in a json format"""
    return jsonify(categories = catalog_dict())

@app.route('/catalog/categories.json')
def categories_json():
    """Return the catalog's categories data in a json format"""
    return jsonify(categories=categories_dict())

@app.route('/catalog/category/<string:category_name>.json')
def category_json(category_name):
    """
    Return the items related to a category.in a json format

    Args:
      category_name: the category's name.
    """
    return jsonify(category=category_dict(category_name))

@app.route('/catalog/category/<string:category_name>/<string:item_title>.json')
def item_json(category_name, item_title):
    """Return the item data in a json format.

    Args:
      category_name: the category's name.
      item_title: the category's name.
    """
    return jsonify(item=item_dict(category_name, item_title)) 

# Xml data
@app.route('/catalog.xml')
def catalog_xml():
    """Return the catalog data in an xml format"""
    data = catalog_dict()
    xml  = dicttoxml.dicttoxml(data, attr_type=False, custom_root='catalog')
    return render_xml(xml)

@app.route('/catalog/categories.xml')
def categories_xml():
    """Return the catalog's categories data in a xml format"""
    categories = categories_dict()
    xml  = dicttoxml.dicttoxml(categories, attr_type=False, custom_root='categories')
    return render_xml(xml)

@app.route('/catalog/category/<string:category_name>.xml')
def category_xml(category_name): 
    """
    Return the items related to a category.in a xml format

    Args:
      category_name: the category's name.
    """
    data = category_dict(category_name)
    xml  = dicttoxml.dicttoxml(data, attr_type=False, custom_root='category')  
    return render_xml(xml)

@app.route('/catalog/category/<string:category_name>/<string:item_title>.xml')
def item_xml(category_name, item_title):
    """Return the item data in an xml format.

    Args:
      category_name: the category's name.
      item_title: the category's name.
    """
    data = item_dict(category_name, item_title)
    xml  = dicttoxml.dicttoxml(data, attr_type=False, custom_root='item')  
    return render_xml(xml)

def render_xml(xml):
    """Render an xml response

    Args:
      xml: the data in xml format
    """
    response = make_response(xml, 200)
    response.headers['Content-Type'] = 'application/xml'
    return response

# Dictionary data
def catalog_dict():
    """Return the catalog data as a dictionary"""
    categories = db_helper.get_categories()
    
    categories_json = []
    
    for category in categories:
        category_json = category.serialize
        items = db_helper.get_items(category.id)
        
        items_json = []
        
        for item in items:
            items_json.append(item.serialize)
            
        category_json['items'] = items_json
        categories_json.append(category_json)
        
    return categories_json

def categories_dict():
    """Return the catalog's categories data as a dictionary"""
    items = db_helper.get_categories()
    return [item.serialize for item in items]

def category_dict(category_name):
    """
    Return the items related to a category as a dictionary

    Args:
      category_name: the category's name.
    """
    category = db_helper.get_category_by_name(category_name)
    
    category_json = category.serialize
    items = db_helper.get_items(category.id)
        
    items_json = []
    for item in items:
        items_json.append(item.serialize)
            
    category_json['items'] = items_json
    
    return category_json  

def item_dict(category_name, item_title):
    """Return the item data as a dictionary.

    Args:
      category_name: the category's name.
      item_title: the category's name.
    """
    category = db_helper.get_category_by_name(category_name)
    item = db_helper.get_item_by_title(item_title, category.id)
    return item.serialize  


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)