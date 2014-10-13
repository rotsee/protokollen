#coding=utf-8
import logging

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

		profile = webdriver.FirefoxProfile()
		self.browser = webdriver.Firefox(profile)
		#profile2 = webdriver.FirefoxProfile()
		#profile.set_preference("browser.link.open_newwindow", 1)
		#browser2 = webdriver.Firefox(profile2)

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

	def getHrefList(self,xPath):
		#TODO accept direct hits AND a hits and hits in subelements
		hrefList = []
		elementList = self.findElements(xPath)
		for element in elementList:
			href = element.get_attribute("href")
			if href is not None:
				hrefList.append(href)
		return hrefList

	def kill(self):
		self.browser.close()
		self.vdisplay.stop()


# FIXME 
#					try:
#					    elements = WebDriverWait(browser, 10).until(
#					    	ExpectedConditions.visibilityOfElementLocated(
#					    		By.xpath(pageLoadedCheck)))
#					    print elements
#					except:
#						logging.warning("Page at %s timed out, or first xPath (%s) wasn't found" % (url,pageLoadedCheck))
#						browser.quit()
