#!/usr/bin/python
# -*- coding:utf-8; tab-width:4; mode:python -*-

import json
from flask import Flask, jsonify, abort, make_response, request, url_for
from gcm import GCM
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
import httplib as http
from itemTypes import User, Image, Tag, KeyWord, ImageUsed
from werkzeug import parse_options_header


app = Flask(__name__)
app.config['DEBUG'] = True


#http methods

POST = 'POST'
GET = 'GET'
PUT = 'PUT'
DELETE = 'DELETE'

#GCM stuff

API_KEY = 'AIzaSyCFo39giOeV_OH0rE6_H7BWgGNisAeI5UM'
GCM_HEADERS = {"Content-type": "application/json", "Authorization": "key=" + API_KEY}
GCM_SEND_URL = "gcm-http.googleapis.com/gcm/send"

#Client shared constants

MESSAGE = "message"
TYPE = "type"
REG_ID = "regID"
FROM = "phoneNumberFrom"
PHONE_NUMBER = "phoneNumber"
USERS = "contacts"
USER_ID = PHONE_NUMBER

TAG = "tag"
KEY_WORDS = "key_words"
LINK = "link"
SITE_LINK = "site_link"
FLICKR_TAGS = "flickr_tags"

@app.errorhandler(http.NOT_FOUND)
def not_found(error):
    return make_response(jsonify({'error': 'Not Found'}), http.NOT_FOUND)

@app.errorhandler(409)
def not_found(error):
    return make_response(jsonify({'error': 'Email already in use'}), 409)


@app.errorhandler(501)
def not_found(error):
    return make_response(jsonify({'error': 'Not Implemented'}), 501)




	
@app.route('/users', methods = [GET, POST])
def manager_users():
    if request.method == GET:
        return getUsers()
    if request.method == POST:
        if USERS in request.json:
            return checkRegisteredUsers()
        return newUser()

def getUsers():
    return make_response(jsonify({'users': User.getAll()}), http.OK)
        
def newUser():
    if not request.json or not all(x in request.json for x in {PHONE_NUMBER, REG_ID}):
        abort(http.NOT_FOUND)
       
    u = request.json
    
	user = User(
		phoneNumber = u[PHONE_NUMBER],
		regID = u[REG_ID],
		id = u[PHONE_NUMBER])
	
	user.put()
		
    return make_response(jsonify({'created':user.key.id()}), http.CREATED)

def checkRegisteredUsers():
    users = request.json[USERS]
    matches = []
    
    for u in users:
        key = ndb.Key(User, u[PHONE_NUMBER])
        user = key.get()
        if user:
            matches.append(u)
            
    return make_response(jsonify({USERS: matches}), http.OK)            
    

@app.route('/users/<path:id_user>', methods = [GET, PUT, DELETE, POST])
def manager_user(id_user):
    if request.method == GET:
        return getUserDetails(id_user)
    if request.method == PUT:
        return updateUser(id_user)
    if request.method == DELETE:
        return deleteUser(id_user)
    

def getUserDetails(id_user):
    key = ndb.Key(User, id_user)
	user = key.get()
    return make_response(jsonify(user.userComplete2json()), http.OK)

def updateUser(id_user):
	if not request.json or not REG_ID in request.json:
		abort(http.NOT_FOUND)
		
	key = ndb.Key(User, id_user)
    user = key.get()
    u = request.json
    
    user.regID = u[REG_ID]
			
	user.put()
		
	return make_response(jsonify({'updated':user.to_dict()}), http.OK)
	
def deleteUser(id_user):
    key = ndb.Key(User, id_user)
	key.delete()
    return make_response(jsonify({'deleted':id_user}), http.OK)
       
@app.route('/users/<path:id_user>/send', methods = [POST])
def manager_user_send(id_user): 
    if request.method == POST:
        return sendMsg(id_user)
    
def sendMessage(id_user):
    key = ndb.Key(User, id_user)
    user = key.get()

    gcm = GCM(API_KEY)
    
    data = request.json
    reg_id = [user.regID]
    
    response = gcm.json_request(registration_ids = reg_id, data = data)
	return make_response(jsonify({'sent':data}), http.OK)	
    
def sendMsg(id_user):
	u = request.json
    key = ndb.Key(User, id_user)
    user = key.get()   
    
    params = json.dumps({"data": {FROM: u[FROM], TYPE: u[TYPE], MESSAGE: u[MESSAGE]}, "to": user.regID})
       
    conn = http.HTTPSConnection(GCM_SEND_URL)
    conn.request("POST", "", params, GCM_HEADERS)
    
    response = conn.getresponse()
    
    status = response.status
    data = response.read()
    
    conn.close
    
    return make_response(jsonify({'response':data}), status)  
    
