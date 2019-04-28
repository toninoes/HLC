#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import Queue
import argparse
import threading
import pyinotify

########################################################################
# Para hacer los bloqueos con python-iptables
# Para bloquear IPs debe ejecutarse el script como ROOT.
# Más info: http://nilvec.com/python-iptables/
#           https://github.com/ldx/python-iptables
#           http://nilvec.com/stuff/python-iptables/docs/html/index.html
########################################################################
import iptc

##########################################################################
# Para bloquear las IPs también podría usar el modulo python-netfilter:
# 	sudo apt-get install python-netfilter
# Para bloquear IPs debe ejecutarse el script como ROOT.
# Tambien disponible en:
# http://opensource.bolloretelecom.eu/files/python-netfilter-0.5.7.tar.gz
##########################################################################
# from netfilter.rule import Rule
# from netfilter.table import Table

parser = argparse.ArgumentParser(description='Bloquea de forma inmediata una IP no autorizada que intenta conectarse al sistema. Para ello vigilará diferentes ficheros logs')
parser.add_argument('log', type=str, nargs='+', help='Lista de logs que voy a monitorizar')
parser.add_argument('-q', dest='noregistrar', action='store_true', default=False, help='No se registran los bloqueos')
parser.add_argument('-t', dest='tipos', type=list, help='Tipos de incidentes que se van a controlar. A: Escaneo de puertos, B: Intento loguearse como root, C: Busca usuarios válidos, D: Falseos de host de origen')
parser.add_argument('-n', dest='veces', type=int, default=4, help='Veces que se tiene que repetir el incidente para bloquear la IP. Por defecto:  %(default)s')

args = parser.parse_args()


########################################################################
# Defino la clase MiHilo, la cual hereda de la clase Thread, su misión 
# es coger de la cola (si hay algo) y quedarse con una lista, la cual 
# contendrá las últimas lineas que se han generado en el log 								
# El diccionario (dicc) contiene:													 
#  -Clave: nombre y ruta absoluta de un fichero										
#  -Valor: Objeto fichero abierto y con el puntero situado en la 
#          ultima posición de lectura realizada.														
########################################################################
class MiHilo(threading.Thread):
	def __init__(self, q, diccFiles):
		self.q = q
		self.diccFiles = diccFiles
		threading.Thread.__init__(self)
	def run(self):
		while True:
			fichero = q.get()
			ultimasL = diccFiles[fichero].readlines()
			analizalineas(ultimasL)

########################################################################
# Aqui defino una clase, la cual hereda de ProcessEvent y manejará las 
# notificaciones específicamente cuando detecte una modificación 
# "_IN_MODIFY", simplemente lo que hace cuando detecta una modificación 
# en un fichero será meter en la cola "q", el nombre y ruta del fichero 
# que ha generado ese evento.							
########################################################################
class EventHandler(pyinotify.ProcessEvent):		
	def process_IN_MODIFY(self, event):
		q.put(event.pathname)
		print "Modificado fichero "+event.pathname


########################################################################
# Función para analizar una lista de lineas recibidas y guarda  
# aquellas IPs que cumpla con los criterios de busqueda.
########################################################################
def analizalineas(listalineas):
	global busquedas
	for linea in listalineas:
		for cad in busquedas:
			if cad in linea:
				IP = linea.split()[busquedas[cad]]
				guardaIP(IP)

########################################################################
# Función para guardar las IP sospechosas en un diccionario.
# Las guarda en el diccionario de ámbito global (dicIP). Además si la IP
# se encuentra un número de veces superior al indicado en args.veces,
# llamará a la función bloqueaIP, para bloquear esa IP.
########################################################################
def guardaIP(IP):
	global dicIP
	global args
	if dicIP.has_key(IP):
		dicIP[IP] +=1					
	else:
		dicIP[IP] =1
	if dicIP[IP] >= args.veces:
		bloqueaIP(IP)
		if not args.noregistrar:
			print "Detectadas %s maniobras no autorizadas para IP: %s" % (dicIP[IP], IP)

