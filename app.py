# Import Dependencies
from flask import Flask, jsonify, render_template
import os
import json
import os.path
import sys
from pymongo import MongoClient
import pymongo
from get_score import analyzer
import pandas as pd
import threading
import time

app = Flask(__name__)

# Create  api serving up the data we need for the dashboard
@app.route('/')
def hello():
    return 'To see the data use /display.html, to download use /download'

@app.route('/display.html')
def display_results():
    return render_template('display.html')

@app.route('/download')
def download():
    data = start()
    return jsonify(data)

def start():
    analyzer()
    # Connect to MongoDB
    conn = os.environ['MONGOLAB_URI']
    client = pymongo.MongoClient(conn)
    db = client.qqq_cloud
    collection = db.results
    results_data = list(db.results.find())
    display_df = pd.DataFrame(results_data)
    display_df = display_df.drop(['_id'], axis=1)
    download_df = display_df.to_json(orient='records')
    display_df.to_html('./templates/display.html')
    data_ordered = download_df
    return data_ordered

def go():
    start()
    time.sleep(900)
    start()

if __name__ == "__main__":
    app.run(debug=True)
    go()
