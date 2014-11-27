#coding=utf-8
from selenium.webdriver import Firefox, Chrome, FirefoxProfile
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.events import EventFiringWebDriver,\
                                            AbstractEventListener
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.common.exceptions import InvalidSelectorException, ElementNotVisibleException
from xvfbwrapper import Xvfb
from time import sleep
import urlparse
from shutil import rmtree
from os import listdir
from os import sep as os_sep
#from os.path import getctime
from tempfile import mkdtemp


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
        self.temp_dir = mkdtemp()

        self.vdisplay = Xvfb()
        self.vdisplay.start()
        if browser == "firefox":
            profile = FirefoxProfile()
            # Open links in same window
            profile.set_preference("browser.link.open_newwindow", 1)
            # Download to temp dir, for files we can't open inline
            profile.set_preference("browser.download.dir", self.temp_dir)
            profile.set_preference("browser.download.folderList", 2)
            profile.set_preference("browser.download.manager.showWhenStarting", "False")
            profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/msword, application/vnd.ms-word, application/rtf, application/octet-stream")

            # Add extension for overriding Content-Disposition headers, etc
            extensions_dir = os_sep.join(['bin', 'firefox-plugins-enabled'])
            for filename in listdir(extensions_dir):
                fullfilename = os_sep.join([extensions_dir, filename])
                profile.add_extension(extension=fullfilename)

            driver = Firefox(profile)
        elif browser == "chrome":
            # Add extension for overriding Content-Disposition headers
            options = ChromeOptions()
            options.add_extension('bin/undisposition.crx')
            driver = Chrome(executable_path='bin/chromedriver', chrome_options=options)
        else:
            raise Exception("Not a valid browser name")
        self.selenium_driver = EventFiringWebDriver(driver, CustomListener())
        """selenium_driver is a EventFiringWebDriver, so that it can
           trigger javascript event
        """
        self.browser_version = \
            self.selenium_driver.capabilities['browserName'] \
            + " " \
            + self.selenium_driver.capabilities['version']
        """Browser name and version, e.g. 'Firefox 33.0' """

    def get_last_download(self):
        files = sorted([
            f for f in listdir(self.temp_dir)])
        if len(files) > 0:
            return self.temp_dir + os_sep + files[-1]
        else:
            return None

    def _get_nearest_ancestor(self, element, tagname):
        ancestor = element.find_element_by_xpath("..")
        while ancestor is not None and ancestor.tag_name != tagname:
            try:
                ancestor = element.find_element_by_xpath("..")
            except InvalidSelectorException:
                ancestor = None
        return ancestor

    def with_open_in_new_window(self, element, callback_, *args, **kwargs):
        """Shift-clicks on an element to open a new window,
           calls the callback function, and then closes the
           window and returns.
           This is useful for iterating through a link tree
           we cannot easily step back in (e.g. where the starting
           the result of a POST request)

           Callback function is called like this: `callback(Surfer, arguments)`
           with a Surfer object placed in the new window

           Returns the result of `callback`
        """
        try:
            element.send_keys(Keys.SHIFT + Keys.ENTER)
        except ElementNotVisibleException:
            raise
        self.selenium_driver.implicitly_wait(self.extra_delay)
        #FIXME implicitly_wait doesnät work on FF?
        sleep(self.extra_delay)
        windows = self.selenium_driver.window_handles
        self.selenium_driver.switch_to_window(windows[-1])
        res = callback_(self, *args, **kwargs)
        if len(windows) > 1:
            self.selenium_driver.close()
        windows = self.selenium_driver.window_handles
        self.selenium_driver.switch_to_window(windows[-1])
        return res

    def surf_to(self, url):
        """Simply go to an URL"""
        self.selenium_driver.get(url)
        self.selenium_driver.implicitly_wait(self.extra_delay)

    def click_on_stuff(self, xPath):
        """Will click on any elements pointed out by xPath.

           Options in select menus will be selected, and an
           onChange event fired (as this does not always happen automatically):
           http://stackoverflow.com/questions/2544336/selenium-onchange-not-working

           Currently assumes there is an id on the select element.
        """
        element_list = self.selenium_driver.find_elements_by_xpath(xPath)
        if not element_list:
            raise("No elements found for xPath `%s`" % xPath)
        else:
            for element in element_list:
                try:
                    element.click()
                except ElementNotVisibleException:
                    # Element not visible. This is not necessarily an error.
                    # but the user might want to consider using a more
                    # specific xPath expression.
                    continue
#                actions = ActionChains(self.selenium_driver)
#                actions.move_to_element(element)
#                actions.click(element)
#                actions.send_keys_to_element(element, Keys.ENTER)
#                actions.perform()
                if "tag_name" in dir(element) and element.tag_name == "option":
                    parent = self._get_nearest_ancestor(element, "select")
                    if parent is not None:
                        # Should be selected already, when clicking,
                        # but it seems like this does not always happen
                        value = element.get_attribute("value") or None
                        if value is not None:
                            select = Select(parent)
                            select.select_by_value(value)
                        # Manually trigger JS events
                        select_id = parent.get_attribute("id") or None
                        if select_id is not None:
                            js_function = """
    window.triggerChange=function(){\
        var el = document.getElementById('""" + select_id + """');\
        el.dispatchEvent(new Event('change', { 'bubbles': true }));\
        el.dispatchEvent(new Event('select', { 'bubbles': true }));\
        el.dispatchEvent(new Event('click', { 'bubbles': true }));\
    };"""
                            self.selenium_driver.execute_script(js_function)
                            self.selenium_driver.execute_script("triggerChange();")
                    else:
                        raise Exception("No <select> parent found for <option>")
            self.selenium_driver.implicitly_wait(self.extra_delay)

    def get_url_list(self, xPath):
        url_list = []
        element_list = self.selenium_driver.find_elements_by_xpath(xPath)
        for element in element_list:
            href = element.get_attribute("href")
            if href is not None:
                url_list.append(Url(href))
        return url_list  # list of Url objects

    def get_element_list(self, xPath):
        try:
            return self.selenium_driver.find_elements_by_xpath(xPath)
        except InvalidSelectorException:
            pass
        # maybe our xPath points at an attribute?
        try:
            return self.selenium_driver.find_elements_by_xpath(xPath + "/..")
        except InvalidSelectorException:
            pass
        return None

    def kill(self):
        self.selenium_driver.close()
        self.vdisplay.stop()
        rmtree(self.temp_dir)


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
