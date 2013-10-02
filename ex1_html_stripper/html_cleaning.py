#!/usr/bin/python
import os
import sys
import codecs
import time
import re
import traceback
from mmap import mmap

import common_support as sup

# sys.path.append("D:/Hector/Documents/fyp/WePS/tools/BeautifulSoup-3.0.8.1")
sys.path.append("./BeautifulSoup-3.0.8.1")

from BeautifulSoup import BeautifulSoup, Comment , CData, Declaration, ProcessingInstruction
from BeautifulSoup import BeautifulStoneSoup
# from BeautifulSoup import BeautifulSoup
# from BeautifulSoup import BeautifulSoup, CData
# from BeautifulSoup import BeautifulSoup, Declaration
# from BeautifulSoup import BeautifulSoup, ProcessingInstruction

#pre-define parameters


#Globals, value defined by the config file
BLOCK_LENGTH_THRESHOLD = 10
FILE_PER_NAME = 200
DELETE_BAR_DELI_TEXT = 0
DELETE_AFTER_COPYRIGHT = 0
CONVERT_LI_A_TO_BAR = 0
BAR_TEXT_MAX_LEN = 15
DEBUG = False


#To print non-ascii to terminal
streamWriter = codecs.lookup('utf-8')[-1]
sys.stdout = streamWriter(sys.stdout)
#set recursion limit
sys.setrecursionlimit(3000)




buggypage_name = "buggy_page.txt"


def insertToFile(page,str,pos,page_name):
	m = mmap(page.fileno(), os.path.getsize(page_name))
	origSize = m.size()
	
	if pos > origSize:
		pos = origSize
	elif pos <0:
		pos = 0
	
	m.resize(origSize + len(str))
	m[pos+len(str):] = m[pos:origSize]
	m[pos:pos+len(str)] = str
	m.close()
	
def deleteFromFile(page,pos_s,pos_e,page_name):
	m = mmap(page.fileno(), os.path.getsize(page_name))
	origSize = m.size()
	
	if pos_s > origSize:
		pos_s = origSize
	elif pos_s <0:
		pos_s = 0
		
	if pos_e <pos_s:
		return
	if pos_e > origSize:
		pos_e = origSize

	length = pos_e - pos_s
	con_af = m[pos_e:]
	m.resize(origSize - length)
	m[pos_s:] = con_af
	m.close()
	
#Rstrip for navigatable string	
def stripEndLine(instr):
	flag = 1
	while flag:
		if instr[-1:]=='\n' or instr[-1:]=='\r' or instr[-1:]==" ":
			instr=instr[:-1]
		else:
			flag = 0
	return instr

def countWords(string):
	numberOfWords = 0
	for line in string.split("\n"):
		tempwords = line.split(None)
		numberOfWords += len(tempwords)
	return numberOfWords
	
#Traverse the tree and construct a string as the origin order
#Need to consider using block level tags later
def visitSiblings(node):
	resultString = ""
	if node.__class__.__name__ == 'NavigableString':
		if node.string!=None and stripEndLine(node.string)!="":
			tempString = node.string
			if node.parent.name != 'p' or node.parent.name !='pre':
				tempString = tempString.replace('\n',' ')
				tempString = tempString.replace('&nbsp',' ')
			resultString += tempString + ' '
			# resultString += stripEndLine(node.string) + ' '
		
	elif not node is None:  #possible exception, may not cover all node types
		if node.name.lower() == "meta":
			try:
				if node['name'].lower() == "description":
					metaString = "[meta_des]" + node['content']+ "[/meta_des]\n"
					resultString += metaString
					
				elif node['name'].lower() == "keywords":
					metaString = "[meta_key]" + node['content'] + "[/meta_key]\n"
					resultString += metaString
			except KeyError:
				pass
		
		# try :
			# pass
		# except:
			# traceback.print_exc(file=sys.stdout)
		
		try :
			sons = node.contents
		except AttributeError as detail:
			print "AttributeError when get content: ",detail
			return ""
		else:
			if not sons is None:
				for son in sons:
					try:
						resultString += visitSiblings(son)
					except AttributeError as detail:
						print "AttributeError when get son: ", detail
						return ""
					except Exception as detail:
						print "Other exception: ",detail
					
					if CONVERT_LI_A_TO_BAR == 1: #if converted, the grouped <li><a></a><li> will be deleted
						if node.name == 'li':
							if son.__class__.__name__ == 'Tag':
								if son.name == 'a':
									resultString += " | "	
				
				if (tags_block_level.has_key(node.name) and not tags_important.has_key(node.name)):
					if countWords(resultString) < BLOCK_LENGTH_THRESHOLD:
						# print "Block ", node.name ," too small: " ,resultString, " word count = ",countWords(resultString)
						resultString = "" #eniminate blocks less than 10 words
				
				# if node.name == "a":
					# try:
						# something = node['href']
					# except:
						# print node
						
				if tags_replaced_with_line.has_key(node.name):
					if resultString[-3:] != " | ":
						resultString += '\n'
					
				if tags_important.has_key(node.name):
					resultString = rstrip(resultString)
					resultString = "["+node.name+"]" +resultString + "[/"+node.name+"]"	
					resultString +='\n'

	return resultString

