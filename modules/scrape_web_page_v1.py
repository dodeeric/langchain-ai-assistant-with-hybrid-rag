#!/usr/bin/env python

"""
One function to scrape the text and the metadata of a web page
"""

import requests, bs4
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader

def scrape_web_page(url, filter):
    """
    Name: swp
    Scrape the text and the metadata of a web page
    Input: URL of the page
    Output: list of dictionaries with: url: url, metadata: metadata, text: text
    """

    #filter = "two-third last"  # balat / irpa
    #filter = "media-body"  # belgica / kbr
    #filter = "hproduct commons-file-information-table"  # commons / wikimedia: summary or description section
    #filter = "card metadata-box-card mb-3"  # europeana / kul, irpa, etc.

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
