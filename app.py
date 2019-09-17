import random
import time
import tweepy

from config import create_api

FORBIDDEN_WORDS = ["porn", "sex", "brazzers", "onlyfans", "horny", "xxx", "comment", "tag", "reply", "full video",
                   "vote", "video", "democrats", "quote" "republicans", "mygirlfund", "only fans", "boob", "sugarbaby",
                   "sugardaddy", "snapchat", "botspot", "bot spot", "trump", "tits", "rt.com", "milf", "nude",
                   " justfor.fans", "taylorswift", "xtube", "ass", "bdsm"]

BLOCKED_HANDLES = ["bot spot", "bot spotting", "b0t", "botspot", "보라해방탄"]


class FavRetweetListener(tweepy.StreamListener):
    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.competition_tweet_count = 1
        self.backoff_tweet_count = random.randint(200, 300)
        self.total_backoff_count = 0

    def on_status(self, tweet):
        """
        Called when a new tweet arrives - overrides parent method of the same name
        :param tweet: a JSON tweet object
        """
        # Force bot to sleep for a random time after 200 to 300 competitions have been entered
        if self.competition_tweet_count == self.backoff_tweet_count:
            self.total_backoff_count += 1
            # On the 4th backoff take a longer break between 1 to 2 hours
            if self.total_backoff_count == 4:
                random_sleep_time = random.randint(3600, 7200)
                self.total_backoff_count = 0
            else:
                random_sleep_time = random.randint(1200, 1800)
            print("Sleeping now for {} minutes ".format(random_sleep_time / 60))
            time.sleep(random_sleep_time)
            self.backoff_tweet_count = random.randint(200, 300)
        # The tweet is judged against multiple criteria before it is deemed to be an applicable competition
        try:
            source_tweet, author = get_source_tweet(tweet)
            source_tweet_text = retrieve_tweet_text(source_tweet)
            contains_forbidden_url = check_forbidden_urls(source_tweet)
            if not any(word in source_tweet_text for word in FORBIDDEN_WORDS) and not contains_forbidden_url:
                if not any(word in source_tweet.user.name.lower() for word in BLOCKED_HANDLES):
                    if "rt" in source_tweet_text or "retweet" in source_tweet_text and "win" in source_tweet_text:
                        self.enter_competition(source_tweet, author)
        except tweepy.error.TweepError:
            pass
        except Exception as exception:
            print(exception)

    def enter_competition(self, competition_tweet, username):
        """
        Enters a competition by retweeting and if applicable, liking the tweet and
        following the appropriate Twitter user
        :param competition_tweet: a JSON tweet object which has deemed to be a competition
        :param username: the username of the account posting the competition
        """
        tweet_text = retrieve_tweet_text(competition_tweet)
        if "follow" in tweet_text:
            self.api.create_friendship(username)
        if "like" in tweet_text:
            competition_tweet.favorite()
        competition_tweet.retweet()
        print("{}. Success: Competition entered".format(self.competition_tweet_count))
        self.competition_tweet_count += 1


def get_source_tweet(tweet):
    """
    If the tweet is a retweet or a quote tweet, then retrieve the original tweet.
    :param tweet: a JSON tweet object
    :return: original tweet as a JSON object
    :return: the author's username of the original tweet
    """
    if hasattr(tweet, "quoted_status"):
        quote_tweet = tweet.quoted_status
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


def check_forbidden_urls(tweet_to_check):
    """
    Checks to see if the tweet contains a url and if the url contains any words in the FORBIDDEN_WORDS list
    :param tweet_to_check: a JSON tweet object
    :return: boolean value whether that indicates whether the tweet contains a forbidden URL
    """
    for url in tweet_to_check.entities['urls']:
        if any(word in url['expanded_url'].lower() for word in FORBIDDEN_WORDS):
            return True
    return False


def retrieve_tweet_text(tweet):
    """
    Retrieves the text that appears in the tweet object
    :param tweet: a JSON tweet object
    :return: the text of the tweet all in lowercase
    """
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
