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

import datetime

def create_template(temp_filename, main_list):
  try:
    temp_file = open(temp_filename, 'r')
  except OSError:
    main_list.set_title("Plantilla no encontrada", MessageList.ERR)
    return None

  msg_list = MessageList()
  template = OfferTemplate.fromFile(temp_file, msg_list)
  main_list.add_msg_list(msg_list)

  if template is None:
    main_list.set_title("No se pudo inicializar la plantilla", MessageList.ERR)
    return None
  else:
    main_list.set_title("Plantilla creada", MessageList.INF)
    return template


def send_email(sender, password, receiver, filename):

  msg = MIMEMultipart()
  with open("summary.txt") as repFile:
    part = MIMEText(repFile.read())
    msg.attach(part)
  msg['Subject'] = "Resultados del WebScraping"
  msg['From'] = "btpucp"
  msg['To'] =receiver


  sys.stderr.flush()

  with open(filename, "rb") as file:
    part = MIMEApplication(file.read(), Name = basename(filename))
    part['Content-Disposition'] = 'attachment; filename="%s"' % basename(filename)
    msg.attach(part)
        

  s = smtplib.SMTP('smtp.gmail.com', 587)
  s.starttls()
  try:
    s.login(sender, password)
    s.send_message(msg)
  except:
    print("No se pudo enviar el correo por error en el usuario o contraseña")

  s.quit()

def read_config_file(main_list):

  config_filename = "../../config"

  try:
    conf_file = open(config_filename, 'r')
  except OSError:
    main_list.set_title("Configuration file not found", MessageList.ERR)
    return None

  sender, _ = utils.read_text_from_file(conf_file)
  password, _ = utils.read_text_from_file(conf_file)
  receiver, _ = utils.read_text_from_file(conf_file)
  out, _ = utils.read_text_from_file(conf_file)

  filenames = []
  while True:
    filename, _ = utils.read_text_from_file(conf_file)
    if filename is None:
      break
    else:
      filename = add_template_path(filename)
      filenames.append(filename)
  
  if check_config_values(sender, password, receiver, out, filenames):
    main_list.set_title("Archivo de configuracion leído correctamente", MessageList.INF)
    return sender, password, receiver, out, filenames
  else:
    main_list.set_title("Valores incorrectos en el archivo de configuración", MessageList.ERR)
    return None


def check_config_values(sender, password, receiver, out, filenames):
  if sender is None or password is None or receiver is None or out is None :
    return False
  return not len(filenames) == 0


def add_template_path(filename):
  relativePath = "../../Templates/"
  return relativePath + filename


def main():

  main_list = MessageList("Resumen:")
  msg_list = MessageList()

  sender, password, receiver, out, filenames = read_config_file(msg_list)
  main_list.add_msg_list(msg_list)

  sys.stdout = open("summary.txt", 'w')
  sys.stderr = open(out, 'w')
  
  for filename in filenames:
    msg_list = MessageList()
    template = create_template(filename, msg_list)
    main_list.add_msg_list(msg_list)

    if template is not None:
      msg_list = MessageList()
      template.execute(msg_list)
      main_list.add_msg_list(msg_list)

  main_list.show_all(0, sys.stdout)
  sys.stdout.flush()

  send_email(sender, password, receiver, out)


if __name__ == "__main__":
  main()
