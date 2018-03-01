# -*- coding: utf-8 -*-

"""
otmt.archiveit_collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module acquires data about an Archvie-It collection both from its results
pages and its CSV seed report.

Note: In addition to being used as a library, this file can be run standalone
to download and extract information about an Archive-It collection.

Note: There be dragons here. This code was originally written for a different 
project. I'm sure it can be improved.
"""

import os
import json
import requests
import logging
import logging.config
import argparse
import csv
import sys

from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

collection_uri_prefix = "https://archive-it.org/collections"

class ArchiveItCollectionException(Exception):
    """An exception class to be used by the functions in this file so that the
    source of error can be detected.
    """
    pass

def fetch_collection_web_page(collection_id, pages_dir):
    """Save the first results web page of an Archive-It collection specified by
    `collection_id` in the working directory `pages_dir`.
    """

    collection_uri = "{}/{}".format(collection_uri_prefix, collection_id) 

    logger.debug("fetching page at {}".format(collection_uri))

    # get first page
    r = requests.get(collection_uri)

    logger.debug("writing content to {}".format("{}/1.html".format(pages_dir)))

    with open("{}/1.html".format(pages_dir), 'w') as page:
        page.write(r.text)

    return pages_dir

def fetch_collection_web_pages(collection_id, pages_dir, page_number=1, 
    result_count=None, use_cache=True):
    """Save all results web pages associated with an Archive-It collection
    specified by `collection_id` into the working directory `pages_dir`,
    starting at the page number specified by `page_number`.

    This function handles pagination between results pages so that all
    results pages can be acquired.
    """

    nextpage = get_next_collection_page(
        collection_id, pages_dir, page_number, result_count, use_cache)

    #if nextpage == None:
    #    return
    logger.debug("nextpage is {}".format(nextpage))

    while nextpage:
        logger.debug("nextpage is not None, it is {}".format(nextpage))
        nextpage = get_next_collection_page(
            collection_id, pages_dir, page_number=nextpage, 
            result_count=result_count, use_cache=use_cache)

    logger.info("all collection web pages fetched")

#    fetch_collection_web_pages(collection_id, pages_dir, page_number=nextpage, 
#        result_count=result_count, use_cache=use_cache)

def get_next_collection_page(collection_id, pages_dir, page_number=1, 
    result_count=None, use_cache=True):
    """Parse the Archive-It results page associated with `collection_id`
    to find the URI of the next page. Pages are stored in `pages_dir`
    if not already downloaded.
    """

    logger.debug("result count: [{}]".format(result_count))
    logger.debug("page_number: [{}]".format(page_number))

    if int(page_number) > 1:
        page_uri = "{}/{}/?page={}&totalResultCount={}".format(
            collection_uri_prefix, collection_id, page_number, result_count)
    else:
        page_uri = "{}/{}".format(collection_uri_prefix, collection_id)

    logger.debug("loading page number {} using uri [{}]".format(page_number, page_uri))

    if (not os.path.exists("{}/{}.html".format(pages_dir, page_number))) or use_cache == False:

        logger.debug("downloading data for page {}".format(page_number))

        r = requests.get(page_uri)
        pagedata = r.text

        logger.debug("saving data from page {}".format(page_number))

        with open("{}/{}.html".format(pages_dir, page_number), 'w') as page:
            page.write(pagedata)

    else:

        logger.debug("loading data from page {}".format(page_number))

        with open("{}/{}.html".format(pages_dir, page_number)) as page:
            pagedata = page.read()

    if '<div class="stacktrace">' in pagedata:
        raise ArchiveItCollectionException("Archive-It Page for collection {} "
            "contains stacktrace on page {}, refusing to continue".format(
            page_number, collection_id))

    soup = BeautifulSoup(pagedata, 'html5lib')

    nextpagematch = soup.find_all('a', {'id': 'pageNext'})

    logger.debug("nextpagematch: {}".format(nextpagematch))

    nextpage = None

    if len(nextpagematch) == 2:
        nextpage_uri = nextpagematch[0]['href'] 
        nextpage = nextpage_uri[nextpage_uri.find('page='):][:nextpage_uri.find('&') - 1].replace("page=", "") 

    logger.debug("returning next page of {}".format(nextpage))

    return nextpage

