from random import randint

import requests

from botapitamtam import BotHandler, logger
from token_file import token
from text import greeting_text, ask_for_perms_text, create_poll_intro, create_poll_ask_num

url = 'https://botapi.tamtam.chat/'
bot = BotHandler(token)
opened_polls = {}


class Poll:
    def __init__(self):
        self.id = None
        self.poll_name = None
        self.answers = []

    def add(self, name):
        self.answers.append([name, 0])


class Post:
    def __init__(self):
        self.id = None
        self.time_created = None
        self.views = []  # добавляем раз в день просмотры, расчет по формуле происходит


def get_all_messages(channel_id):
    method = 'messages'
    params = (
        ('access_token', token),
        ('chat_id', channel_id),
        # ('from', int64), потом эти поля будут нужны для запросов
        # ('to', int64),
        # ('count', int64),
    )
    try:
        response = requests.get(url + method, params)
        if response.status_code == 200:
            messages = response.json()
        else:
            logger.error("Error get chat info: {}".format(response.status_code))
            messages = None
    except Exception as e:
        logger.error("Error connect get chat info: %s.", e)
        chat = None
    return messages


def get_integer(chat_id):
    number_of_ans = -1
    while 1:
        upd = bot.get_updates()
        text = bot.get_text(upd)
        try:
            number_of_ans = int(text)
        except ValueError:
            bot.send_message("Неправильно введено число. Попробуйте еще раз.", chat_id)

        if number_of_ans > 0:
            return number_of_ans
        else:
            bot.send_message("Неправильно введено число. Попробуйте еще раз.", chat_id)


def set_channel(chat_id):
    chats = bot.get_all_chats()
    channels = []
    for chat in chats['chats']:
        if chat['type'] == 'channel':
            channels.append(chat)
    if len(channels) == 0:
        bot.send_message("Бот пока что не состоит ни в одном канале.", chat_id)
    elif len(channels) > 0:
        msg = "Выберите канал, с которым вы ходите работать:\n"
        i = 1
        for ch in channels:
            msg += (str(i) + ". " + ch['title'] + "\n")
        bot.send_message(msg, chat_id)
        num = get_integer(chat_id)
        return channels[num - 1]['chat_id']
    return channels[0]['chat_id']


def get_channel_statistics(channel_id):



def create_poll(chat_id, channel_id):
    positions = []
    bot.send_message(create_poll_intro, chat_id)
    upd = bot.get_updates()
    poll_text_main = bot.get_text(upd)
    bot.send_message(create_poll_ask_num, chat_id)
    number_of_ans = get_integer(chat_id)

    poll_id = randint(0, 100000)
    pl = Poll()
    pl.id = poll_id
    pl.poll_name = poll_text_main

    for i in range(number_of_ans):
        bot.send_message("Введите вариант ответа №" + str(i + 1), chat_id)
        upd = bot.get_updates()
        text = bot.get_text(upd)
        positions.append(text)
        pl.add(text)

    opened_polls[str(poll_id)] = pl
    buttons = []
    i = 1
    for var in positions:
        buttons.append(bot.button_callback(var, str(poll_id) + "~~" + str(i), intent='default'))
        i += 1
    bot.send_message(poll_text_main, channel_id, attachments=bot.attach_buttons(buttons))
    return


def close_poll(chat_id):
    msg = "Выберите, какой опрос вы хотите закрыть:\n"
    i = 1
    tmp = []
    for poll in opened_polls:
        msg += ("№" + str(i) + ". " + opened_polls[poll].poll_name + "\n")
        i += 1
        tmp.append(poll)
    msg += "Обратите внимание, что после закрытия по опросу нельзя будет получить статистику"
    bot.send_message(msg, chat_id)
    num = get_integer(chat_id)
    del opened_polls[tmp[num - 1]]
    bot.send_message("Опрос был закрыт", chat_id)


def get_poll_statistics(chat_id):
    msg = "Выберите, по какому опросу вы хотите получить статистику:\n"
    i = 1
    tmp = []
    for poll in opened_polls:
        msg += ("№" + str(i) + ". " + opened_polls[poll].poll_name + "\n")
        i += 1
        tmp.append(poll)
    bot.send_message(msg, chat_id)
    num = get_integer(chat_id)
    msg = "Варианты:\n"
    i = 1
    for v in opened_polls[tmp[num - 1]].answers:
        msg += ("\"" + v[0] + "\": получено " + str(v[1]) + " голосов\n")
    bot.send_message(msg, chat_id)


def poll_callback(callback_id, callback_payload):
    bot.send_answer_callback(callback_id, "Ваш голос засчитан")
    fst_part = callback_payload.split("~~")[0]
    snd_part = callback_payload.split("~~")[1]
    if fst_part in opened_polls:
        opened_polls[fst_part].answers[int(snd_part) - 1][1] += 1
    else:
        bot.send_answer_callback(callback_id, "Опрос закрыт")
    return


def main():
    channel_id = -1

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
                    poll_callback(bot.get_callback_id(upd), bot.get_payload(upd))
            else:
                if upd_type == "bot_started":
                    bot.send_message(greeting_text, chat_id)
                elif upd_type == "message_created":
                    text = bot.get_text(upd)
                    if text == "/create_poll":
                        create_poll(chat_id, channel_id)
                        bot.get_updates()
                    elif text == "/close_poll":
                        close_poll(chat_id)
                    elif text == "/poll_statistics":
                        get_poll_statistics(chat_id)
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
