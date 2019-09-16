import logging, sys, tweepy, time, random
from config import create_api
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

FORBIDDEN_WORDS = ["porn", "sex", "brazzers", "onlyfans", "horny", "xxx", "ariana", "swift", "taylorswift",
                   "comment", "tag", "reply", "full video", "vote", "video", "democrats",
                   "republicans"]


class FavRetweetListener(tweepy.StreamListener):
    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.me = api.me()
        self.tweet_count = 1
        self.backoff_count = 1

    def on_status(self, tweet):
        try:
            source_tweet, author = get_source_tweet(tweet)
            source_tweet_text = retrieve_tweet_text(source_tweet)
            if not any(word in retrieve_tweet_text(source_tweet).split() for word in FORBIDDEN_WORDS):
                if "rt" in source_tweet_text or "retweet" in source_tweet_text and "win" in source_tweet_text:
                    self.enter_competition(source_tweet, author)
        except tweepy.error.TweepError as e:
            pass
            # print("\n" + str(e))
        except Exception as e:
            print(e.with_traceback())

    def enter_competition(self, competition_tweet, username):
        tweet_text = retrieve_tweet_text(competition_tweet)
        if "follow" in tweet_text:
            self.api.create_friendship(username)
        if "like" in tweet_text:
            competition_tweet.favorite()
        competition_tweet.retweet()
        out_file = open("tweet.json", "w", encoding='utf-8')
        print(str(competition_tweet), file=out_file)
        print("\n{}. Success: Competition entered".format(self.tweet_count))
        self.backoff_count = 1
        self.tweet_count += 1


def get_source_tweet(tweet):
    if hasattr(tweet, "quoted_status"):
        quote_tweet = tweet.quoted_status
        out_file = open("quote.json", "w", encoding='utf-8')
        print(str(quote_tweet), file=out_file)
        if hasattr(quote_tweet, 'user') and quote_tweet.user is not None:
            if hasattr(quote_tweet.user, "screen_name") and quote_tweet.user.screen_name is not None:
                return quote_tweet, quote_tweet.user.screen_name
    elif hasattr(tweet, "retweeted_status"):
        retweet = tweet.retweeted_status
        if hasattr(retweet, 'user') and hasattr(retweet.user, "screen_name") and retweet.user is not None:
            if retweet.user.screen_name is not None:
                return retweet, retweet.user.screen_name
    else:
        return tweet, tweet.user.screen_name


def retrieve_tweet_text(tweet):
    if hasattr(tweet, 'extended_tweet'):
        return tweet.extended_tweet['full_text'].lower()
    else:
        return tweet.text.lower()


def main(keywords):
    api = create_api()
    tweets_listener = FavRetweetListener(api)
    stream = tweepy.Stream(api.auth, tweets_listener)
    stream.filter(track=keywords, languages=["en"])


if __name__ == "__main__":
    main(["RT to win", "Retweet to win"])
