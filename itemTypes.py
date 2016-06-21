from google.appengine.ext import ndb

class KeyWord(ndb.Model):
	keyWord = ndb.StringProperty()
	count = ndb.IntegerProperty()


class Tag(ndb.Model):
	tag = ndb.StringProperty()
	probability = ndb.FloatProperty()
	
	def tag2json(self):
		tag = {tag: probability}


class ImageUsed(ndb.Model):
	img = ndb.KeyProperty()
	count = ndb.IntegerProperty()


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

	def updateKeyWords(self, newKeyWords):
		updateKeyWords(self, newKeyWords)


class User(ndb.Model):
	phoneNumber = ndb.StringProperty()
	regID = ndb.StringProperty()
	keyWords = ndb.StructuredProperty(KeyWord, repeated=True)
	imagesUsed = ndb.StructuredProperty(ImageUsed, repeated=True)
    
    
	def user2json(self):
		return {"user":self.key.id()}
        
	def userComplete2json(self):
		uDetails = {"phoneNumber": self.key.id(), "regID": self.regID}
		return uDetails
        
	@classmethod
	def getAll(self):
		auxList = []
		for item in User.query():
			auxList.append(item.user2json())
		return auxList

	
	def updateKeyWords(self, newKeyWords):
		updateKeyWords(self, newKeyWords)

	def updateImagesUsed(self, imgKey):
		updated = False
		updatedImagesUsed = []
		for img in self.imagesUsed:
			if img.key != imgKey
				updatedImagesUsed.append(img)
			else:
				updatedImagesUsed.append(ImageUsed(img = imgKey, count = img.count + 1)
				updated = True
		if !updated:
			updatedImagesUsed.append(ImageUsed(img = imgKey, count = 1))
		self.imagesUsed = updatedImagesUsed
		self.put()

def updateKeyWords(entity, newKeyWords):
		updatedKeyWords = []
		oldKeyWords = entity.keyWords

		for k in oldKeyWords:
			if k.keyWord in newKeyWords:
				updatedKeyWords.append(KeyWord(keyWord = k.keyWord, count = k.count + 1))
				newKeyWords.remove(k.keyWord)
			else:
				updatedKeyWords.append(k)
		for keyWord in newKeyWords.
			updatedKeyWords.append(KeyWord(keyWord = keyWord, count = 1)
		
		entity.keyWords = updatedKeywords
		entity.put()

