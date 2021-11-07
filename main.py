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
            update_type = bot.get_update_type(upd)
            if(update_type == 'bot_started'):
                if (chat_info['type'] == 'dialog'):
                    bot.send_message('Добрый день, {}, добавьте меня в канал или начните настройку прямо здесь.'.format({bot.get_chat(chat_id)['dialog_with_user']['name']}), chat_id)
                    continue
            bot.get_chat_membership(chat_id)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
