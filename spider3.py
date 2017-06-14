# encoding: utf-8
import urllib2
import re
import json
import bs4 
from bs4 import BeautifulSoup
import sys
import MySQLdb
import thread 
import time
from multiprocessing.dummy import Pool as ThreadPool
import requests
import time
import socket
socket.setdefaulttimeout(2)
reload(sys)
sys.setdefaultencoding('utf8')


# 封装数据库操作
# save_blog_with_retweetedwb(self,uid,wb,retweeted_status,retweeted_wb):存转载微博
# save_blog_without_retweetedwb(self,uid,wb):存非转载微博
# uid需要设置bigint类型
class XLWB_Spider_DB_IO:
    def __init__(self):
        self.db = MySQLdb.connect("localhost","root","root","data_mining",charset="utf8")
        self.cursor = self.db.cursor()


    def save_blog_with_retweetedwb(self,uid,wb,retweeted_status,retweeted_wb,created_at):
        try:
            sql = "insert into xlwb_spider_data(id,uid,wb,retweeted_status,retweeted_wb,created_at) values(0,'%d','%s','%d','%s','%s')" % (uid,wb,retweeted_status,retweeted_wb,created_at)
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print "save_blog_with_retweetedwb error"
    def save_blog_without_retweetedwb(self,uid,wb,created_at):
        try:
            sql = "insert into xlwb_spider_data(id,uid,wb,retweeted_status,created_at) values(0,'%d','%s',0,'%s')" % (uid,wb,created_at)
            self.cursor.execute(sql)
            self.db.commit()
        except:
            print "save_blog_without_retweetedwb error"
    def check_if_uid_exist(self,uid):
        try:
            sql = "select * from xlwb_spider_data where uid=%d" % (uid)
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
            if(results):
                return True
            else:
                return False
        except:
            print "check_if_uid_exist error"
    def __del__(self):
        self.cursor.close()
        self.db.close()

class BaseSpider:

	def __init__(self):
		#self.setProxy()
		self.ip_pools = []
		#self.getIpPools()
		#print self.ip_pools


	def setHeader(self):
		user_agent = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36"
		headers = {'User-Agent':user_agent}
		return headers

	def setProxy(self,proxy):
		proxy_support = urllib2.ProxyHandler(proxy)
		opener = urllib2.build_opener(proxy_support)
		urllib2.install_opener(opener)

	def getPage(self,url):
		#self.setProxy()
		request = urllib2.Request(url,headers=self.setHeader())
		response = urllib2.urlopen(request)
		return response.read()

	def getIpPools(self):
		#获取ip代理池url
		ip_url = "http://www.xicidaili.com/nn/1"
		baidu_url = "https://www.baidu.com/"
		proxys = []
		request = urllib2.Request(ip_url,headers=self.setHeader())
		res = urllib2.urlopen(request).read()
		soup = BeautifulSoup(res)
		ips = soup.findAll('tr')
		for x in range(1,len(ips)):
			ip = ips[x]
			tds = ip.findAll('td')
			proxy_host = "http://"+str(tds[1].contents[0])+":"+str(tds[2].contents[0])
			proxy_temp = {"http":proxy_host}
			self.setProxy(proxy_temp)
			try:
				req = urllib2.Request(baidu_url,headers=self.setHeader())
				res = urllib2.urlopen(req).read()
				self.ip_pools.append(proxy_temp)
			except Exception,e:
				print e
				continue
		#print ip_pools



        

'''
微博内容url: https://m.weibo.cn/api/container/getIndex?type=uid&value=1713926427&containerid=1076031713926427
转发内容url：https://m.weibo.cn/api/statuses/repostTimeline?id=4070116385690289&page=1
评论内容url: https://m.weibo.cn/api/comments/show?id=4070116385690289&page=1
'''

