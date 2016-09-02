def makeAreaUrls(areas,urlBase):

	urls = []
	for area in areas:
		url = urlBase + area
		urls.append(url)

	return urls

def makePeriodUrl(period, url):
	periodUrl = url[:-5] #delete .html
	periodUrl += "-publicacion-"+period
	periodUrl += ".html"

	return periodUrl


def makePageUrl(pageNum, url):
	if pageNum == 1:
		return url
	else:
		pageUrl = url[:-5] #delete .html
		pageUrl += "-pagina-" + str(pageNum)
		pageUrl += ".html"

		return pageUrl


def makeLinkUrl(link, url):
	linkUrl = "http://bumeran.com.pe" + link
	return linkUrl
	
	

