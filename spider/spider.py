import time

from spider_token import token
import requests
import spider_db
import re
import queue
import threading
from time import sleep
from bs4 import BeautifulSoup

message_count = 100
visited_channels = set()
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
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{chat_id}", params={"access_token": token}).json()
    if ("link" in chat.keys()):
        chat_link = chat["link"][14:]
    else:
        print("can't find channel with id " + str(chat_id))
        return FAIL
    return chat_link


def get_chat(link):
    return requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()


def add_mention(link):
    try:
        chat = get_chat(link)
        if not chat["is_public"]:
            return FAIL
        chat_id = chat["chat_id"]
        if (chat_id == FAIL):
            return FAIL
        visited_channels_lock.acquire()
        spider_db.add_mention(chat_id)
        visited_channels_lock.release()
        return SUCCESS
    except Exception as e:
        print(e)
        return FAIL


def get_last_message_time(chat_id: int):
    params = {
        "chat_id": chat_id,
        "access_token": token,
        "count": 1
    }
    response = requests.get("https://botapi.tamtam.chat/messages", params=params).json()
    if "messages" in response.keys() and len(response["messages"]) > 0:
        return response["messages"][0]["timestamp"]
    return 0


def dfs():
    global channels_queue, visited_channels
    chat_link = channels_queue.get()
    added_channels = set()
    regexpr = r"(tt\.me/)([A-za-z0-9]+)"
    current_chat_id = get_chat_id(chat_link)
    if current_chat_id == FAIL:
        return
    visited_channels_lock.acquire()
    if current_chat_id in visited_channels:
        visited_channels_lock.release()
        dfs()
        return
    first_time = 0
    visited_channels.add(current_chat_id)
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
            status = message
            timestamp = message["timestamp"]
            last_time = min(timestamp, last_time)
            if (timestamp <= first_time):
                need_check = False
                break
            matches = re.findall(regexpr, message["body"]["text"], re.MULTILINE)
            for i in matches:
                if i[1] == chat_link:
                    continue
                add_mention(i[1])
                new_chat_id = get_chat_id(i[1])
                if (new_chat_id == FAIL):
                    print("fail to get chat id")
                    continue
                if new_chat_id not in visited_channels and new_chat_id not in added_channels:
                    channels_queue.put(i[1])
                    added_channels.add(new_chat_id)
            if "markup" not in message["body"].keys():
                continue
            links = message["body"]["markup"]
            for link in links:
                if (link["type"] == "link"):
                    match = re.findall(regexpr, link["url"], re.MULTILINE)
                    for i in match:
                        if (i[1] == chat_link):
                            continue
                        add_mention(i[1])
                        new_chat_id = get_chat_id(i[1])
                        if (new_chat_id == FAIL):
                            continue
                        if new_chat_id not in visited_channels and new_chat_id not in added_channels:
                            channels_queue.put(i[1])
                            added_channels.add(new_chat_id)
        messages = get_chat_messages(chat_link, last_time)
    visited_channels_lock.acquire()
    spider_db.set_last_time(current_chat_id, last_checked_time)
    if spider_db.get_first_time(current_chat_id) == 0:
        spider_db.set_first_time(current_chat_id, last_time)
    visited_channels_lock.release()


def get_params(chat_id, last_time):
    params = {
        "chat_id": chat_id,
        "access_token": token,
        "from": last_time,
        "count": message_count
    }
    return params


def get_links():
    try:
        res = requests.get("https://ttstat.ru/", allow_redirects=True).text
        bs = BeautifulSoup(res, "html")
        blocks = bs.find_all("td", attrs={"class": "tbl_main_td"})
        channels = []
        for i in range(len(blocks)):

            block = blocks[i].find("a", attrs={"target": "_blank"})
            if (block is not None):
                channels.append(block.get("href")[4:-1])
        return channels
    except:
        return []


def get_chat_messages(link: str, last_time: int):
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
    if (not chat["is_public"]):
        return []
    chat_id = chat["chat_id"]

    params = get_params(chat_id, last_time - 1)
    response = requests.get("https://botapi.tamtam.chat/messages", params=params)
    return response.json()["messages"]


channels_queue = queue.Queue()
visited_channels_lock = threading.Lock()


def start_spider():
    processed_chats = spider_db.get_all_chats()
    for i in processed_chats:
        link = get_chat_link(i[0])
        channels_queue.put(link)
    links = get_links()
    for i in links:
        channels_queue.put(i)
    workers = [None for i in range(20)]
    while True:
        any_workers = False
        for i in range(len(workers)):
            any_workers = any_workers or workers[i] is not None and workers[i].is_alive()
            if workers[i] is None or not workers[i].is_alive():
                if not channels_queue.empty():
                    print("starting new thread channel is", channels_queue.queue[0])
                    if workers[i] is not None:
                        workers[i].join()
                    workers[i] = threading.Thread(target=dfs)
                    workers[i].start()

        time.sleep(5)


if __name__ == "__main__":
    sleep(10)
    start_spider()
