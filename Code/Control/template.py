import requests
import bs4
import importlib

import datetime
from time import mktime

from Utils.message import MessageList
from Utils import utils
from Utils.utils import eprint
from Control.scraper import Scraper

from Model.offer import UnprocessedOffer

from Control import textProcessor as tp # TP tu terror


class Template:
  
  def __init__(self, job_center, func_filename, url_base, period, area_url, \
               areas_source, num_offSource, links_per_page, num_sources, list_sources):

    self.job_center = job_center
    self.func_filename = func_filename
    self.url_base = url_base
    self.period = period
    self.area_url = area_url
    self.areas_source = areas_source
    self.num_offSource = num_offSource
    self.links_per_page = links_per_page
    self.num_sources = num_sources
    self.list_sources = list_sources

    self.module = None


  @staticmethod
  def read_attributes_from_file(file,main_list):
    file.readline() #Global:
      
    job_center = utils.read_text_from_file(file)
    if job_center is None: main_list.add_msg("Failed to read the jobcenter", MessageList.ERR)

    func_filename = utils.read_text_from_file(file)
    if func_filename is None: main_list.add_msg("Failed to read the functions filename", MessageList.ERR)

    url_base = utils.read_url_from_file(file)
    if url_base is None: main_list.add_msg("Failed to read the url Base", MessageList.ERR)

    period = utils.read_text_from_file(file)
    if period is None: main_list.add_msg("Failed to read the period", MessageList.ERR)

    area_url = utils.read_url_from_file(file)
    if area_url is None: main_list.add_msg("Failed to read the url to get areas", MessageList.ERR)

    areas_source = utils.read_source_from_file(file)
    if areas_source is None: main_list.add_msg("Failed to read the source to get areas", MessageList.ERR)

    num_offSource = utils.read_source_from_file(file)
    if num_offSource is None: main_list.add_msg("Failed to read the source to get the number of offers", MessageList.ERR)

    links_per_page = utils.read_int_from_file(file)
    if links_per_page is None: main_list.add_msg("Failed to read the number of links per page", MessageList.ERR)

    num_sources = utils.read_int_from_file(file)
    if num_sources is None: main_list.add_msg("Failed to read the number of sources to get offers", MessageList.ERR)
    else:
      list_sources = []
      for i in range(0, num_sources):
        offSource = utils.read_source_from_file(file)
        if offSource is None: main_list.add_msg("Failed to read the offer source #"+ str(i+1), MessageList.ERR)
        else: list_sources.append(offSource)
      
    if main_list.size() is not 0:
      return None
    else:
      return job_center, func_filename, url_base, period, area_url, areas_source, num_offSource, links_per_page, num_sources, list_sources  



  @classmethod
  def fromFile(cls, file,main_list):
    attributes = cls.read_attributes_from_file(file, main_list)
    if attributes is None:
      return None
    else:
      return cls(*attributes)


  def get_areas(self,main_list):
    try:
      web = requests.get(self.area_url)
      soup = bs4.BeautifulSoup(web.text,"lxml")
    except:
      main_list.set_title("Cannot connect: "+ self.area_url,MessageList.ERR)
      return None
    
    scraper = Scraper(soup,self.areas_source)
    data = scraper.scrap()

    areas = data[0]

    #print(areas)
    #areas = ["medicina-salud"] #Test Aptitus
    #areas = ["/empleos-area-salud-medicina-y-farmacia.html"] #Test Bumeran

    if areas is None:
      main_list.set_title("Failed to scrap areas. Check areas source",MessageList.ERR)
      return None
    else:
      main_list.set_title(str(len(areas)) + " Areas obtained",MessageList.INF)
      return areas


  def get_num_offers(self,date_url,main_list):
    try:
      web = requests.get(date_url)
      soup = bs4.BeautifulSoup(web.text,"lxml")
    except:
      main_list.add_msg("Cannot access to the url " + date_url,MessageList.ERR)
      return None

    scraper = Scraper(soup, self.num_offSource)

    data = scraper.scrap()

    num_off = data[0]
      

    try:
      num_off = int(num_off.split()[0])
    except:
      main_list.add_msg("value obtained is not a number",MessageList.ERR)
      num_off = None

    if num_off is None:
      main_list.set_title("Fail scraping number of offers.",MessageList.ERR)
      return None

    return num_off


  def get_offers_from_page_url(self,page_url):

    try:
      web = requests.get(page_url)
      soup = bs4.BeautifulSoup(web.text,"lxml")

    except:
      eprint("Cannot access to the url: "+ page_url + "\n")
      return None


    tot_links = []
    tot_dates = []

    for source in self.list_sources:
      levels = source.split('->')
      index = 0

      scraper = Scraper(soup,source)
      data = scraper.scrap()

      off_links = data[0]
      dates = data[1]
        

      if off_links is None or len(off_links) == 0:
        #Useless source
        eprint("No offers obtained using Source: " + source)
        continue

      else:
        #Remember:offLink must be a list

        for index, link in enumerate(off_links):
          if not link in tot_links:
            tot_links.append(link)
            tot_dates.append(dates[index])

    tot_offers = []
    for index,link in enumerate(tot_links):
      eprint("    Offer #"+str(index+1))

      try:
        link_url = self.module.make_link_url(link,page_url)
      except:
        main_list.set_title("make_link_url is not working propertly", MessageList.ERR)
        return None

      offer = self.get_offer_from_link(link_url)

      if offer is not None:
        pass_time = tot_dates[index]
        #check!
        pub_date = self.to_publication_date(pass_time)
        offer.month = pub_date.month
        offer.year = pub_date.year
        tot_offers.append(offer)
      else:
        tot_offers.append(offer)

    return tot_offers


  def get_offers_from_period_url(self,period_url, main_list):

    msg_list = MessageList()
    self.num_off = self.get_num_offers(period_url,msg_list)
    main_list.add_msg_list(msg_list)

    if self.num_off is None:
      return None

    main_list.add_msg("Número de ofertas encontradas: " + str(self.num_off),MessageList.INF)

    max = 2000
    num_pag = 0
    total_offers = []

    while num_pag < max and len(total_offers) < self.num_off:
      num_pag += 1

      try:
        page_url = self.module.make_page_url(num_pag,period_url)
      except:
        main_list.set_title("make_page_url is not working propertly", MessageList.ERR)
        #Abort everything
        return None #Return total_offers if you dont wanna abort all

      eprint("  Page #"+str(num_pag))
      offers = self.get_offers_from_page_url(page_url)
      eprint("")

      if offers is None:
        #Error page
        break
      else:
        total_offers += offers
        if len(offers)!=self.links_per_page and len(total_offers)!=self.num_off:
          main_list.add_msg("Unexpected number of offers at page #"+ str(num_pag), MessageList.INF)

    main_list.set_title(str(len(total_offers)) + " offers obtained in total (Invalid included)",MessageList.INF)
    return total_offers
          
  #Must be sent to Functions
  def to_publication_date(self, pass_time):
    cur_date = datetime.datetime.now()
  
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
      pub_date = cur_date - datetime.timedelta(days = value*30)
    
    return pub_date
  
  def get_offers_from_area_url(self,area_url,main_list):

    period_url = self.module.make_period_url(self.period,area_url)
    try:
      period_url = self.module.make_period_url(self.period,area_url)
    except:
      main_list.set_title("make_period_url function is not working propertly",MessageList.ERR)
      return None

    msg_list = MessageList()
    offers = self.get_offers_from_period_url(period_url,msg_list)
    main_list.add_msg_list(msg_list)

    if offers is None:
      main_list.set_title("No se pudo obtener las ofertas",MessageList.ERR)
      return None

    else:
      valid_offers = []
      for offer in offers:
        if offer is not None:
          valid_offers.append(offer)

      main_list.set_title(str(len(valid_offers))+ " ofertas validas seleccionadas",MessageList.INF)
      return valid_offers


  def execute(self,main_list):

    print(self.job_center)
    UnprocessedOffer.connectToDatabase(self.job_center)

    #Importing Custom Functions
    msg_list = MessageList()
    mod = custom_import(self.func_filename,msg_list)
    main_list.add_msg_list(msg_list)

    if mod is not None:
      self.module = mod

      msg_list = MessageList()
      areas = self.get_areas(msg_list)
      main_list.add_msg_list(msg_list)

      if areas is not None:
        try:
          urls = self.module.make_area_urls(areas,self.url_base)
          area_urls = list(urls)
        except:
          main_list.add_msg("La funcion make_area_urls no esta funcionando correctamente",MessageList.ERR)
          main_list.set_title("La plantilla falló al ejecutarse"+ self.job_center, MessageList.ERR)
          return None

        for index,area_url in enumerate(area_urls):
          
          main_list.add_msg("Area #"+str(index+1),MessageList.INF)
          main_list.add_msg(area_url,MessageList.INF)
          msg_list = MessageList()
          eprint("Area #"+str(index+1)+"   "+area_url)
          offers = self.get_offers_from_area_url(area_url,msg_list)
          eprint("------------------------------------------------------------------------------")
          main_list.add_msg_list(msg_list)

          if offers is not None:
            msg_list = MessageList()
            load_offers(offers,msg_list)
            main_list.add_msg_list(msg_list)

        main_list.set_title("La plantilla " + self.job_center + " se ejecutó correctamente.", MessageList.INF)
        return 

    main_list.set_title("La plantilla " +self.job_center + " falló al ejecutarse",MessageList.ERR)
    return
    


