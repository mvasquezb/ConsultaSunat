import sys
sys.path.append('..') #Code path added
sys.path.append('../..') #Project path added

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

from Utils.message import MessageList
from Utils import utils

from Control.template import Template
from Control.template import OfferTemplate

from Control.store import Store

import datetime

def createTemplate(tempFilename, mainList):

	try:
		tempFile = open(tempFilename,'r')
	except OSError:
		mainList.setTitle("Template File not found",MessageList.ERR)
		return None

	msgList = MessageList()
	template = OfferTemplate.fromFile(tempFile,msgList)
	mainList.addMsgList(msgList)

	if template is None:
		mainList.setTitle("Unable to create Template Instance",MessageList.ERR)
		return None
	else:
		mainList.setTitle("Template Instance created",MessageList.INF)
		return template


def sendEmail(sender, password, receiver, filename):

	msg = MIMEMultipart()
	with open("summary.txt") as repFile:
		part = MIMEText(repFile.read())
		msg.attach(part)
	msg['Subject'] = "Web Scraping resuts"
	msg['From'] = "btpucp"
	msg['To'] =receiver


	sys.stderr.flush()

	with open(filename, "rb") as file:
		part = MIMEApplication(file.read(), Name = basename(filename))
		part['Content-Disposition'] = 'attachment; filename="%s"' % basename(filename)
		msg.attach(part)
				



	s = smtplib.SMTP('smtp.gmail.com', 587)
	s.starttls()
	s.login(sender,password)
	s.send_message(msg)
	s.quit()

	
def readConfigFile(mainList):

	configFilename = "../../config"

	try:
		confFile = open(configFilename, 'r')
	except OSError:
		mainList.setTitle("Configuration file not found", MessageList.ERR)
		return None

	sender = utils.readTextFromFile(confFile)
	password = utils.readTextFromFile(confFile)
	receiver = utils.readTextFromFile(confFile)
	keyspace = utils.readTextFromFile(confFile)
	out = utils.readTextFromFile(confFile)

	filenames = []
	while True:
		filename = utils.readTextFromFile(confFile)
		if filename is None:
			break
		else:
			filename = _addTemplatePath(filename)
			filenames.append(filename)

	if _checkConfigValues(sender, password, receiver, keyspace, out,filenames):
		mainList.setTitle("Configuration file read correctly",MessageList.INF)
		return sender, password, receiver, keyspace, out, filenames
	else:
		mainList.setTitle("Incorrect configuration file values",MessageList.ERR)
		return None


def _checkConfigValues(sender, password, receiver, keyspace, out, filenames):
	if sender is None or password is None or receiver is None or keyspace is None or out is None :
		return False
	if len(filenames)==0:
		return False

	return True
		


def _addTemplatePath(filename):
	relativePath = "../../Templates/"
	return relativePath + filename


def main():

	mainList = MessageList("Detail:")

	msgList = MessageList()
	sender, password, receiver, keyspace,out, filenames = readConfigFile(msgList)
	mainList.addMsgList(msgList)

	database = Store(keyspace)
	if not database.connect():
		return None

	sys.stdout = open("summary.txt", 'w')
	sys.stderr = open(out,'w')
		
	for filename in filenames:
		msgList = MessageList()
		template = createTemplate(filename, msgList)
		mainList.addMsgList(msgList)

		if template is not None:
			msgList = MessageList()
			template.execute(database, msgList)
			mainList.addMsgList(msgList)

	mainList.showAll(0,sys.stdout)
	sys.stdout.flush()

	sendEmail(sender, password, receiver, out)


if __name__ == "__main__":
	main()
