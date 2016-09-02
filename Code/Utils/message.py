class Message:
	NEW = 0
	INF = 1
	ERR = 2

	def __init__(self,text="",type=NEW):
		self.text = text
		self.type = type #(0->NEW, 1->INFO, 2-> ERROR)

	def toString(self):
		str = ""
		if (self.type == Message.INF):
			str = "INFO: "
		if (self.type == Message.ERR):
			str = "ERROR: "


		str += self.text
		return str

class MessageList:
	NEW = Message.NEW
	INF = Message.INF
	ERR = Message.ERR

	def __init__(self,text = "", type = NEW):
		msg = Message(text,type)
		self.title = msg
		self.list = []

	def size(self):
		return len(self.list)


	def isEmpty(self):
		return len(self.list) ==0
	

	def containErrors(self):
		if self.title.type == MessageList.ERR:
			return True
		else:
			for msgList in self.list:
				if msgList.containErrors():
					return True

			return False

	def setTitle(self,text,type):
		msg = Message(text,type)
		self.title = msg


	def addMsgList(self,msgList):
		self.list.append(msgList)

	
	def addMsg(self,text,type):
		msgList = MessageList(text,type)
		self.list.append(msgList)

	def showTitle(self,depth,file):
		print(' '*depth + self.title.toString(),file = file)

	def showList(self,detph,file):
		for msgList in self.list:
			msgList.showTitle(depth+1,file)

	def show(self,depth,file):
		self.showTitle(depth,file)
		self.showList(depth,file)
		if len(self.list)>0:
			print(' ',file =file)

		
	def showAll(self,depth,file):
		self.showTitle(depth,file)
		for msgList in self.list:
			msgList.showAll(depth + 1,file)
		if len(self.list)>0:
			print(' ',file = file)


