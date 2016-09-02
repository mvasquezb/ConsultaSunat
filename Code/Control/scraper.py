import bs4

class Scraper:
	
	def __init__(self, mainTag,source):
		self.mainTag = mainTag
		self.source = source
		self.levels = []
		self.results = []


	def scrap(self):
		self.levels = self.source.split('->')
		index = 0

		data = self.scrapRec(self.mainTag,index)
		self.results.append(data)
		return self.results



	def _isFinalLvl(self,actualIndex):
		return actualIndex==(len(self.levels)-1)


	def getList(self, soup, tag, dict, attr, index):

		if tag == '*':
			clsSearch = dict["class"]
			tagList = soup.find_all(class_ = clsSearch)
		else:
			tagList = soup.find_all(tag,dict)

		dataList = []
		if (attr != ""):
			for tag in tagList:
				try:
					data = tag[attr]
				except:
					data = None
				dataList.append(data)

			if self._isFinalLvl(index):
				return dataList
			else:
				self.results.append(dataList)

		dataList = []
		if self._isFinalLvl(index):
			for tag in tagList:
				data = tag.get_text().strip()
				dataList.append(data)
			return dataList

		else:
			for tag in tagList:
				data = self.scrapRec(tag,index+1)
				dataList.append(data)
			return dataList


	def getValue(self,soup, idxTag, tag, dict, attr, index):

		tagList = soup.find_all(tag,dict)

		if (attr != ""):
			try:
				data = tagList[idxTag-1][attr]
			except:
				data = None

			if self._isFinalLvl(index):
				return data
			else:
				self.results.append(data)


		if self._isFinalLvl(index):
			try:
				data = tagList[idxTag-1].get_text().strip()
			except:
				data = None
			return data
		else:
			try:
				data = self.scrapRec(tagList[idxTag-1], index+1)
			except:
				data = None
			return data

	def scrapRec(self, soup, index):

		TAGIDX = 0
		DICIDX = 1
		ATTIDX = 2

		curlvl = self.levels[index]
		parts = curlvl.split('/')
		
		tagFormat = parts[TAGIDX].split()

		flagIterative = False
		idxTag = 0
		
		tag = tagFormat[1]
		dict = eval(parts[DICIDX])
		attr = parts[ATTIDX]

		if self._isIterative(tagFormat):
			return self.getList(soup, tag, dict, attr, index)
		else:
			idxTag = self._getIndex(tagFormat)
			return self.getValue(soup,idxTag, tag,dict, attr, index)

	def _isIterative(self,tagFormat):
		return tagFormat[0] == '*'

	def _getIndex(self, tagFormat):
		return int(tagFormat[0])




