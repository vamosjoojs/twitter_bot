import random
import time

from twitter import Twitter, OAuth
from twitter_info import *

ALREADY_FOLLOWED_FILE = "already-followed.csv"
SENDED_USERS_FILE = "sended_users.csv"

t = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_SECRET,
            CONSUMER_KEY, CONSUMER_SECRET))


def search_tweets(q, count=100, result_type="recent"):
    result = t.geo.search(query="BR", granularity="country")
    place_id = result['result']['places'][0]['id']

    result = t.search.tweets(q=f"{q} AND place:{place_id}", result_type=result_type, count=count)
    return result


def send_message(message, link, q, count, result_type='recent'):
    if not os.path.isfile(SENDED_USERS_FILE):
        with open(SENDED_USERS_FILE, "w") as out_file:
            out_file.write("")

    sended_users = set()
    snd_list = []
    with open(SENDED_USERS_FILE) as in_file:
        for line in in_file:
            snd_list.append(int(line))

    sended_users.update(set(snd_list))
    del snd_list

    sended = []
    result = search_tweets(q, 100, result_type)
    count_sended = 0
    for tweet in result["statuses"]:
        message_to_send = f"Olá {tweet['user']['name']}, {message} {link}"
        if int(tweet["user"]["id"]) not in sended_users:
            if int(tweet["user"]["id"]) not in sended:
                try:
                    t.direct_messages.events.new(
                    _json={
                        "event": {
                            "type": "message_create",
                            "message_create": {
                                "target": {
                                    "recipient_id": tweet["user"]["id"]},
                                "message_data": {
                                    "text": message_to_send}}}})
                    print(f"Mensagem enviada para {tweet['user']['name']}.")
                    with open(SENDED_USERS_FILE, 'a') as my_file:
                        my_file.write(str(tweet["user"]["id"]))
                    sended.append(int(tweet["user"]["id"]))
                    count_sended += 1
                    seconds = random.randint(12, 70)
                    print(f"Aguardando {seconds} segundos para o próximo envio.")
                    time.sleep(seconds)
                except Exception as ex:
                    print(ex)
                    if ex.e.code == 403:
                        with open(SENDED_USERS_FILE, 'a') as my_file:
                            my_file.write(str(tweet["user"]["id"])+'\n')
                        sended.append(int(tweet["user"]["id"]))
                if count_sended == count:
                    break

total = 0

while True:
    try:
        print('Começando envio de mensagens com o codigo.')
        for send in range(0, 24):
            send_message(
                os.getenv('MESSAGE'),
                os.getenv('LINK'),
                os.getenv('TAG'),
                40)
            print("aguardando 15 minutos para continuar o loop")
            time.sleep(3600)
    except Exception as e:
        print(e)
        break