def get_metadata_timestamp(collection_id, pages_dir, use_cache=True):
    """Acquires the file timestamp of when the collection specified by 
    `collection_id` was last downloaded, checking for the file in `pages_dir`.
    If the file does not exist, the collection is downloaded.
    """

    if (not os.path.exists("{}/1.html".format(pages_dir))) or \
        use_cache == False:

        collection_uri = "{}/{}".format(collection_uri_prefix, collection_id) 

        r = requests.get(collection_uri)
        pagedata = r.text

        with open("{}/1.html".format(pages_dir), 'w') as page:
            page.write(pagedata)

    timestamp = os.path.getmtime("{}/1.html".format(pages_dir))

    return timestamp

def get_seed_metadata_timestamp(collection_id, pages_dir, use_cache=True):
    """Acquires the file timestamp of when the seed metadata specified by 
    `collection_id` was last downloaded, checking for the file in `pages_dir`.
    If the file does not exist, the collection is downloaded.
    """

    page_count = get_page_count(collection_id, pages_dir, use_cache=use_cache)

    if page_count:
        if int(page_count) > 1:
            testfile = "{}/2.html".format(pages_dir)
        else:
            testfile = "{}/1.html".format(pages_dir)
    else:
        testfile = "{}/1.html".format(pages_dir)

    timestamp = os.path.getmtime(testfile)

    return timestamp

def get_seed_report_timestamp(collection_id, pages_dir, use_cache=True):
    """Acquries the file timestamp of the CSV seed report accessible outside
    of the collection results page.
    """

    get_seed_metadata_from_seed_report(collection_id, pages_dir, use_cache=True)

    seed_report_filename = "{}/seed_report.xt".format(pages_dir)

    timestamp = os.path.getmtime(seed_report_filename)
   
    return timestamp 

def get_result_count(collection_id, pages_dir, use_cache=True):
    """Scrapes the nubmer of results from the Archive-It collection results
    page.
    """

    result_count = None

    logger.debug("calculating result count for cid {} using pages directory {}".format(
        collection_id, pages_dir
    ))

    if (not os.path.exists("{}/1.html".format(pages_dir))) or \
        use_cache == False:

        collection_uri = "{}/{}".format(collection_uri_prefix, collection_id) 

        r = requests.get(collection_uri)
        pagedata = r.text

        with open("{}/1.html".format(pages_dir), 'w') as page:
            page.write(pagedata)

    else:
        with open("{}/1.html".format(pages_dir), encoding='utf8') as page:
            pagedata = page.read()

    soup = BeautifulSoup(pagedata, 'html5lib')

    try:

        pagestring = soup.find_all("div", "paginator")[0].text

        logger.debug("pagestring: [{}]".format(pagestring))

        result_count = pagestring[pagestring.find('(') + 1:].replace(' Total Results', '').rstrip(')')

        result_count = pagestring[pagestring.find('(') + 1:pagestring.find(' Total Results')]

    except IndexError:
        result_count = None

    logger.debug("result count before comma removal is [{}]".format(result_count))

    if result_count:

        result_count = result_count.replace(',', '')

    logger.debug("result count is [{}]".format(result_count))

    return result_count

def get_page_count(collection_id, pages_dir, use_cache=True):
    """Scrapes the page count from the Archive-It collection results
    page.
    """ 

    logger.debug("getting page count for collection id {}, "
        "saving to directory {}".format(collection_id, pages_dir)
    )

    page_count = None

    if (not os.path.exists("{}/1.html".format(pages_dir))) or \
        use_cache == False:

        collection_uri = "{}/{}".format(collection_uri_prefix, collection_id) 

        r = requests.get(collection_uri)
        pagedata = r.text

        with open("{}/1.html".format(pages_dir), 'w') as page:
            page.write(pagedata)

    else:
        with open("{}/1.html".format(pages_dir), encoding='utf8') as page:
            pagedata = page.read()

    soup = BeautifulSoup(pagedata, 'html5lib')

    try:

        pagestring = soup.find_all("div", "paginator")[0].text

        page_count = pagestring.split("of")[1].strip().split()[0]
    except IndexError:
        page_count = None

    if page_count:
        page_count = page_count.replace(',', '')

    logger.debug("returning page count of [{}]".format(page_count))

    return page_count


