import datetime

def make_area_urls(areas,url_base):
	str = url_base
	str += "/de-"
	str += areas[0]

	for i in range(1,len(areas)):
		str += "--" + areas[i]
	
	return [str]  



def make_period_url(period,url):
	period_url = url + "/publicado-" + period
	return period_url



def make_page_url(page_num, url):
	if page_num == 1:
		return url
	else:
		new_url= url + "?page=" + str(page_num)
		return new_url


def make_link_url(link, url):
	return link
		

#Must be sent to Functions
def to_publication_date(pass_time):
		cur_date = datetime.date.today()

		if pass_time == "Ayer":
			pub_date= cur_date - datetime.timedelta(days = 1)
			return pub_date


		parts = pass_time.split()

		type = parts[2]
		value = int(parts[1])

		if type in ['segundos','segundo']:
			pub_date = cur_date - datetime.timedelta(seconds = value)

		if type in ['minutos', 'minuto']:
			pub_date = cur_date - datetime.timedelta(minutes = value)

		if type in ['hora', 'horas']:
			pub_date = cur_date - datetime.timedelta(hours = value)

		if type in ["día", "días"]:
			pub_date = cur_date - datetime.timedelta(days = value)

		if type in ["semana", "semanas"]:
			pub_date = cur_date - datetime.timedelta(weeks = value)

		if type in ["mes", "meses"]:
			pub_date = cur_date - datetime.timedelta(months = value)
		
		return pub_date




