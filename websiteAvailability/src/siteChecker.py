#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Detect HTTP URL health status
#   @see Might be used as a module (from producer.py) or as a standalone utility:
#           ./siteChecker.py <URL> [regexp]
#           ./siteChecker.py https://www.google.com
#           ./siteChecker.py https://www.google.com '<title>'
#
import re
import sys
import time
import requests
from bs4 import BeautifulSoup


# siteChecker - get site reliability with simple http GET
# @param url (string) The URL to check
# @return ()
class siteChecker:
    # @param *arg [void] Object might be initialized empty and use self->Check() later on
    # @param *arg (URL, [RegExp Content]). Just like calling Object->Check(URL, RegExpContent)
    def __init__(self, *arg):
        self._constructor()
        if (len(arg) <= 0):
            return
        if isinstance(arg[0], str):
            self.Check(arg[0])
    def _constructor(self):             # 2nd stage constructor
        self._url = None
        self._status = 0
        self._content = None
        self._datetime = None
        self._hasContent = False        # True/False when needed content is found inside the page
        self._responseTime = None
        self._headers = {
            'User-Agent': 'MyOwnCrawler v1.0'
        }
        self._precision = 3             # ms decimal precision

    @property
    def url(self):                      # Requested url
        return self._url
    @property
    def datetime(self):                 # date/time request start
        return self._datetime
    @property
    def status(self):                   # http status result code
        return self._status
    @property
    def content(self):                  # http page content (might be useful for other purposes)
        return self._content
    @property
    def responseTime(self):             # Time to get the page (ms.3)
        return self._responseTime
    @property                           # Bool. True/False if SomeContent is needed/found
    def contentAvailable(self):
        return self._hasContent

    # Check - Get a website URL and return information through this object properties (see above)
    # @param URL         (String) Absolute URL to check [GET]
    # @param SomeContent (String) possible content to look at inside the page
    # @return see object properties above
    def Check(self, URL=None, SomeContent=None):
        if (URL == None): return
        try:
            self._url = URL
            self._datetime = round(time.time(), self._precision)
            response = requests.get(self._url, headers=self._headers)
            self._responseTime = round(time.time() - self._datetime, self._precision)
            self._content = response.content
            if isinstance(SomeContent, str):
                soup = BeautifulSoup(self._content, "html.parser")
                self._hasContent = False if len(soup.find_all(text=re.compile(SomeContent)))==0 else True
            self._status = response.status_code
        except:
            self._constructor()

# When running as utility  "./$0 <URL> [regexp]"
if __name__ == "__main__":
    Arguments = sys.argv[1:]
    URL     = Arguments[0] if len(Arguments)>0 else None
    Content = Arguments[1] if len(Arguments)>1 else None
    website = siteChecker()
    website.Check(URL, Content)
    # website.Check("http://www.google.com")
    # website.Check("http://www.google.com", "body*")
    # website.Check("http://www.googleaaaaaaa.com")
# print(website.url, website.status, website.datetime, website.responseTime, website.contentAvailable)
