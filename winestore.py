#!/usr/bin/python
# -*- coding:utf-8; tab-width:4; mode:python -*-

import json
from flask import Flask, jsonify, abort, make_response, request, url_for
from google.appengine.ext import ndb

from itemTypes import Wine, User, Cart, WineType

app = Flask(__name__)
app.config['DEBUG'] = True


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)

@app.errorhandler(409)
def not_found(error):
    return make_response(jsonify({'error': 'Email already in use'}), 409)

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad Request'}), 404)

@app.errorhandler(501)
def not_found(error):
    return make_response(jsonify({'error': 'Not Implemented'}), 501)





	
@app.route('/users', methods = ['GET', 'POST'])
def manager_users():
    if request.method == 'GET':
        return getContacts()
    if request.method == 'POST':
        return newContact()

def getUsers():
    return make_response(jsonify({'users': Contact.getAll()}), 200)
        
def newUser():
    if not request.json or not all(x in request.json for x in {'phoneNumber', 'regID'}):
        abort(400)
       
    u = request.json
    
	user = User(
		phoneNumber = u['phoneNumber'],
		regID = u['regID'],
		id = u['phoneNumber'])
	
	user.put()
		
    return make_response(jsonify({'created':user.key.id()}), 201)

@app.route('/users/<path:id_user>', methods = ['GET', 'PUT', 'DELETE'])
def manager_user(id_user):
    if request.method == 'GET':
        return getUserDetails(id_user)
    if request.method == 'PUT':
        return updateUser(id_user)
    if request.method == 'DELETE':
        return deleteUser(id_user)

def getUserDetails(id_user):
    key = ndb.Key(User, id_user)
	user = key.get()
    return make_response(jsonify(user.userComplete2json()), 200)

def updateUser(id_user):
	if not request.json or not 'regID' in request.json:
		abort(400)
		
	key = ndb.Key(User, id_user)
	user = key.get()
	
    u = request.json
    
    user.regID = u['regID']
			
	user.put()
		
	return make_response(jsonify({'updated':user.to_dict()}), 200)
	
def deleteUser(id_user):
    key = ndb.Key(User, id_user)
	key.delete()
    return make_response(jsonify({'deleted':id_user}), 200)
        
@app.route('/users/<path:id_user>/carts', methods = ['POST'])
def manager_users_carts(id_user):
    if request.method == 'POST':
        return addCart(id_user)

def addCart(id_user):
	
	c = request.json
	
    cart = Cart(items = c['items'])
    if 'name' in c:
		cart.name = c['name']
	
	cartKey = cart.put()
	
	userKey = ndb.Key(User, id_user)
	user = userKey.get()	
	user.carts.append(cartKey)
	user.put()
	
    return make_response(jsonify({'created':cart.key.id()}), 201)
    
@app.route('/users/<path:id_user>/carts/<path:id_cart>', methods = ['DELETE'])
def manager_user_cart(id_user, id_cart):
    if request.method == 'DELETE':
        return deleteCart(id_user, int(id_cart))
   
#No se si hace falta borrar tambien la referencia 
def deleteCart(id_user, id_cart):
    cartKey = ndb.Key(Cart, id_cart)
    
    userKey = ndb.Key(User, id_user)
    user = userKey.get()
    user.carts.remove(cartKey)
    
    cartKey.delete()
    
    return make_response(jsonify({'deleted':id_cart}), 200)
    
############################
@app.route('/carts/<path:id_cart>/items', methods = ['GET', 'POST'])
def manager_user_cart_items(id_cart):
    if request.method == 'GET':
        return getItems(int(id_cart))
    if request.method == 'POST':
        return addItem(int(id_cart))
        
def getItems(id_cart):
    key = ndb.Key(Cart, id_cart)
    cart = key.get()
    wines = []
    for kw in cart.items:
		wine = kw.get()
		wines.append(str(kw.id()) + " " + wine.name)
    return make_response(jsonify({"items":wines}), 200)
        
def addItem(id_cart):   
	
	w = request.json
	
	id_item = int(w['id'])
	
	wineKey = ndb.Key(Wine, id_item)
	cartKey = ndb.Key(Cart, id_cart)
	cart = cartKey.get()
	cart.items.append(wineKey)
	
	cart.put()
	
	return make_response(jsonify({'added': wineKey.id()}), 201)
    
@app.route('/carts/<path:id_cart>/items/<path:id_item>', methods = ['PUT', 'DELETE'])
def manager_user_cart_item(id_cart, id_item):    
    if request.method == 'PUT':
        return updateItem(int(id_cart), int(id_item))
    if request.method == 'DELETE':
        return deleteItem(int(id_cart), int(id_item))


    
    
#No tiene sentido actualizar los vinos aqui. Este metodo hace lo mismo 
#que updateWine
def updateItem(id_cart, id_item):
    wineKey = ndb.Key(Wine, id_item)
    wine = wineKey.get()
    
    w = request.json
    for k in w:
		if k == 'grade':
			wine.grade = w['grade']
		if k == 'size':
			wine.size = w['size']
		if k == 'varietals':
			wine.varietals.append(w['varietals'])
		if k == 'do' :
			wine.do = w['do']
		if k == 'price':
			wine.price = w['wine']
		if k == 'name' :
			wine.name = w['name']
		if k == 'photo' :
			wine.photo = w['photo']
			
	wine.put()
		
    return make_response(jsonify({'updated':wine.to_dict()}), 200)
    
    