def docuPrettify(old_string):
	result_string=''
	for line in old_string.split('\n'):
		line = line.strip()
		if not line is None and not line == "" and not line ==".":
			line = line.rstrip('.')
			result_string += line +'.\n'
	return result_string
	
#This use a pattern deletion method
#DELETE_AFTER_COPYRIGHT delete the text after "copyright"
#DELETE_BAR_DELI_TEXT delete the text like "abc | bcd | efg | opq"
def patternClean(old_string):
	output_lines = ""
	barlike_lines = ""
	aftercopyright_lines = ""
	
	comeAcrossCopyright = 0
	
	for line in old_string.split('\n'):
		lineLow = line.lower() #Note that we don't want to make the text lower, instead, we just use a lower case copy to test the string
		
		if DELETE_AFTER_COPYRIGHT > 0: 
			if lineLow.find("copyright") != -1:
				comeAcrossCopyright = 1
	
		if DELETE_BAR_DELI_TEXT > 0: 
			parts = line.split('|')
			if len(parts) > DELETE_BAR_DELI_TEXT: #this parameter itself is the threshold value
				for part in parts:
					if len(part) > BAR_TEXT_MAX_LEN:
						output_lines += (" " + part + " ")
						if DEBUG:
							print (" " + part + " "),len(part)
					else:
						barlike_lines += (" " + part + " ") 
				continue
			barlike_lines+='\n'
			output_lines += '\n'
		
		if comeAcrossCopyright == 1: #text after copyright are all deleted IF THE DELETE_AFTER_COPYRIGHT  IS SWITCHED ON
			aftercopyright_lines+=line
			aftercopyright_lines+='\n'
		else:	
			output_lines+=line
			output_lines+='\n'
			
	return [output_lines,barlike_lines,aftercopyright_lines]

