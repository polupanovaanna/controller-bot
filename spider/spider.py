import time

from spider_token import token
import requests
import spider_db
import re
import queue
import threading
from time import sleep
message_count = 100
visited_channels = set()  # set(spider_db.get_all_chats())
FAIL = 0
SUCCESS = 1

def get_chat_id(link):
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
    if ("chat_id" in chat.keys()):
        chat_id = chat["chat_id"]
    else:
        print("No such channel: http://tt.me/" + link)
        return FAIL
    return chat_id


def get_chat_link(chat_id):
    pass


def add_mention(link):
    try:
        chat_id = get_chat_id(link)
        spider_db.add_mention(chat_id)
        return SUCCESS
    except:
        print("Someting went wrong...")
        return FAIL


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


def dfs():
    global status
    if channels_queue.empty():
        return
    chat_link = channels_queue.get_nowait()
    regexpr = r"(tt\.me/)([A-za-z0-9]+)"
    current_chat_id = get_chat_id(chat_link)
    if current_chat_id == FAIL:
        return
    visited_channels_lock.acquire()
    if current_chat_id in visited_channels:
        visited_channels_lock.release()
        return
    first_time = 0
    status = "started"
    print(spider_db.get_all_chats())
    last_time = get_last_message_time(current_chat_id)
    last_checked_time = last_time
    if (current_chat_id,) not in set(spider_db.get_all_chats()):
        spider_db.set_last_time(current_chat_id, last_time)
        spider_db.set_first_time(current_chat_id, 0)
        spider_db.add_channel(current_chat_id, last_time)
    else:
        first_time = spider_db.get_last_time(current_chat_id)[0]
    visited_channels_lock.release()
    messages = get_chat_messages(chat_link, last_time + 1)
    need_check = True
    while need_check and len(messages) > 0:
        for message in messages:
            print(message)
            status = message
            timestamp = message["timestamp"]
            last_time = min(timestamp, last_time)
            if (timestamp <= first_time):
                print("checked message")
                need_check = False
                break
            matches = re.findall(regexpr, message["body"]["text"], re.MULTILINE)
            status = "checking mathes"
            print(matches)
            for i in matches:
                if i[1] == chat_link:
                    continue
                add_mention(i[1])
                new_chat_id = get_chat_id(i[1])
                if (new_chat_id == FAIL):
                    print("fail to get chat id")
                    continue
                visited_channels_lock.acquire()
                if new_chat_id not in visited_channels:
                    list_of_all.append(i[1])
                    channels_queue.put(i[1])
                    visited_channels.add(new_chat_id)
                visited_channels_lock.release()
            if "markup" not in message["body"].keys():
                continue
            links = message["body"]["markup"]
            status = "checking links"
            for link in links:
                print(link)
                if (link["type"] == "link"):
                    match = re.findall(regexpr, link["url"], re.MULTILINE)
                    for i in match:
                        print(i[1])
                        if (i[1] == chat_link):
                            continue
                        add_mention(i[1])
                        list_of_all.append(i[1])
                        new_chat_id = get_chat_id(i[1])
                        if (new_chat_id == FAIL):
                            continue
                        visited_channels_lock.acquire()
                        if new_chat_id not in visited_channels:
                            channels_queue.put(i[1])
                            visited_channels.add(new_chat_id)
                            print(i[1])
                        visited_channels_lock.release()
        status = "getting new messages"
        messages = get_chat_messages(chat_link, last_time)
    spider_db.set_last_time(current_chat_id, last_checked_time)
    if spider_db.get_first_time(current_chat_id) == 0:
        spider_db.set_first_time(current_chat_id, last_time)
    if channels_queue.empty():
        return
    status = "finished"

def get_params(chat_id, last_time):
    params = {
        "chat_id": chat_id,
        "access_token": token,
        "from": last_time,
        "count": message_count
    }
    # print(params)
    return params


def get_chat_messages(link: str, last_time: int):
    # try:
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
    # print(chat)
    if (not chat["is_public"]):
        return []
    chat_id = chat["chat_id"]

    params = get_params(chat_id, last_time - 1)
    response = requests.get("https://botapi.tamtam.chat/messages", params=params)
    return response.json()["messages"]



channels_queue = queue.Queue()
channels_queue.put("mytestchannel")
#channels_queue.put("shootki")
list_of_all = []
visited_channels_lock = threading.Lock()
workers = [None for i in range(10)] #TODO take links from internet
status = "no status"
while(True):
    print(visited_channels)
    any_workers = False
    for i in range(len(workers)):
        any_workers = any_workers or workers[i] is not None and workers[i].is_alive()
        if workers[i] is None or not workers[i].is_alive():
            if not channels_queue.empty():
                print("starting new thread channel is", channels_queue.queue[0])
                workers[i] = threading.Thread(target=dfs)
                workers[i].start()
    print(visited_channels_lock.locked())
    print(channels_queue.mutex.locked())
    print(status)
    print(channels_queue.empty())
    print(list_of_all)
    print(channels_queue.queue)
    sleep(150)
#print(get_chat_id("mytestchannel"))
#print(spider_db.get_mentions(get_chat_id("mytestchannel")))
