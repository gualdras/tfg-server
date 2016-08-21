from google.appengine.ext import ndb

class KeyWord(ndb.Model):
	keyWord = ndb.StringProperty()
	count = ndb.IntegerProperty()


class Tag(ndb.Model):
	tag = ndb.StringProperty()
	probability = ndb.FloatProperty()
	
	def tag2json(self):
		tag = {self.tag: self.probability}


class Image(ndb.Model):
	blobKey = ndb.StringProperty()
	tags = ndb.StructuredProperty(Tag, repeated=True)
	keyWords = ndb.StructuredProperty(KeyWord, repeated=True)
	link = ndb.StringProperty()
	siteLink = ndb.StringProperty()
	flickrTags = ndb.StringProperty(repeated=True)
	
	def imageComplete2json(self):
		tags = {}
		for t in self.tags:
			tags[t.tag] = t.probability
		iDetails = {"tags": tags, "keyWords": self.keyWords, "link":self.link, "siteLink":self.siteLink}
		return iDetails	

	def update_key_words(self, newKeyWords):
		update_key_words(self, newKeyWords)


class User(ndb.Model):
	phoneNumber = ndb.StringProperty()
	regID = ndb.StringProperty()
	keyWords = ndb.StructuredProperty(KeyWord, repeated=True)

	def user2json(self):
		return {"user" :self.key.id()}

	def user_complete2json(self):
		u_details = {"phoneNumber": self.key.id(), "regID": self.regID}
		return u_details

	@classmethod
	def get_all(self):
		aux_list = []
		for item in User.query():
			aux_list.append(item.user2json())
		return aux_list

	def update_key_words(self, new_key_words):
		update_key_words(self, new_key_words)


class ImageUsed(ndb.Model):
	image = ndb.KeyProperty(kind=Image)
	user = ndb.KeyProperty(kind=User)
	count = ndb.IntegerProperty()


class RelatedUsers(ndb.Model):
	user1 = ndb.KeyProperty(kind=User)
	user2 = ndb.KeyProperty(kind=User)
	relation = ndb.IntegerProperty()

	def get_related_user(self, user):
		if self.user1 == user:
			return self.user2
		else:
			return self.user1