def deleteItem(id_cart, id_item):
    wineKey = ndb.Key(Wine, id_item)
    
    cartKey = ndb.Key(Cart, id_cart)
    cart = cartKey.get()
    
    cart.items.remove(wineKey)
    cart.put()
    
    return make_response(jsonify({'deleted from cart':id_item}), 200)
    
    
@app.route('/types', methods = ['POST', 'GET'])
def manager_types():
	if request.method == 'POST':
		return addType()
	if request.method == 'GET':
		return getTypes()
		
def addType():
    if not request.json or not 'name' in request.json:
		abort(400)
	
	t = request.json
	
	wineType = WineType(name = t['name'], id = t['name'])
	idType = wineType.put()
	return make_response(jsonify({'added': idType.id()}))
	
def getTypes():
	return make_response(jsonify({"types": WineType.getAll()}), 200)
	
@app.route('/wines', methods = ['POST', 'GET', 'DELETE', 'PUT'])
def manager_wines():  
    if request.method == 'GET':
		if request.args.get('name'):
			return wineByName()
		if request.args.get('min'):
			return wineBetweenPrices()
		if request.args.get('type'):
			return wineByType() 
	if request.method == 'POST':	
		return addWine()
    if request.method == 'GET':
		return getWines()
    if request.method == 'DELETE':
        return deleteWines()
		

def addWine():
    if not request.json or not all(x in request.json for x in {'varietals', 'name'}):
        abort(400)
    
    w = request.json
    if(not 'do' in request.json):
        w['do'] = False
    if(not 'grade' in request.json):
        w['grade'] = 12
    if(not 'size' in request.json):
        w['size'] = 75
        
    if 'type' in w:
		parentKey = ndb.Key(WineType, w['type'])
				 
		wine = Wine(
			varietals = w['varietals'],
			do = w['do'],
			name = w['name'],
			parent = parentKey)
	else:		
		wine = Wine(
			varietals = w['varietals'],
			do = w['do'],
			name = w['name'])
		
	if 'grade' in w:
		wine.grade = w['grade']
	if 'size' in w:
		wine.size = w['size']
	if 'price' in w:
		wine.price = w['price']
	if 'photo' in w:
		wine.photo = w['photo']
	if 'cask' in w:
		wine.cask = c['cask']
	if 'bottle' in w: 
		wine.bottle = c['bottle']
		
		
	wine.put()
	
	return make_response(jsonify({'created':wine.key.id()}), 201)

def getWines():
    return make_response(jsonify({'wines': Wine.getAll()}), 200)

#TODO
def wineByType():
	idAncestro = ndb.Key(WineType, request.args.get('type'))
	print(idAncestro)
	result = getJSONlist(Wine.query(ancestor = idAncestro))
	return make_response(jsonify({"wines":result}),200)
	
	
def wineByName():
	result = getJSONlist(Wine.query(Wine.name == request.args.get('name')))
	return make_response(jsonify({"wines":result}),200)
	
def wineBetweenPrices():
	min = float(request.args.get('min'))
	max = float(request.args.get('max'))
	result = getJSONlist(Wine.query(Wine.price > min, Wine.price < max))
	return make_response(jsonify({"wines":result}),200)  
    
def deleteWines():
    Wine.deleteAll()
    return make_response(jsonify({'deleted':Wine.getAll()}), 200)


@app.route('/wines/<path:id_wine>', methods = ['PUT', 'GET', 'DELETE'])
def manager_wine(id_wine):  
    if request.method == 'PUT':
        return updateWine(int(id_wine))
    if request.method == 'GET':
        return getWineProperties(int(id_wine))
    if request.method == 'DELETE':
        return deleteWine(int(id_wine))
    
def updateWine(id_wine):
    wineKey = ndb.Key(Wine, id_item)
    wine = wineKey.get()
    
    w = request.json
    for k in w:
		if k == 'grade':
			wine.grade = c['grade']
		if k == 'size':
			wine.size = c['size']
		if k == 'varietals':
			wine.varietals.append(c['varietals'])
		if k == 'do':
			wine.do = c['do']
		if k == 'price':
			wine.price = c['price']
		if k == 'name': 
			wine.name = c['name']
		if k == 'photo': 
			wine.photo = c['photo']
		if k == 'cask':
			wine.cask = c['cask']
		if k == 'bottle': 
			wine.bottle = c['bottle']
			
	wine.put()
		
    return make_response(jsonify({'updated':wine.key.id()}), 200)
    
def deleteWine(id_wine):
    wineKey = ndb.Key(Wine, id_wine)
    wineKey.delete()
    return make_response(jsonify({'deleted': id_wine}))

def getWineProperties(id_wine):
	wineKey = ndb.Key(Wine, id_wine)
    wine = wineKey.get()
    
    return make_response(jsonify({'wine': wine.to_dict()}))


def getJSONlist(entities):
		auxJSON = []
		for it in entities:
			auxJSON.append(it.wine2json())
		return auxJSON
		

if __name__ == '__main__':
    app.run(debug=True)
