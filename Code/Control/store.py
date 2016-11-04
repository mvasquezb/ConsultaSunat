from cassandra.cluster import Cluster

from Model.offer import Offer

from unidecode import unidecode

from Utils.utils import eprint

from Utils.message import MessageList


import time

class Store:
	
	def __init__(self,ip= None):

		self.keyspace = ""
		self.ip = ip
		self.sesion = None
		self.curIndex = 0

	def connect(self,keyspace):

		keyspace = keyspace.lower()
		self.keyspace = keyspace
		cluster = Cluster()
		try:
			self.sesion = cluster.connect(keyspace)
		except:
			print("Unable to connect to database. (Hint: Start cassandra)")
			return False
		return True

	def createTables(self,jobCenter):

		findTable = "unprocessed_offers_by_id"
		storeTable = "unprocessed_offers"

		try:
			self.sesion.execute("""
				CREATE TABLE IF NOT EXISTS {0} (
				  id text,
					year int,
					month int,
					features map<text,text>,
					PRIMARY KEY(id,year, month));
				""".format(findTable))


			self.sesion.execute("""
				CREATE TABLE IF NOT EXISTS {0} (
					auto_process boolean,
					date_process timestamp,
					year int,
					month int,
					id text,
					features map<text,text>,
					PRIMARY KEY(auto_process, date_process, year, month, id));
				""".format(storeTable))

		except:
			print("Error trying to create store tables")
			return False
		return True



	def loadOffers(self, offers,jobCenter,mainList):

		errorLoading = False


		cntLoad = 0
		cntDisc = 0
		cntErr = 0
		for offer in offers:
			inserted =  self.insertOffer(offer,jobCenter)
			if inserted is None:
				cntErr += 1
				errorLoading = True
			else:
				if inserted:
					cntLoad += 1
				else:
					cntDisc += 1

		
		mainList.addMsg(str(cntLoad)+ " Offers succesfully loaded to database", MessageList.INF)
		mainList.addMsg(str(cntDisc)+ " Offers discarted because of duplication in database", MessageList.INF)
		mainList.addMsg(str(cntErr) + " Offers failed to load to database", MessageList.ERR)

		if errorLoading:
			mainList.setTitle("Some offers couldn't be loaded. Check detail file", MessageList.ERR)
		else:
			mainList.setTitle("All offers were loaded", MessageList.INF)


	@staticmethod
	def dbFormat(value):
		if value is None:
			return ""

		if type(value) is str:
			return value.replace("'","''")
		else:
			return value


	@staticmethod
	def getCurIndex(jobCenter):
		filename = "curIndex_" + jobCenter

		with open(filename) as file:
			#get both indexes
			idxApt = int(file.readline())
			return idxApt

	def setCurIndex(self,jobCenter):
		filename = "curIndex_" + jobCenter
		file = open(filename, 'w')
		file.write(str(self.curIndex))
		


	def insertOffer(self, offer,jobCenter):
		month = offer.pubDate.month
		year = offer.pubDate.year

		id = Store.dbFormat(offer.description)
		pubDate = offer.pubDate

		auto_process = False
		date_process = 0


		findTable = "unprocessed_offers_by_id"
		storeTable = "unprocessed_offers"


		cmd = """
					SELECT * FROM {0} WHERE id = %s and  year = %s and month = %s;
					""".format(findTable)

		try:
			result = self.sesion.execute(cmd, [id,year, month])
		except:
			return None

		if len(list(result)) == 0:
			#No duplication
			cmd = """
						INSERT INTO {0} (id,year,month, features)
						VALUES (%s,%s,%s,%s);
						""".format(findTable)

			try:
				self.sesion.execute(cmd, [id,year, month,offer.features])
			except:
				eprint("")
				eprint("Error running the cql command: " + cmd)
				eprint(" ---------------------------------------------------------------------")

			cmd = """
						INSERT INTO {0}
						(auto_process, date_process,year, month, id, features)
						VALUES
						(%s,%s,%s,%s,%s,%s);
						""".format(storeTable)

			try:
				self.sesion.execute(cmd, [auto_process, date_process, year,  month, id, offer.features])
				self.curIndex += 1
			except:
				eprint("")
				eprint("Error runing the cql command: " + cmd)
				eprint(" -------------------------------------------------------------------------")
				return None
			return True
		else:
			return False


