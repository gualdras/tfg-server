#!/usr/bin/python
# -*- coding:utf-8; tab-width:4; mode:python -*-

import json
from flask import Flask, jsonify, abort, make_response, request
from gcm import GCM
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
import httplib as http
from werkzeug import parse_options_header
import os.path
from itemTypes import User, Image, Tag, KeyWord, ImageUsed, RelatedUsers
import recommender_system


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

IMAGE = "image"
BLOB = "blob"
TAG = "tag"
KEY_WORDS = "key_words"
CATEGORIES = "categories"
LINK = "link"
SITE_LINK = "site_link"


@app.errorhandler(http.NOT_FOUND)
def not_found(error):
	return make_response(jsonify({'error': 'Not Found'}), http.NOT_FOUND)


@app.route('/users', methods = [POST, PUT])
def manager_users():
	if request.method == PUT:
		return check_registered_users()
	if request.method == POST:
		return new_user()


def new_user():
	if not request.json or not all(x in request.json for x in {PHONE_NUMBER, REG_ID}):
		abort(http.NOT_FOUND)

	u = request.json

	user = User(phoneNumber=u[PHONE_NUMBER], regID=u[REG_ID], id=u[USER_ID])

	user.put()

	return make_response(jsonify({'created':user.key.id()}), http.CREATED)


def check_registered_users():
	users = request.json[USERS]
	matches = []

	for u in users:
		key = ndb.Key(User, u[USER_ID])
		user = key.get()
		if user:
			matches.append(u)

	return make_response(jsonify({USERS: matches}), http.OK)


@app.route('/users/<path:id_user>', methods=[PUT, DELETE])
def manager_user(id_user):
	if request.method == PUT:
		if FROM in request.json:
			return send_msg(id_user)
		return update_user(id_user)
	if request.method == DELETE:
		return delete_user(id_user)


def update_user(id_user):
	if not request.json or not (REG_ID in request.json):
		abort(http.BAD_REQUEST)

	key = ndb.Key(User, id_user)
	user = key.get()
	u = request.json

	user.regID = u[REG_ID]

	user.put()

	return make_response(jsonify({'updated': user.to_dict()}), http.OK)


def send_msg(id_user):
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


def delete_user(id_user):
	key = ndb.Key(User, id_user)
	key.delete()
	return make_response(jsonify({'deleted':id_user}), http.OK)


'''
Blobstore for photos management
'''


# Get blob uri
@app.route("/upload_form", methods=[GET])
def manager_upload_form():
	if request.method == GET:
		return upload()


def upload():
	upload_uri = blobstore.create_upload_url('/upload_photo')
	return make_response(upload_uri, http.OK)


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


@app.route("/images", methods=[GET])
def manager_images():
	if request.method == GET:
		if request.args.get(LINK):
			return get_image_by_link()
		return get_images_by_keywords()


def get_image_by_link():
	image = Image.query(Image.link == request.args.get(LINK))

	if image.get() is not None:
		return make_response(jsonify({BLOB: image.get().blobKey}), http.OK)
	else:
		return make_response("No images", http.NOT_FOUND)


def get_images_by_keywords():
	u = request.args.get(USER_ID)
	user = ndb.Key(User, u)
	key_words = request.args.getlist(KEY_WORDS)
	categories = request.args.getlist(CATEGORIES)

	knowledge_site = recommender_system.get_knowledge_site(categories)
	content_sites = recommender_system.get_images_content(user)

	sites = content_sites + [knowledge_site]

	pictograms = recommender_system.get_pictograms(key_words)
	collaborative_images = recommender_system.get_images_collaborative(user, key_words, pictograms)

	return make_response(jsonify({IMAGE: collaborative_images, SITE_LINK: sites}), http.OK)


@app.route("/images/<path:id_img>", methods=[GET, PUT])
def manager_image(id_img):
	if request.method == GET:
		return download_image(id_img)
	if request.method == PUT:
		return edit_img(id_img)


def download_image(id_img):
	blob_info = blobstore.get(id_img)
	response = make_response(blob_info.open().read())
	response.headers['Content-Type'] = blob_info.content_type
	return response


def edit_img(id_img):
	if not request.json or not all(x in request.json for x in {KEY_WORDS, USER_ID}):
		abort(http.BAD_REQUEST)

	key = ndb.Key(Image, id_img)
	image = key.get()

	img = request.json

	user = (ndb.Key(User, img[USER_ID])).get()

	new_key_words = img[KEY_WORDS]
	update_key_words(image, new_key_words)

	if LINK in img:
		image.link = img[LINK]

	if SITE_LINK in img:
		image.siteLink = img[SITE_LINK]

	if TAG in img:
		tags = img[TAG]
		for k in tags:
			image.tags.append(Tag(tag=k, probability=tags[k]))

	image.put()

	update_key_words(user, new_key_words)
	user.put()

	update_images_used(image.key, user.key)

	return make_response(jsonify({'updated': image.key.id()}), http.OK)


def update_key_words(entity, new_key_words):
	updated_key_words = []
	old_key_words = entity.keyWords

	for k in old_key_words:
		if k.keyWord in new_key_words:
			updated_key_words.append(KeyWord(keyWord=k.keyWord, count=k.count + 1))
			new_key_words.remove(k.keyWord)
		else:
			updated_key_words.append(k)
	for keyWord in new_key_words:
		updated_key_words.append(KeyWord(keyWord=keyWord, count=1))

	entity.keyWords = updated_key_words
	entity.put()


def update_images_used(image, user):
	images_used = ImageUsed.get_by_id(image.id() + user.id())

	if images_used is not None:
		images_used.count += 1
	else:
		images_used = ImageUsed(image=image, user=user, count=1, id=image.id() + user.id())
		update_related_users(user, image)

	images_used.put()


def update_related_users(user1, image):
	images_used = ImageUsed.query(ImageUsed.image == image)
	for imgUsed in images_used:
		user2 = imgUsed.user
		r_user = RelatedUsers.query(RelatedUsers.user1.IN([user1, user2]),
		                            RelatedUsers.user2.IN([user1, user2])).get()
		if r_user is not None:
			r_user.relation += 1
		else:
			r_user = RelatedUsers(user1=user1, user2=user2, relation=1)
		r_user.put()


@app.route("/pictograms/<path:id_img>", methods=[PUT])
def manager_pictogram(id_img):
	return update_pictogram(id_img)


def update_pictogram(id_img):
	key = ndb.Key(Image, id_img)
	image = key.get()

	img = request.json

	tags = img[TAG]

	key_words = []
	key_word = KeyWord(keyWord="__pictogram__", count=1)
	key_words.append(key_word)
	image.keyWords = key_words
	for k in tags:
		image.tags.append(Tag(tag=k, probability=tags[k]))

	image.put()

	return make_response(jsonify({'updated': image.key.id()}), http.OK)


@app.route("/try", methods=[GET])
def manager_try():
	categories = request.args.getlist(CATEGORIES)

	with open("knowledge_sites.json") as data_file:
		category_sites = json.load(data_file)

	for category in categories:
		if category in category_sites:
			return make_response(jsonify({category: category_sites[category]}), 200)
	return make_response(jsonify(categories), 200)


if __name__ == '__main__':
	app.run(debug=True)
