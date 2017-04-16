from __future__ import absolute_import, print_function, unicode_literals

import itertools, time
import tweepy, copy 
import Queue, threading

from streamparse.spout import Spout

################################################################################
# Twitter credentials
################################################################################
twitter_credentials = {
    "consumer_key"        :  "YBBUh4mehGbp6MFkzAFsfDNHl",
    "consumer_secret"     :  "6ttL4wtLIrORgwWzyCyNM33t2Atswbaakwru4uoWg7FTnmuRFd",
    "access_token"        :  "1511952991-pukEYajl8dr8a0kTJqPK6HSLIFsDmfeDl7jpljz",
    "access_token_secret" :  "KUMzwLwWTQbdJ4xxJGoOm3P11xGJhZtEH7qPS1jLZQlSh",
}

def auth_get(auth_key):
    if auth_key in twitter_credentials:
        return twitter_credentials[auth_key]
    return None

################################################################################
# Class to listen and act on the incoming tweets
################################################################################
class TweetStreamListener(tweepy.StreamListener):

    def __init__(self, listener):
        self.listener = listener
        super(self.__class__, self).__init__(listener.tweepy_api())

    def on_status(self, status):
        self.listener.queue().put(status.text, timeout = 0.01)
        return True
  
    def on_error(self, status_code):
        return True # keep stream alive
  
    def on_limit(self, track):
        return True # keep stream alive

class Tweets(Spout):

    def initialize(self, stormconf, context):
        self._queue = Queue.Queue(maxsize = 100)

        consumer_key = auth_get("consumer_key") 
        consumer_secret = auth_get("consumer_secret") 
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

        if auth_get("access_token") and auth_get("access_token_secret"):
            access_token = auth_get("access_token")
            access_token_secret = auth_get("access_token_secret")
            auth.set_access_token(access_token, access_token_secret)

        self._tweepy_api = tweepy.API(auth)

        # Create the listener for twitter stream
        listener = TweetStreamListener(self)

        # Create the stream and listen for english tweets
        stream = tweepy.Stream(auth, listener, timeout=None, follow=['QuakesinCA', 'Monkiejens'])
        stream.filter(languages=["en"], track=["#earthquake"], async=True)
      
        # Collect tweets from user CA Earthquakes
        #tweepy_api = tweepy.API(auth)
        posts = tweepy_api.user_timeline(screen_name = 'Monkiejens', count = 10, include_rts = True)
        # print CAEarthquakes tweets
        #for post in posts:
             #return post.text  

    def queue(self):
        return self._queue

    def tweepy_api(self):
        return self._tweepy_api

    def next_tuple(self):
        try:
            tweet = self.queue().get(timeout = 0.1) 
            if tweet:
                self.queue().task_done()
                self.emit([tweet])
 
        except Queue.Empty:
            self.log("Empty queue exception ")
            time.sleep(0.1) 

    def ack(self, tup_id):
        pass  # if a tuple is processed properly, do nothing

    def fail(self, tup_id):
        pass  # if a tuple fails to process, do nothing
