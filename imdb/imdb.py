#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys
import urllib2
import pynotify
from BeautifulSoup import *

########################################################################
# Instalar con sudo apt-get install python-beautifulsoup
# La version 3.1.0 da problemas en ciertas webs que contengan etiquetas
# script y cuyos tags están mal formados. La versión 3.1.0.1 es la
# incluída en los repositorios de Ubuntu.
# Mejor descargar la version BeautifulSoup-3.0.8.py de:
#   http://www.crummy.com/software/BeautifulSoup/download/3.x/
# O bien la versión 3.2
# Saber version instalada, en ipython:
# import BeautifulSoup
# print BeautifulSoup.__version__
########################################################################


pelicula = sys.argv[1]
pelicula = pelicula.replace(" ","+")

imdb = "http://www.imdb.com"
url = imdb+"/find?s=kw&q="+pelicula

ua = "Mozilla/5.0 (X11; Linux i686; rv:6.0.2) Gecko/20100101 Firefox/6.0.2"
h = {"User-Agent": ua}

peticion = urllib2.Request(url, headers=h)

#Descargo el recurso para luego leerlo y analizarlo
try:
	recurso = urllib2.urlopen(peticion)
except:
	print "No se ha podido conectar a la web de los resultados"
	sys.exit()

#Leo y analizo el recurso
try:
	doc = BeautifulSoup(recurso.read())
except:
	print "No se ha podido analizar correctamente el documento"
	sys.exit(-1)


#Busco en primer lugar que haya una pelicula que coincida exactamente con el criterio de busqueda
#Si no hay coincidencia exacta aborto el script.
try:
	div = doc.find("div", {"id": "main"})
	p = div.find("p")
	b = p.find("b")
	if b.string != "Keywords (Exact Matches)":
		print "No existe ninguna pelicula que coincida exactamente con ese tÃ­tulo"
		sys.exit(-1)
except:
	print "Error en la busqueda de resultados"
	sys.exit()


#Llegados a este punto (hay una coincidencia exacta) obtengo la url donde está la nota de la peli
try:
	td = doc.findAll("td", {"valign": "top"})
	a = td[2].findAll("a")
	url = imdb + a[1]['href']
	print "Obteniendo pagina "+url
except:
	print "No se ha podido conseguir la url de la pelicula"
	sys.exit()


#Accedo a la segunda web en la cual está la nota de la pelicula:

peticion = urllib2.Request(url, headers=h)


try:
	recurso = urllib2.urlopen(peticion)
except:
	print "No se ha podido conectar con la web de la pelicula"
	sys.exit()


#Analizo el documento
try:
	doc = BeautifulSoup(recurso.read())
except:
	print "No se ha podido leer el documento de la pelicula"
	sys.exit(-1)

pelicula = pelicula.replace("+"," ")

#Obtengo la nota y la muestro con un notificador
try:
	div = doc.find("div", {"class": "star-box-giga-star"})
	nota = pynotify.Notification("NOTA PELICULA: "+pelicula, message=div.string)
	nota.show()
except:
	print "No se ha podido conseguir la NOTA de la pelicula"
	sys.exit()

