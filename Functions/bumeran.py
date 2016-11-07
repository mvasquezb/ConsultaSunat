def make_area_urls(areas,url_base):

	urls = []
	for area in areas:
		url = url_base + area
		urls.append(url)

	return urls

def make_period_url(period, url):
	period_url = url[:-5] #delete .html
	period_url += "-publicacion-"+period
	period_url += ".html"

	return period_url


def make_page_url(page_num, url):
	if page_num == 1:
		return url
	else:
		page_url = url[:-5] #delete .html
		page_url += "-pagina-" + str(page_num)
		page_url += ".html"

		return page_url


def make_link_url(link, url):
	link_url = "http://bumeran.com.pe" + link
	return link_url
	
	

