def makeAreaUrls(areas,urlBase):
	str = urlBase
	str += "/de-"
	str += areas[0]

	for i in range(1,len(areas)):
		str += "--" + areas[i]
	
	return [str]  



def makePeriodUrl(period,url):
	periodUrl = url + "/publicado-" + period
	return periodUrl



def makePageUrl(pageNum, url):
	if pageNum == 1:
		return url
	else:
		newUrl= url + "?page=" + str(pageNum)
		return newUrl


def makeLinkUrl(link, url):
	return link

		



#Must be sent to Functions
def toPublicationDate(passTime):
		curDate = datetime.date.today()

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
			pubDate = curDate - datetime.timedelta(months = value)
		
		return pubDate




