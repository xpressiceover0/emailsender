# -*- coding: utf-8 -*-
import smtplib
import ssl
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import time
import datetime as dt

import uvicorn
from fastapi import FastAPI, Body, Header
from fastapi.middleware.cors import CORSMiddleware

import mysql.connector
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

# La clase fastApi inicia los endpionts de la api
app=FastAPI()

# CORS
app.add_middleware(CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'])

# 
email_sender = 'thelegendofmax19@gmail.com'
email_password = 'cbelvesalapkaepo'

datos_conn = {
            'user': 'nora_martinez',
            'password': '*nora2021*',
            'host': '10.10.160.31',
            'port': '3306',
            'database': 'intermedia_espejo',
            'raise_on_warnings': True}

class Navegador:

    def __init__(self):
    
        # Ruta del web driver chromedriver.exe (Este driver funciona para brave)
        
        self.driver_path = "/usr/src/emailsender/webdrivers/chromedriver"
        #self.driver_path = "C:\\Users\\Intermedia\\Desktop\\screenshuts\\webdrivers\\chromedriver.exe"

        # Ruta del ejecutable del navegador brave. Es necesario instalarlo y esta ruta es la ruta por default de la instalación
        #self.brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        self.brave_path = "/usr/bin/brave-browser"
        
        # Se mandan las opciones inician el perfil del navegador
        option = webdriver.ChromeOptions()
        # Se manda el path del navegador brave ya que por default funciona con chrome
        option.binary_location = self.brave_path
        # Evita que l navegador imprima los logs
        option.add_argument("--log-level=3")
        # Manda modo incognito que evita guardar cache
        option.add_argument("--incognito")
        # Usa el navegador sin interface gráfica
        option.add_argument("--headless")
        # Inicia el navegador en pantalla completa
        option.add_argument("start-maximized")
        # Habilita la automatizacion
        option.add_argument("enable-automation")
        # Desabilita las barras de información que emite el navegador
        option.add_argument("disable-infobars")
        # Deshabilita las extensiones
        option.add_argument("--disable-extensions")
        # deshabilita el uso del gpu
        option.add_argument("--disable-gpu")
        # 
        option.add_argument("--disable-dev-shm-usage")
        #
        option.add_argument("--no-sandbox")
        # Crea una navegador listo para usarse

        self.driver = webdriver.Chrome(self.driver_path, chrome_options=option)
    
    def get(self, url):
        
        # Intentamos hacer una peticion con el metodo .get() del navegador y 
        # esperamos hasta que el el documento html se haya cargado por completo con un tiempo maximo de 20 seg 
        try:    
            self.driver.get(url)
            WebDriverWait(self.driver, 20).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

            return True
        except:
            return False


def email1(data, nav):
    email_receiver=data[1]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = data[2]
    msg["From"] = email_sender
    msg["To"] = email_receiver
    r=nav.driver.page_source
    time.sleep(1)
    
    r=re.sub('[\n\t\r]', "", r)
   
    part = MIMEText(r, "html")
    msg.attach(part)
    encoders.encode_base64(part)
    
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, msg.as_string())
        return True
    except:
        return False
        

# targets son los urls de los que se extrae el id
@app.post("/sendto", status_code=201) 
def sendmails(master_id: str = Header(...), target: str = Body(...), userid: int = Body(...), clientid: int = Body(...)):
    if master_id=='12345':
        #para usar el UUID del usuario se debe hacer un select anidado a los usuarios para obtener el ID principal
        #idcliente=re.findall('u=.+', target)[0][2:]

        conn=mysql.connector.connect(**datos_conn)
        cursor = conn.cursor(buffered=True)
        nav=Navegador()
        try:
            cursor.execute('SELECT usuario_envio_correo.cfUsuClave, correo, asunto, FechaInicial, FechaFinal, estatus, conFecha, NOW()'\
                     ' FROM intermedia_espejo.usuario_envio_correo INNER JOIN intermedia_espejo.usuario_envio ON'\
                         f' usuario_envio_correo.cfUsuClave = usuario_envio.cfUsuClave WHERE usuario_envio.cfUsuClave={clientid};')
        except:
            return {'message':'Error al conectar con la base de datos'}
            
        finally:
            conn.commit()

        rows=list(cursor)
        if len(rows[0][1])>1:
            exito=nav.get(target)
            time.sleep(3)
            
            if exito:
                enviados=[]
                erroneos=[]

                for r in range(len(rows)):
                    
                    fecha_hoy=dt.datetime.now()
                    data=[target, rows[r][1], rows[r][2]]
                    if rows[r][5]==1 and rows[r][3]<=fecha_hoy and fecha_hoy<=rows[r][4]:
                       
                        if rows[r][6]:
                            data[2]=data[2]+', '+str(fecha_hoy)
                        exito=email1(data, nav)
                        if exito:
                            enviados.append(rows[r][1]+'|'+str(200))
                        else:
                            erroneos.append(rows[r][1]+'|'+str(500))
                    else:
                        erroneos.append(rows[r][1]+'|'+str(401))
                   
                query=f"INSERT INTO intermedia_espejo.usuario_envio_fecha (cfUsuClaveEnvio, cfUsuClave, FechaInicioEnvio) VALUES ({userid}, {clientid}, '{rows[0][-1]}');"
               
                try:
                    cursor.execute(query)
                    
                except:
                    return {'message': 'Error al actualizar la base: usuario_envio_fecha'}
                
                finally:
                    conn.commit()

                response={}
                response['message']='Elementos enviados: '+ str(len(enviados))+'. Elementos erroneos: '+ str(len(erroneos))
                response['count']=len(enviados)+len(erroneos)
                response['sent']=enviados
                response['notsent']=erroneos
                return response
                
            else:
                return {'message':'Error al cargar la url del informe: '+target}
        else:
            return {'message':'El usuario no tiene correos registrados'}
    else:
        return {'message':'Requiere autorización'}
    

if __name__=='__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)