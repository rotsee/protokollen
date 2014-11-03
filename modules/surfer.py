#coding=utf-8
import logging

from selenium.webdriver import Firefox, Chrome
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener
import selenium as selenium2
from xvfbwrapper import Xvfb
import urlparse


class CustomListener(AbstractEventListener):
    """This class is needed by EventFiringWebDriver.
    """
    pass


class Surfer:
    """This class does virtual web surfing on our demand
    """

    def __init__(self, delay=1, browser="firefox"):
        """delay: Number of extra seconds to wait when a page is
           supposedly loaded. Try raising this in case of weird errors.

           browser: `firefox` or `chrome`. The ChromeDriver executable for your
           OS must be inside the bin directory for Chrome to work. Get it from:
           http://chromedriver.storage.googleapis.com/index.html
        """
        self.extra_delay = delay  # extra time to wait after each operation (s)

        self.vdisplay = Xvfb()
        self.vdisplay.start()
        if browser == "firefox":
            driver = Firefox()
        elif browser == "chrome":
            driver = Chrome(executable_path='bin/chromedriver')
        else:
            raise Exception("Not a valid browser name")
        self.selenium_driver = EventFiringWebDriver(driver, CustomListener())
        """selenium_driver is a EventFiringWebDriver, so that it can
           trigger javascript event
        """

    def surf_to(self, url):
        """Simply go to an URL"""
        self.selenium_driver.get(url)
        self.selenium_driver.implicitly_wait(self.extra_delay)

    def click_on_stuff(self, xPath):
        """Will click on any elemts pointed out by xPath.

           Options in select menus will be selected, and an
           onChange event fired (as this does not always happen automatically):
           http://stackoverflow.com/questions/2544336/selenium-onchange-not-working

           Currently assumes there is an id on the select element.
        """
        elementList = self.selenium_driver.find_elements_by_xpath(xPath)
        if not elementList:
            logging.warning("No elements found for xPath `%s`" % xPath)
        else:
            for element in elementList:
                if element.tag_name == "option":
                    value = element.get_attribute("value")
                    parent = element.find_element_by_xpath("..")
                    if parent.tag_name == "optgroup":
                        parent = parent.find_element_by_xpath("..")
                    if parent.tag_name == "select":
                        element.click()
                        select = Select(parent)
                        select.select_by_value(value)
                        # Manually trigger some JS events
                        select_id = parent.get_attribute("id") or None
                        if select_id is not None:
                            js_function = "window.triggerChange=function(){\
                                                var el = document.getElementById(\'" + select_id + "\');\
                                                el.dispatchEvent(new Event('change', { 'bubbles': true }));\
                                                el.dispatchEvent(new Event('select', { 'bubbles': true }));\
                                                el.dispatchEvent(new Event('click', { 'bubbles': true }));\
                                           }"
                            self.selenium_driver.execute_script(js_function)
                            self.selenium_driver.execute_script("triggerChange();")
#                            self.selenium_driver.fire_event(self.selenium_driver,("id", select_id), "change")
                    else:
                        raise Exception("No <select> parent found for <option>")
                else:
                    element.click()
            self.selenium_driver.implicitly_wait(self.extra_delay)

    def get_url_list(self, xPath):
        urlList = []
        elementList = self.selenium_driver.find_elements_by_xpath(xPath)
        for element in elementList:
            href = element.get_attribute("href")
            if href is not None:
                urlList.append(Url(href))
        return urlList  # list of Url objects

    def kill(self):
        self.selenium_driver.close()
        self.vdisplay.stop()


class Url:
    """Represents a url, from e.g. Surfer.get_url_list()
    """
    def __init__(self, url):
        self.href = url

    def is_absolute(self):
        """Check if url is absolute or relative"""
        return bool(urlparse.urlparse(self.href).netloc)

    def make_absolute(self, reference_url):
        """Makes this Url absolute, by using the domain from reference_url.

           Does not handle protocol relative URLs
        """
        parse_object = urlparse(reference_url)
        url_base = parse_object.scheme + "://" + parse_object.netloc
        self.href = url_base + self.href

if __name__ == "__main__":
    print "This module is only intended to be called from other scripts."
    import sys
    sys.exit()
