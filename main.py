from random import randint
from datetime import datetime

import requests
from connect import *

from botapitamtam import BotHandler, logger
from token_file import token
from text import *

url = 'https://botapi.tamtam.chat/'
bot = BotHandler(token)
posts = {}  # dict: {channel_id, {timestamp, Post[]}}

commands = [{"name": '/create_poll', "description": "Создание опроса"},
            {"name": '/close_poll', "description": "Закрытие опроса"},
            {"name": '/poll_statistics', "description": "Результаты опроса"},
            {"name": '/get_posts_statistics', "description": "Получить статистику по постам"},
            {"name": '/clear_members', "description": "Удалить неактивных участников канала"}]


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


def convert_date_to_ms(date):
    dt_obj = datetime.strptime(date,
                               '%d.%m.%Y %H:%M:%S,%f')  # '20.12.2016 09:38:42,76' - формат даты
    ms = dt_obj.timestamp() * 1000
    return ms


def convert_ms_to_date(ms):
    date = datetime.fromtimestamp(ms // 1000)
    return date


def get_all_messages(channel_id, date_begin=None, date_end=None, num_of_posts=50):
    messages = []
    method = 'messages'
    params_0 = [
        ('access_token', token),
        ('chat_id', channel_id)]
    if date_begin:
        params_0.append(('from', convert_date_to_ms(date_begin)))
    if date_end:
        params_0.append(('to', convert_date_to_ms(date_end)))
    params_0.append(('count', num_of_posts))
    params = tuple(params_0)
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


def get_all_channel_members(channel_id, marker=None):
    method = 'chats/{}'.format(channel_id) + '/members'
    params = {
        "access_token": token,
        "count": 100
    }
    if marker:
        params["marker"] = marker
    try:
        response = requests.get(url + method, params=params)
        if response.status_code == 200:
            members = response.json()
        else:
            logger.error("Error get members: {}".format(response.status_code))
            members = None
    except Exception as e:
        logger.error("Error connect get members: %s.", e)
        members = None
    return members


def get_integer(chat_id):
    number_of_ans = -1
    while 1:
        upd = bot.get_updates()
        text = bot.get_text(upd)
        try:
            number_of_ans = int(text)
        except ValueError:
            bot.send_message("Неправильно введено число. Попробуйте еще раз.", chat_id)
            continue

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


def update_channel_statistics(channel_id):
    messages = get_all_messages(channel_id)
    for msg in messages:
        add_post(msg['timestamp'], msg['stat']['views'])


def get_channel_statistics(chat_id, channel_id, num_of_posts=100):
    messages = get_all_messages(channel_id, num_of_posts)
    bot_msg = "Выберите, статистику за какой промежуток вы хотите получить:\n 1. Последний день\n" \
              "2. Последняя неделя\n" \
              "3. Последний месяц\n"
    bot.send_message(bot_msg, chat_id)
    variant = get_integer(chat_id)
    if variant == 1:
        get_post_stat_by_day_db()
    return messages


def get_posts_statistics(channel_id, chat_id):
    bot_msg = "Для того, чтобы получить статистику по просмотрам, выберите даты первого и последнего поста в выборке:"
    # база данных
    bot.send_message(bot_msg, chat_id)
    # принять два числа и опять бд
    messages = get_channel_statistics(channel_id, 1, 2, 50)
    # вызвать функцию рисования графика


def create_poll(chat_id, channel_id):
    bot.send_message(create_poll_intro, chat_id)
    upd = bot.get_updates()
    poll_text_main = bot.get_text(upd)
    bot.send_message(create_poll_ask_num, chat_id)
    number_of_ans = get_integer(chat_id)

    poll_id = randint(0, 100000)

    answers = []

    for i in range(number_of_ans):
        bot.send_message("Введите вариант ответа №" + str(i + 1), chat_id)
        upd = bot.get_updates()
        text = bot.get_text(upd)
        answers.append([text, 0])

    add_poll(poll_id, poll_text_main, answers)
    buttons = []
    i = 1
    for var in answers:
        buttons.append(bot.button_callback(var[0], str(poll_id) + "~~" + str(i), intent='default'))
        i += 1
    bot.send_message(poll_text_main, channel_id, attachments=bot.attach_buttons(buttons))
    return


def close_poll(chat_id):
    opened_polls = get_all_polls()
    if len(opened_polls) == 0:
        msg = "В данный момент в канале нет открытых опросов\n"
        bot.send_message(msg, chat_id)
        return
    msg = "Выберите, какой опрос вы хотите закрыть:\n"
    i = 1
    tmp = []
    for poll in opened_polls:
        msg += ("№" + str(i) + ". " + poll[1] + "\n")
        i += 1
    msg += "Обратите внимание, что после закрытия по опросу нельзя будет получить статистику"
    bot.send_message(msg, chat_id)
    num = get_integer(chat_id)
    db_close_poll(opened_polls[num - 1][0])
    bot.send_message("Опрос был закрыт", chat_id)


def get_poll_statistics(chat_id):
    msg = "Выберите, по какому опросу вы хотите получить статистику:\n"
    i = 1
    tmp = []
    opened_polls = get_all_polls()
    for poll in opened_polls:
        msg += ("№" + str(i) + ". " + poll['name'] + "\n")
        i += 1
    bot.send_message(msg, chat_id)
    num = get_integer(chat_id)
    msg = "Варианты:\n"
    i = 1
    for v in get_poll_statistics_db(opened_polls[num-1][0]):
        msg += ("\"" + v[0] + "\": получено " + str(v[1]) + " голосов\n")
    bot.send_message(msg, chat_id)


def poll_callback(callback_id, callback_payload):
    opened_polls = get_all_polls()
    bot.send_answer_callback(callback_id, "Ваш голос засчитан")
    poll_id = callback_payload.split("~~")[0]
    num = callback_payload.split("~~")[1]
    rs = update_votes(poll_id, num)
    if rs is False:
        bot.send_answer_callback(callback_id, "Опрос закрыт")
    return


def clear_channel_followers(chat_id, channel_id):
    bot.send_message("Укажите, какое время (в днях) пользователь должен быть не активным, чтобы быть удаленным ботом",
                     chat_id)
    duration = get_integer(chat_id)
    members = get_all_channel_members(channel_id)
    while True:
        if members is None:
            break
        for mem in members['members']:
            print("ура")
            if int(datetime.now().timestamp() * 1000) - duration * 24 * 60 * 60 * 1000 > mem['last_activity_time']:
                bot.remove_member(channel_id, mem['user_id'])
        if 'marker' not in members:
            break
        else:
            members = get_all_channel_members(channel_id, marker=members['marker'])

    bot.send_message("Пользователи были удалены", chat_id)


def main():
    channel_id = -1
    bot.edit_bot_info("TESTbot", commands=commands)

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
                    elif text == "/get_posts_statistics":
                        get_posts_statistics(channel_id, chat_id)
                    elif text == "/clear_members":
                        clear_channel_followers(chat_id, channel_id)
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
        close()
    except KeyboardInterrupt:
        exit()
