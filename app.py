import time
import tweepy

from config import create_api

# List of locations that are permitted for contest entry
LOCATIONS = ["au", "aus", "australia", "sydney", "brisbane", "melbourne", "perth", "global", "world", "queensland",
             "new south wales", "victoria", "townsville", "cairns", "new zealand"]


class FavRetweetListener(tweepy.StreamListener):
    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.competition_tweet_count = 0
        self.backoff_time = 2
        self.forbidden_words = load_text_file("forbidden/forbidden_words")
        self.forbidden_handles = load_text_file("forbidden/forbidden_handles")

    def on_status(self, tweet):
        """
        Called when a new tweet arrives - overrides parent method of the same name
        :param tweet: a JSON tweet object
        """
        # Force bot to pause for a certain amout of seconds between requests to reduce spam
        start = time.time()
        while time.time() - start < self.backoff_time:
            pass
        # The tweet is judged against multiple criteria before it is deemed to be an applicable competition
        try:
            source_tweet, author = get_source_tweet(tweet)
            source_tweet_text = retrieve_tweet_text(source_tweet)
            contains_forbidden_url = check_forbidden_urls(source_tweet, self.forbidden_words)

            if source_tweet.user.location and any(
                    location in source_tweet.user.location.lower() for location in LOCATIONS):
                print("LOCATION: " + source_tweet.user.location.lower())
                if not any(word in source_tweet_text for word in self.forbidden_words) and not contains_forbidden_url:
                    if not any(word in source_tweet.user.name.lower() for word in self.forbidden_handles):
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
        self.competition_tweet_count += 1
        print("{}. Success: Competition entered".format(self.competition_tweet_count))


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


def load_text_file(file_location):
    """
    Stores a text file as a list
    :param file_location: Location of the file and filename
    :return: A list containing words from the appropriate file
    """
    text = []
    in_file = open(file_location, "r")
    for line in in_file:
        item = line.strip()
        text.append(item)
    in_file.close()
    return text


def check_forbidden_urls(tweet_to_check, forbidden_words):
    """
    Checks to see if the tweet contains a url and if the url contains any words in the FORBIDDEN_WORDS list
    :param tweet_to_check: a JSON tweet object
    :param forbidden_words: the forbidden word list
    :return: boolean value whether that indicates whether the tweet contains a forbidden URL
    """
    for url in tweet_to_check.entities['urls']:
        if any(word in url['expanded_url'].lower() for word in forbidden_words):
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
