class Offer:

	def __init__(self, description):
		self.description = description
		self.features = {}
		self.pubDate = None

	def setPubDate(self,pubDate):
		self.pubDate = pubDate

	def addFeature(self,name,value):
		self.features[name] = value


	def show(self):
		print("Offer: ")
		print(" Description:			"+self.description)
		print(" publication Date:	"+str(self.pubDate))
		print(" Features: 				"+str(self.features))

			



