from itemTypes import User, Image, Tag, KeyWord, ImageUsed, RelatedUsers
from google.appengine.ext import ndb
import numpy
import math
import tfg_server
import json


LIMIT_OF_RUSERS = 5
NUMBER_OF_IMAGES = 10
IMAGES_CONTENT = int(NUMBER_OF_IMAGES * 0.2)
IMAGES_COLLABORATIVE = int(NUMBER_OF_IMAGES * 0.4)
MINIMUM_RELATION = 0

PICTOGRAM_TAG = ["__pictogram__"]



def get_images_collaborative(user, key_words, pictograms):
	def callback(images_used):
		return images_used.user

	recommended_images = pictograms
	images = Image.query(ndb.OR(Image.keyWords.keyWord.IN(key_words), Image.tags.tag.IN(key_words))).fetch(keys_only=True)

	if len(images) > 0:
		query = ImageUsed.query(ImageUsed.image.IN(images))
		if query.count() > 0:
			users = query.map(callback)
			query = RelatedUsers.query(ndb.OR(RelatedUsers.user1 == user, RelatedUsers.user2 == user)).filter(
										ndb.OR(RelatedUsers.user1.IN(users), RelatedUsers.user2.IN(users))).order(-
										RelatedUsers.relation)

			related = query.fetch(LIMIT_OF_RUSERS)
			for ru in related:
				if ru.relation > MINIMUM_RELATION:
					related_user = ru.get_related_user(user)
					images_used = ImageUsed.query(ImageUsed.user == related_user, ImageUsed.image.IN(images)).order(ImageUsed.count)
					for image_used in images_used:
						image = image_used.image
						if not (image.id() in recommended_images):
							recommended_images.append({tfg_server.BLOB: image.id(), tfg_server.LINK: image.get().link})
							break
					if len(recommended_images) > IMAGES_COLLABORATIVE:
						break

				else:
					break
	return recommended_images


def get_images_content(user):
	favorite_sites = []
	sites = {}
	images_used = ImageUsed.query(ImageUsed.user == user)
	for image_used in images_used:
		image = image_used.image.get()
		try:
			sites[image.siteLink] += math.log(image_used.count)
		except KeyError:
			sites[image.siteLink] = math.log(image_used.count)

	if len(sites) > 0:
		median = int(numpy.median(sites.values()))

		sorted_sites = sorted(sites, key=sites.__getitem__, reverse=True)

		for i in range(IMAGES_CONTENT):
			if i < len(sorted_sites) and sites[sorted_sites[i]] > 2 * median:
				favorite_sites.append(sorted_sites[i])
			else:
				break
	return favorite_sites

def get_knowledge_site(categories):

	with open("knowledge_sites.json") as data_file:
		category_sites = json.load(data_file)

	for category in categories:
		if category in category_sites:
			return category_sites[category]

def get_pictograms(key_words):
	images = []
	pictograms = Image.query(Image.keyWords.keyWord.IN(PICTOGRAM_TAG), Image.tags.tag.IN(key_words))

	for pictogram in pictograms:
		images.append({tfg_server.BLOB: pictogram.blobKey, tfg_server.LINK: pictogram.link})

	return images
