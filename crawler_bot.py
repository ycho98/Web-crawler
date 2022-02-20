# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 16:28:04 2022

@author: Ariel
@author: Clarence
"""

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from outlinks_count import *
from download_page import *
from language_detection import detect_language


def crawler_bot(seeds, max_pages):
    # One session will be active for all requests, as opposed to creating a new one at every iteration
    session = build_session()

    for seed in seeds:
        report_filename = "reports{}.csv".format(seeds.index(seed) + 1)
        clear_report_file(report_filename)

        folder = get_folder_name(seed)

        # all the urls for the current domain (eng, fr, kr)
        urls = [seed]

        # professor wants us to go 500 to 1000 pages deep, with an absolute minimum of 100
        visited_pages = 0

        # iterate through the urls list
        # it constantly increases size (StackOverFlow says not to alter iterables when looping over them)
        index = 0

        while visited_pages < max_pages:
            url = urls[index]
            visited_pages += 1

            soup = make_request(session, url)
            if index == 0:
                detect_language(soup)

            # download current page and save to appropriate folder
            write_to_repository(folder, "page{}.txt".format(visited_pages), soup.prettify())

            # get all the domain links from current page and add seed url to hrefs
            # we also remove duplicates using a set then converting back to list
            outlinks = list(set([link.get('href') for link in soup.findAll('a') if link.get('href') is not None]))

            # Some links are full urls, others are hrefs so append the seed prefix to those
            # To know if some urls are complete or not, we check if they contain https, www or .com
            outlinks = [seed + link for link in outlinks if not any(s in link for s in ["https", "www", ".com"])]

            # remove all links that would lead us outside the current domain
            outlinks = [link for link in outlinks if seed.removeprefix('https://www.') in link]

            # write url and outlinks count to relevant reports.csv
            write_links_count(url, len(outlinks), report_filename)

            # add new links at the end of urls list, as we will eventually scrape them as well
            # only if our list does not have more urls than max_pages
            if len(urls) < max_pages:
                urls.extend(outlinks)

            index += 1

            # If we go through here, the domain might not have any more outlinks and we've visited all pages
            if index >= len(urls):
                break


def make_request(sesh, url):
    # headers are required for certain websites
    source_code = sesh.get(url, headers={'User-Agent': 'test_spider'})
    html_text = source_code.text
    source_code.close()
    soup = BeautifulSoup(html_text, features="html.parser")
    return soup


def build_session():
    session = requests.Session()
    # This helps ease off the servers we are crawling by waiting between subsequent requests
    retry = Retry(connect=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    # This will only request urls with https
    session.mount('https://', adapter)
    return session

