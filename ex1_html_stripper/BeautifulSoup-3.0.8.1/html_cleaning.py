#!/usr/bin/python
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulSoup, Comment
from BeautifulSoup import BeautifulSoup, CData
from BeautifulSoup import BeautifulSoup, Declaration
from BeautifulSoup import BeautifulSoup, ProcessingInstruction

from BeautifulSoup import BeautifulStoneSoup
import os
import sys
import codecs
import time
import re
from mmap import mmap

#pre-define parameters
experi_dir="D:/Hector/Documents/fyp/WePS/experiment/"
os.chdir(experi_dir)#go to the experiment dir
#To print non-ascii to terminal
streamWriter = codecs.lookup('utf-8')[-1]
sys.stdout = streamWriter(sys.stdout)
#set recursion limit
sys.setrecursionlimit(3000)

#Globals
BLOCK_LENGTH_THRESHOLD = 10
FILE_PER_NAME = 200
tags_replaced_with_line={'li':1,'br':1,'tr':1,'h1':1,'h2':1,'h3':1,'h4':1,'h5':1,'h6':1,'div':1,'table':1}
# tags_important={'title':1,'body':1,'table':1,'h1':1,'h2':1,'h3':1,'h4':1,'h5':1,'h6':1}

tags_important_file = open("filters/html_tags_important",'r')
tags_important={}

for line in tags_important_file.readlines():
	tags_important[str.rstrip(line)] = 1
	

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
	
#Function that generate the tail of file name		
def addFileNumberTill(max):
	tail_list=[]
	for integer in range(max):
		if integer < 10:
			page_string = "00"+str(integer)
		elif integer <100:
			page_string = "0"+str(integer)
		else:
			page_string = ""+str(integer)		
		page_name=page_string+".html"
		tail_list.append(page_name)
	return tail_list

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
			resultString += stripEndLine(node.string) + ' '
		
	elif not node is None:  #possible exception, may not cover all node types
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
						print "AttributeError when get sonns: ", detail
						return ""
					except Exception as detail:
						print "Other exception: ",detail
				
				if (tags_block_level.has_key(node.name) and not tags_important.has_key(node.name)):
					if countWords(resultString) < BLOCK_LENGTH_THRESHOLD:
						# print "Block ", node.name ," too small: " ,resultString, " word count = ",countWords(resultString)
						resultString = "" #eniminate blocks less than 10 words
				
				if tags_replaced_with_line.has_key(node.name):
					resultString +='\n'
					
				if tags_important.has_key(node.name):
					resultString = stripEndLine(resultString)
					resultString = "["+node.name+"]" +resultString + "[/"+node.name+"]"	
					resultString +='\n'
				
		 
	return resultString

def removeBlankLines(old_string):
	result_string=''
	for line in old_string.split('\n'):
		if line.strip():
			result_string += line +'\n'
	return result_string
	
def cleanPage(name,tail):
	page_name="web_pages/"+name+"/"+tail
	if not os.path.isfile(page_name):
		print "The searching file ["+ page_name +"] is not included in the data, or the data directory path is wrong."
	else:
		page = open(page_name,'r+')
		
		# #Delete any content in <! >, recongnize as bad comments
		# m = re.search("(<!.*?>)",page.read(),re.DOTALL)
		# while not m is None:
			# deleteFromFile(page,m.start(),m.end(),page_name)
			# page.close()
			# page = open(page_name,'r+')
			# m = re.search("(<!.*?>)",page.read(),re.DOTALL)
			# print m.group()
			
		# page = open(page_name,'r+')
			
		try:
			soup = BeautifulSoup(page,convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
		except Exception as detail:
			print "Error to soup a file:", detail
			if not os.path.isfile(buggypage_name):
				buggy_page=open(buggypage_name,'w')
			else:
				buggy_page=open(buggypage_name,'a')
			print >>buggy_page, name+"/"+tail,", error to soup this page"
		else:#if import successfully, then do strip	
			try:
				soup.prettify()
			except Exception as detail:
				print "Error when prettify: ",detail
				if not os.path.isfile(buggypage_name):
					buggy_page=open(buggypage_name,'w')
				else:
					buggy_page=open(buggypage_name,'a')
				print >> buggy_page, name+"/"+tail,", error to prettify this page"
			
			print soup.originalEncoding
			
			if not os.path.exists("cleaned/"+name+"/"):
				os.makedirs("cleaned/"+name+"/")
			stripped_page = codecs.open("cleaned/"+name+"/"+tail+".cld",'w',"utf-8") #open file with codecs
			
			#Cleaning log
			if not os.path.exists("log/"+name+"/"):
				os.makedirs("log/"+name+"/")
			cl_log = codecs.open("log/"+name+"/deleted_log_"+name+"_"+tail+".log",'w',"utf-8")
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
					
					print>>cl_log, tag.name+" is not useful, content listed below is deleted:"
					# print>>cl_log, tag.contents
					
					# print "Doing deletion"
					abandonedContent = visitSiblings(tag)
					try:
						print>>cl_log, removeBlankLines(abandonedContent)	
					except UnicodeDecodeError:
						print UnicodeDecodeError,
						print "in deleted content"
					# print "Deletion done"
			#print to file
			html_tags = soup.findAll("html")
			
			if len(html_tags) != 0:
				for html_tag in html_tags:
					root = html_tag
					cleanedContent = visitSiblings(root)
					try:
						print>>stripped_page, removeBlankLines(cleanedContent)	
					except UnicodeDecodeError:
						print UnicodeDecodeError,
						print "in reserved content"
			else:
				if (os.path.getsize(page_name) !=0):
					print "HTML tag of the page not found, manually added and clean again!"
					insertToFile(page,"<html>",0,page_name)
					m = mmap(page.fileno(), os.path.getsize(page_name))
					origSize = m.size()
					insertToFile(page,"</html>",origSize,page_name)
					cleanPage(name,tail)
				else:
					print "File is empty, no need to handle"
			
		page.close()
################Function ends, program start####################		
arg = sys.argv
if len(arg) >2 :
	print "Cleaning page " + arg[2] + " about " +arg[1]
	cleanPage(arg[1],arg[2]+".html")
elif len(arg) == 2:
	print "Clean pages of '" + arg[1] +"'"
	name = arg[1]
	name = str.rstrip(name)
	print "Processing ["+name+"]: "
	tail_list=addFileNumberTill(FILE_PER_NAME)
	for tail in tail_list:
		print tail+" ",
		cleanPage(name,tail)
else:
	for name in os.listdir("web_pages"):
		name = str.rstrip(name)
		print "Processing ["+name+"]: "
		tail_list=addFileNumberTill(FILE_PER_NAME)
		for tail in tail_list:
			print tail+" ",
			cleanPage(name,tail)
		
sys.exit()