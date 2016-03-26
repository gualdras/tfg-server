#!/usr/bin/python
# -*- coding:utf-8; tab-width:4; mode:python -*-

import json
from flask import Flask, jsonify, abort, make_response, request, url_for
from gcm import GCM
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
import httplib as http
from itemTypes import User


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
REG_ID = "regID"
FROM = "phoneNumberFrom"
PHONE_NUMBER = "phoneNumber"
USERS = "contacts"

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
        abort(httlib.NOT_FOUND)
       
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
    
    params = json.dumps({"data": {MESSAGE: u[MESSAGE], FROM: u[FROM]}, "to": user.regID})
       
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
    
@app.route("/upload_form", methods=[GET])
def manager_upload_form():
	if request.method == GET:
		return upload()
			
def upload():
	uploadUri = blobstore.create_upload_url('/upload_photo')
    return make_response(uploadUri, http.OK)

    
@app.route("/upload_photo", methods=[POST])
def manager_upload_photo():
	if request.method == POST:
		upload_photo()
	
def upload_photo():
	f = request.files['file']
	header = f.headers['Content-Type']
	parsed_header = parse_options_header(header)
	blob_key = parsed_header[1]['blob-key']
	return blob_key
        
@app.route("/img/<id_blob>", methods=[GET])
def manager_download_photo(id_blob):
	if request.method == GET:
		return download_photo()
	
def download_photo(id_blob):
    blob_info = blobstore.get(id_blob)
    response = make_response(blob_info.open().read())
    response.headers['Content-Type'] = blob_info.content_type
    return response
    
if __name__ == '__main__':
    app.run(debug=True)
