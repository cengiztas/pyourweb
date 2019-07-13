#!/usr/bin/env python

import os
import cgi
import requests
import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# hosting server url including query path
base_url = "query.cgi?q="

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
}

# https://www.w3schools.com/tags/ref_byfunc.asp
basic = ['!doctype', 'html', 'head', 'title', 'body', 'h1', 'h2', 'h3',
         'h4', 'h5', 'h6', 'p', 'br', 'hr']
links = ['a', 'nav']  # link
meta_info = ['meta']  # base
styles_and_semantics = ['div', 'span', 'header', 'footer', 'main', 'section',
                        'article', 'summary']  # aside, details, dialog, data
tables = ['table', 'caption', 'th', 'tr', 'td', 'thead', 'tbody', 'tfoot',
          'col', 'colgroup']
lists = ['ul', 'ol', 'li', 'dl', 'dt', 'dd']
formatting = ['b', 'blockquote', 'code', 'center', 'pre', 'i', 'q', 's', 'strong', 'u']

whitelist = basic + links + meta_info + styles_and_semantics + tables + lists + formatting

# don't remove whitelist tags even if empty
empty_tags = ['meta', 'td']
# keep all attributes for whitelist tags
keep_attributes = ['meta']

form = cgi.FieldStorage()
query = form.getvalue('q')

purl = urlparse(query)

# extend query with scheme, else take care that user input is in lower case
if purl.scheme == '':
    url = "http://" + purl.netloc.lower() + purl.path
else:
    url = purl.scheme + "://" + purl.netloc.lower() + purl.path

def die(lastwill):
    print("Content-type:text/html\r\n\r\n")
    print(lastwill)
    sys.exit(1)

try:
    r = requests.get(url, headers=header)
except requests.exceptions.ConnectionError as e:
    die("Connection error.")

soup = BeautifulSoup(r.text, 'lxml')

for tag in soup.find_all(True):
    #if tag.name == 'td' and tag.attrs == 'colspan':
    #    print("Content-type:text/html\r\n\r\n")
    #    print(tag.attrs)
    #    sys.exit(1)
    if tag.name not in whitelist:
        tag.decompose()
    elif (len(tag.get_text(strip=True)) == 0) and (tag.name not in empty_tags):
        tag.decompose()
    else:
        attrs = dict(tag.attrs)
        for attr in attrs:
            # delete all attributes except href and atrributes from meta tag
            if attr not in ['href', 'colspan'] and (tag.name not in keep_attributes):
                del tag.attrs[attr]

# remove span tags but keep children
for tag in ['span']:
	for match in soup.findAll(tag):
		match.replaceWithChildren()

# extend href with server prefix 
for tag in soup.findAll('a', href=True):
    anchor_url = urljoin(r.url, tag.attrs['href']) 
    tag.attrs['href'] = base_url + anchor_url


tag = soup.find(name='meta', attrs={'name': 'viewport'})
if tag:
    tag.decompose()

# append css link 
css_tag = soup.new_tag('link', href='/css/styles.min.css', rel='stylesheet', type='text/css')
met_tag = soup.new_tag(name='meta', attrs={'content':'width=device-width, initial-scale=1.0', 'name':'viewport'})
soup.head.append(css_tag)
soup.head.append(met_tag)

# now everything is nice and clean
sys.stdout.buffer.write("Content-type:text/html;charset=utf-8\r\n\r\n".encode('utf-8'))
sys.stdout.buffer.write(soup.prettify().encode('utf-8'))