def load_offers(offers, main_list):
  error_loading = False
  cnt_load = 0
  cnt_disc = 0
  cnt_err = 0

  for offer in offers:
    inserted = offer.insert()
    if inserted is None:
      cnt_err += 1
      error_loading = True
    else:
      if inserted:
        cnt_load += 1
      else:
        cnt_disc += 1

  main_list.add_msg(str(cnt_load)+ " Offers succesfully loaded to database", MessageList.INF)
  main_list.add_msg(str(cnt_disc)+ " Offers discarted because of duplication in database", MessageList.INF)
  main_list.add_msg(str(cnt_err) + " Offers failed to load to database", MessageList.ERR)

  if error_loading:
    main_list.set_title("Some offers couldn't be loaded. Check detail file", MessageList.ERR)
  else:
    main_list.set_title("All offers were loaded", MessageList.INF)



def custom_import(filename, main_list):

  mod_name = "Functions." + filename

  try:
    mod = importlib.import_module(mod_name)
  except:
    main_list.set_title("Incorrect function module filename", MessageList.ERR)
    return None

  #Check function existence
  custom_functions = dir(mod)

  if not "make_area_urls" in custom_functions:
    main_list.add_msg("Missing make_area_urls function",MessageList.ERR)

  if not "make_period_url" in custom_functions:
    main_list.add_msg("Missing make_period_url function", MessageList.ERR)

  if not "make_page_url" in custom_functions:
    main_list.add_msg("Missing make_page_url function",MessageList.ERR)

  if not "make_link_url" in custom_functions:
    main_list.add_msg("Missing make_link_url function",MessageList.ERR)

  if main_list.size() is not 0:
    main_list.set_title("Fail importing function file", MessageList.ERR)
    return None
  else:
    main_list.set_title("Function file imported", MessageList.INF)
    return mod 




