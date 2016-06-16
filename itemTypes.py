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
	keyWords = ndb.JsonProperty()
	link = ndb.StringProperty()
	siteLink = ndb.StringProperty()
	flickrTags = ndb.StringProperty(repeated=True)
	
	def imageComplete2json(self):
		tags = {}
		for t in self.tags:
			tags[t.tag] = t.probability
		iDetails = {"tags": tags, "keyWords": self.keyWords, "link":self.link, "siteLink":self.siteLink}
		return iDetails	


class User(ndb.Model):
	phoneNumber = ndb.StringProperty()
	regID = ndb.StringProperty()
	keyWords = ndb.JsonProperty()
	imagesUsed = ndb.JsonProperty()
    
    
    
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
