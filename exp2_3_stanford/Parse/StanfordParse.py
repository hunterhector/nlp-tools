#!/usr/bin/python 
from subprocess import call
import argparse

def parse(inFile,isList,outDir = ".", propertyFile='default.properties',jarSplit=':'):
	corenlpVersion = "1.3.5"
	corenlpPath = "../lib/stanford-corenlp-full-2013-04-04/"

	corenlpCmd = ["java","-cp",corenlpPath+"stanford-corenlp-"+corenlpVersion+".jar"+jarSplit+corenlpPath+"stanford-corenlp-"+corenlpVersion+"-models.jar"+jarSplit+corenlpPath+"xom.jar"+jarSplit+corenlpPath+"joda-time.jar"+jarSplit+corenlpPath+"jollyday.jar","-Xmx5g","edu.stanford.nlp.pipeline.StanfordCoreNLP"]

	propsAnno = ["-props", propertyFile]

	propsFile = []
	if not isList:
		propsFile = ["-file",inFile]
	else:
		propsFile = ["-filelist",inFileList]

	propsOutput = ["-outputDirectory",outDir]

	corenlpCmd.extend(propsAnno)
	corenlpCmd.extend(propsFile)
	corenlpCmd.extend(propsOutput)

	print "Executing ",corenlpCmd
	call(corenlpCmd)

parser = argparse.ArgumentParser(description='I/O setting for Stanford parser')

parser.add_argument('-f','--inFile',metavar='InputFile' ,help='The path to the document to be processed')

parser.add_argument('-l','--fileList',metavar='fileList', help="File list to be processed by parser")

parser.add_argument('-p','--propFile',metavar='PropertyFile' ,help='The path to the property file')

parser.add_argument('-s','--jarSplit',metavar='JarSplitter' , help = 'The Jar splitter, in *NIX is :, in Windows is ;, default is :')

parser.add_argument('-o','--outPath',metavar ='OutputPath', help = 'The output file path to save the results')



args = vars(parser.parse_args())

props =  args['propFile']
inFile = args['inFile']
inFileList = args['fileList']
outDir = args['outPath']

if props is None:
	props = 'default.properties'
if outDir is None:
	outDir = '.'


if not inFile is None:
	parse(inFile,False,outDir,props)

elif not inFileList is None:
	parse(inFileList,True,outDir,props)
else:
	print 'Either a filelist or a file need to be specified'
