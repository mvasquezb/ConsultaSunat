class Message:
	NEW = 0
	INF = 1
	ERR = 2

	def __init__(self,text="",type=NEW):
		self.text = text
		self.type = type #(0->NEW, 1->INFO, 2-> ERROR)

	def to_string(self):
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


	def is_empty(self):
		return len(self.list) ==0
	

	def contains_errors(self):
		if self.title.type == MessageList.ERR:
			return True
		else:
			for msgList in self.list:
				if msgList.contains_errors():
					return True

			return False

	def set_title(self,text,type):
		msg = Message(text,type)
		self.title = msg


	def add_msg_list(self,msgList):
		self.list.append(msgList)

	
	def add_msg(self,text,type):
		msgList = MessageList(text,type)
		self.list.append(msgList)

	def show_title(self,depth,file):
		print(' '*depth + self.title.to_string(),file = file)

	def show_list(self,detph,file):
		for msgList in self.list:
			msgList.show_title(depth+1,file)

	def show(self,depth,file):
		self.show_title(depth,file)
		self.show_list(depth,file)
		if len(self.list)>0:
			print(' ',file =file)

		
	def show_all(self,depth,file):
		self.show_title(depth,file)
		for msgList in self.list:
			msgList.show_all(depth + 1,file)
		if len(self.list)>0:
			print(' ',file = file)


