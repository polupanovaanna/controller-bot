import time

from spider_token import token
import requests
import spider_db
import re
import queue

delta_time = 4002352240
message_count = 100
visited_channels = set()  # set(spider_db.get_all_chats())
channels_queue = queue.Queue()


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
        spider_db.add_mention(chat_id)
    except:
        print("Someting went wrong...")
        raise


def get_last_message_time(chat_id: int):
    params = {
        "chat_id": chat_id,
        "access_token": token,
        "count": 1
    }
    response = requests.get("https://botapi.tamtam.chat/messages", params=params).json()
    if ("messages" in response.keys() and len(response["messages"]) > 0):
        return response["messages"][0]["timestamp"]
    return 0


def dfs(chat_link):
    regexpr = r"(tt\.me/)([A-za-z0-9]+)"
    current_chat_id = get_chat_id(chat_link)
    last_time = 0
    first_time = 0
    print("started")
    if current_chat_id not in set(spider_db.get_all_chats()):
        last_time = get_last_message_time(current_chat_id)
        spider_db.set_last_time(current_chat_id, last_time)
        spider_db.set_first_time(current_chat_id, 0)
        print("channel is new")
    else:
        first_time = spider_db.get_last_time(current_chat_id)
        print("channel is old")
    messages = get_chat_messages(chat_link, last_time)
    need_check = True
    print(len(messages))
    while need_check and len(messages) > 0:
        for message in messages:
            timestamp = message["timestamp"]
            last_time = min(timestamp, last_time-10000)
            print(last_time)
            if (timestamp <= first_time):
                need_check = False
                break
            if ("markup" not in message["body"].keys()):
                continue
            links = message["body"]["markup"]
            for link in links:
                if (link["type"] == "link"):
                    match = re.findall(regexpr, link["url"], re.MULTILINE)
                    for i in match:
                        if (i[1] == chat_link):
                            continue
                        add_mention(i[1])
                        if (get_chat_id(i[1]) not in visited_channels):
                            channels_queue.put(i[1])
        messages = get_chat_messages(chat_link, last_time)
    if spider_db.get_first_time(current_chat_id) == 0:
        spider_db.set_first_time(current_chat_id, last_time)
    next_link = channels_queue.get()
    dfs(next_link)


def get_params(chat_id, last_time):
    params = {
        "chat_id": chat_id,
        "access_token": token,
        "from": last_time,
        "count": message_count
    }
    print(params)
    return params


def get_chat_messages(link: str, last_time: int):
    # try:
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
    print(chat)
    if (not chat["is_public"]):
        return []
    chat_id = chat["chat_id"]

    params = get_params(chat_id, last_time)
    response = requests.get("https://botapi.tamtam.chat/messages", params=params)
    print(len(response.json()["messages"]))
    return response.json()["messages"]


#get_last_message_time(get_chat_id("shootki"))

dfs("shootki")
print(spider_db.get_all_chats())