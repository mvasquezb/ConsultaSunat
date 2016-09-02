import requests
import bs4
import importlib

import datetime
from time import mktime

from Utils.message import MessageList
from Utils import utils
from Utils.utils import eprint
from Control.scraper import Scraper

from Model.offer import Offer


class Template:
	
	def __init__(self, jobCenter, funcFilename, urlBase, period, areaUrl, \
							 areasSource, numOffSource, linksPerPage, numSources, listSources):

		self.jobCenter = jobCenter
		self.funcFilename = funcFilename
		self.urlBase = urlBase
		self.period = period
		self.areaUrl = areaUrl
		self.areasSource = areasSource
		self.numOffSource = numOffSource
		self.linksPerPage = linksPerPage
		self.numSources = numSources
		self.listSources = listSources

		self.module = None


	@staticmethod
	def readAttributesFromFile(file,mainList):
		file.readline() #Global:
			
		jobCenter = utils.readTextFromFile(file)
		if jobCenter is None: mainList.addMsg("Failed to read the jobcenter", MessageList.ERR)

		funcFilename = utils.readTextFromFile(file)
		if funcFilename is None: mainList.addMsg("Failed to read the functions filename", MessageList.ERR)

		urlBase = utils.readUrlFromFile(file)
		if urlBase is None: mainList.addMsg("Failed to read the url Base", MessageList.ERR)

		period = utils.readTextFromFile(file)
		if period is None: mainList.addMsg("Failed to read the period", MessageList.ERR)

		areaUrl = utils.readUrlFromFile(file)
		if areaUrl is None: mainList.addMsg("Failed to read the url to get areas", MessageList.ERR)

		areasSource = utils.readSourceFromFile(file)
		if areasSource is None: mainList.addMsg("Failed to read the source to get areas", MessageList.ERR)

		numOffSource = utils.readSourceFromFile(file)
		if numOffSource is None: mainList.addMsg("Failed to read the source to get the number of offers", MessageList.ERR)

		linksPerPage = utils.readIntFromFile(file)
		if linksPerPage is None: mainList.addMsg("Failed to read the number of links per page", MessageList.ERR)

		numSources = utils.readIntFromFile(file)
		if numSources is None: mainList.addMsg("Failed to read the number of sources to get offers", MessageList.ERR)
		else:
			listSources = []
			for i in range(0, numSources):
				offSource = utils.readSourceFromFile(file)
				if offSource is None:	mainList.addMsg("Failed to read the offer source #"+ str(i+1), MessageList.ERR)
				else: listSources.append(offSource)
			
		if mainList.size() is not 0:
			return None
		else:
			return jobCenter, funcFilename, urlBase, period, areaUrl, areasSource, numOffSource, linksPerPage, numSources, listSources	



	@classmethod
	def fromFile(cls, file,mainList):
		attributes = cls.readAttributesFromFile(file, mainList)
		if attributes is None:
			return None
		else:
			return cls(*attributes)


	def getAreas(self,mainList):
		try:
			web = requests.get(self.areaUrl)
			soup = bs4.BeautifulSoup(web.text,"lxml")
		except:
			mainList.setTitle("Cannot connect: "+ self.areaUrl,MessageList.ERR)
			return None
		
		scraper = Scraper(soup,self.areasSource)
		data = scraper.scrap()

		areas = data[0]

		#print(areas)
		#areas = ["medicina-salud"]
		#areas = ["/empleos-area-salud-medicina-y-farmacia.html"]

		if areas is None:
			mainList.setTitle("Failed to scrap areas. Check areas source",MessageList.ERR)
			return None
		else:
			mainList.setTitle(str(len(areas)) + " Areas obtained",MessageList.INF)
			return areas




	def getNumOffers(self,dateUrl,mainList):
		try:
			web = requests.get(dateUrl)
			soup = bs4.BeautifulSoup(web.text,"lxml")
		except:
			mainList.addMsg("Cannot access to the url " + dateUrl,MessageList.ERR)
			return None

		scraper = Scraper(soup, self.numOffSource)

		data = scraper.scrap()

		numOff = data[0]
			

		try:
			numOff = int(numOff.split()[0])
		except:
			mainList.addMsg("value obtained is not a number",MessageList.ERR)
			numOff = None

		if numOff is None:
			mainList.setTitle("Fail scraping number of offers.",MessageList.ERR)
			return None

		return numOff


	def getOffersFromPageUrl(self,pageUrl):

		try:
			web = requests.get(pageUrl)
			soup = bs4.BeautifulSoup(web.text,"lxml")

		except:
			eprint("Cannot access to the url: "+ pageUrl + "\n")
			return None


		totLinks = []
		totDates = []

		for source in self.listSources:
			levels = source.split('->')
			index = 0

			scraper = Scraper(soup,source)
			data = scraper.scrap()

			offLinks = data[0]
			dates = data[1]
				

			if offLinks is None or len(offLinks) == 0:
				#Useless source
				eprint("No offers obtained using Source: " + source)
				continue

			else:
				#Remember:offLink must be a list

				for index, link in enumerate(offLinks):
					if not link in totLinks:
						totLinks.append(link)
						totDates.append(dates[index])

		totOffers = []
		for index,link in enumerate(totLinks):
			eprint("		Offer #"+str(index+1))

			try:
				linkUrl = self.module.makeLinkUrl(link,pageUrl)
			except:
				mainList.setTitle("makeLinkUrl is not working propertly", MessageList.ERR)
				return None

			offer = self.getOfferFromLink(linkUrl)

			if offer is not None:
				passTime = totDates[index]
				offer.pubDate = self.toPublicationDate(passTime)
				totOffers.append(offer)
			else:
				totOffers.append(offer)

		return totOffers


	def getOffersFromPeriodUrl(self,periodUrl, mainList):

		msgList = MessageList()
		self.numOff = self.getNumOffers(periodUrl,msgList)
		mainList.addMsgList(msgList)

		if self.numOff is None:
			return None

		mainList.addMsg("Number of Offers filtered: " + str(self.numOff),MessageList.INF)

		max = 2000
		numPag = 0
		totalOffers = []

		while numPag < max and len(totalOffers) < self.numOff:
			numPag += 1

			try:
				pageUrl = self.module.makePageUrl(numPag,periodUrl)
			except:
				mainList.setTitle("makePageUrl is not working propertly", MessageList.ERR)
				#Abort everything
				return None #Return totalOffers if you dont wanna abort all

			eprint("	Page #"+str(numPag))
			offers = self.getOffersFromPageUrl(pageUrl)
			eprint("")

			if offers is None:
				#Error page
				break
			else:
				totalOffers += offers
				if len(offers)!=self.linksPerPage and len(totalOffers)!=self.numOff:
					mainList.addMsg("Unexpected number of offers at page #"+ str(numPag), MessageList.INF)

		mainList.setTitle(str(len(totalOffers)) + " offers obtained in total (Invalid included)",MessageList.INF)
		return totalOffers
					
	#Must be sent to Functions
	def toPublicationDate(self, passTime):
		curDate = datetime.datetime.now()
	
		if passTime == "Ayer":
			pubDate= curDate - datetime.timedelta(days = 1)
			return pubDate
	
		parts = passTime.split()

		type = parts[2]
		value = int(parts[1])

		if type in ['segundos','segundo']:
			pubDate = curDate - datetime.timedelta(seconds = value)

		if type in ['minutos', 'minuto']:
			pubDate = curDate - datetime.timedelta(minutes = value)

		if type in ['hora', 'horas']:
			pubDate = curDate - datetime.timedelta(hours = value)

		if type in ["día", "días"]:
			pubDate = curDate - datetime.timedelta(days = value)

		if type in ["semana", "semanas"]:
			pubDate = curDate - datetime.timedelta(weeks = value)

		if type in ["mes", "meses"]:
			pubDate = curDate - datetime.timedelta(days = value*30)
		
		return pubDate
	
	def getOffersFromAreaUrl(self,areaUrl,mainList):

		periodUrl = self.module.makePeriodUrl(self.period,areaUrl)
		try:
			periodUrl = self.module.makePeriodUrl(self.period,areaUrl)
		except:
			mainList.setTitle("makePeriodUrl function is not working propertly",MessageList.ERR)
			return None

		msgList = MessageList()
		offers = self.getOffersFromPeriodUrl(periodUrl,msgList)
		mainList.addMsgList(msgList)

		if offers is None:
			mainList.setTitle("Cannot obtain offers",MessageList.ERR)
			return None

		else:
			validOffers = []
			for offer in offers:
				if offer is not None:
					validOffers.append(offer)

			mainList.setTitle(str(len(validOffers))+ " valid offers selected",MessageList.INF)
			return validOffers


	def execute(self,db, mainList):

		if not db.createTables(self.jobCenter):
			return None


		#Importing Custom Functions
		msgList = MessageList()
		mod = customImport(self.funcFilename,msgList)
		mainList.addMsgList(msgList)

		if mod is not None:
			self.module = mod

			msgList = MessageList()
			areas = self.getAreas(msgList)
			mainList.addMsgList(msgList)

			if areas is not None:
				
				try:
					urls = self.module.makeAreaUrls(areas,self.urlBase)
					areaUrls = list(urls)
				except:
					mainList.addMsg("makeAreaUrls function is not working propertly",MessageList.ERR)
					mainList.setTitle("Failed to execute Template "+ self.jobCenter, MessgaeList.ERR)
					return None

				for index,areaUrl in enumerate(areaUrls):
					
					mainList.addMsg("Area #"+str(index+1),MessageList.INF)
					mainList.addMsg(areaUrl,MessageList.INF)
					msgList = MessageList()
					eprint("Area #"+str(index+1)+"   "+areaUrl)
					offers = self.getOffersFromAreaUrl(areaUrl,msgList)
					eprint("------------------------------------------------------------------------------")
					mainList.addMsgList(msgList)

					if offers is not None:
						msgList = MessageList()
						db.loadOffers(offers, self.jobCenter,msgList)
						mainList.addMsgList(msgList)

				db.setCurIndex()
				mainList.setTitle("Template " + self.jobCenter + " executed.", MessageList.INF)
				return 

		mainList.setTitle("Failed to execute Template " +self.jobCenter,MessageList.ERR)
		return
		