def scrape_main_collection_data(soup):
    """Scrapes general collection metadata the Archive-It collection
    results page using the BeautfulSoup object `soup`.
    """

    data = {}

    metadata_tags = soup.find_all("div", "entity-meta")

    try:
        data["name"] = metadata_tags[0].find_all("h1")[0].get_text().strip()
        data["exists"] = True
    except IndexError:

        try:

            if "Not Found" in metadata_tags[0].find_all("h2")[0].get_text().strip():
                data["exists"] = False
                return data
            else:
                raise IndexError("Could not find 'Not Found' string using screen scraping")

        except IndexError as e:
            logger.error("Failed to find collection name using screen scraping")
            logger.error("Failed to determine if collection does not exist using screen scraping")
            logger.error(metadata_tags)
            raise e

    try:
        data["collection_uri"] = metadata_tags[0].find_all("h1")[0].find_all("a")[0]["href"]
    except IndexError as e:
        logger.error("Failed to find collection URI using screen scraping")
        logger.error(metadata_tags)
        raise e

    try:
        data["institution_name"] = \
            metadata_tags[0].find_all("p", "collectedBy")[0].get_text().strip().replace("Collected by:", "").strip()
    except IndexError as e:
        logger.error("Failed to find institution name using screen scraping")
        logger.error(metadata_tags)
        raise e

    try:
        data["institution_uri"] = metadata_tags[0].find_all("p", "collectedBy")[0].find_all("a")[0]['href']
    except IndexError as e:
        logger.error("Failed to find institution URI using screen scraping")
        logger.error(metadata_tags)
        raise e

    try:
        data["description"] = \
            metadata_tags[0].find_all("p", "seamTextPara")[0].get_text().strip().replace('\n', '<br />')
    except IndexError:
        logger.warning("Failed to find description using screen scraping, "
            "setting to No description...")
        data["description"] = "No description."

    search_results = soup.find_all("div", {"id": "all-search-results"})

    try:
        public_stmt = search_results[0].find_all("h2")[0].get_text().strip()

        if "There is no public content available for this Collection yet. Please check back soon!" in public_stmt:
            data["public"] = "private"
        else:
            data["public"] = "public"

    except IndexError:
        data["public"] = "unknown" 

    data["archived_since"] = "unknown"

    subjects = []

    for item in metadata_tags[0].find_all("p"):

        bolds = item.find_all('b')

        if len(bolds) > 0:

            for bold in bolds:

                if "Subject" in bold.get_text():
                    subjects = [i.strip(',').strip() for i in item.text.replace('Subject:', '').replace('\xa0', '').replace('\t', '').strip().split('\n')]

                if "Archived since" in bold.get_text():
                    archived_since = [i.strip(',').strip() for i in item.text.replace('Archived since:', '').replace('\xa0', '').replace('\t', '').strip().split('\n')][0]

    data["subject"] = subjects
    data["archived_since"] = archived_since

    return data

def scrape_optional_collection_data(soup):
    """Scrapes optional collection metadata the Archive-It collection
    results page using the BeautfulSoup object `soup`.
    """

    data = {}

    metadata_tags = soup.find_all("div", "entity-meta")
    moreMetadata = metadata_tags[0].find_all("div", "moreMetadata")

    for item in moreMetadata[0].find_all("p"):
        key = item.find_all("b")[0].text.replace('\xa0', '').strip().strip(':')
        values = [i.strip(',').strip() for i in item.text.replace("{}:".format(key), '').replace('\xa0', '').replace('\t', '').strip().split('\n')]
        key = key.lower()
        data[key] = values

    return data


