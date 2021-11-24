from botapitamtam import BotHandler
from token_file import token
from db import *
bot = BotHandler(token)

greeting_text = "Здравствуйте! \n Я бот для авторов каналов, для начала работы добавьте меня в свой канал."
ask_for_perms_text = "В данный момент у бота нет доступа ко всем сообщениям чата. Пожалуйста, измените настройки бота."

def main():
    while True:
        upd = bot.get_updates()
        if upd:
            chat_id = bot.get_chat_id(upd)
            chat_info = bot.get_chat(chat_id)
            upd_type = bot.get_update_type(upd)
            if not chat_info:
                continue
            elif chat_info['type'] == 'channel':
                print("...")  # тут будет код
            else:
                if upd_type == "bot_started":
                    bot.send_message(greeting_text, chat_id)
                elif upd_type == "message_created":
                    text = bot.get_text(upd)
                    bot.send_message(text, chat_id)  # здесь будут команды в диалоге
                if chat_info['type'] == 'chat':
                    if bot.get_chat_membership(chat_id)['is_admin'] is False:
                        bot.send_message(ask_for_perms_text, chat_id)
                    elif 'read_all_messages' not in bot.get_chat_membership(chat_id)['permissions']:
                        bot.send_message(ask_for_perms_text, chat_id)


if __name__ == '__main__':
    try:
        connect()
        main()
    except KeyboardInterrupt:
        disconnect()
        exit()
