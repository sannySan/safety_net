#!/usr/bin/env python3

# scrape.py
# Project: Safety Net
# Purpose: to retrieve messages and statistics for posts in feed of a Facebook page given as input.

import datetime
import json
import os
import random
import requests
import time


def request_until_succeed(url):
    success = False
    while success is False:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                success = True
            else:
                print('\n{}: status {} for URL {}, retrying in 5s'.format(datetime.datetime.now(), response.status_code, url) )
                time.sleep(5)
        except Exception as e:
            print('\n{}: error for URL {}: {}, retrying in 5s'.format(datetime.datetime.now(), url, e))
            time.sleep(5)

    return response.text


def getFacebookPageFeedData(page_id, msg_limit, access_token):
    # construct the URL string from template
    url_template = ('https://graph.facebook.com/{}/feed/?fields=message,link,created_time,type,name,id,'
        'likes.limit(1).summary(true),comments.limit(1).summary(true),shares&'
        'limit={}&access_token={}')
    url = url_template.format(page_id, msg_limit, access_token)
    # retrieve data
    data = json.loads(request_until_succeed(url))
    return data


def isAcceptable(text):
    r = requests.post('https://ca-image-analyzer.herokuapp.com/api/analyses',
                      json={'analysis': {'resource': text, 'category': 'text'}})
    return r.json()['results']['value'] == 'Non-Adult'


def isAcceptableSimulate(text):
    if random.random() < 0.6:
        return True
    else:
        return False


class FeedDataAnalyzer(object):
    def __init__(self, acceptability_check):
        self._acc_check = acceptability_check
        self._good_ratio_threshold = 0.5

    def analize(self, feed_data):
        ngood = 0
        print('isOk  shares  likes   message')
        for m in feed_data:
            message = m['message']
            likes = m['likes']['summary']['total_count']
            shares = m['shares']['count']
            is_ok = self._acc_check(message) 
            if is_ok:
                ngood += 1
            print('{:<5} {:>6} {:>6}   {:<}'.format(str(is_ok), shares, likes, message[:60]))
        print('\nNumber of good messages {} of {}, good ratio {:.2f}'.format(ngood, len(feed_data), ngood/len(feed_data)))
        return self._good_ratio_threshold < ngood/len(feed_data)


if __name__ == '__main__':
    try:
        app_id = os.environ['FB_APP_ID']
        app_secret = os.environ['FB_APP_SECRET']
    except KeyError as e:
        print('ERROR: Please define environment variables FB_APP_ID and FB_APP_SECRET.')
        exit(1)

    access_token = app_id + '|' + app_secret
    page_id = 'nytimes'
    random.seed()

    feed_data = getFacebookPageFeedData(page_id, 20, access_token)['data']
    fda = FeedDataAnalyzer(isAcceptableSimulate)
    verdict = fda.analize(feed_data)
    print( 'Verdict for the page:', verdict  )

# [eof]
