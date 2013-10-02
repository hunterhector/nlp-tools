#!/usr/bin/python 
import sys
import os
import xml.etree.ElementTree as et 

args = sys.argv

if len(args) < 2:
	print "Usage: StanfordXml2PlainText.py [stanford result folder] [plain text output folder]"

inputDir = args[1]
outputDir = args[2]

for resultFile in os.listdir(inputDir):
	print "processing",resultFile
	r = open(inputDir+"/"+resultFile)
	root = et.fromstring(r.read())

	if not os.path.exists(outputDir):
		os.makedirs(outputDir)

	out = open(outputDir + "/"+ resultFile+".txt",'w')

	for document in root:
		for sentences in document:
			for sent in sentences:
				for tokens in sent:
					for token in tokens:
						for tokenAtt in token:
							if tokenAtt.tag == 'word':
								print >> out,tokenAtt.text, 
							if tokenAtt.tag == 'POS':
								print >> out,tokenAtt.text,
				print >> out, '\n'
