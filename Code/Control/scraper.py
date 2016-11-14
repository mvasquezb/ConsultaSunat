import bs4

class Scraper:
	
	def __init__(self, main_tag,source):
		self.main_tag = main_tag
		self.source = source
		self.levels = []
		self.results = []


	def scrape(self):
		self.levels = self.source.split('->')
		index = 0

		data = self.scrape_rec(self.main_tag,index)
		self.results.append(data)
		return self.results



	def is_final_lvl(self,actual_index):
		return actual_index==(len(self.levels)-1)


	def get_list(self, soup, tag, dict, attr, index):

		if tag == '*':
			cls_search = dict["class"]
			tag_list = soup.find_all(class_ = cls_search)
		else:
			tag_list = soup.find_all(tag,dict)

		data_list = []
		if (attr != ""):
			for tag in tag_list:
				try:
					data = tag[attr]
				except:
					data = None
				data_list.append(data)

			if self.is_final_lvl(index):
				return data_list
			else:
				self.results.append(data_list)

		data_list = []
		if self.is_final_lvl(index):
			for tag in tag_list:
				data = tag.get_text().strip()
				data_list.append(data)
			return data_list

		else:
			for tag in tag_list:
				data = self.scrape_rec(tag,index+1)
				data_list.append(data)
			return data_list


	def get_value(self,soup, idx_tag, tag, dict, attr, index):

		tag_list = soup.find_all(tag,dict)

		if (attr != ""):
			try:
				data = tag_list[idx_tag-1][attr]
			except:
				data = None

			if self.is_final_lvl(index):
				return data
			else:
				self.results.append(data)


		if self.is_final_lvl(index):
			try:
				data = tag_list[idx_tag-1].get_text().strip()
			except:
				data = None
			return data
		else:
			try:
				data = self.scrape_rec(tag_list[idx_tag-1], index+1)
			except:
				data = None
			return data

	def scrape_rec(self, soup, index):

		TAGIDX = 0
		DICIDX = 1
		ATTIDX = 2

		curlvl = self.levels[index]
		parts = curlvl.split('\\')
		
		tag_format = parts[TAGIDX].split()

		flag_iterative = False
		idx_tag = 0
		
		tag = tag_format[1]
		dict = eval(parts[DICIDX])
		attr = parts[ATTIDX]

		if self.is_iterative(tag_format):
			return self.get_list(soup, tag, dict, attr, index)
		else:
			idx_tag = self.get_index(tag_format)
			return self.get_value(soup,idx_tag, tag,dict, attr, index)

	def is_iterative(self,tag_format):
		return tag_format[0] == '*'

	def get_index(self, tag_format):
		return int(tag_format[0])




