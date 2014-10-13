#coding=utf-8
import logging
import urlparse

class Surfer:
	"""This class does virtual web surfing on our demand
	"""
	def __init__(self,delay=2):
		self.extraDelay = delay #extra time to wait after each operation (s)
		from selenium import webdriver
		from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
		from selenium.webdriver.common.by import By
		from selenium.webdriver.support import expected_conditions as ExpectedConditions
		from xvfbwrapper import Xvfb

		self.vdisplay = Xvfb()
		self.vdisplay.start()

		self.profile = webdriver.FirefoxProfile()
		self.browser = webdriver.Firefox(self.profile)

	def surfTo(self,url):
		self.browser.get(url)
		self.browser.implicitly_wait(self.extraDelay)

	def clickOnStuff(self,xPath):
		elementList = self.browser.find_elements_by_xpath(xPath)
		if not elementList:
			logging.warning("No elements found for xPath `%s`" % xPath)
		else:
			for element in elementList:
				element.click()
			self.browser.implicitly_wait(self.extraDelay)

	def findElements(self,xPath):
		return self.browser.find_elements_by_xpath(xPath)

	def getUrlList(self,xPath):
		urlList = []
		elementList = self.findElements(xPath)
		for element in elementList:
			href = element.get_attribute("href")
			if href is not None:
				urlList.append(Url(href))
		return urlList#list of Url objects

	def kill(self):
		self.browser.close()
		self.vdisplay.stop()

class Url:
	"""Represents a url, from e.g. Surfer.getHrefList()
	"""
	def __init__(self,url):
		self.href = url

	def is_absolute(self):
		"""Check if url is absolute or relative"""
		return bool(urlparse.urlparse(self.url).netloc)

	def makeAbsolute(self):
		parse_object = urlparse(self.href)
		urlBase = parse_object.scheme + "://" + parse_object.netloc
		self.href = urlBase + self.href
# FIXME 
#					try:
#					    elements = WebDriverWait(browser, 10).until(
#					    	ExpectedConditions.visibilityOfElementLocated(
#					    		By.xpath(pageLoadedCheck)))
#					    print elements
#					except:
#						logging.warning("Page at %s timed out, or first xPath (%s) wasn't found" % (url,pageLoadedCheck))
#						browser.quit()
