from cassandra.cluster import Cluster

from Model.offer import Offer

from unidecode import unidecode

from Utils.utils import eprint

from Utils.message import MessageList


class Store:
	
	def __init__(self,keyspace,ip= None):

		self.keyspace = keyspace
		self.ip = ip
		self.sesion = None
		self.curIndex = 0

	def connect(self):

		if self.ip is None:
			cluster = Cluster()
		else:
			cluster = Cluster(self.ip)

		try:
			self.sesion = cluster.connect()
		except:
			print("Unable to connect to database. (Hint: Start cassandra)")
			return False
		return True

	def createTables(self,jobCenter):

		self.curIndex = Store.getCurIndex(jobCenter)
		#self.curIndex = 1

		findTable = "unproc_offer_"+jobCenter+"_by_desc"
		storeTable = "unproc_offer_"+jobCenter

		try:
			self.sesion.execute("""
				CREATE TABLE IF NOT EXISTS {0}.{1}
				( description text,
					month int,
					year int,
					PRIMARY KEY(description,month, year));
				""".format(self.keyspace,findTable))


			self.sesion.execute("""
				CREATE TABLE IF NOT EXISTS {0}.{1}
				(	position int,
					description text,
					pubdate timestamp,
					features map<text,text>,
					PRIMARY KEY(position));
				""".format(self.keyspace,storeTable))

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

		with open("curIndex") as file:
			#get both indexes
			idxApt = int(file.readline())
			idxBum = int(file.radline())

			if jobCenter == "Aptitus":
				return idxApt
			if jobCenter == "Bumeran":
				return idxBum

	def setCurIndex(self):
		file = open("curIndex", 'w')
		file.write(str(self.curIndex))
		


	def insertOffer(self, offer,jobCenter):
		month = offer.pubDate.month
		year = offer.pubDate.year

		description = Store.dbFormat(offer.description)
		pubDate = Store.dbFormat(offer.pubDate)



		findTable = "unproc_offer_"+jobCenter+"_by_desc"
		storeTable = "unproc_offer_"+jobCenter

		try:
			cmd = """
				SELECT * FROM {0}.{1} WHERE description = '{2}';
				""".format(self.keyspace, findTable, description)	
			result = self.sesion.execute(cmd)
		except:
			return None

		if len(list(result)) == 0:
			#No duplication
			cmd = """
				INSERT INTO {0}.{1}(description, month, year) values
				(%s,%s,%s)
				""".format(self.keyspace, findTable)

			try:
				self.sesion.execute(cmd,[description,month, year])
			except:
				eprint("")
				eprint("Error running the cql command: "+ cmd)
				eprint("---------------------------------------------------------------------------------------------------------")
				return None

			cmd = """
				INSERT INTO {0}.{1}(position, description, pubdate, features)
				VALUES (
				%s,%s,%s,%s)
				""".format(self.keyspace, storeTable)

			try:
				self.sesion.execute(cmd, [self.curIndex,description, pubDate, offer.features])
				self.curIndex+=1
			except:
				eprint("")
				eprint("Error running the cql command: "+cmd)
				eprint("---------------------------------------------------------------------------------------------------------")
				return None


			return True
			
		else:
			return False
