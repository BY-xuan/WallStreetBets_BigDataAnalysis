# -*- coding: utf-8 -*-
"""ProjectWallStreetBetsSpark.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wL3UnzMuHG9ZjVSWQUkmO4pQ2EdqODLS
"""

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
- returns: Spark RDD consisting of python objects (each one is a reddit post)
"""
def get_request(uri, max_retry = 5):
  def get(uri):
    response = requests.get(uri)
    assert response.status_code == 200
    # deserialize JSON object and get the data containing the posts
    data = json.loads(response.content)['data']
    return spark.sparkContext.parallelize(data)
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

# Testing get_request()
# Use this to check format: https://jsonformatter.curiousconcept.com/#
# first() returns latest post (highest created_utc)
rdd = get_request('https://api.pushshift.io/reddit/search/submission?subreddit=wallstreetbets')
print("Size of rdd: ", rdd.count())
#print("Data: ", rdd.collect())
print(rdd.first())
only_time = rdd.map(lambda post: post['created_utc'])
top5 = only_time.take(5)
print(top5)
first = rdd.first()['created_utc']
print(first)
# test rdd union order: appends right after
top5 = spark.sparkContext.parallelize(top5)
random = spark.sparkContext.parallelize([1,2,3])
print(top5.union(random).collect())
#print(rdd.max(key=lambda post: post['created_utc']))

print(rdd.max(key=lambda post: post['created_utc']))

"""
Gets the all the posts from a given subreddit in the specific time range.
- subreddit: name of subreddit
- begin: timestamp (in unix) of start date
- end: timestamp (in unix) of end date
- returns: RDD consisting of all the post ids in the time interval.
"""
def get_posts(subreddit, begin, end):
  # Max size of each Pushshift API request is 100 posts.
  SIZE = 100
  PUSHSHIFT_URI = r'https://api.pushshift.io/reddit/search/submission?subreddit={}&after={}&before={}&size={}'

  # Get the ids and creation time of the posts only. Used later to get the actual posts with PRAW with these ids.
  # - returns: RDD consisting of python objects containing post id & creation date.
  def filter_ids_time(uri, begin, end):
    full_posts = get_request(uri.format(subreddit, begin, end, SIZE))
    if full_posts.isEmpty():
      raise ValueError("Response is empty or none.")

    # RDD of only the posts' ids and creation date
    filtered = full_posts.map(lambda post: {
        'id': post['id'],
        'created_utc': post['created_utc']
    })
    return filtered


  posts = filter_ids_time(PUSHSHIFT_URI, begin, end)
  posts_amount = posts.count()
  last_post = posts.first()['created_utc'] - 10
  print(posts.first()['created_utc'],last_post)
  nb_requests_made = 1
  # If reached limit of 100 posts retrieved, make request again until 'end' time.
  while posts_amount == SIZE:
    # Timestamp of the last post we previously retrieved.
    # The RDD's first element will always be the most recent post.
    new_begin = last_post
    more_posts = filter_ids_time(PUSHSHIFT_URI, new_begin, end)
    last_post = more_posts.first()['created_utc'] - 10
    posts_amount = more_posts.count()
    posts.union(more_posts)
    nb_requests_made += 1
    print(nb_requests_made,more_posts.first()['created_utc'],last_post)
  print("Number of requests made: ", nb_requests_made)
  return posts.map(lambda post: post['id'])

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
start_time = time.time()
posts = get_posts('wallstreetbets', 1615824107, 1615838507)
print("--- %s seconds ---" % (time.time() - start_time))
unique_posts = posts.distinct()
# Use np.unique to get rid of duplicates and filter posts only by id (only need id for praw).
print("Size: ", posts.count())
print("Size of uniques: ", unique_posts.count())
print("Example posts: ", unique_posts.take(5))

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

a = [1,2,3]
b = spark.sparkContext.parallelize([1,2,3,4])
print(b)
