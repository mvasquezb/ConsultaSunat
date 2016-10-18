from cassandra.cluster import Cluster

from Model.offer import Offer

from unidecode import unidecode

from Utils.utils import eprint

from Utils.message import MessageList


import time

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
				(	position int, description text,
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

		description = Store.dbFormat(offer.description)
		#pubDate = Store.dbFormat(offer.pubDate)
		pubDate = offer.pubDate

		auto_process = False
		date_process = 0


		findTable = "unprocessed_"+jobCenter + "_by_desc"
		storeTable = "unprocessed_"+jobCenter
		cmd = """
					SELECT * FROM {0}.{1} WHERE description = %s and month = %s and year = %s;
					""".format(self.keyspace, findTable)

		try:
			result = self.sesion.execute(cmd, [description, month, year])
		except:
			return None

		if len(list(result)) == 0:
			#No duplication
			cmd = """
						INSERT INTO {0}.{1} (description, month, year, features)
						VALUES (%s,%s,%s,%s);
						""".format(self.keyspace, findTable)

			try:
				self.sesion.execute(cmd, [description,month,year,offer.features])
			except:
				eprint("")
				eprint("Error running the cql command: " + cmd)
				eprint(" ---------------------------------------------------------------------")

			cmd = """
						INSERT INTO {0}.{1}
						(auto_process, date_process, description, features, publication_date)
						VALUES
						(%s,%s,%s,%s,%s);
						""".format(self.keyspace, storeTable)

			try:
				self.sesion.execute(cmd, [auto_process, date_process, description,offer.features, pubDate])
				self.curIndex += 1
			except:
				eprint("")
				eprint("Error runing the cql command: " + cmd)
				eprint(" -------------------------------------------------------------------------")
				return None
			return True
		else:
			return False


		#findTable = "unproc_offer_"+jobCenter+"_by_desc"
		#storeTable = "unproc_offer_"+jobCenter

		#try:
		#	cmd = """
		#		SELECT * FROM {0}.{1} WHERE description = %s and month = %s and year = %s;
		#		""".format(self.keyspace, findTable)	
		#	result = self.sesion.execute(cmd,[description, month, year])
		#except:
		#	return None

		#if len(list(result)) == 0:
		#	#No duplication
		#	cmd = """
		#		INSERT INTO {0}.{1}(description, month, year) values
		#		(%s,%s,%s);
		#		""".format(self.keyspace, findTable)

		#	try:
		#		self.sesion.execute(cmd,[description,month, year])
		#	except:
		#		eprint("")
		#		eprint("Error running the cql command: "+ cmd)
		#		eprint("---------------------------------------------------------------------------------------------------------")
		#		return None

		#	cmd = """
		#				INSERT INTO {0}.{1}
		#				(auto_process, date_process, description, feature, publication_date)
		#				VALUES
		#				(%s,%s,%s,%s,%s);
		#				""".format(self.keyspace, storeTable)

		#	try:
		#		self.sesion.execute(cmd, [self.curIndex,description, pubDate, offer.features])
		#		self.curIndex+=1
		#	except:
		#		eprint("")
		#		eprint("Error running the cql command: "+cmd)
		#		eprint("---------------------------------------------------------------------------------------------------------")
		#		return None


		#	return True
		#	
		#else:
		#	return False
