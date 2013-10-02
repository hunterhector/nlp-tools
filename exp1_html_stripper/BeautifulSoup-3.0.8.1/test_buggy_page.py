from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulSoup, Comment
import os
import sys
import urllib2

file_name="bug_pages/186.html"

page = open(file_name,'r')
#page = urllib2.urlopen("http://www.turluhanliyiz.biz/sizden_gelenler/")


soup = BeautifulSoup(page)
	
#soup.prettify()

#soup.findAll(True)
