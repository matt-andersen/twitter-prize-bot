source_tweet_text = "This gift is hard to unwrap. Who can help me? rtes to win"
source_tweet_text = source_tweet_text.lower()

FORBIDDEN_WORDS = ["porn", "sex", "brazzers", "onlyfans", "#porn", "#sex", "horny", "sexy", "xxx", "ariana", "swift",
                   "anal", "taylorswift", "comment", "tag", "reply", "cum", "full video"]

if "rt" in source_tweet_text.split() or "retweet" in source_tweet_text.split() and "win" in source_tweet_text.split():
    print(source_tweet_text.split())