def customImport(filename, mainList):

	modname = "Functions." + filename

	try:
		mod = importlib.import_module(modname)
	except:
		mainList.setTitle("Incorrect function module filename", MessageList.ERR)
		return None

	#Check function existence
	customFunctions = dir(mod)

	if not "makeAreaUrls" in customFunctions:
		mainList.addMsg("Missing makeAreaUrls function",MessageList.ERR)

	if not "makePeriodUrl" in customFunctions:
		mainList.addMsg("Missing makePeriodUrl function", MessageList.ERR)

	if not "makePageUrl" in customFunctions:
		mainList.addMsg("Missing makePageUrl function",MessageList.ERR)

	if not "makeLinkUrl" in customFunctions:
		mainList.addMsg("Missing makeLinkUrl function",MessageList.ERR)

	if mainList.size() is not 0:
		mainList.setTitle("Fail importing function file", MessageList.ERR)
		return None
	else:
		mainList.setTitle("Function file imported", MessageList.INF)
		return mod 




#------------------------------------------------------------------------------------------------
class FeaturesSource:
	def __init__(self,namesSource, valuesSource):
		self.namesSource = namesSource
		self.valuesSource = valuesSource

	

	@classmethod
	def fromFile(cls, file, mainList):
		fileline = file.readline()
		if fileline is None or utils.isblank(fileline) :
			return None
			
		names = utils.readSourceFromString(fileline,mainList)
		if names is None:
			mainList.addMsg("Failed to read names", MessageList.ERR)
		values = utils.readSourceFromFile(file)
		if values is None:
			mainList.addMsg("Failed to read values", MessageList.ERR)

		if mainList.containErrors():
			return None
		else:
			return cls(names,values)






