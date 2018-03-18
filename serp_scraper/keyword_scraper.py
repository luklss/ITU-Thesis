""" A simple commandline interface for scraping images

    You pass a folder where the images will be saved on, 
    multiple keywords and multiple search engines. This little guy does the
    rest.
"""
import os
import urllib.request
import imagehash
import serpscrap
from PIL import Image
from bs4 import BeautifulSoup
import json
import pprint
from selenium import webdriver
import time
from io import BytesIO
import requests
from selenium.webdriver.common.keys import Keys
from protestDB.cursor import ProtestCursor


class Scraper:


	def __init__(self, keywords, folder, n_images, timeout, includedb, label, tpe):
		self.includedb = includedb
		self.type = tpe
		self.label = label
		self.keywords = keywords
		self.timeout = timeout
		self.n_images = n_images
		self.folder = folder
		self.bing_limit = 210
		self.bing_images_per_page = 35
		self.pc = ProtestCursor()
		self.google_base_url = "https://www.google.co.in/search?q="
		self.google_end_url = "&source=lnms&tbm=isch"
		self.bing_base_url = "http://www.bing.com/images/search?q=" 
		self.bing_end_url = "&FORM=HDRSC2"
		self.bing_header ={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
		self.google_header = {"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"}
		createFolder(self.folder) 
	

	def scrape(self, searchEng):
		"""
		Main method for scraping. Just defines the logic for which method to use according
		to the search engine choosen
		"""
		if (searchEng == 'google'):
			print('\n')
			for keyword in self.keywords:
				self.scrapeGoogle(keyword)
			print('-' * 80)
			print('\n')
		elif(searchEng == 'bing'):
			print('\n')
			for keyword in self.keywords:
				self.scrapeBing(keyword)
			print('-' * 80)
			print('\n')
		else:
			print("no handlers for " + str(searchEng))

	def scrapeBing(self,keyword):
		"""
		Scrapes bing. Uses the parameters "first" and "count" to go forward in the search pages, using the fact
		that bing exposes 35 images at a time.
		"""
		print("scraping keyword: " + keyword + " on bing")
		print('\n')
		query= keyword.split()
		tags = query
		query='+'.join(query)
		current_image = 1
		current_page = 1
		while (True):	
			first = current_page * self.bing_images_per_page - 34
			query_url = self.bing_base_url + query + self.bing_end_url + "&first=" + str(first) + "&count=" + str(self.bing_images_per_page)
			soup = get_soup(query_url,self.bing_header)
			for a in soup.find_all("a",{"class":"iusc"}):
				m = json.loads(a["m"])
				url = m["murl"]
				print("(image " + str(current_image) + " out of " + str(self.n_images) + ")" + "downloading url: " + url)
				self.saveImageFromUrl(url, self.folder, self.timeout, "bing", current_image, tags)
				if((current_image >= self.n_images) or current_image > self.bing_limit):
					print('-' * 80)
					print('\n')
					return
				current_image += 1
				time.sleep(0.1) 
			current_page += 1
			time.sleep(0.3) 

	def scrapeGoogle(self, keyword):
		"""
		Scrapes google images using a webdriver that simulates a browser. Here we have to scroll down to the end of the page
		regardless of how many images we will scrape. From the fully open page we can get the urls and then download the images
		"""
		print("scraping keyword: " + keyword + " on google")
		print('\n')
		query= keyword.split()
		tags=query
		query='+'.join(query)
		query_url = self.google_base_url + query + self.google_end_url
		driver = webdriver.Chrome()
		driver.get(query_url)

		img_count = 1
		element = driver.find_element_by_tag_name("body")
		# Scroll down
		for i in range(30):
		    element.send_keys(Keys.PAGE_DOWN)
		    time.sleep(0.3)  # bot id protection

		driver.find_element_by_id("smb").click()

		for i in range(50):
		    element.send_keys(Keys.PAGE_DOWN)
		    time.sleep(0.3)  # bot id protection

		time.sleep(0.2)

		imges = driver.find_elements_by_xpath('//div[contains(@class,"rg_meta")]')
		for img in imges:
			url = json.loads(img.get_attribute('innerHTML'))["ou"]
			print("(image " + str(img_count) + " out of " + str(self.n_images) + ")" + "downloading url: " + url)
			self.saveImageFromUrl(url, self.folder, self.timeout, "google", img_count, tags)
			img_count += 1

			if (img_count > self.n_images):
				break
		driver.quit()


	def saveImageFromUrl(self, url, folder, timeout, source, pos, tags = None):
		"""
		Given an image, tries to download it saving it in the givel folder. The name of the file is the 
		image dhash plus the extension detected by PIL
		Params:
			folder: the folder name
		"""

		try:
			r = requests.get(url, timeout = timeout)
			img = Image.open(BytesIO(r.content))
			#imgpath, headers = urllib.request.urlretrieve(url)
			#img = Image.open(imgpath)
			imgHash = str(imagehash.dhash(img))
			filename = imgHash + '.' + img.format
			path = os.path.join(folder, filename)
			img.save(path)
			if(self.includedb):
				self.pc.insertImage(
		   			path_and_name = path,
		   			source        = source,
		   			origin        = self.type,
		   			url           = url,
		   			tags          = tags,
		   			label         = self.label,
		   			position 	  = pos,
				)
		except Exception as e:
			print(e)
			print("somenthing went wrong scraping the image url")

def createFolder(folder_path):
	"""
	Creates a folder if it does not exist given a path
	"""
	if (not os.path.exists(folder_path)):
		os.mkdir(folder_path)

def get_soup(url,header):
	return BeautifulSoup(urllib.request.urlopen(
	    urllib.request.Request(url,headers=header)),
	'html.parser')


