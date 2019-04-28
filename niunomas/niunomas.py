#!/usr/bin/env python
# -*- coding: utf-8 -*-

##########################################################################
# Para bloquear una IP: iptables -I INPUT -s IP-A-BLOQUEAR -j DROP
# o bien utilizar el modulo python-netfilter:
# 	sudo apt-get install python-netfilter
# Para bloquear IPs debe ejecutarse como ROOT.
# Tambien disponible en:
# http://opensource.bolloretelecom.eu/files/python-netfilter-0.5.7.tar.gz
##########################################################################

import argparse
from netfilter.rule import Rule
from netfilter.table import Table

parser = argparse.ArgumentParser(description='Bloquea una IP no autorizada que intenta conectarse al sistema.')
parser.add_argument('log', nargs='?', type=argparse.FileType('r'), default="/var/log/auth.log")
parser.add_argument('-q', dest='noregistrar', action='store_true', default=False, help='No se registran los bloqueos')
parser.add_argument('-t', dest='tipos', type=list, help='Tipos de incidentes que se van a controlar. A: Escaneo de puertos, B: Intento loguearse como root, C: Busca usuarios válidos, D: Falseos de host de origen')
parser.add_argument('-n', dest='veces', type=int, default=4, help='Veces que se tiene que repetir el incidente para bloquear la IP. Por defecto:  %(default)s')

args = parser.parse_args()

########################################################################
# Voy primero a guardar el contenido del log en una lista de cadenas. El
# log por defecto si no se pasa como argumento en '/var/log/auth.log'
########################################################################
log = args.log.readlines()

########################################################################
# Esta función toma una cadena como parámetro, la cual es la IP origen a
# bloquear, la cual la añado a la cadena INPUT de la tabla FILTER.
# La acción será DROP, con lo que se elimina el paquete sin avisar al
# equipo que hace la petición. Mas ejemplos:
# http://opensource.bolloretelecom.eu/projects/python-netfilter/
########################################################################
def bloqueaIP(ip):
	regla = Rule(source = ip, jump='DROP')
	tabla = Table('filter')
	tabla.append_rule('INPUT', regla)

########################################################################
# Esta función no hace falta sólo la he escrito para cuando hago pruebas
# poder borrar luego las reglas.
########################################################################
def desbloqueaIP(ip):
	regla = Rule(source = ip, jump = 'DROP')
	tabla = Table('filter')
	tabla.delete_rule('INPUT', regla)

diccIP = {}
busquedas = {}

########################################################################
# Como la opción -t es de tipo lista, puede recibir 1 o mas argumentos,
# que se guarda en args.tipos, voy a iterar sobre esa lista para ver que
# son y en función de lo que sean, añadir entradas a un diccionario, en
# la que la clave es la cadena que quiero buscar en cada línea del log,
# y el valor es el lugar que ocupa dentro de la linea la IP atacante,
# cuando haga un linea.split().
########################################################################
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
# Ahora voy a ver en cada linea del log, si se encuentra alguna de las
# cadenas que busco, en caso de encontrarse me quedo con la IP que la
# genera, según el caso.
# A su vez voy añadiendo a otro diccionario dichas IPs como clave y como
# valor el número de veces que se repite esa IP.
########################################################################
for linea in log:
	for cad in busquedas:
		if cad in linea:
			IP = linea.split()[busquedas[cad]]
			if diccIP.has_key(IP):
				diccIP[IP] += 1
			else:
				diccIP[IP] = 1

########################################################################
# Finalmente miro en el diccionario qué IPs sobrepasan el límite de
# veces establecido (por defecto 4), en dicho caso la IP será bloqueada
# utilizando la función que arriba me he creado gracias al módulo
# python-netfilter. Si la opción -q no está activada mostrará también
# que IP ha sido bloqueada. Para que funcione el script y bloquee, debe
# ejecutarse el script como root.
########################################################################
for elemento in diccIP:
	if diccIP[elemento] > args.veces:
		if not args.noregistrar:
			print "Detectadas %s maniobras no autorizadas para IP: %s" % (diccIP[elemento],elemento)
		bloqueaIP(elemento)
