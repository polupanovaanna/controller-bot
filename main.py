from botapitamtam import BotHandler
from token_file import token
from text import greeting_text, ask_for_perms_text, create_poll_intro, create_poll_ask_num

bot = BotHandler(token)


def set_channel(chat_id):
    chats = bot.get_all_chats()
    channels = []
    for chat in chats['chats']:
        if chat['type'] == 'channel':
            channels.append(chat)
    return channels[0]['chat_id']


def create_poll(chat_id, channel_id):
    positions = []
    bot.send_message(create_poll_intro, chat_id)
    upd = bot.get_updates()
    poll_text_main = bot.get_text(upd)
    number_of_ans = 0
    bot.send_message(create_poll_ask_num, chat_id)
    while 1:
        upd = bot.get_updates()
        text = bot.get_text(upd)
        try:
            number_of_ans = int(text)
        except ValueError:
            bot.send_message("Неправильно введено число. Попробуйте еще раз.", chat_id)

        if number_of_ans > 0:
            break
        else:
            bot.send_message("Неправильно введено число. Попробуйте еще раз.", chat_id)

    for i in range(number_of_ans):
        bot.send_message("Введите вариант ответа №" + str(i+1), chat_id)
        upd = bot.get_updates()
        text = bot.get_text(upd)
        positions.append(text)

    buttons = []
    for var in positions:
        buttons.append(bot.button_callback(var, "pushed", intent='default'))
    bot.send_message(poll_text_main, channel_id, attachments=bot.attach_buttons(buttons))
    return


def poll_callback(callback_id):
    bot.send_answer_callback(callback_id, "Ваш голос засчитан")
    return


def main():
    channel_id = -1
    opened_polls = set()

    while True:
        upd = bot.get_updates()
        if upd:
            chat_id = bot.get_chat_id(upd)
            chat_info = bot.get_chat(chat_id)
            upd_type = bot.get_update_type(upd)

            if channel_id == -1:
                channel_id = set_channel(chat_id)

            if not chat_info:
                continue
            elif chat_info['type'] == 'channel':
                if upd_type == "message_callback":
                    poll_callback(bot.get_callback_id(upd))
            else:
                if upd_type == "bot_started":
                    bot.send_message(greeting_text, chat_id)
                elif upd_type == "message_created":
                    text = bot.get_text(upd)
                    if text == "\create_poll":
                        create_poll(chat_id, channel_id)
                        bot.get_updates()
                        #opened_polls.update(bot.get_message_id(channel_id))
                    else:
                        bot.send_message("Ваша команда не распознана", chat_id)  # здесь будут команды в диалоге
                if chat_info['type'] == 'chat':
                    if bot.get_chat_membership(chat_id)['is_admin'] is False:
                        bot.send_message(ask_for_perms_text, chat_id)
                    elif 'read_all_messages' not in bot.get_chat_membership(chat_id)['permissions']:
                        bot.send_message(ask_for_perms_text, chat_id)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