def cleanPage(name):
	page_name=dataDir+"/"+name
	if not os.path.isfile(page_name):
		print "The searching file ["+ page_name +"] is not included in the data, or the data directory path is wrong."
	else:
		page = open(page_name,'r+')
		if (os.path.getsize(page_name) ==0):
			return 
		raw_content = page.read()
		
		#Delete any content in <! >, recongnize as bad comments
		splitedContent = re.split("<![^<-]+?>",raw_content)
		page_content = " ".join(splitedContent)
		# page_content = page_content.replace("&nbsp;"," ")
		# page_content = page_content.replace("&nbsp"," ")
			
		try:
			soup = BeautifulSoup(page_content,convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
		except Exception as detail:
			print "Error to soup a file:", detail
			if not os.path.isfile(buggypage_name):
				buggy_page=open(buggypage_name,'w')
			else:
				buggy_page=open(buggypage_name,'a')
			print >>buggy_page, name,", error to soup this page"
		else:#if import successfully, then do strip	
			try:
				soup.prettify()
			except Exception as detail:
				print "Error when prettify: ",detail
				if not os.path.isfile(buggypage_name):
					buggy_page=open(buggypage_name,'w')
				else:
					buggy_page=open(buggypage_name,'a')
				print >> buggy_page, name,", error to prettify this page"
			
			# print soup.originalEncoding
			# print >> open("temp.html",'w'),soup.findAll("html")[0]
			
			if not os.path.exists("cleaned/"):
				os.makedirs("cleaned/")
			stripped_page = codecs.open("cleaned/"+name+".cld",'w',"utf-8") #open file with codecs
			
			# print >>stripped_page,"#!",soup.originalEncoding
			
			#Cleaning log
			if not os.path.exists("log/"):
				os.makedirs("log/")
			cl_log = codecs.open("log/"+name+"_deleted.log",'w',"utf-8")
			missed_tags = open("log/missed_tags.log",'w')
			
			#Clean the sub navigable strings 
			comments = soup.findAll(text=lambda text:isinstance(text, Comment))
			# print [comment for comment in comments]
			[comment.extract() for comment in comments]
			
			cdatas = soup.findAll(text=lambda text:isinstance(text, CData))
			[cdata.extract() for cdata in cdatas]
			
			declarations = soup.findAll(text=lambda text:isinstance(text, Declaration))
			[declaration.extract() for declaration in declarations]
			
			prInstructions = soup.findAll(text=lambda text:isinstance(text, ProcessingInstruction))
			[prInstruction.extract() for prInstruction in prInstructions]
			
			#Extract unused tags
			allTags = soup.findAll(True)
			for tag in allTags:
				try:
					isTagUseful = tag_list[tag.name]
				except KeyError:
					print >> missed_tags, "The tag <"+tag.name+"> does not exist in html list"
					isTagUseful = 0
				if isTagUseful == 0:
					tag.extract()
					
					print>>cl_log, tag.name+" is deleted:"
					print>>cl_log, '[---'
					# print>>cl_log, tag.contents
					
					# print "Doing deletion"
					# abandonedContent = visitSiblings(tag)
					try:
						# print>>cl_log, docuPrettify(abandonedContent)	
						print>>cl_log, tag
						print>>cl_log, '---]'	
					except UnicodeDecodeError:
						pass
						# print UnicodeDecodeError,
						# print "in deleted content"
					# print "Deletion done"
			#print to file
			
			root_tags = soup.contents

				
			# if len(root_tags) != 0:
			for root in root_tags:	
				cleanedContent = visitSiblings(root)
				barlikeContent = ""
				afterCopyrightContent = ""
				
				if DELETE_BAR_DELI_TEXT > 0:
					patternCleanResult = patternClean(cleanedContent)
					cleanedContent = patternCleanResult[0]
					barlikeContent = patternCleanResult[1]
					afterCopyrightContent = patternCleanResult[2]
				try:
					if barlikeContent != "":
						print>>cl_log, "===========Bar like content deleted==========="
						print>>cl_log,barlikeContent
					if afterCopyrightContent != "":
						print>>cl_log, "===========Content after copyright==========="
						print>>cl_log,afterCopyrightContent
					
					print>>stripped_page, docuPrettify(cleanedContent)	
				except UnicodeDecodeError:
					print UnicodeDecodeError,
					print "in reserved content"
			# else:
				# if (os.path.getsize(page_name) !=0):
					# print "HTML tag of the page not found, manually added and clean again!"
					# insertToFile(page,"<html>",0,page_name)
					# m = mmap(page.fileno(), os.path.getsize(page_name))
					# origSize = m.size()
					# insertToFile(page,"</html>",origSize,page_name)
					# cleanPage(name,tail)
				# else:
					# print "File is empty, no need to handle"
			
		page.close()
		
################Function ends, program start####################		
arg = sys.argv



#dataDir = "web_pages/"
# if len(arg) >2 :
	# DEBUG = True
	# print "Cleaning page " + arg[2] + " about " +arg[1]
	# cleanPage(arg[1],arg[2]+".html")
# elif len(arg) == 2:
	# DEBUG = True
	# print "Clean pages of '" + arg[1] +"'"
	# name = arg[1]
	# name = str.rstrip(name)
	# print "Processing ["+name+"]: "
	
	# tail_list= os.listdir(dataDir+name)
	# for tail in tail_list:
		# print tail+" ",
		# cleanPage(name,tail)
if len(arg) < 2:		
	print "Usage: ./html_cleaning.py [experiment dir] [data dir name]"
else:
	experiDir = arg[1]
	dataDir = arg[2]
	os.chdir(experiDir)#go to the experiment dir

	#To load the config from file
	configFile = open("config.txt",'r')

	flag_read_config = 0	
	for line in configFile.readlines():
		line = str.strip(line)
		line = str.rstrip(line)
		
		if flag_read_config == 1 and line != "":
			var = line.split()[0]
			val = line.split()[1]
			if var == "BLOCK_LENGTH_THRESHOLD":
				BLOCK_LENGTH_THRESHOLD= int(val)
				print "BLOCK_LENGTH_THRESHOLD is",BLOCK_LENGTH_THRESHOLD
			elif var == "FILE_PER_NAME":
				FILE_PER_NAME = int(val)
				print "FILE_PER_NAME is",FILE_PER_NAME
			elif var == "DELETE_BAR_DELI_TEXT":
				DELETE_BAR_DELI_TEXT = int(val)
				print "DELETE_BAR_DELI_TEXT is", DELETE_BAR_DELI_TEXT
			elif var == "DELETE_AFTER_COPYRIGHT":
				DELETE_AFTER_COPYRIGHT = int(val)
				print "DELETE_AFTER_COPYRIGHT is",DELETE_AFTER_COPYRIGHT
			elif var == "CONVERT_LI_A_TO_BAR":
				CONVERT_LI_A_TO_BAR = int(val)
				print "CONVERT_LI_A_TO_BAR is",CONVERT_LI_A_TO_BAR
			elif var == "BAR_TEXT_MAX_LEN":
				BAR_TEXT_MAX_LEN = int(val)
				print "BAR_TEXT_MAX_LEN is", BAR_TEXT_MAX_LEN
		
		if line == "--for webpage cleaning": #following line will be the config
			flag_read_config = 1
	
	tags_replaced_with_line={'li':1,'br':1,'tr':1,'h1':1,'h2':1,'h3':1,'h4':1,'h5':1,'h6':1,'div':1,'table':1,'center':1,'p':1}
	# tags_important={'title':1,'h1':1,'h2':1,'h3':1}
	tags_important={} #not a useful feature

	#A tag classification file
	html_tags = open("filters/html_tags_full",'r')

	tag_list={}
	tags_block_level={}

	for line in html_tags.readlines():
		tag_info=line.split()
		if len(tag_info) == 1: 
			tag_list[tag_info[0]] = 0
		if len(tag_info) > 1:
			tag_list[tag_info[0]] = 1
			if tag_info[1]== "block":
				tags_block_level[tag_info[0]] = 1
	
	
	sup.startTimer()
	for name in os.listdir(dataDir):
		cleanPage(name)
	print "Clean pages for", name, "in",sup.printTimer(),"seconds"
		
sys.exit()