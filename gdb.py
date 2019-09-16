#!/usr/bin/env python
# -*- coding:utf-8 _*-
# @User    : CCF
# @Date    : 2019/9/14 12:49
# Software : PyCharm
# version  : Python 3.7.4
# @File    : gdb.py
import json
import re
import time
import traceback
from pyvirtualdisplay import Display
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from bookspider.settings import USER_AGENT
from lxml import html

start = time.perf_counter()
etree = html.etree
headers = {'User_Agent': USER_AGENT, 'Connection': 'close'}
search_rooturl = "https://book.douban.com/subject_search?search_text=&cat=1001"
result = {
	# 1书名
	"bookname": '',
    # 2封面
	"cover": '',
    # 3图书基本信息
	"bookinfo": '',
    # 4简介
	"fullintro": '',
    # 5目录
	"catalog": '',
    # 6标签
	"tags": '',
    # 7丛书信息
	"seriesintro": '',
    # 8豆瓣评分
	"ratenum": '',
    # 9评分人数
	"ratevoters": '',
	# 10ISBN
	"isbn": '',
	# 11 book_url
	"book_url": ''
}


class GetDetailBook:

	def __init__(self, isbn_code):
		self.isbn_code = isbn_code
		self.dbu = '获取书籍详情url失败'

	def gdbu(self):
		chrome_options = Options()
		chrome_options.add_argument("--ignore-certificate-errors-spki-list")
		chrome_options.add_argument("--ignore-ssl-errors")
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('--disable-gpu')
		chrome_options.add_argument('--user-agent={}'.format(USER_AGENT))
		chrome_options.add_argument("--referer={}".format(search_rooturl))

		driver = webdriver.Chrome(chrome_options=chrome_options)
		# driver.get执行较慢，此处为卡点
		driver.get('https://book.douban.com/subject_search?search_text={}&cat=1001'.format(self.isbn_code))

		try:
			# we have to wait for the page to refresh, the last thing that seems to be updated is the title
			WebDriverWait(driver, 5).until(ec.title_contains(self.isbn_code))
			book_root = driver.find_element_by_css_selector('#root')
			WebDriverWait(driver, book_root)  # 防止页面加载不全
			soup = bs(driver.page_source, 'lxml')
			bookdetailURL = soup.select("a[class='title-text']")[0]['href']
			if bookdetailURL:
				self.dbu = bookdetailURL
				result["book_url"] = bookdetailURL
				# log(bookdetailURL)
			else:
				log("---获取书籍详情页url失败---")
			return bookdetailURL
		except Exception as e:
			print('str(Exception):\t{}'.format(str(Exception)))
			print('str(e):\t\t{}'.format(str(e)))
			print('repr(e):\t{}'.format(repr(e)))
			print('e.message:\t{}'.format(e.args))
			print('traceback.print_exc():{}'.format(traceback.print_exc()))
			print('traceback.format_exc():\n{}'.format(traceback.format_exc()))
		finally:
			driver.quit()

	time.sleep(2)   # 休眠5秒，防止操作过快

	def test(self):
		book_detail_url = self.dbu
		# 取得地址中的数字，抓取目录时生成id属性值
		catalog_id = "dir_{}_full".format("".join(list(filter(str.isdigit, book_detail_url))))
		# log(catalog_id)
		log("---提取书籍详情页url ID完成---")

		response = requests.get(book_detail_url, headers=headers)
		response.encoding = 'utf-8'  # 设置网页编码格式
		source = etree.HTML(response.content)  # 将request.content 转化为 Element
		# log(source)
		log("---提取书籍详情页source完成---")

		time.sleep(1)  # 休眠5秒，防止操作过快
		# 1.获取书名
		book_name = source.xpath("//div[@id='wrapper']/h1/span/text()")[0]
		# log(book_name)
		log("---提取书籍详情页书名完成---")
		# 2.图书封面照片src
		cover_src = source.xpath("//div[@id='mainpic']/a/@href")[0]
		if 'update' in cover_src:
			cover_src = ''
		# log(cover_src)
		log(type(cover_src))
		log("---提取书籍详情页图书封面照片src完成---")
		# 1767945，特立独行的猪
		# 带有“：”的特例：3259440 白夜行
		# 文本中间带有“\n”的特例：27204803 消失的孩子 ，以及白夜行，如[日]东野圭吾这种的，[日]与名字之间有换行
		# html特例的：1362753 超越時空的愛戀，作者信息用两个span套着，“：”单独一行的，对应xpath的第2/3行
		# 26297606，从0到1，有“副标题、原作名、译者、页数、定价”等信息
		# 27608239，原则，俩个译者
		# 3.获取图书基本信息
		bookinfo_dict = {}
		datas = source.xpath("//div[@id='info']//text()")
		datas = [data.strip() for data in datas]
		datas = [data for data in datas if data != ""]
		datas = [re.sub('\s+', '', data) for data in datas]
		# for i, data in enumerate(datas):
		# 	print("index {} : {}".format(i, data))
		for data in datas:
			if u"作者" in data:
				if u":" in data:
					bookinfo_dict["author"] = datas[datas.index(data) + 1]
				elif u":" not in data:
					bookinfo_dict["author"] = datas[datas.index(data) + 2]
			elif u"/" in data:
				if datas.index(data) < 4:
					bookinfo_dict["author"] += "/{}".format(datas[datas.index(data) + 1])
			elif u"出版社:" in data:
				bookinfo_dict["press"] = datas[datas.index(data) + 1]
			elif u"出版年:" in data:
				bookinfo_dict["date"] = datas[datas.index(data) + 1]
			elif u"页数:" in data:
				bookinfo_dict["page"] = datas[datas.index(data) + 1]
			elif u"定价:" in data:
				bookinfo_dict["price"] = datas[datas.index(data) + 1]
			if self.isbn_code:
				bookinfo_dict["ISBN"] = self.isbn_code
		# log(bookinfo_dict)
		log("---提取书籍详情页图书基本信息完成---")
		# 4.获取图书简介（如有）
		full_intro = {}
		# 4.1 内容简介
		try:
			# 无隐藏内容 9787532728893  舞！舞！舞！
			contents_short = source.xpath("//div[@id='link-report']//div[@class='intro']//p//text()")
			# 有隐藏内容 9787532725694 挪威的森林 9787020139927 失踪的孩子
			contents_full = source.xpath("//div[@id='link-report']//span[contains(@class,'hidden')]//div[@class='intro']//p//text()")
			if contents_full:
				full_intro["content_description"] = "\n".join(content for content in contents_full)
			else:
				if contents_short:
					full_intro["content_description"] = "\n".join(content for content in contents_short)
		except:
			full_intro["content_description"] = ""
		# 4.2 作者简介
		try:
			# 无隐藏内容 9787532725694 挪威的森林
			profiles_short = source.xpath("//div[@class='related_info']//*[contains(text(),'作者简介')]/following::div[contains(@class,'intro')]//p//text()")
			# 有隐藏内容 9787020139927 失踪的孩子
			profiles_full = source.xpath("//div[@class='related_info']//*[contains(text(),'作者简介')]/following::*[contains(@class,'hidden')]/div[contains(@class,'intro')]//p//text()")
			if profiles_full:
				full_intro["author_profile"] = "\n".join(profile for profile in profiles_full)
			else:
				if profiles_short:
					full_intro["author_profile"] = "\n".join(profile for profile in profiles_short)
		except:
			full_intro["author_profile"] = ""
		# log(full_intro)
		log("---提取书籍详情页图书相关介绍完成---")
		# 5.获取目录（如有）
		# 9787559413727 我们一无所有
		catalog_info = source.xpath("//div[@id='{}']//text()".format(catalog_id))
		catalog_info = [x.replace('·', '') for x in catalog_info]  # 去除目录最后的省略号，不是点.是·
		catalog_info = [x.strip() for x in catalog_info if x.strip() != '' and x.strip() != '(' and x.strip() != ')']  # 去除目录最后的括号
		if catalog_info:
			catalog_info.remove(catalog_info[-1])
		# log(catalog_info)
		log("---提取书籍详情页图书目录完成---")
		# 6.获取标签
		book_tags = source.xpath("//div[@id='db-tags-section']/div[@class='indent']//span//text()")
		book_tags = [x.strip() for x in book_tags if x.strip() != '']
		# log(book_tags)
		log("---提取书籍详情页图书标签完成---")
		# 7.获取丛书信息（如有）
		series_intro = source.xpath("//div[contains(@class,'subject_show block5')]//div//text()")
		series_intro = [x.strip() for x in series_intro if x.strip() != '']
		series_intro = [re.sub('\s+', '', x) for x in series_intro if x.strip()]
		series_intro = "".join(x for x in series_intro)
		if series_intro:
			series_intro = series_intro
		else:
			series_intro = ''
		# log(series_intro)
		log("---提取书籍详情页图书所属丛书信息完成---")
		# 8.获取豆瓣评分（如有）
		# 1362753 9789867761361 超越時空的愛戀 无评分
		rating_num = source.xpath("//strong[contains(@class,'rating_num')]/text()")
		if rating_num:
			rating_num = rating_num[0].strip()
		else:
			rating_num = ''
		# log(rating_num)
		log("---提取书籍详情页评分完成---")
		# 9.获取评分人数（如有）
		rating_votes = source.xpath("//span[contains(@property,'votes')]/text()")
		if rating_votes:
			rating_votes = rating_votes[0].strip()
		else:
			rating_votes = ''
		# log(rating_votes)
		log("---提取书籍详情页图书评分人数完成---")

		if book_name:
			result["bookname"] = book_name
		if cover_src:
			result["cover"] = cover_src
		if bookinfo_dict:
			result["bookinfo"] = bookinfo_dict
		if full_intro:
			result["fullintro"] = full_intro
		if catalog_info:
			result["catalog"] = catalog_info
		if book_tags:
			result["tags"] = book_tags
		if series_intro:
			result["seriesintro"] = series_intro
		if rating_num:
			result["ratenum"] = rating_num
		if rating_votes:
			result["ratevoters"] = rating_votes
		return result



def log(msg):
	print(u'{}: {}'.format(time.strftime('%Y.%m.%d_%H.%M.%S'), msg))


gdb = GetDetailBook('9789867761361')
log("---获取书籍详情页url开始---")
gdb.gdbu()
log("---获取书籍详情页url结束---")
log("---获取书籍详情页信息开始---")
gdb.test()
log("---获取书籍详情页信息结束---")
js = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
log(js)
end = time.perf_counter()
log("抓取耗时： "+"{:.2f}".format(end - start)+"秒")
