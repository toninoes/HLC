#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import argparse

parser = argparse.ArgumentParser(description='Cuenta las palabras de un texto dado.')
parser.add_argument('fichero', type=argparse.FileType('r'))
parser.add_argument('-r', dest='reverse', action='store_false', default=True, help='Invierte el orden de los resultados, según vaya ligado a la opción -f o -a')
parser.add_argument('-n', dest='num', type=int, help='Limita el numero de resultados a num resultados')
group = parser.add_mutually_exclusive_group()
group.add_argument('-a', dest='alpha', action='store_true', help='Ordena los resultados alfabeticamente.')
group.add_argument('-f', dest='frecuencia', action='store_true', help='Ordena los resultados por frecuencia de aparición. Por defecto ACTIVADA')

args = parser.parse_args()

texto = args.fichero.read()
args.fichero.close()

dicc={}

#########################################################################################################
# El método SPLIT del modulo RE toma como parámetros un patrón y una cadena, utilizando el patrón 
# a modo de puntos de separación para la cadena, devolviendo una lista con las subcadenas.
####### Como patrones se pueden utilizar varias secuencias especiales:
# "\d": un dígito. Equivale a [0-9]
# "\D": cualquier carácter que no sea un dígito. Equivale a [^0-9]
# "\w": cualquier caracter alfanumérico. Equivale a [a-zA-Z0-9_]
# "\W": cualquier carácter no alfanumérico. Equivale a [^a-zA-Z0-9_]
# "\s": cualquier carácter en blanco. Equivale a [ \t\n\r\f\v]
# "\S": cualquier carácter que no sea un espacio en blanco. Equivale a [^\t\n\r\f\v]
####### Para la repetición de caracteres:
#   + : lo que tenemos a la izquierda, puede encontrarse una o mas veces
#   * : lo que se sitúa a su izquierda puede encontrarse cero o mas veces
#   ? : lo que tenemos a la izquierda puede aparecer 0 o 1 veces
#  {n}: las n veces exactas que pueden aparecer el carácter de la izquierda
#######
# A continuación establezco el separador por: 1 o más caracteres no alfanuméricos: "\W+" 
#########################################################################################################

lista = re.split( "\W+", texto.lower())

numpalabras=0

for palabra in lista:
	if palabra.isalpha():
		if dicc.has_key (palabra):
			dicc [palabra] += 1
		else:
			dicc [palabra] = 1
		numpalabras += 1

lista = []

#########################################################################################################
# Voy añadiendo los elementos del diccionario en forma de tuplas a una lista. Por tanto obtengo una
# lista de tuplas, en la que cada tupla contiene (CLAVE, VALOR) del diccionario. 
#########################################################################################################

for elem in dicc:
	lista.append( (elem, dicc[elem]) )	
		
#########################################################################################################
# El valor del parámetro 'key' debe ser una función (por ejemplo una función lambda o anónima en línea) 
# que toma un solo argumento y devuelve una clave para fines de ordenación.
# Ordeno la lista utilizando según me interese algún índice de la tupla como clave de ordenación.
#########################################################################################################

if args.alpha:
	lista = sorted(lista, key = lambda tupla: tupla[0], reverse = args.reverse)
else:
	lista = sorted(lista, key = lambda tupla: tupla[1], reverse = args.reverse)

#########################################################################################################
#			http://wiki.python.org/moin/HowTo/Sorting/
#...o también:
#
# import operator
# if args.alpha:
# 	lista = sorted(lista, key = operator.itemgetter(0), reverse = args.reverse)
# else:
# 	lista = sorted(lista, key = operator.itemgetter(1), reverse = args.reverse)
#########################################################################################################

contador = 0
for tupla in lista:
	porcentaje = (100 * tupla[1]) / numpalabras
	print tupla[0] + ": ",tupla[1]," veces - ",porcentaje,"%"
	contador += 1
	if contador == args.num:
		break

print "TOTAL ", numpalabras, " PALABRAS"

