#Printint Error File
from __future__ import print_function
import sys

def eprint(*args,**kwargs):
	print(*args, file = sys.stderr, **kwargs)


	
from Utils.message import MessageList

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

def readUrlFromFile(tempFile):
	str = tempFile.readline()
	data = str.split('|')

	err = False
	if (len(data)!=3):
		return None
	else:
		validate = URLValidator()
		try:
			validate(data[1])
		except ValidationError:
			return None

		return data[1]


def readTextFromFile(tempFile):
	str = tempFile.readline()
	data = str.split('|')

	err = False

	if (len(data)!=3):
		return None
	else:
		return data[1]
		

def readIntFromFile(tempFile):
	str = tempFile.readline()
	data = str.split('|')

	err = False
	if(len(data)!=3):
		return None
	else:
		try:
			val = int(data[1])
		except:
			return None
		return val


def _validateTagFormat(tag):
	tagParts = tag.split()
	if len(tagParts) is not 2:
		return False
	else:
		index = tagParts[0]
		if index.isdigit() or index == '*':
			return True
		else:
			return False


def _validateDiccionaryFormat(dicc):
	try:
		diccionary = eval(dicc)
	except:
		return False

	if type(diccionary) is dict:
		return True
	else:
		return False

def _validateAttributeFormat(attr):
	return attr.isalpha() or attr == ""



def _validateStringSource(source):

	if source is "":
		return False

	nlvls = len(source.split('->'))
	if (nlvls == 1):
		nparts = len(source.split('/'))
		if nparts == 1:
			return True
		else:
			return False
	else:
		return False



def readSourceFromString(strdata	,mainList = MessageList() ):


	data = strdata.split('|')

	if (len(data)!=3):
		return None
	else:
			
		if _validateStringSource(data[1]):
			listData = eval(data[1])
			if type(listData) is list:
				mainList.addMsg("Using list data from template: " + str(listData),MessageList.INF)
				return listData

			try:	
				listData = eval(data[1])
				if type(listData) is list:
					mainList.addMsg("Using list data from template: " + str(listData),MessageList.INF)
					return listData

			except:
				return None

				
		else:

			levels = data[1].split('->')
			for level in levels:
				parts = level.split('/')

				if (len(parts)!=3):
					return None
				else:
					
					tag = parts[0]
					if not _validateTagFormat(tag):
						return None

					dicc = parts[1]
					if not _validateDiccionaryFormat(dicc):
						return None

					attr = parts[2]
					if not _validateAttributeFormat(attr):
						return None

			return data[1]


def readSourceFromFile(tempFile):
	fileline = tempFile.readline()
	if fileline is None:
		return None
	else:
		return readSourceFromString(fileline)
	


def isblank(mystring):
	if mystring and mystring.strip():
		return False
	return True
	

	
		





















		









