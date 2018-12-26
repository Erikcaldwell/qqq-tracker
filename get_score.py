# Import Dependencies
import pandas as pd
import tweepy
import numpy as np
import os
import requests
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import datetime
import time
import os.path
import sys
from flask import jsonify
import pyEX as iex
from pymongo import MongoClient
import pymongo

#keys for twitter API and the newsapi
consumer_key = os.environ['consumer_key']
consumer_secret = os.environ['consumer_secret']
access_token = os.environ['access_token']
access_token_secret = os.environ['access_token_secret']
news_api = os.environ['news_api']

# Setup Tweepy API Authentication
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

def analyzer():
    handles = ['@Nasdaq', '@Apple', '@Microsoft', '@amazon', '@Google', '@facebook', '@GileadSciences', '@intel']
    data = []
    current_time = time.time()
    # Grab twitter handles and append the name to data
    for handle in handles:
        data_dict = {}
        tweets = []
        tweets = api.user_timeline(handle)
        data_dict['Handle'] = handle
        data_dict['timestamp'] = current_time
        if tweets:
            data_dict['Name'] = tweets[0]['user']['name']
            data.append(data_dict)

    # Setup sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()

    # Grab tweets containing the user name of the twitter handle
    for user in data:
        compound_scores = []
        tweets = api.search_users(user['Name'])
        query_name = user['Name']
        articles = requests.get('https://newsapi.org/v2/everything?q=' + query_name + '&language=en' + "&apiKey=" + news_api).json()

        # Run sentiment analysis on tweets and append the average
        # compound sentiment score to data
        for tweet in tweets:
            try:
                sent = analyzer.polarity_scores(tweet['status']['text'])
                compound_scores.append(sent['compound'])
            except KeyError:
                pass

        for article in articles['articles']:
            if article['content']:
                senti = analyzer.polarity_scores(article["content"])
                compound_scores.append(senti['compound'])

        user['Score'] = np.mean(compound_scores)

    # Compute the average senti score and get the current stock price
    #price data is updated by the api host every 15 mins
    data_df = pd.DataFrame(data)
    mean_score = data_df["Score"].mean()
    timestamp = current_time
    mylist = []
    today = datetime.datetime.now()
    mylist.append(today)
    stock = 'QQQ'
    response = requests.get("https://api.iextrading.com/1.0/stock/qqq/price?")
    price = float(response.content.decode("utf-8"))
    my_dict = {
     'timestamp' : [timestamp],
     'date' : [mylist[0]],
     'stock' : [stock],
     'price': [price],
     'score' : [mean_score],
}
    score_df = pd.DataFrame(my_dict)
    #score_df.to_csv('test.csv')

    #setting up the MongoDB to hold the my_dict results
    mng_client = pymongo.MongoClient(os.environ['MONGOLAB_URI'])
    mng_db = mng_client['qqq_cloud']
    collection_name = 'results'
    db_cm = mng_db[collection_name]
    score_df = score_df.apply(pd.to_numeric, errors='ignore')
    score_df = json.loads(score_df.to_json(orient='records'))
    db_cm.insert(score_df)
    time.sleep(900)
    return
