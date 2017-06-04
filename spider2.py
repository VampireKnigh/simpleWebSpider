# encoding: utf-8
import urllib2
import re
import bs4 
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf8')



def getHtml(url):
	page = urllib2.urlopen(url)
	html = page.read()
	return html

def getcontents(soup):
	contents = soup.findAll('cc')
	a = 1
	for content in contents:
		print a,'楼：'
		print content.get_text()
		a=a+1




html = getHtml("https://tieba.baidu.com/p/3138733512")
soup = BeautifulSoup(html)
print soup.h3.get_text()
getcontents(soup)
#print soup.prettify()
#print soup.title
#print soup.head
#print soup.find('img', {"class":'BDE_Image'})
#print soup.find(id='post_content_53018668923')





