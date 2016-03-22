from google.appengine.ext import ndb

class User(ndb.Model):
    phoneNumber = ndb.StringProperty()
    regID = ndb.StringProperty()
    
    
    
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