def get_metadata_from_web_page(pages_dir, data_type):
    """Using the pages downloaded in `pages_dir`, this function returns the
    metadata scraped based on the metadata type specified in `data_type`.
    """

    logger.info("processing collection pages from directory {}".format(pages_dir))

    if os.listdir(pages_dir) == 0:
        raise ArchiveItCollectionException("Pages directory empty, remove {} "
            "and start over".format(pages_dir))

    with open("{}/1.html".format(pages_dir), encoding='utf8') as htmlfile:
        content = htmlfile.read()

    soup = BeautifulSoup(content, 'html5lib')

    if data_type == 'main':
        return scrape_main_collection_data(soup)
    elif data_type == 'optional':
        return scrape_optional_collection_data(soup)
    else:
        raise ArchiveItCollectionException("Cannot scrape collection "
            "metadata type {} in directory {}".format(
            data_type, pages_dir))

def scrape_seed_metadata(soup):
    """Scrapes the seed metadata form an Archive-It results page stored in the
    BeautifulSoup object `soup`.
    """

    data = []

    for item in soup.find_all("div", "result-item"):

        itemdict = {}

        for entry in item.find_all("h3", "url"):
    
            if 'URL:' in entry.text:
                url = entry.text.replace("URL:", "").strip()
                itemdict["uri"] = url

            if 'Title:' in entry.text:
                title = entry.text.replace("Title:", "").strip()
                itemdict["title"] = title

        for entry in item.find_all("p"):
            if len(entry.find_all("b")) > 0:
                key = entry.find_all("b")[0].text.replace('\xa0', '').strip().rstrip(':')
                #value = entry.find_all("a")[0].text.strip()
                values = [i.strip(',').strip() for i in entry.text.replace("{}:".format(key), '').replace('\xa0', '').replace('\t', '').strip().split('\n')]
                itemdict[key.lower()] = values


        data.append(itemdict)

    return data

def get_seed_metadata_from_web_pages(pages_dir):
    """This function iterates through all downloaded pages in `pages_dir`
    and extracts the seed metadata from those pages using
    `scrape_seed_metadata`.
    """

    seed_metadata = [] 

    if os.listdir(pages_dir) == 0:
        raise ArchiveItCollectionException("Pages directory empty, remove {} "
            "and start over".format(pages_dir))

    for filename in os.listdir(pages_dir):

        filename = "{}/{}".format(pages_dir, filename)

        logger.debug("scraping content from {}".format(filename))

        with open(filename, encoding='utf8') as htmlfile:
            content = htmlfile.read()

        soup = BeautifulSoup(content, 'html5lib')

        page_seed_metadata = scrape_seed_metadata(soup)    

#        logger.debug("psm: {}".format(page_seed_metadata))

        seed_metadata.extend(page_seed_metadata)

    return seed_metadata

def get_seed_metadata_from_seed_report(collection_id, pages_dir, use_cache=True):
    """Builds the CSV seed report URI using `collection_id` and saves the
    seed report in `pages_dir`.
    """

    seed_metadata = {}

    seed_report_uri = "https://partner.archive-it.org/api/seed?" \
        "annotate__max=seed_group__name&annotate__max=crawl_definition__recurrence_type" \
        "&collection={}&csv_header=Seed+URL&csv_header=Group&csv_header=Status" \
        "&csv_header=Frequency&csv_header=Type&csv_header=Access&format=csv&" \
        "show_field=url&show_field=seed_group__name&show_field=active&" \
        "show_field=crawl_definition__recurrence_type&show_field=seed_type&" \
        "show_field=publicly_visible&sort=-id".format(collection_id)

    seed_report_filename = "{}/seed_report.xt".format(pages_dir)
   
    if not os.path.exists(seed_report_filename):

        r = requests.get(seed_report_uri)

        with open(seed_report_filename, 'w') as seed_report:
            seed_report.write(r.text)

    with open(seed_report_filename) as seed_report:
    
        csvreader = csv.DictReader(seed_report, delimiter=',')
    
        for row in csvreader:
        
            seed_metadata[ row["Seed URL"] ] = {} 
            seed_metadata[ row["Seed URL"] ]["group"] = row["Group"]
            seed_metadata[ row["Seed URL"] ]["status"] = row["Status"]
            seed_metadata[ row["Seed URL"] ]["frequency"] = row["Frequency"]
            seed_metadata[ row["Seed URL"] ]["type"] = row["Type"]
            seed_metadata[ row["Seed URL"] ]["access"] = row["Access"]

    return seed_metadata 

