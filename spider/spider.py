import time

from spider_token import token
import requests
import spider_db
import re

delta_time = 1000000
message_count = 100
visited_channels = set()#set(spider_db.get_all_chats())


def get_chat_id(link):
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
    if ("chat_id" in chat.keys()):
        chat_id = chat["chat_id"]
    else:
        print("No such channel: http://tt.me/" + link)
        raise
    return chat_id


def get_chat_link(chat_id):
    pass


def add_mention(link):
    try:
        chat_id = get_chat_id(link)

        spider_db.add_channel(chat_id)
    except:
        print("Someting went wrong...")


def dfs(link):
    print("link: ", link)
    regexpr = r"(tt\.me/)([A-za-z0-9]+)"
    messages = get_chat_messages(link)
    current_chat_id = get_chat_id(link)
    prev_time = spider_db.get_first_time(current_chat_id)
    print("times for", link, spider_db.get_first_time(current_chat_id), spider_db.get_last_time(current_chat_id))
    visited_channels.add(current_chat_id)
    spider_db.add_channel(current_chat_id)
    #print(spider_db.get_first_time(current_chat_id))
    if (len(messages) == 0):
        print("bad link")
    mintime = 10 ** 12
    for (message, timestamp) in messages:
        mintime = min(mintime, timestamp)
        spider_db.set_first_time(current_chat_id, timestamp)
        match = re.findall(regexpr, message, re.MULTILINE)
        for i in match:
            if (i[1] == link):
                continue
            add_mention(i[1])
            if (get_chat_id(i[1]) not in visited_channels):
                dfs(i[1])
    if(mintime != 10**12):
        print("current mintime for:", link, mintime)
    if (len(messages) > 0 and prev_time is None or spider_db.get_first_time(current_chat_id) < prev_time):
        #pass
        dfs(link)


def get_params(chat_id):
    if (chat_id in visited_channels):
        last_time = spider_db.get_last_time(chat_id)
        if(last_time is None):
            last_time = (time.time() - delta_time, )
        #print("last time", time.time())
        return {
            "chat_id": chat_id,
            "access_token": token,
            "count": message_count,
            "from": int(last_time[0])
        }
    else:
        first_time = spider_db.get_first_time(chat_id)
        #print("first time", first_time)

        if(first_time is None):
            first_time = (time.time(), )
        return {
            "chat_id": chat_id,
            "access_token": token,
            "to": int(first_time[0]),
            "count": message_count
        }


def get_chat_messages(link: str):
    # try:
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
    if (not chat["is_public"]):
        return []
    chat_id = chat["chat_id"]

    params = get_params(chat_id)
    #print(params)
    response = requests.get("https://botapi.tamtam.chat/messages", params=params)
    messages = []
    #print(response.json())

    for message in response.json()["messages"]:
        if ("markup" not in message["body"].keys()):
            continue
        links = message["body"]["markup"]
        for link in links:
            if (link["type"] == "link"):
                messages.append((link["url"], message["timestamp"]))
    return messages


# except:
#    return []


dfs("mytestchannel")
print(spider_db.get_all_chats())