########################################################################
# Esta función toma una cadena como parámetro, la cual es la IP origen a
# bloquear, la cual la añado a la cadena INPUT de la tabla FILTER.
# La acción será DROP, con lo que se elimina el paquete sin avisar al
# equipo que hace la petición. Mas ejemplos:
# http://opensource.bolloretelecom.eu/projects/python-netfilter/
########################################################################
# Así es como lo hacía con python-netfilter:
#def bloqueaIP(IP):
#	print "Bloqueada la IP "+IP
#	regla = Rule(source = IP, jump='DROP')
#	tabla = Table('filter')
#	tabla.append_rule('INPUT', regla)
	
def bloqueaIP(IP):		
	cadenaInput = iptc.Chain(iptc.TABLE_FILTER, "INPUT")
	regla = iptc.Rule()
	regla.src = IP
	hacer = iptc.Target(regla, "DROP")
	regla.target = hacer
	cadenaInput.insert_rule(regla)
	print "Bloqueada la IP %s" % (IP)

	
	
########################################################################
# En este diccionario voy a ir guardando las IPs que son sospechosas
# Con la Clave:Valor -->  IP : nº veces que ha intentado hacer la gracia
########################################################################
dicIP = {}

########################################################################
# Como la opción -t es de tipo lista, puede recibir 1 o mas argumentos,
# que se guarda en args.tipos, voy a iterar sobre esa lista para ver que
# son y en función de lo que sean, añadir entradas a un diccionario, en
# la que la clave es la cadena que quiero buscar en cada línea del log,
# y el valor es el lugar que ocupa dentro de la linea la IP atacante,
# cuando haga un linea.split().
########################################################################
busquedas = {}
for tipo in args.tipos:
	if tipo == 'A':
		busquedas['Did not receive identification string from'] = -1
	elif tipo == 'B':
		busquedas['Failed password for root from'] = -4
	elif tipo == 'C':
		busquedas['Illegal user'] = -1
	elif tipo == 'D':
		busquedas['but this does not map back to the address'] = 6

########################################################################
# El diccionario (diccFiles) contiene:													
#  -Clave: nombre de un fichero	de log									  
#  -Valor: Objeto fichero abierto y con el puntero situado al final del 
#          fichero (EOF), eso lo hago con el .seek(0,2)											 
########################################################################
diccFiles={}
for f in args.log:
	fichero = os.path.abspath(f)
	diccFiles[fichero]=open(fichero,"r")
	diccFiles[fichero].seek(0,2)

########################################################################
# Creo una cola que utilizaré para ir añadiendo los nombres de los	 
# ficheros que generan el evento buscado. 
########################################################################
q = Queue.Queue()

########################################################################
# Creo un objeto WatchManager, que provee funciones de vigilancia
########################################################################
wm = pyinotify.WatchManager() 

########################################################################
# Establezco la máscara o los eventos de los que voy a estar pendiente
########################################################################
mask = pyinotify.IN_MODIFY 

########################################################################
# Ahora instancio la clase ThreadedNotifier, que creará un objeto 
# notificador a modo de hilo. Luego comienza el notificador 
# (se crea el hilo con notifier.start())    
# aunque todavía no va a monitorizar ningún fichero ni directorio.					 
########################################################################
notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
notifier.start()

########################################################################
# Seguidamente le añado algo para monitorizar con wm.add_watch(), 
# en este caso le añado cada uno de los ficheros que se almacena en la 
# lista lo que me pasa argparse en args.log.
# Además para cada log voy a lanzar un hilo.
########################################################################
for log in args.log:
	wdd = wm.add_watch(log, mask)
	print "Monitorizando log: %s"% (log)
	hilo = MiHilo(q, diccFiles)	
	hilo.start()