'''
Blobstore for photos management
'''

# Get blob uri
@app.route("/upload_form", methods=[GET])
def manager_upload_form():
	if request.method == GET:
		return upload()
			
def upload():
	uploadUri = blobstore.create_upload_url('/upload_photo')
    return make_response(uploadUri, http.OK)

# upload photo and get blob_key
@app.route("/upload_photo", methods=[POST])
def manager_upload_photo():
	if request.method == POST:
		return upload_photo()
	
def upload_photo():
	f = request.files['file']
	header = f.headers['Content-Type']
	parsed_header = parse_options_header(header)
	blob_key = parsed_header[1]['blob-key']
	
	image = Image(blobKey=blob_key, id=blob_key)

	image.put()

	return make_response(blob_key, http.CREATED)
       
#Download photo
@app.route("/img/<id_blob>", methods=[GET])
def manager_download_photo(id_blob):
	if request.method == GET:
		return download_photo(id_blob)
	
def download_photo(id_blob):
    blob_info = blobstore.get(id_blob)
    response = make_response(blob_info.open().read())
    response.headers['Content-Type'] = blob_info.content_type
    return response

'''
@app.route("/images", methods=[POST])
def manager_imgs():
	if request.method == POST:
		return addInformation()

def addImg():
	if not request.json or not all(x in request.json for x in {LINK, SITE_LINK, TAG, KEY_WORDS, USER_ID}):
		abort(http.NOT_FOUND)

	img = request.json
	user = (ndb.Key(User, img[USER_ID])).get()

	image = Image(
		link = img[LINK],
		siteLink = img[SITE_LINK],
		id = img[LINK])

	tags = img[TAG]
	keyWords= img[KEY_WORDS]

	for k in tags:
		image.tags.append(Tag(tag=k, probability=tags[k]))

	for k in keyWords:
		image.keyWords.append(KeyWord(keyWord=k, count=keyWords[k]))

	if FLICKR_TAGS in img:
		image.flickr_tags = img[FLICKR_TAGS]

	image.put()


	updateUserKeyWords(user, keyWords)

	updateImageUsed(user, image)

	user.put()

	return make_response(image.key.id(), http.OK)
'''

@app.route("/images/<path:id_img>", methods=[PUT])
def manager_img(id_img):
	if request.method == PUT:
		return editImg(id_img)

def editImg(id_img):
	if not request.json or not all(x in request.json for x in {KEY_WORDS, USER_ID}):
		abort(http.NOT_FOUND)
	
	key = ndb.Key(Image, id_img)
	image = key.get()

	img = request.json

	user = (ndb.Key(User, img[USER_ID])).get()

	newKeyWords = img[KEY_WORDS]


		
	for k in newKeyWords:
		try:
			image.keyWords[k] = image.keyWords[k] + 1
		except TypeError:
			image.keyWords = {k:1}
		except KeyError:
			image.keyWords[k] = 1

	if LINK in img:
		image.link = img[LINK]
	
	if SITE_LINK in img:
		image.siteLink = img[SITE_LINK]
	
	if TAG in img:
		tags = img[TAG]
		for k in tags:
			image.tags.append(Tag(tag=k, probability=tags[k]))


	image.put()

	updateUserKeyWords(user, newKeyWords)
	updateImageUsed(user, image)

	user.put()

	return make_response(jsonify({'updated': image.key.id()}), http.OK)

def updateUserKeyWords(user, newKeyWords):
	keyWords = user.keyWords
	for k in newKeyWords:
		try:
			keyWords[k] = keyWords[k] + 1
		except TypeError:
			keyWords = {k:1}
		except KeyError:
			keyWords[k] = 1
		

def updateImageUsed(user, imgKey):
	imagesUsed = user.imagesUsed
	try:
		imagesUsed[imgKey] = imagesUsed[imgKey] + 1
	except TypeError:
		imagesUsed = {}
		imagesUsed[imgKey] = 1
	except KeyError:
		imagesUsed[imgKey] = 1
		

@app.route("/try/<path:id_img>", methods=[GET])
def manager_try(id_img):
	image = (ndb.Key(Image, id_img)).get()
	return make_response(jsonify(image.imageComplete2json()), 200)


    
if __name__ == '__main__':
    app.run(debug=True)
