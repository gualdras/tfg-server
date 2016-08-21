from itemTypes import User, Image, Tag, KeyWord, ImageUsed, RelatedUsers
from google.appengine.ext import ndb
import numpy
import tfg_server


LIMIT_OF_RUSERS = 5
NUMBER_OF_IMAGES = 10
IMAGES_CONTENT = NUMBER_OF_IMAGES * 0.3
MINIMUM_RELATION = 20


def get_images_collaborative(user, key_words):
	def callback(images_used):
		return images_used.user

	collaborative_images = []
	images = Image.query(ndb.OR(Image.keyWords.keyWord.IN(key_words), Image.tags.tag.IN(key_words))).fetch(keys_only=True)

	users = ImageUsed.query(ImageUsed.image.IN(images)).map(callback)

	query = RelatedUsers.query(ndb.OR(RelatedUsers.user1 == user, RelatedUsers.user2 == user)).filter(
								ndb.OR(RelatedUsers.user1.IN(users), RelatedUsers.user2.IN(users))).order(-
								RelatedUsers.relation)

	related = query.fetch(LIMIT_OF_RUSERS)
	for ru in related:
		if ru.relation > MINIMUM_RELATION:
			searching = True
			related_user = ru.get_related_user(user)
			images_used = ImageUsed.query(ImageUsed.user == related_user, ImageUsed.img.IN(images)).order(ImageUsed.count)
			while searching:
				image = images_used.pop()
				if not (image.id() in collaborative_images):
					collaborative_images.append({tfg_server.BLOB: image.id(), tfg_server.LINK: image.get().link})
					searching = False
			if len(collaborative_images) > MINIMUM_RELATION:
				break

		else:
			break
	return collaborative_images


def get_images_content(user):
	favorite_sites = []
	sites = {}
	total_sites = 0
	images_used = ImageUsed.query(ImageUsed.user == user)
	for image_used in images_used:
		image = image_used.image
		try:
			sites[image.siteLink] += 1
		except KeyError:
			sites[image.siteLink] = 1

	median = int(numpy.median(sites.values()))

	sorted_sites = sorted(sites, key=sites.__getitem__, reverse=True)

	for i in range(IMAGES_CONTENT):
		if sites[sorted_sites[i]] > 2* median:
			favorite_sites.append(sorted_sites[i])
		else:
			break
	return favorite_sites



