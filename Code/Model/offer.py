import sys
from cassandra.cluster import Cluster
sys.path.append("..") 
from Utils import utils
import uuid
from pyexcel_ods import get_data

class Offer:
  session = None

  def __init__(self,year = 0, month = 0, id = ""):
    self.year = year
    self.month = month
    self.id = id

  @classmethod
  def connectToDatabase(cls,source):
    cluster = Cluster()
    cls.session = cluster.connect(source)

#------------------------------------------------------------------------------------------------

from datetime import datetime

class UnprocessedOffer(Offer):

  def __init__(self, year=0, month=0, id = "", auto_process = True, date_process=0, features = {}):
    Offer.__init__(self,year,month, id)
    self.auto_process = auto_process
    self.date_process = date_process
    self.features = features

  @classmethod
  def fromCassandra(cls, auto_process):
    cmd = """
          SELECT * FROM unprocessed_offers WHERE auto_process = %s;
          """
    try:
      rows = cls.session.execute(cmd, [auto_process])
    except:
      return False

    offers = []
    rows = list(rows)

    for row in rows:
      date_process = row.date_process
      year = row.year
      month = row.month
      id = row.id
      features = row.features
      offer = UnprocessedOffer(year, month, id, auto_process, date_process, features)
      offers.append(offer)

    return offers


  @classmethod
  def fromExcel(cls,filename):
    try:
      wb = get_data(filename)
    except:
      print("")
      print("Error al leer el archivo de excel. Archivo no encontrado")
      print("Por favor revise que el nombre del archivo sea el correcto.")
      print("--------------------------")
      return False

    sheets = list(wb.items())
    sheet = sheets[0][1]  # 0-> First sheet, 1-> Sheet data
    columns = sheet[0]
    num_columns = len(columns)
    num_rows = len(sheet)
      
    offers = []
    for r in range(1,num_rows):
      id = ""
      features = {}
      for c in range(0,num_columns):
        feature = columns[c]
        if feature == "Job: Posting Date":
          try:
            dt = datetime.strptime(sheet[r][c], '%d/%m/%Y')
          except:
            print("")
            print("Error al tratar de obtener la fecha de la oferta: {0}. \
                   Formato incorrecto".format(r))
            print("Por favor revise que la oferta contenga una fecha de publicación \
                   y que esta se encuentre en el formato dd/mm/yyyy")
            return False
          month = dt.month
          year = dt.year
        else:
          try:
            features[feature] = str(sheet[r][c])
          except:
            features[feature] = ""
          id += str(features[feature])
    
      unprocOffer = cls(year, month, id, True, 0, features)
      offers.append(unprocOffer)

    return offers

  @classmethod
  def createTable(cls):
    cmd = """
          CREATE TABLE IF NOT EXISTS unprocessed_offers (
          auto_process boolean,
          date_process timestamp,
          year int,
          month int,
          id text,
          features map<text,text>,
          PRIMARY KEY(auto_process,date_process, year, month, id));
          """

    try:
      UnprocessedOffer.session.execute(cmd)
    except:
      print("")
      print("Error al ejecutar un comando cql para crear la tabla de ofertas no procesadas.")
      print("Por favor, revise el nombre de la tabla o su conexión con la base de datos")
      print("---------------------")
      return False

    return True

  def disable_auto_process(self,auto_process):

    cmd_delete = """
                 DELETE FROM unprocessed_offers WHERE
                 auto_process = %s AND
                 date_process = %s AND
                 year = %s AND
                 month = %s AND
                 id = %s;
                 """

    cmd_insert = """
                 INSERT INTO unprocessed_offers
                 (auto_process, date_process, year, month, id, features)
                 VALUES
                 (%s,%s,%s,%s,%s,%s);
                 """


    UnprocessedOffer.session.execute(cmd_delete, [self.auto_process, self.date_process,
                                                  self.year, self.month, self.id])


    if not auto_process:
      UnprocessedOffer.session.execute(cmd_insert, [False, self.date_process,
                                                    self.year, self.month, self.id,self.features])
    else:
      UnprocessedOffer.session.execute(cmd_insert, [False, datetime.now().date(),
                                                    self.year, self.month, self.id, self.features])

    return True

  def insert(self):

    findTable = "unprocessed_offers_by_id"
    storeTable = "unprocessed_offers"

    cmd = """
          SELECT * FROM {0} WHERE id = %s and year = %s and month = %s;
          """.format(findTable)
            
    result = UnprocessedOffer.session.execute(cmd, [self.id,self.year,self.month])
    try:
      pass
    except:
      return None

    if len(list(result)) == 0:
      cmd = """
            INSERT INTO {0}
            (id, year, month, features)
            VALUES
            (%s,%s,%s,%s);
            """.format(findTable)

      UnprocessedOffer.session.execute(cmd, [self.id,self.year, self.month,self.features])
      try:
        pass
      except:
        eprint("")
        eprint("Error al insertar en la tabla de ofertas por id")
        eprint("----------------------------------------------")
        return None



      cmd = """
            INSERT INTO {0}
            (auto_process, date_process, year, month, id, features)
            VALUES
            (%s,%s,%s,%s,%s,%s);
            """.format(storeTable)


      UnprocessedOffer.session.execute(cmd, [self.auto_process, self.date_process, self.year, self.month, self.id, self.features])
      try:
        pass
      except:
        eprint("")
        eprint("Error al ejecutar un comand cql para insertar la oferta no procesada.")
        eprint("Por favor revise los atributos de la oferta o su conexión con la base de datos")
        eprint("----------------------")
        return None

      return True
    else:
      return False



