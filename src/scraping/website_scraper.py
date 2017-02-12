import pandas as pd
import numpy as np
import random
import time
import project
import founder
import requests
from bs4 import BeautifulSoup
from project import get_project, get_rewards
from founder import get_profile, get_bio
from pymongo import MongoClient
import urllib2

import multiprocessing
import sys
import threading
from timeit import Timer


# Initialize MongoDB database and collection
client = MongoClient()
db = client['ksdb']
collection = db['ksdata']

# Load array of project_id,founder_id, project_url, founder_url, rewards_url
ls = pd.read_csv('id_url_list.csv', dtype=object, header=None)
id_url_list = ls.values


def featurize(project_id, founder_id, project_url, founder_url, rewards_url, project_soup, founder_soup, rewards_soup, collection):
    '''
    Parses html for features and inserts them into MongoDB.
    '''

    features = {'founder_id': int(founder_id),
                'project_id': int(project_id),
                'project_url': project_url,
                'founder_url': founder_url,
                'pledges': project.get_pledges(rewards_soup),
                'pledge_backer_count' : project.get_pledges_backed(rewards_soup),
                'main_video': project.has_project_video(project_soup),
                'image_count': project.count_images(project_soup),
                'emb_video_count': project.count_emb_videos(project_soup),
                'founder_backed': founder.get_backed(founder_soup),
                'founder_created': founder.get_created(founder_soup),
                'founder_comments': founder.get_commented(founder_soup),
                'tag': project.get_tag(project_soup),
                'description': project.get_full_desc(project_soup)}

    collection.insert(features)


def pool_extract(id_url_list):
    '''
    INPUT: list of project ids, founder ids, project url, founder url and project rewards url.
    OUTPUT: None
    Scrapes Kickstarter website based on the provided list of ids and urls.
    '''
    failed = 0
    skipped = 0
    progress = 0

    project_id,founder_id, project_url, founder_url, rewards_url = id_url_list

    collection_check = set(db.ksdata.distinct('project_id', {}))
    if int(project_id) in collection_check:
            print "Already scraped"
            skipped += 1
    else:
        try:
            project_soup, project_url, status1 = get_project(project_url)

            founder_soup, founder_url, status2 = get_profile(founder_url)

            rewards_soup, rewards_url, status3 = get_rewards(rewards_url)

            if (status1 & status2 & status3) == 200:
                featurize(project_id, founder_id, project_url, founder_url, rewards_url, project_soup, founder_soup, rewards_soup, collection)

                progress += 1
                wait = True

        except requests.ConnectionError:
            failed +=1

    print '\n'
    print 'Scraped: {}'.format(progress)
    print 'Skipped: {}'.format(skipped)
    print 'Failed: {}'.format(failed)