#------------------------------------------------------------------------------------------------
class FeaturesSource:
  def __init__(self,names_source, values_source):
    self.names_source = names_source
    self.values_source = values_source


  @classmethod
  def fromFile(cls, file, main_list):
    fileline = file.readline()
    if fileline is None or utils.is_blank(fileline) :
      return None
      
    names = utils.read_source_from_string(fileline,main_list)
    if names is None:
      main_list.add_msg("Failed to read names", MessageList.ERR)
    values = utils.read_source_from_file(file)
    if values is None:
      main_list.add_msg("Failed to read values", MessageList.ERR)

    if main_list.contain_errors():
      return None
    else:
      return cls(names,values)






#------------------------------------------------------------------------------------------------
class OfferTemplate(Template):

  def __init__(self,global_attributes, id_features, feat_sources):

    Template.__init__(self,*global_attributes)
    self.id_features = id_features
    self.feat_sources = feat_sources
  

  @staticmethod
  def read_attributes_from_file(file,main_list):
    global_attr = Template.read_attributes_from_file(file,main_list)
    file.readline() #newline
    file.readline() #Offer Structure:

    id_features = utils.read_source_from_string(file.readline())
    id_feat = []
    for feature in id_features:
        id_feat.append(feature.lower())

    id_features = id_feat

    features_sources = []
    while True:
      msg_list = MessageList()
      features_source = FeaturesSource.fromFile(file,msg_list)
    
      if features_source is None:
        if msg_list.contain_errors():
          msg_list.set_title("Failed to read features Source #"+ str(len(features_sources)+1),MessageList.ERR)
          main_list.add_msg_list(msg_list)

        break
      else:

        features_sources.append(features_source)

    if not main_list.contain_errors():
      main_list.set_title("All Offer Template Attributes are OK :)",MessageList.INF)
      return global_attr, id_features, features_sources
    else:
      main_list.set_title("Some Offer Template Attributes are WRONG :(",MessageList.ERR)
      return None



  def get_data_from_source(self, soup, source):
    if source == "":
      return None

    else:
      if (type(source) is list):
        return source

      scraper = Scraper(soup, source)
      data = scraper.scrap()[0]
      return data


  def get_offer_from_link(self,link):

    try:
      web = requests.get(link)
      soup = bs4.BeautifulSoup(web.text,"lxml")

    except:
      eprint("Cannot access to the link "+link)
      return None


    features = {}
    for feat_source in self.feat_sources:
      names = self.get_data_from_source(soup, feat_source.names_source)
      values = self.get_data_from_source(soup, feat_source.values_source)
      print(values)

      for idx in range(min(len(names), len(values))):
        features[names[idx].lower()] = values[idx]
        

    #Get id
    id = ""
    for id_feat in self.id_features:
      try:
        id += features[id_feat] + ' '
      except:
        id += ' '
        #Hardcoding!!!!
        if id_feat == "descripción":
            eprint("    Descripción vacía. Oferta INVÁLIDA")
            eprint("    Link: ", link)
            return None

    id = tp.preprocess(id)
    if id =="": 
      eprint("    ID vacío. Oferta INVÁLIDA")
      eprint("    Link: ", link)
      return None
    else:
      offer = UnprocessedOffer(0,0,id,True, 0, features)
      return offer



