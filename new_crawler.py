import os
import sys
import urllib3
from bs4 import BeautifulSoup
import queuelib
import threading
from threading import Thread
from time import sleep
import bs4
import logging
import requests
import time
import gc
import mysql.connector
import configparser
from config import DatabaseConfig
from config import FilesConfig
import os.path
import csv
from config import CSVColumnConfig
from config import UnwatedUrlsConfig
from config import PoliteConfig
import re
import json
import socket
from tldextract import tldextract
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from new_db import *

# import newdb.sorting_ip
# import gensim
# from gensim.models import KeyedVectors
# from w2vec import *
# from Database import *

w2v_model_300 = KeyedVectors.load_word2vec_format("model300.bin", binary=True)

queue = []
visited = []
sub_urls = {}
sno = sno()
if sno is not None:
    j = int(sno[0])
else:
    j = 0
f = open(FilesConfig.sub_urls, "a")
csv_filename = FilesConfig.csv_file_name + "Urls.csv"
with open(csv_filename, "a") as Url_csvFile:
    column_names = CSVColumnConfig.url_column_names
    csv_writer = csv.DictWriter(Url_csvFile, fieldnames=column_names)


def crawling(url):  # crawling plain text, and sub urls
    if len(queue) > 0:
        queue.pop(0)
    global i, j
    with open(csv_filename, "a") as Url_csvFile:
        csv_writer = csv.DictWriter(Url_csvFile, fieldnames=column_names)
        row_dict = {}
        row_dict["URLs"] = url
        try:
            req = requests.get(url)
            visited.append(url)
            soup = bs4.BeautifulSoup(req.text, "html.parser")
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text() #plain text crawled
            hash_x = hash(text) # hash value of the text crawled
            row_dict["H1"] = hash_x
            row_dict["Flag"] = 1
            j = j + 1
            row_dict["SNO"] = j
            row_dict["PID"] = j
            IP = IP_add(url)
            row_dict["IP_Address"] = IP
            csv_writer.writerow(row_dict)
            fn = open(FilesConfig.text_storing + str(j) + ".txt", "w")
            fn.write(url + "\n")
            fn.write(text)
            f1 = open(FilesConfig.hash_value + str(j) + ".txt", "w")
            f1.write("%d" % hash_x)
            f1.close()
            w2v_sim(url, text)
            n = 0
            for link in soup.find_all("a"):
                sub_link = link.get(
                    "href"
                )  # sub_link is the one by one sub links from link
                if sub_link is not None and "https" in sub_link:
                    for x in UnwatedUrlsConfig.web_sites:
                        x = UnwatedUrlsConfig.web_sites.encode("ascii")
                        web_sites = json.loads(x)
                        res = any(ele in sub_link for ele in web_sites)
                        if res is True:
                            pass
                        else:
                            if sub_link not in visited:
                                # appending data into visited list
                                visited.append(sub_link)
                                j = j + 1
                                row_dict["URLs"] = sub_link
                                row_dict["SNO"] = j
                                row_dict["Flag"] = 0
                                row_dict["H1"] = ""
                                n = n + 1
                                IP = IP_add(sub_link)
                                row_dict["IP_Address"] = IP
                                f.write(str(n) + " ) " + sub_link + "-" + IP + "\n")
                                print(row_dict)
                                csv_writer.writerow(row_dict) # Writing sub-urls data to CSV
        except Exception as e:
            print(e)
            pass
    gc.collect()
    time.sleep(5)
    crawled_list = sorting_ip() # getting the urls from DB
    for url in crawled_list:
        if url not in queue:
            queue.append(url)
        thread_initializer(queue) # initialising threads for the urls got from the DB


# def get_url(url):
#     polite_flag = PoliteConfig.POLITE_FLAG
#     polite = PoliteConfig().is_polite(url)
#     if polite_flag is False:  # Force crawling of URL if needed.
#         polite = True
#     if polite is True:
#         crawling(url)
#     else:
#         pass


def IP_add(l):  # extraction of IP address
    ext = tldextract.extract(l)
    URL = ext.subdomain + "." + ext.domain + "." + ext.suffix
    ip = socket.gethostbyname(URL)
    return ip


def thread_initializer(queue):
    thrs = []
    for u1 in queue:
        if u1 is not None:
            # initialising of threads
            thr = Thread(target=crawling, args=(u1,))
            thr.start()
            thrs.append((u1, thr))
    # for thr in thrs:
    #     upd(thr[0])
    #     thr[1].join()


if __name__ == "__main__":

    result = seed_url()
    if (
        result is not None
    ):  # if there are URL's in DB, add those to the queue and start thread.
        seed_url = result[6]
        print(seed_url)
        queue.append(seed_url)
        thread_initializer(queue)
    else:
        with open("wiki_urls.txt", "r") as seed_url_file:
            content = seed_url_file.read()
            content = content.split("\n")
            for url in content:
                seed_url = url
                queue.append(seed_url)  # Adding seed-url into queue
                print(queue)
                thread_initializer(queue)
