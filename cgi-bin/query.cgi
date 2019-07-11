#!/usr/bin/env python

import os
import cgi
import requests
import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# query path
query_path = "query.cgi?q="

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
formatting = ['b', 'blockquote', 'code', 'center']

whitelist = basic + links + meta_info + styles_and_semantics + tables + lists + formatting

# don't remove whitelist tags even if empty
empty_tags = ['meta', 'td']
# keep all attributes for whitelist tags
keep_attributes = ['meta']

form = cgi.FieldStorage()
query = form.getvalue('q')#.lower()

rex = re.search('^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$', query)

if not rex:
    print("Content-type:text/html\r\n\r\n")
    print("<h1>Not valid</h1>\r\n\r\n" + query)
    sys.exit(1)
purl = urlparse(query)

# extend query with scheme, else take care that user input is in lower case
if purl.scheme == '':
    url = "http://" + purl.netloc.lower() + purl.path
else:
    url = purl.scheme + "://" + purl.netloc.lower() + purl.path
    

try:
    r = requests.get(url, headers=header)
except requests.exceptions.RequestException as e:
    print("Content-type:text/html\r\n\r\n")
    print("<h1>Not found</h1>\r\n\r\n" + url)

# exit if page not found
if r.status_code != 200:
    print("Content-type:text/html\r\n\r\n")
    print(str(r.status_code) + "\r\n")
    print(url)
    sys.exit(1)

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

# extend href with server prefix 
for tag in soup.findAll('a', href=True):
    anchor_url = urljoin(r.url, tag.attrs['href']) 
    tag.attrs['href'] = query_path + anchor_url

# append css link 
css_tag = soup.new_tag('link', href='/css/styles.min.css', rel='stylesheet', type='text/css')
soup.head.append(css_tag)

# now everything is nice and clean
sys.stdout.buffer.write("Content-type:text/html;charset=utf-8\r\n\r\n".encode('utf-8'))
sys.stdout.buffer.write(soup.prettify().encode('utf-8'))

