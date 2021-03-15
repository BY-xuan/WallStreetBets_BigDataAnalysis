# -*- coding: utf-8 -*-
"""ProjectWallStreetBets.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/108ofFsEzbswK2E1tzkPfr6UU6jPHRTx-
"""

!pip install pyspark
!pip install praw

from pyspark.rdd import RDD
from pyspark.sql import Row
from pyspark.sql import DataFrame
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from pyspark.sql.functions import desc
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark import SparkContext as sc
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
# tools
import math
import json
import requests
import itertools
import numpy as np
import time
from datetime import datetime, timedelta

def init_spark():
    spark = SparkSession \
        .builder \
        .appName("Python Spark SQL basic example") \
        .config("spark.some.config.option", "some-value") \
        .getOrCreate()
    return spark
spark = init_spark()

"""
Function to make an HTTP request to the Pushshift API.
- max_retry: Nb of times the request is re-tried if failure occurs.
- returns: Python object with the content of the request. (index 'data' property)
"""
def get_request(uri, max_retry = 5):
  def get(uri):
    response = requests.get(uri)
    assert response.status_code == 200
    return json.loads(response.content)
  # Retry if request call failed
  retry = 1
  while retry < max_retry:
    try:
      response = get(uri)
      return response
    except:
      print(f"[{retry}] Request failed, re-trying...")
      # wait 1 second before retry
      time.sleep(1)
      retry += 1

# Testing get_request() with test uri. Should return a non-empty Python object.
obj = get_request("https://httpbin.org/get")
print(obj['url'])
# Returning posts from wallstreetbets. The posts are in the "data" property of the response.
# Use this to check format: https://jsonformatter.curiousconcept.com/#
# obj2 = get_request('https://api.pushshift.io/reddit/search/submission?subreddit=wallstreetbets')
# print(obj2)

"""
Gets the all the posts from a given subreddit in the specific time range.
- subreddit: name of subreddit
- begin: timestamp (in unix) of start date
- end: timestamp (in unix) of end date
- returns: list of all the posts in the time interval. the posts are objects with properties "id", "title" and "creation_utc".
"""
def get_posts(subreddit, begin, end):
  # Max size of Pushshift API retrieve is 500 posts.
  SIZE = 100
  PUSHSHIFT_URI = r'https://api.pushshift.io/reddit/search/submission?subreddit={}&after={}&before={}&size={}'
  nb_requests_made = 1

  # Get the ids and creation time of the posts only. Can use later to get the actual posts with PRAW with these ids.
  # Alternatively, we could also directly use get_request() instead of this function, and get all the posts with their content.
  def filter_ids_time(uri, begin, end):
    full_posts = get_request(uri.format(subreddit, begin, end, SIZE))
    # Test prints
    #if nb_requests_made != 1:
    #  print(f"Retrieved full_posts {nb_requests_made} times", len(full_posts['data']))
    if full_posts is None:
      raise ValueError("Response is empty or none.")

    filtered = map(lambda post: {
        'id': post['id'],
        'title': post['title'],
        'created_utc': post['created_utc']
    }, full_posts['data'])
    return list(filtered)

  posts = filter_ids_time(PUSHSHIFT_URI, begin, end)
  posts_amount = len(posts)
  # If reached limit of 500 posts retrieved, make request again until 'end' time.
  while posts_amount == SIZE:
    # Timestamp of the last post we previously retrieved
    new_begin = posts[-1]['created_utc'] - 10
    more_posts = filter_ids_time(PUSHSHIFT_URI, new_begin, end)
    posts_amount = len(more_posts)
    posts.extend(more_posts)
    nb_requests_made += 1
  
  return posts

"""
Testing get_posts() function.
- Timestamp converter: https://www.unixtimestamp.com/index.php?ref=theredish.com%2Fweb
- Able to retrieve up till latest posts from 6 hours ago.
- To print till "now": math.ceil(datetime.utcnow().timestamp())
"""
# Posts from March 13th
#posts = get_posts('wallstreetbets', 1615687200, math.ceil(datetime.utcnow().timestamp()))
# All posts from nb_days_from_today
nb_days_from_today = 5
begin = math.ceil((datetime.utcnow() - timedelta(days=nb_days_from_today)).timestamp())
end = math.ceil(datetime.utcnow().timestamp())
print("Timestamps: ", begin, end)
posts = get_posts('wallstreetbets', begin, end)
unique_posts = np.unique([post['id'] for post in posts])
# Use np.unique to get rid of duplicates and filter posts only by id (only need id for praw).
print("Size: ", len(posts))
print("Size of uniques: ", len(unique_posts))
print("Example posts: ", unique_posts[:5])

import praw
import os
"""
Connect to Reddit API using environment variables. (values from reddit app)
- returns: reddit instance
"""
def connect_reddit():
  reddit = praw.Reddit(
    username = "fryingpannnnnn", #os.environ['REDDIT_NAME'],
    password = "wsbpan123", #os.environ['REDDIT_PASS'],
    client_secret = "GWFFdjptuoOsDPjpxERQsBY-xV7GfQ", #os.environ['REDDIT_SECRET'],
    client_id = "VWDfl0X3JFVwWQ", #os.environ['REDDIT_CLIENTWSB'],
    user_agent = "wsbscrape"
  )
  return reddit

# Testing connect_reddit() function
# Should print "<praw.reddit.Reddit object at ...>"
reddit = connect_reddit()
print(reddit)

"""
Function to retrieve all Reddit posts of given ids.
- unique_posts: the id of the posts you want to retrieve.
- returns: list of reddit submission instances (reddit posts) of the input ids.
"""
def get_reddit_posts(unique_posts):
  reddit = connect_reddit()
  PAUSE_BEFORE_NEXT_CALL = 0.3

  reddit_posts = []

  for post_id in unique_posts:
    reddit_posts.append(reddit.submission(id=post_id))
    time.sleep(PAUSE_BEFORE_NEXT_CALL)

  return reddit_posts

# Testing get_reddit_posts(): retrieving 1000 posts.
thousand_posts = unique_posts[:1000]
reddit_posts = get_reddit_posts(thousand_posts)
print("Size of posts: ", len(reddit_posts))
print("First 5 posts: ", reddit_posts[:5])

reddit_posts[0].score

