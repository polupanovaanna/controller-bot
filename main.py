from TOKEN import TOKEN
from botapitamtam import BotHandler
#simple bot that prints миу in dialogs and find мяу and миу in chat's messages

bot = BotHandler(TOKEN)


def main():
    while True:
        upd = bot.get_updates()
        if upd:
            chat_id = bot.get_chat_id(upd)
            chat_info = bot.get_chat(chat_id)
            if not chat_info:
                continue
            if (chat_info['type'] == 'dialog'):
                bot.send_message("Миу!", chat_id)
                continue
            text = bot.get_text(upd)
            if not text:
                continue
            if 'миу' in text.lower():
                bot.send_message("Миу!", chat_id)
            elif 'мяу' in text.lower():
                bot.send_message("Не мяу, а миу!!!", chat_id)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
