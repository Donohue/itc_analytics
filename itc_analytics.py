#!/usr/bin/python
#
# itc_analytics.py
#
# iTunes Connect Analytics Tool
# Copyright 2014-2015 Brian Donohue
#
# Version 1.0
#
# Latest version and additional information available at:
#   http://appdailysales.googlecode.com/
#
# This script will automate TestFlight invites for Apple's TestFlight integration.
#
# This script is heavily based off of appdailysales.py (https://github.com/kirbyt/appdailysales)
# Original Maintainer
#   Kirby Turner
#
# Original Contributors:
#   Leon Ho
#   Rogue Amoeba Software, LLC
#   Keith Simmons
#   Andrew de los Reyes
#   Maarten Billemont
#   Daniel Dickison
#   Mike Kasprzak
#   Shintaro TAKEMURA
#   aaarrrggh (Paul)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import json
import urllib
import urllib2
import cookielib
import re
import sys
import os
import traceback
import dateutil.parser
from collections import defaultdict
from getpass import getpass

class ITCException(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value);

# There is an issue with Python 2.5 where it assumes the 'version'
# cookie value is always interger.  However, itunesconnect.apple.com
# returns this value as a string, i.e., "1" instead of 1.  Because
# of this we need a workaround that "fixes" the version field.
#
# More information at: http://bugs.python.org/issue3924
class MyCookieJar(cookielib.CookieJar):
    def _cookie_from_cookie_tuple(self, tup, request):
        name, value, standard, rest = tup
        version = standard.get('version', None)
        if version is not None:
            version = version.replace('"', '')
            standard["version"] = version
        return cookielib.CookieJar._cookie_from_cookie_tuple(self, tup, request)

class ITCAnalytics:
    urlITCBase = 'https://itunesconnect.apple.com%s'
    urlAnalyticsBase = 'https://analytics.itunes.apple.com/analytics/api/v1/data/%s'

    def __init__(self, itcLogin, itcPassword, appId, proxy=''):
        self.itcLogin = itcLogin
        self.itcPassword = itcPassword
        self.appId = str(appId)
        self.proxy = proxy
        self.opener = self.createOpener()

    def readHtml(self, url, data=None, content_type=None):
        request = urllib2.Request(url, data, {'Content-Type': content_type}) if content_type else urllib2.Request(url, data)
        urlHandle = self.opener.open(request)
        html = urlHandle.read()
        return html

    def createOpener(self):
        handlers = []                                                       # proxy support
        if self.proxy:                                                      # proxy support
            handlers.append(urllib2.ProxyHandler({"https": self.proxy}))    # proxy support

        cj = MyCookieJar();
        cj.set_policy(cookielib.DefaultCookiePolicy(rfc2965=True))
        cjhdr = urllib2.HTTPCookieProcessor(cj)
        handlers.append(cjhdr)                                              # proxy support
        return urllib2.build_opener(*handlers)                              # proxy support

    def login(self):
        # Go to the iTunes Connect website and retrieve the
        # form action for logging into the site.
        urlWebsite = self.urlITCBase % '/WebObjects/iTunesConnect.woa'
        html = self.readHtml(urlWebsite)
        match = re.search('" action="(.*)"', html)
        urlActionLogin = self.urlITCBase % match.group(1)

        # Login to iTunes Connect web site
        webFormLoginData = urllib.urlencode({'theAccountName':self.itcLogin, 'theAccountPW':self.itcPassword, '1.Continue':'0'})
        html = self.readHtml(urlActionLogin, webFormLoginData)
        if (html.find('Your Apple ID or password was entered incorrectly.') != -1):
            raise ITCException, 'User or password incorrect.'
    
    def api_call(self, url, data=None):
        self.login()
        response = self.readHtml(url, data=json.dumps(data), content_type='application/json')
        return json.loads(response)
    
    def measures(self):
        data = {
            'adamId': [self.appId],
            'frequency': 'MONTH',
            'measures': ['pageViewCount', 'units', 'iap', 'sales', 'activeDevices', 'sessions'],
            'startTime': None,
            'endTime': '2015-04-01T00:00:00Z'
        }
        response = self.api_call(self.urlAnalyticsBase % 'app/detail/measures', data=data)
        return response['results']

    def print_measures(self):
        measures = self.measures()
        day_dict = defaultdict(list)
        print 'date,%s' % (','.join(measure['measure'] for measure in measures))
        for measure in measures:
            line = measure['data'][0]['date']
            for datum in measure['data']:
                day_dict[datum['date']].append(str(datum['value']))
        for key in sorted(day_dict.iterkeys()):
            date = dateutil.parser.parse(key)
            print '%s,%s' % (date.strftime('%Y-%m-%d'), ','.join(day_dict[key]))

    def all_time(self):
        data = {
            'adamId': [self.appId],
            'measures': ['pageViewCount', 'units', 'sales', 'sessions']
        }
        response = self.api_call(self.urlAnalyticsBase % 'app/detail/all-time', data=data)
        return response['data']

    def print_all_time(self):
        all_time = self.all_time()
        print ','.join(all_time.keys())
        print ','.join([str(x) for x in all_time.values()])

    def retention(self):
        data = {
            'adamId': [self.appId],
            'frequency': 'DAY',
            'endTime': '2015-04-29T00:00:00Z',
            'dimensionFilters': []
        }
        return self.api_call(self.urlAnalyticsBase % 'retention', data=data)['results']

    def print_retention(self):
        for result in self.retention():
            purchase_date = dateutil.parser.parse(result['appPurchase'])
            retention_line = '%s,%d' % (purchase_date.strftime('%Y-%m-%d'), result['data'][0]['value'])
            for datum in result['data'][1:]:
                retention_line += ',%0.2f' % (datum['retentionPercentage'])
            print retention_line

def usage():
    print 'Usage: %s [measures|all-time|retention] <iTC login email> <App ID>'

def main():
    if len(sys.argv) < 4:
        usage()
        return -1 

    method = sys.argv[1]
    itcLogin = sys.argv[2]

    try:
        appId = int(sys.argv[3])
    except Exception as e:
        print 'Invalid App ID'
        usage()
        sys.exit(-1)

    try:
        itcPassword = getpass('iTunes Connect Password: ')
        assert len(itcPassword)
    except:
        print '\nFailed to get iTunes Connect password. Aborting...'
        usage()
        return -1

    analytics = ITCAnalytics(itcLogin, itcPassword, appId)
    methods = {
        'measures': analytics.print_measures,
        'all-time': analytics.print_all_time,
        'retention': analytics.print_retention
    }

    if not method in methods:
        print 'Invalid method: %s' % method
        usage()
        return -1

    try:
        methods[method]()
    except Exception as e:
        print 'Invite Failed: %s' % str(e)
        traceback.print_exc()
        return -2

if __name__ == '__main__':
    sys.exit(main())

