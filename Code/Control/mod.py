from cassandra.cluster import Cluster
from datetime import datetime
import time
import textProcessor as tp

import sys
sys.path.append('..')
sys.path.append('../..')

from Model.offer import UnprocessedOffer



cluster = Cluster()
session = cluster.connect('aptitus')

UnprocessedOffer.connectToDatabase('aptitus')



id_features = ['descripción','requisitos','titulo']

#id_features.sort()

cmd = """
      SELECT * FROM unprocessed_offers where auto_process = True;
      """

cmd_insert = """
             INSERT INTO unprocessed_offers
             (id, year, month, features)
             VALUES
             """

cmd_find = """
           SELECT * FROM unprocessed_offers_by_id WHERE
           id = %s AND
           year = %s AND
           month = %s;
           """




result = session.execute(cmd)
cnt = 0

for row in result:
    features = row.features
    new_features = {}
    for feature,value in features.items():
        new_features[feature.lower()] = value

    new_id =  ""
    for id_feat in id_features:
        try:
            new_id += new_features[id_feat] + ' '
        except:
            new_id += ' '

    new_id = tp.preprocess(new_id)
    offer = UnprocessedOffer(row.year, row.month, new_id, False, 0, new_features)
    offer.insert()


#
#
#cmd1 = "select * from unprocessed_offers_by_id;"
#cmd2 = "select * from unprocessed_offers;"
#cmd3 = "delete from unprocessed_offers_by_id where id = %s and year = %s and month = %s;"

#
#
#r1 = list(session.execute(cmd1))
#
#cnt = 0
#for row in r1:
#    if row.year == 2018:
#        session.execute(cmd3,[row.id,row.year, row.month])
#


#r2 = list(session.execute(cmd2))
#
#id2 = []
#for row in r2:
#    id2.append(row.id)
#
#
#cnt = 0
#for row in r1:
#    if row.id not in id2:
#        session.execute(cmd3,[row.id,row.year, row.month])
#
#
#result = list(session.execute(cmd))






#
#cluster = Cluster()
#session = cluster.connect('bumeran')
#
#cmd = """
#      SELECT * FROM unprocessed_offers where auto_process = False;
#      """
#
#
#cmdFind = """
#          SELECT * FROM unprocessed_offers_by_id where id = %s and year= %s and month = %s;
#          """
#
#
#cmdDelete = """
#            DELETE FROM unprocessed_offers where auto_process = False;
#            """
#
#
#session.execute(cmdDelete)
#

#
#
#result = list(session.execute(cmd))
#cnt = 0
#for row in result:
#  session.execute(cmdDelete, [row.id, row.year, row.month])
#  cnt += 1
# 
#print(cnt)
#









#session.execute(cmdDelete)
#
#result = list(session.execute(cmd))
#cnt = 0
#for row in result:
#  session.execute(cmdDelete, [row.id, row.year, row.month])
#  #res = list(session.execute(cmdFind,[row.id, row.year, row.month]))
#  cnt += 1
#
#
#print(cnt)









  

















#cmdI = """
#       INSERT INTO foo 
#       (auto_process, date_process, year, month, id, features)
#       VALUES
#       (%s,%s,%s,%s,%s,%s)
#       IF NOT EXISTS;
#       """
#
#check = """personas con gran nivel de energía orientado a la satisfacción del cliente trabajo en equipo y trabajo bajo presión modalidad full time atractivo paquete remunerativo oportunidad de crecimiento entrenamiento permanente y trabajar en un lugar divertido"""
#
#
#result = list(session.execute(cmd))
#for row in result:
#  features = list(row.features.keys())
#  features.sort()
#
#  newFeat = {}
#  for feat in features:
#    newFeat[feat.lower()] = row.features[feat]
#
#  r = session.execute(cmdI, [row.auto_process, row.date_process, row.year, row.month, row.id, newFeat])
#  if (r[0].applied is False):
#    print(r[0])
#    
#
#
#

  #Ordenamos para tener un orden ps

  #id = ""
  #for feat in features:
  #  text = tp.preprocess(row.features[feat])
  #  id += text + ' '

  #print(id)
  #r = session.execute(cmdI,[row.auto_process, row.date_process, row.year, row.month, id, row.features])
  #id = tp.preprocess(row.id)



  #res = session.execute(cmdI,[row.auto_process, row.date_process, row.year, row.month, id, row.features])

  #if (res[0].applied is False):
  #  print(res[0]) 


#cluster1 = Cluster()
#ses1 = cluster1.connect('btpucp')
#
#cluster2 = Cluster()
#ses2 = cluster2.connect('bumeran')
#
#cmd1 = """
#			 SELECT * FROM unprocessed_bumeran_by_desc;
#			 """
#
#cmd2 = """
#			 INSERT INTO unprocessed_offers_by_id
#			 (id, year, month, features)
#			 VALUES
#			 (%s,%s,%s,%s)
#			 """
#
#cmd3 = """
#			 INSERT INTO unprocessed_offers
#			 (auto_process, date_process, year, month, id, features)
#			 VALUES
#			 (%s,%s,%s,%s,%s,%s)
#			 """
#
#res1 = list(ses1.execute(cmd1))
#
#for row in res1:
#	ses2.execute(cmd2, [row.description, row. year, row.month, row.features])
#	ses2.execute(cmd3, [True, 0, row.year, row.month, row.description, row.features ])
#
#
#
#res2 = list(session.execute(cmd2))

#d1 = []
#d2 = []
#for row in res1:
#	d1.append(row.description)
#
#
#for row in res2:
#	d2.append(row.description)
#
#
#cnt = 0
#for d in d1:
#	if d in d2:
#		cnt+=1
#
#
#print(cnt)
#







#
#
#
#
#result = list(session.execute(cmd1))
#
#cmd2 = """
#			 INSERT INTO unprocessed_bumeran_by_desc
#			 (description,month, year, features)
#			 VALUES
#			 (%s,%s,%s,%s);
#			 """
#
#cmd3 = """
#			 INSERT INTO unprocessed_bumeran
#			 (auto_process, date_process, description, features, publication_date)
#			 VALUES
#			 (%s,%s,%s,%s,%s);
#			 """
#
#for row in result:
#	desc = row.description
#	features = row.features
#	pubDate = row.pubdate
#
#	month = pubDate.month
#	year = pubDate.year
#
#	session.execute(cmd2,[desc,month,year,features])
#	session.execute(cmd3,[False,0,desc, features, pubDate])
#
#
#
##
##cmd4 = """
##			 SELECT * FROM unproc_offer_aptitus_by_desc;
##			 """
##
##result = list(session.execute(cmd4))
##
##
##cnt2 = 0
##for row in result:
##	if (row.year == 2016):
##		cnt2 += 1
##	
##
##print(cnt1, cnt2)
##
##
##
#
#	#session.execute(cmd2,[desc,month,year,features])
#	#session.execute(cmd3,[false,0,desc, features, pubdate])
#
#
#
#
#
#
#
#
#	
#
#
#
#
#
