import datetime
import time

from twitter import Twitter, OAuth, TwitterHTTPError
from twitter_info import *

ALREADY_FOLLOWED_FILE = "already-followed.csv"

t = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
            CONSUMER_KEY, CONSUMER_SECRET))


def search_tweets(q, count=100, result_type="recent"):
    """
        Returns a list of tweets matching a certain phrase (hashtag, word, etc.)
    """

    result = t.geo.search(query="BR", granularity="country")
    place_id = result['result']['places'][0]['id']

    result = t.search.tweets(q=f"{q} AND place:{place_id}", result_type=result_type, count=count)
    return result


def auto_fav(q, count=100, result_type="recent"):
    """
        Favorites tweets that match a certain phrase (hashtag, word, etc.)
    """

    result = search_tweets(q, count, result_type)

    for tweet in result["statuses"]:
        try:
            # don't favorite your own tweets
            if tweet["user"]["screen_name"] == TWITTER_HANDLE:
                continue

            result = t.favorites.create(_id=tweet["id"])
            print("favorited: %s" % (result["text"].encode("utf-8")))

        # when you have already favorited a tweet, this error is thrown
        except TwitterHTTPError as e:
            print("error: %s" % (str(e)))


def auto_rt(q, count=100, result_type="recent"):
    """
        Retweets tweets that match a certain phrase (hashtag, word, etc.)
    """

    result = search_tweets(q, count, result_type)

    for tweet in result["statuses"]:
        try:
            # don't retweet your own tweets
            if tweet["user"]["screen_name"] == TWITTER_HANDLE:
                continue

            result = t.statuses.retweet(id=tweet["id"])
            print("retweeted: %s" % (result["text"].encode("utf-8")))

        # when you have already retweeted a tweet, this error is thrown
        except TwitterHTTPError as e:
            print("error: %s" % (str(e)))


def get_do_not_follow_list():
    """
        Returns list of users the bot has already followed.
    """

    # make sure the "already followed" file exists
    if not os.path.isfile(ALREADY_FOLLOWED_FILE):
        with open(ALREADY_FOLLOWED_FILE, "w") as out_file:
            out_file.write("")

        # read in the list of user IDs that the bot has already followed in the
        # past
    do_not_follow = set()
    dnf_list = []
    with open(ALREADY_FOLLOWED_FILE) as in_file:
        for line in in_file:
            dnf_list.append(int(line))

    do_not_follow.update(set(dnf_list))
    del dnf_list

    return do_not_follow


def auto_follow(q, count, max_per_round, result_type='recent'):
    """
        Follows anyone who tweets about a specific phrase (hashtag, word, etc.)
    """

    result = search_tweets(q, count, result_type)
    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    do_not_follow = get_do_not_follow_list()

    round = 0
    for tweet in result["statuses"]:
        try:
            if (tweet["user"]["screen_name"] != TWITTER_HANDLE and
                    tweet["user"]["id"] not in following and
                    tweet["user"]["id"] not in do_not_follow):

                t.friendships.create(user_id=tweet["user"]["id"], follow=False)
                following.update(set([tweet["user"]["id"]]))

                print("followed %s" % (tweet["user"]["screen_name"]))
                round += 1
                if round >= max_per_round:
                    break

        except TwitterHTTPError as e:
            print("error: %s" % (str(e)))

            # quit on error unless it's because someone blocked me
            if "blocked" not in str(e).lower():
                quit()


def auto_follow_followers():
    """
        Follows back everyone who's followed you
    """

    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    followers = set(t.followers.ids(screen_name=TWITTER_HANDLE)["ids"])

    not_following_back = followers - following

    for user_id in not_following_back:
        try:
            t.friendships.create(user_id=user_id, follow=False)
        except Exception as e:
            print("error: %s" % (str(e)))


def auto_unfollow_nonfollowers():
    """
        Unfollows everyone who hasn't followed you back
    """

    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    followers = set(t.followers.ids(screen_name=TWITTER_HANDLE)["ids"])

    # put user IDs here that you want to keep following even if they don't
    # follow you back
    users_keep_following = set([])

    not_following_back = following - followers

    # make sure the "already followed" file exists
    if not os.path.isfile(ALREADY_FOLLOWED_FILE):
        with open(ALREADY_FOLLOWED_FILE, "w") as out_file:
            out_file.write("")

    # update the "already followed" file with users who didn't follow back
    already_followed = set(not_following_back)
    af_list = []
    with open(ALREADY_FOLLOWED_FILE) as in_file:
        for line in in_file:
            af_list.append(int(line))

    already_followed.update(set(af_list))
    del af_list

    with open(ALREADY_FOLLOWED_FILE, "w") as out_file:
        for val in already_followed:
            out_file.write(str(val) + "\n")

    for user_id in not_following_back:
        if user_id not in users_keep_following:
            t.friendships.destroy(user_id=user_id)
            print("unfollowed %d" % (user_id))


def auto_mute_following():
    """
        Mutes everyone that you are following
    """
    following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
    muted = set(t.mutes.users.ids(screen_name=TWITTER_HANDLE)["ids"])

    not_muted = following - muted

    # put user IDs of people you do not want to mute here
    users_keep_unmuted = set([])
            
    # mute all        
    for user_id in not_muted:
        if user_id not in users_keep_unmuted:
            t.mutes.users.create(user_id=user_id)
            print("muted %d" % (user_id))


def auto_unmute():
    """
        Unmutes everyone that you have muted
    """
    muted = set(t.mutes.users.ids(screen_name=TWITTER_HANDLE)["ids"])

    # put user IDs of people you want to remain muted here
    users_keep_muted = set([])
            
    # mute all        
    for user_id in muted:
        if user_id not in users_keep_muted:
            t.mutes.users.destroy(user_id=user_id)
            print("unmuted %d" % (user_id))

total = 0

while True:
    try:
        following = set(t.friends.ids(screen_name=TWITTER_HANDLE)["ids"])
        if len(following) >= int(os.getenv('total_geral')):
            print("Não roda mais")
            break
        #if datetime.datetime.utcnow().day in [7, 14, 21, 30]:
        #    print(f"LIMPEZA SEMANAL ... dia {datetime.datetime.utcnow().day}")
        #    auto_unfollow_nonfollowers()
        print("auto follow")
        auto_follow(q=os.getenv('tag'), max_per_round=30, count=100)
        total += 10
        print("aguardando 1 hora para começar novamente o loop")
        time.sleep(3600)
        if total >= int(os.getenv('total')):
            print("Parando por hoje!")
            break
    except Exception as e:
        print(e)
        break

