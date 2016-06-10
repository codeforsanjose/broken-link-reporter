#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import sys


import httplib2
import requests
import urlparse
from BeautifulSoup import BeautifulSoup, SoupStrainer

checked = []
broken = []
base_url = None

def check(url):
    print 'checking URL '+url
    session = requests.Session()
    response = session.get(url)

    soups = BeautifulSoup(response.content, parseOnlyThese=SoupStrainer('a'))
    for a_tag in soups:
        
        try:
            href = str(a_tag['href'])
            if href.startswith(r'/'):
                href = base_url + href

            if href not in checked and href not in broken:
                print 'looking at '+href
                if href.startswith(r'http') or href.startswith(r'https') or href.startswith(r'//'):
                    
                    try:
                        res = session.get(href)
                        if res.status_code == 200:
                            checked.append(href)
                            print href, 'worked'
                            base_parts = urlparse.urlparse(base_url)
                            link_parts = urlparse.urlparse(href)
                            internal = base_parts.scheme == link_parts.scheme and base_parts.netloc == link_parts.netloc
                            if internal:
                                print 'found a link within the same host. Checking it out at: '+str(href)
                                check(href)

                        else:
                            print 'BROKEN:', href, res.status_code
                            broken.append(href)
                    except httplib2.RedirectLimit:
                        broken.append(href)
                        print 'skipping', href, 'too many redirects'
                    except requests.exceptions.ConnectionError:
                        broken.append(href)
                        print 'skipping', href, 'too many retries'
                    except UnicodeEncodeError:
                        print "couldn't parse the url"
                    

        except KeyError:
            print 'skipping', a_tag, 'no href'
            pass


if __name__ == '__main__':
    base_url = sys.argv[1]
    check(base_url)
    print 'found '+str(len(checked))+' working links'
    print 'found '+str(len(broken))+' broken links'
