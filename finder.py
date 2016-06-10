#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import sys
import urlparse
from multiprocessing import Process, Queue, current_process

import httplib2
import requests
from BeautifulSoup import BeautifulSoup, SoupStrainer

checked = []
broken = []
base_url = None


def append_line_to_file(*text):
    with open('statuses.txt', 'a') as outfile:
        outfile.write(str(text) + '\n')


def check(url):
    print 'checking URL ' + url
    session = requests.Session()
    response = session.get(url)

    soups = BeautifulSoup(response.content, parseOnlyThese=SoupStrainer('a'))
    for a_tag in soups:

        try:
            href = str(a_tag['href'])
            if href.startswith(r'/'):
                href = base_url + href

            if href not in checked and href not in broken:
                append_line_to_file('looking at ' + href)
                if href.startswith(r'http') or href.startswith(r'https') or href.startswith(r'//'):

                    try:
                        res = session.get(href)
                        if res.status_code == 200:
                            checked.append(href)
                            append_line_to_file(href, 'worked')
                            base_parts = urlparse.urlparse(base_url)
                            link_parts = urlparse.urlparse(href)
                            internal = base_parts.scheme == link_parts.scheme and base_parts.netloc == link_parts.netloc
                            if internal:
                                print 'found a link within the same host. Checking it out at: ' + str(
                                    href)
                                check(href)

                        else:
                            append_line_to_file('BROKEN:', href, res.status_code)
                            broken.append(href)
                    except httplib2.RedirectLimit:
                        broken.append(href)
                        append_line_to_file('skipping', href, 'too many redirects')
                    except requests.exceptions.ConnectionError:
                        broken.append(href)
                        append_line_to_file('skipping', href, 'too many retries')
                    except UnicodeEncodeError:
                        append_line_to_file("couldn't parse the url")

        except KeyError:
            print 'skipping', a_tag, 'no href'
            pass


def worker(work_queue, done_queue):
    try:
        while not work_queue.empty():
            url = work_queue.get()
            for status, done_url in iter(done_queue):
                if done_url != url:
                    found = True
                    break
            if found:
                continue
            status_code = check(url)
            done_queue.put("%s - %s got %s." % (current_process().name, url, status_code))
    except Exception, e:
        done_queue.put("%s failed on %s with: %s" % (current_process().name, url, e.message))
    return True


def main(base_url):
    workers = 2
    work_queue = Queue()
    done_queue = Queue()
    processes = []

    work_queue.put(base_url)

    for w in xrange(workers):
        p = Process(target=worker, args=(work_queue, done_queue))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    while not done_queue.empty():
        status, url = done_queue.get()
        print status, url

    check(base_url)
    print 'found ' + str(len(checked)) + ' working links'
    print 'found ' + str(len(broken)) + ' broken links'


if __name__ == '__main__':
    base_url = sys.argv[1]
    main(base_url)
