#!/usr/bin/env python

# Ragai - (c) Eric Dodémont, 2024.

"""
Functions to scrape the text and the metadata of web pages
"""

import requests, bs4
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
from typing import Any
import streamlit as st
import requests, json
from bs4 import BeautifulSoup

from config.config import *


def scrape_web_page(url: str, filter: str) -> dict[str, Any]:
    """
    Name: swp
    Scrape the text and the metadata of a web page
    Input: url of the page, css class to filter
    Output: dictionary with: url: url, metadata: metadata, text: text
    """

    # Get the page content
    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=(filter)
            )
        ),
    )
    text = loader.load()
    # Covert Document type into string type
    text = text[0].page_content

    # Get the metadata (open graph from Facebook, og:xxx)
    # Get the HTML code
    response = requests.get(url)
    # Transform the HTML code from a Response object type into a BeautifulSoup object type to be scraped by Beautiful Soup
    soup = BeautifulSoup(response.text, "html.parser")
    # Get the metadata fields
    metadata = {}
    # Find all the meta tags in the HTML
    meta_tags = soup.find_all("meta")
    # Loop through the meta tags
    for tag in meta_tags:
        property = tag.get("property")
        content = tag.get("content")
        # Add the property-content pair to the dictionary
        if property and content:
            metadata[property] = content

    # Build JSON string with: url: url, metadata: metadata, text: summary text
    # Create a dictionary
    page = {
        "url": url,  # String
        "metadata": metadata,  # Dictionary
        "text": text  # String
    }

    return page  # Dictionary


def scrape_commons_category(category: str) -> None:
    """
    For Wikimedia Commons: Scrape the URLs from a Category and save the results in a JSON file
    """
    
    FILE_PATH = "./files/json_files/commons-category-"

    FILTER1 = "fileinfotpl-type-information vevent mw-content-ltr"  # Summary: Information template (table class)
    FILTER2 = "fileinfotpl-type-artwork vevent mw-content-ltr"      # Summary: Artwork template (table class)
    #FILTER = "mw-content-ltr mw-parser-output"  # Old (Summary + Licensing)
    #FILTER = "hproduct commons-file-information-table"

    category = category.replace(" ","_")

    items = []
    href_old = ""

    # Step 1: Load the HTML content from a webpage
    url = f"https://commons.wikimedia.org/wiki/Category:{category}"
    response = requests.get(url)
    html_content = response.text

    # Step 2: Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Step 3: Find all URLs in  tags
    urls = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            if href.startswith("/wiki/File:") and href != href_old: # This test because all links are in double!
                urls.append(f"https://commons.wikimedia.org{href}")
                href_old = href

    number_of_pages = len(urls)
    st.write(f"Number of pages to scrape: {number_of_pages}")

    i = 1
    items = []
    for url in urls:
        st.write(f"Scraping {i}/{number_of_pages}...")
        url = url.replace("\ufeff", "")  # Remove BOM (Byte order mark at the start of a text stream)
        item = scrape_web_page(url, (FILTER1, FILTER2))
        print(item)
        items.append(item)
        i = i + 1

    category = category.replace("/","-")
    category = category.replace(" ","-")
    category = category.replace("?","-")
    category = category.replace(":","-")
    category = category.replace(".","-")
    category = category.replace("=","-")

    # Save the Python list in a JSON file
    # json.dump is designed to take the Python objects, not the already-JSONified string. Read docs.python.org/3/library/json.html.
    with open(f"{FILE_PATH}{category}-swp.json", "w") as json_file:
        json.dump(items, json_file) # That step replaces the accentuated characters (ex: é) by its utf8 codes (ex: \u00e9)
    json_file.close()


def scrape_web_page_url(url: str, filter: str) -> None:
    """
    Scrape one URL and save the result in a JSON file
    """

    url = url.replace("\ufeff", "")  # Remove BOM (Byte order mark at the start of a text stream)
    item = scrape_web_page(url, filter)
    print(item)
    items = []
    items.append(item)   # Add in a list, even if only one item/page

    url2 = url.replace("https://","")
    url2 = url2.replace("http://","")
    url2 = url2.replace("/","-")
    url2 = url2.replace(" ","-")
    url2 = url2.replace("?","-")
    url2 = url2.replace(":","-")
    url2 = url2.replace(".","-")
    url2 = url2.replace("=","-")

    # Save the Python list in a JSON file
    # json.dump is designed to take the Python objects, not the already-JSONified string. Read docs.python.org/3/library/json.html.
    with open(f"./files/json_files/{url2}-swp.json", "w") as json_file:
        json.dump(items, json_file) # That step replaces the accentuated characters (ex: é) by its utf8 codes (ex: \u00e9)
    json_file.close()
