#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
t.py and imb.py should contain the imported variables.
"""

from __future__ import print_function

import json
import sys
import threading
import re
import pyttsx3
from random import choice
from threading import Timer
from RepeatedTimer import RepeatedTimer

import twitter
from t import ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET

from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm import WATSONAPIKEY, WATSONURL

import simpleaudio as sa

# Global latest tweet
latest_tweet = 0
lock = threading.Lock()

def get_new_tweets(api=None, screen_name=None):
    with lock:
        try:
            global latest_tweet

            print("get new Tweets. Latest_tweet: "+str(latest_tweet))
            timeline = api.GetUserTimeline(screen_name=screen_name, since_id=latest_tweet, count=200)
            if timeline:
                earliest_tweet = min(timeline, key=lambda x: x.id).id

                while True:
                    tweets = api.GetUserTimeline(
                        screen_name=screen_name, max_id=earliest_tweet, since_id=latest_tweet, count=200
                    )
                    new_earliest = min(tweets, key=lambda x: x.id).id

                    if not tweets or new_earliest == earliest_tweet:
                        break
                    else:
                        earliest_tweet = new_earliest
                        print("getting tweets before:", earliest_tweet)
                        timeline += tweets

                
                timeline.sort(key=lambda x: x.id)
                for tweet in timeline:
                    try:
                        tweet_to_speach(tweet)
                    except Exception as ex:
                        print("ERROR IN TTS")
                        print(ex)
                    
                latest_tweet = max(timeline, key=lambda x: x.id).id
        except:
            print("error in mainloop")

def find_last_tweet(api=None, screen_name=None):
    timeline = api.GetUserTimeline(screen_name=screen_name, count=200)
    latest_tweet = max(timeline, key=lambda x: x.id).id
    print("Last tweet:", latest_tweet)
    return latest_tweet

def tweet_to_speach(tweet):
    print("Tweet ID: " + str(tweet.id) + " TEXT: " + tweet.full_text)
    
    #Clean up any twitter links
    full_text = re.sub( r"https:\/\/t\.co\/[^\s]+",  "",  tweet.full_text )

    if (full_text.strip() != ""):
        try:
            authenticator = IAMAuthenticator(WATSONAPIKEY)
            text_to_speech = TextToSpeechV1(
                authenticator=authenticator
            )

            text_to_speech.set_service_url(WATSONURL)

            audio_data = text_to_speech.synthesize(
                full_text,
                voice='en-US_MichaelV3Voice',
                accept='audio/wav'        
            ).get_result().content

            # Let everyone know that POTUS is about to talk
            and_now_POTUS()

            # Play the TTS
            play_obj = sa.play_buffer(audio_data, 1, 2, 22050)
            play_obj.wait_done()
        except:
            #Wattson is mad, let just run this local
            engine = pyttsx3.init()
            rate = engine.getProperty('rate')
            engine.setProperty('rate', rate-50)
            
            voices = engine.getProperty('voices')
            voice = choice(voices)
            engine.setProperty('voice', voice.id)

            engine.say(full_text)

            # Let everyone know that POTUS is about to talk
            and_now_POTUS()

            engine.runAndWait()

def and_now_POTUS():
    wave_obj = sa.WaveObject.from_wave_file("andNowPOTUS.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

if __name__ == "__main__":
    api = twitter.Api(
        CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET, tweet_mode='extended'
    )
    screen_name = "realdonaldtrump"
    print(screen_name)
    # We just started, find the last thing they tweeted and only show newer stuff
    latest_tweet = find_last_tweet(api=api, screen_name=screen_name)

    print("starting...")
    rt = RepeatedTimer(30, get_new_tweets, api, screen_name)