#------------------------------------------------------------------------------------------------
class OfferTemplate(Template):

	def __init__(self,globalAttributes, descSource, featSources):

		Template.__init__(self,*globalAttributes)
		self.descSource = descSource
		self.featSources = featSources
	

	@staticmethod
	def readAttributesFromFile(file,mainList):
		globalAttr = Template.readAttributesFromFile(file,mainList)
		file.readline() #newline
		file.readline() #Offer Structure:

		descSource = utils.readSourceFromFile(file)
		if descSource is None:
			mainList.addMsg("Failed to read the offer description source", MessageList.ERR)

		featuresSources = []
		while True:
			msgList = MessageList()
			featuresSource = FeaturesSource.fromFile(file,msgList)
		
			if featuresSource is None:
				if msgList.containErrors():
					msgList.setTitle("Failed to read features Source #"+ str(len(featuresSources)+1),MessageList.ERR)
					mainList.addMsgList(msgList)

				break
			else:

				featuresSources.append(featuresSource)

		if not mainList.containErrors():
			mainList.setTitle("All Offer Template Attributes are OK :)",MessageList.INF)
			return globalAttr, descSource, featuresSources
		else:
			mainList.setTitle("Some Offer Template Attributes are WRONG :(",MessageList.ERR)
			return None



	def getDataFromSource(self, soup, source):
		if source == "":
			return None

		else:
			if (type(source) is list):
				return source




			scraper = Scraper(soup, source)
			data = scraper.scrap()[0]
			return data


	def getOfferFromLink(self,link):

		try:
			web = requests.get(link)
			soup = bs4.BeautifulSoup(web.text,"lxml")

		except:
			eprint("Cannot access to the link "+link)
			return None

		description = self.getDataFromSource(soup,self.descSource)
		if description is None:	eprint("  Description source problem. INVALID OFFER")
		if description == "": eprint("  Empty description. INVALID OFFER")


		if description is None or description == "":
			eprint("Link: "+ link)
			return None
		else:
			offer = Offer(description)

			for featSource in self.featSources:
				names = self.getDataFromSource(soup, featSource.namesSource)
				values = self.getDataFromSource(soup, featSource.valuesSource)

				for idx in range(min(len(names),len(values))):
					offer.addFeature(names[idx],values[idx])

			return offer