class spider(BaseSpider):
	def __init__(self,uid):
		self.uid = uid
		url = "https://m.weibo.cn/u/"
		self.user_url = url + str(uid)
		self.blog_url = "https://m.weibo.cn/api/container/getIndex?type=uid&value="+str(uid)+"&containerid=107603"+str(uid)

	def getBlogText(self):
		db_IO = XLWB_Spider_DB_IO()
		for blog_page in range(1,3):
			cur_url = self.blog_url+"&page="+str(blog_page)
			print cur_url
			json_data = self.getPage(cur_url)
			data = json.loads(json_data)
			if int(data.get("ok"))==0:
				print blog_page , "页没有微博，结束该用户的微博爬取"
				break;
			for blog in data.get("cards"):
				if(blog.has_key("mblog")):
					mblog = blog.get("mblog")
					# 获取微博内容，删除表情、超链接等无用信息
					blog_text = re.sub('<br/>|<img.*?>|<a.*?>.*?</a>|<span.*?>.*?</span>', "", mblog.get("text")).encode('utf-8')
					# 获取发微博时间
					created_at = mblog.get("created_at").encode('utf-8')
					#print "text:",blog_text
					#print "created:",created_at
					# 判断是否转载，若转发，获取转发内容
					if(mblog.has_key("retweeted_status")):
						retweeted_status = True
						# 删除转发内容的无用信息
						retweeted_text = re.sub('<br/>|<img.*?>|<a.*?>.*?</a>|<span.*?>.*?</span>',"",mblog.get("retweeted_status").get("text")).encode('utf-8')
						#print "retweeted_status:",retweeted_text
					else:
						retweeted_status = False
						#print "false"
					# 存储到数据库
					if retweeted_status:
						db_IO.save_blog_with_retweetedwb(self.uid,blog_text,1,retweeted_text,created_at)
						print "*****\n%s\n%s\n%s" % (blog_text,created_at,retweeted_text)
					else:
						db_IO.save_blog_without_retweetedwb(self.uid,blog_text,created_at)
						print "*****\n%s\n%s" % (blog_text,created_at)
                    

	def getBlogIdList(self):
		blog_id_list = []
		for blog_page in range(1,6):
			cur_url = self.blog_url + "&page=" + str(blog_page)
			data = self.getPage(cur_url)
			json_data = json.loads(data)
			# 判断该页面是否有内容，没有则结束该用户的微博爬取
			if int(json_data.get("ok")) == 0:
				print "%d页面没有微博，结束该用户的微博爬取" % blog_page
				break;
			for V_blog in json_data.get("cards"):
				V_blog_id = V_blog.get("mblog").get("id")
				print V_blog_id
				blog_id_list.append(V_blog_id)
			print "blog is:",blog_id_list

            
# 爬取评论的粉丝的id的爬虫
# 构造函数传参为微博id
# get_fan_id_list()方法返回20页评论的粉丝id，不重复
class XLWB_blog_comment_spider(BaseSpider):
    def __init__(self,comment_id):
        self.blog_comment_url = "https://m.weibo.cn/api/comments/show?id=" + str(comment_id)
        BaseSpider.__init__(self)
    def getFanIdList(self):
        fan_id_list = []
        for blog_comment_page in range(1,50):
            cur_url = self.blog_comment_url + "&page=" + str(blog_comment_page)
            data = self.getPage(cur_url)
            json_data = json.loads(data)
            if int(json_data.get("ok")) == 0:
                print "%d页面没有微博评论，结束该微博的粉丝id爬取" % blog_comment_page
                break
            for fan_comment in json_data.get("data"):
                fan_id = fan_comment.get("user").get("id")
                if(fan_id not in fan_id_list):
                    print fan_id
                    fan_id_list.append(fan_id)
            if(json_data.has_key("hot_data")):
                for fan_comment in json_data.get("hot_data"):
                    fan_id = fan_comment.get("user").get("id")
                    if (fan_id not in fan_id_list):
                        print fan_id
                        fan_id_list.append(fan_id)
        print fan_id_list
        return fan_id_list






users = [2160328381,2432743515,1713926427]
comments = [4070116385690289]

def getsource(user):
	mySpider = spider(user)
	mySpider.getBlogText()
	mySpider.getBlogIdList

def getComment(comment):
	mySpider = XLWB_blog_comment_spider(comment)
	mySpider.getFanIdList()




time1 = time.time()
for user in users:
	getsource(user)

time2 = time.time()
print '单线程耗时：' + str(time2-time1)

pool = ThreadPool(2)
time3 = time.time()
results = pool.map(getComment, comments)
pool.close()
pool.join()
time4 = time.time()
print '并行耗时：' + str(time4-time3)







