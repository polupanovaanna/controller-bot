from spider_token import token
import requests
import re
message_count = 100
visited_channels = set()
def add_mention(link):
    chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
    if("chat_id" in chat.keys()):
        chat_id = chat["chat_id"]
        #TODO add_one mention by chat_id
    else:
        print("No such channel: http://tt.me/"+link)

def dfs(link):
    print("link: ", link)
    regexpr = r"(tt\.me/)([A-za-z0-9]+(?=[^/]))"
    messages = get_chat_messages(link)
    if(len(messages) == 0):
        print("bad link")
    for message in messages:
        match = re.findall(regexpr, message, re.MULTILINE)
        for i in match:
            add_mention(i[1])
            if(i[1] not in visited_channels):
                visited_channels.add(i[1])
                dfs(i[1])

def get_chat_messages(link: str):
    try:
        chat = requests.get(f"https://botapi.tamtam.chat/chats/{link}", params={"access_token": token}).json()
        if(not chat["is_public"]):
            return []
        chat_id = chat["chat_id"]
        params = {
            "chat_id": chat_id,
            "access_token": token,
            "count": message_count
        }
        response = requests.get("https://botapi.tamtam.chat/messages", params=params)
        messages = []
        print(response.json())
        for message in response.json()["messages"]:
            messages.append(message["body"]["text"])
        return messages
    except:
        return []
#TODO connect database
dfs("botapichannel")