class ArchiveItCollection:
    """Organizes all information acquired about the Archive-It collection."""

    def __init__(self, collection_id, working_directory='/tmp/archiveit_collection',
        use_cached=True, logger=None):

        self.collection_id = str(collection_id)
        self.working = working_directory
        self.collection_dir = "{}/{}".format(self.working, self.collection_id)
        self.pages_dir = "{}/pages".format(self.collection_dir)
        self.metadata_loaded = False
        self.seed_metadata_loaded = False
        self.metadata = {}
        self.seed_metadata = {}
        self.private = None
        self.exists = None
        self.use_cached=use_cached

        self.logger = logger or logging.getLogger(__name__)

        #self.logger.debug("instantiated class...")

    def load_collection_metadata(self):
        """Loads collection metadata from an existing directory, if possible.
        If the existing directory does not exist, it will then download the
        collection and process its metadata.
        """

        #self.logger.debug("load_collection_metadata called")

        if not self.metadata_loaded:

            self.logger.info("metadata has not yet been loaded for "
                "collection {}".format(self.collection_id))

            if not (self.use_cached and os.path.exists(self.pages_dir)):

                self.logger.debug("use cache: {}".format(self.use_cached))
                self.logger.debug("pages directory: {}".format(self.pages_dir))
                self.logger.debug("pages directory exists: {}".format(os.path.exists(self.pages_dir)))
                self.logger.info("could not find cache, fetching web pages")

                if not os.path.exists(self.pages_dir):
                    os.makedirs(self.pages_dir)

                fetch_collection_web_page(self.collection_id, self.pages_dir)

            self.metadata["main"] = get_metadata_from_web_page(self.pages_dir, 'main')

            if self.metadata["main"]["exists"]:
                self.metadata["optional"] = get_metadata_from_web_page(self.pages_dir, 'optional')

            self.metadata["metadata_timestamp"] = get_metadata_timestamp(
                self.collection_id, self.pages_dir, self.use_cached)

            self.metadata_loaded = True

    def load_seed_metadata(self):
        """Loads the seed metadata previously downloaded if possible, otherwise
        acquires all collection results pages and parses them for seed metadata.

        This function is separate to limit the number of requests. It should only
        be called if seed metadata is needed.
        """

        #self.logger.debug("load_seed_metadata called")

        if not self.seed_metadata_loaded:
           
            self.logger.info("seed metadata has not yet been loaded for "
                "collection {}".format(self.collection_id))
            self.logger.debug("caching: {}".format(self.use_cached))

            page_count = get_page_count(self.collection_id, self.pages_dir, use_cache=self.use_cached)

            self.logger.info("page count from loading is [{}]".format(page_count))

            result_count = get_result_count(self.collection_id, self.pages_dir, self.use_cached)

            self.logger.info("result count from loading is [{}]".format(result_count))

            if result_count:

                self.logger.debug("result count: {}".format(result_count))

                if not (self.use_cached and os.path.exists("{}/{}.html".format(self.pages_dir, page_count))):
    
                    self.logger.info("could not find cache, fetching web pages for seed metadata")
    
                    if not os.path.exists(self.pages_dir):
                        os.makedirs(self.pages_dir)
    
                    fetch_collection_web_pages(self.collection_id, self.pages_dir, 
                        page_number=1, result_count=result_count, use_cache=self.use_cached)
  
                self.logger.info("scraping seed metadata from pages")

                scraped_seed_metadata = get_seed_metadata_from_web_pages(self.pages_dir)
  
                self.logger.info("getting seed metadata from seed report")

                seed_report_metadata = get_seed_metadata_from_seed_report(
                    self.collection_id, self.pages_dir, use_cache=self.use_cached)
  
                self.logger.info("building seed metadata data structure")

                for item in scraped_seed_metadata:
                    uri = item["uri"]
    
                    #self.logger.debug("examining uri {}".format(uri))
    
                    itemdict = {}
    
                    for key in item:
                        if key != "uri":
                            itemdict[key] = item[key]
    
   
                    self.seed_metadata.setdefault("seeds", {})
                    self.seed_metadata["seeds"].setdefault(uri, {})
                    self.seed_metadata["seeds"][uri].setdefault(
                        "collection_web_pages", []).append(itemdict)
    
                for uri in seed_report_metadata:
                    self.seed_metadata.setdefault("seeds", {})
                    self.seed_metadata["seeds"].setdefault(uri, {})
                    self.seed_metadata["seeds"][uri].setdefault("seed_report", {})
                    self.seed_metadata["seeds"][uri]["seed_report"]= seed_report_metadata[uri]

                self.seed_metadata["timestamps"] = {}

                self.seed_metadata["timestamps"]["seed_metadata_timestamp"] = \
                    get_seed_metadata_timestamp(
                        self.collection_id, self.pages_dir, self.use_cached)
    
                self.seed_metadata["timestamps"]["seed_report_timestamp"] = \
                    get_seed_report_timestamp(
                        self.collection_id, self.pages_dir, self.use_cached)

                self.logger.info("done building seed metadata data structure")

            self.seed_metadata_loaded = True


    def get_collection_name(self):
        """Getter for the collection name, as scraped."""

        self.load_collection_metadata()

        name = self.metadata["main"]["name"]

        return name

    def get_collection_uri(self):
        """Getter for the collection URI, as constructed."""

        self.load_collection_metadata()

        uri = "https://archive-it.org{}".format(self.metadata["main"]["collection_uri"])

        return uri

    def get_collectedby_uri(self):
        """Getter for the collecting organization's URI, as constructed."""

        self.load_collection_metadata()

        uri = "https://archive-it.org{}".format(self.metadata["main"]["institution_uri"])

        return uri

    def get_description(self):
        """Getter for the collection description, as scraped."""

        self.load_collection_metadata()

        description = self.metadata["main"]["description"]

        return description

    def get_collectedby(self):
        """Getter for the collecting organization's name, as scraped."""

        self.load_collection_metadata()

        collectedby = self.metadata["main"]["institution_name"]

        return collectedby

    def get_subject(self):
        """Getter for the collection's topics, as scraped."""
        
        self.load_collection_metadata()

        subjects = self.metadata["main"]["subject"]

        return subjects

    def get_archived_since(self):
        """Getter for the collection's archived since field, as scraped."""

        self.load_collection_metadata()

        archived_since = self.metadata["main"]["archived_since"]

        return archived_since

    def get_optional_metadata(self, key):
        """Given optional metadata field `key`, returns value as scraped."""

        self.load_collection_metadata()

        value = self.metadata["optional"][key]

        return value

    def list_optional_metadata_fields(self):
        """Lists the optional metadata fields, as scraped."""

        self.load_collection_metadata()

        keylist = self.metadata["optional"].keys()

        return keylist

    def is_private(self):
        """Returns `True` if the collection is public, otherwise `False`."""

        self.load_collection_metadata()

        if self.metadata["main"]["public"] == "private":
            return True
        elif self.metadata["main"]["public"] == "public":
            return False
        else:
            raise ArchiveItCollectionException("Could not determine private/public status")

    def does_exist(self):
        """Returns `True` if the collection actually exists and requests for
        its data did not result in 404s or soft-404s."""

        self.load_collection_metadata()

        exists = self.metadata["main"]["exists"]

        #self.logger.debug("exists is set to {}".format(exists))

        return exists

    def list_seed_uris(self):
        """Lists the seed URIs of an Archive-It collection."""

        self.load_collection_metadata()
        self.load_seed_metadata()

        return list(self.seed_metadata["seeds"].keys())

    def get_seed_metadata(self, uri):
        """Returns a `dict` of seed metadata associated with the memento 
        at `uri`."""

        d = self.seed_metadata["seeds"][uri] 

        return d

    def return_collection_metadata_dict(self):
        """Returns a `dict` of collection metadata."""

        self.load_collection_metadata()

        metadata = {
            "id": self.collection_id
        }    

        metadata["exists"] = self.does_exist()
        metadata["metadata_timestamp"] = \
            datetime.fromtimestamp(
                self.metadata["metadata_timestamp"]
            ).strftime("%Y-%m-%d %H:%M:%S")

        if metadata["exists"]:

            metadata["name"] = self.get_collection_name()
            metadata["uri"] = self.get_collection_uri()
            metadata["collected_by"] = self.get_collectedby()
            metadata["collected_by_uri"] = self.get_collectedby_uri()
            metadata["description"] = self.get_description()
            metadata["subject"] = self.get_subject()
            metadata["archived_since"] = self.get_archived_since()
            metadata["private"] = self.is_private()
            metadata["optional"] = {}

            for key in self.list_optional_metadata_fields():
                metadata["optional"][key] = self.get_optional_metadata(key)

        return metadata

    def return_seed_metadata_dict(self):
        """Returns all seed metadata of all mementos as a `dict`."""

        self.load_seed_metadata()

        metadata = {
            "id": self.collection_id
        }

        metadata["seed_metadata"] = self.seed_metadata

        if len(metadata["seed_metadata"]) > 0:

            metadata["seed_metadata"]["timestamps"]["seed_metadata_timestamp"] = \
                datetime.fromtimestamp(
                    self.seed_metadata["timestamps"]["seed_metadata_timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")
    
            metadata["seed_metadata"]["timestamps"]["seed_report_timestamp"] = \
                datetime.fromtimestamp(
                    self.seed_metadata["timestamps"]["seed_report_timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")

        return metadata


    def return_all_metadata_dict(self):
        """Returns all metadata of the collection as a `dict`."""

        self.load_collection_metadata()
        self.load_seed_metadata()

        collection_metadata = self.return_collection_metadata_dict()
        
        collection_metadata["seed_metadata"] = self.seed_metadata

        if len(collection_metadata["seed_metadata"]) > 0:

            collection_metadata["seed_metadata"]["timestamps"]["seed_metadata_timestamp"] = \
                datetime.fromtimestamp(
                    self.seed_metadata["timestamps"]["seed_metadata_timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")
    
            collection_metadata["seed_metadata"]["timestamps"]["seed_report_timestamp"] = \
                datetime.fromtimestamp(
                    self.seed_metadata["timestamps"]["seed_report_timestamp"]
                ).strftime("%Y-%m-%d %H:%M:%S")

        return collection_metadata
        
    def save_all_metadata_to_file(self, filename):
        """Saves all metadata to `filename` in JSON format."""

        collection_metadata = self.return_all_metadata_dict()

        with open(filename, 'w') as metadata_file:
            json.dump(collection_metadata, metadata_file, indent=4)

if __name__ == "__main__":

    if os.path.exists('logging.ini'):
        logging.config.fileConfig('logging.ini')

    # logger = logging.getLogger(__name__) 

    logger.info("beginning execution...")

    parser = argparse.ArgumentParser(sys.argv)
    parser = argparse.ArgumentParser(description="Download all public content "
        "about an Archive-It Collection")

    requiredArguments = parser.add_argument_group("required arguments")

    parser.add_argument("collection",
        help="the number of the Archive-It collection for which to collect data"
        )

    parser.add_argument("output",
        help="the output file in which to store the collection data"
        )

    parser.add_argument("--overwrite", dest="overwrite", default=False,
        help="do not use cached data in working directory, overwrite it")


    parser.add_argument("--working", dest="working_directory",
        help="the directory containing the cached data stored while "
        "working with the collection, default is /tmp/archiveit_data",
        default="/tmp/archiveit_data")
    
    args = parser.parse_args()

    logger.info("overwrite: {}".format(args.overwrite))

    aic = ArchiveItCollection( args.collection, 
        working_directory=args.working_directory, 
        use_cached=(not args.overwrite),
        logger=logger )

    logger.info("saving output to {}".format(args.output))
    aic.save_all_metadata_to_file(args.output)

    logger.info("finished execution for collection {}".format(
        args.collection))
