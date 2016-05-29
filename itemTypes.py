from google.appengine.ext import ndb

class User(ndb.Model):
    phoneNumber = ndb.StringProperty()
    regID = ndb.StringProperty()
	keyWords = ndb.StructuredProperty()
	images = ndb.KeyProperty(repeated=True)
    
    
    
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


class Image(ndb.Model):
	blobKey = ndb.BlobKeyProperty()
	tags = ndb.StructuredProperty(Tag, repeated=True)
	keyWords = ndb.StructuredProperty(KeyWord, repeated=True)
	link = ndb.StringProperty()
	siteLink = ndb.StringProperty()
	flickrTags = ndb.StringProperty(repeated=True)

class KeyWord(ndb.model):
	keyWord = ndb.StringProperty()
	count = ndb.IntegerProperty()


class Tag(ndb.model):
	tag = ndb.StringProperty()
	probability = ndb.IntegerProperty()
