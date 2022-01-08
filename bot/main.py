from random import randint
import time
from datetime import datetime

import requests
from connect import *

from botapitamtam import BotHandler, logger
from token_file import token
from text import greeting_text, ask_for_perms_text, create_poll_intro, create_poll_ask_num

url = 'https://botapi.tamtam.chat/'
bot = BotHandler(token)
posts = {}  # dict: {channel_id, {timestamp, Post[]}}

commands = [{"name": '/create_poll', "description": "Создание опроса"},
            {"name": '/poll_statistics', "description": "Результаты опроса"},
            {"name": '/close_poll', "description": "Закрытие опроса"},
            {"name": '/get_posts_statistics', "description": "Получить статистику по постам"},
            {"name": '/clear_members', "description": "Удалить неактивных участников канала"},
            {"name": '/set_channel', "description": "Выбор канала для работы с ботом"}]


def convert_date_to_ms(date):
    """
        Перевод даты в стандартном формате в формат UNIX timestamp
     """
    dt_obj = datetime.strptime(date,
                               '%d.%m.%Y %H:%M:%S,%f')  # '20.12.2016 09:38:42,76' - формат даты
    ms = dt_obj.timestamp() * 1000
    return ms


def convert_ms_to_date(ms):
    """
    Перевод даты в формате UNIX timestamp в стандартный формат
    """
    date = datetime.fromtimestamp(ms // 1000)
    return date


def get_all_messages(channel_id, date_begin=None, date_end=None, num_of_posts=50):
    """
    Получает список всех сообщений в канале через запрос
    """
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


def get_fwd_message_id(update):
    """
    Дополнение к библиотеке
    Получение id пересланного сообщения
    :param update = результат работы метода get_update
    :return: возвращает, если это возможно, значение поля 'mid' пересланного боту сообщения
    """
    mid = None
    if update:
        if 'updates' in update.keys():
            upd = update['updates'][0]
        else:
            upd = update
        if 'message' in upd.keys():
            upd = upd['message']
            if 'link' in upd.keys():
                upd = upd['link']
                if 'message' in upd.keys():
                    mid = upd['message']['mid']
    return mid


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


def check_user_rights(user_id, channel_id, chat_id):
    """
    Проверка, что пользователь является админом канала
    Для бота работает аналогично, нужно передать, что user_id = get_bot_user_id
    """
    members = bot.get_chat_admins(channel_id)
    for mem in members:
        if mem['user_id'] == user_id:
            return True
    # bot.send_message("В настоящий момент вы не являетесь администратором данного канала", chat_id)
    return False


def set_channel(chat_id, user_id):
    """
    Определение канала, с которым бот будет работать.
    Важно: пользователь должен быть админом этого канала и бот должен иметь в нём права администратора, иначе
    канал не будет доступен для выбора.
    """
    chats = bot.get_all_chats()
    channels = []
    marker = 0
    while True:
        for chat in chats['chats']:
            if chat['type'] == 'channel' and check_user_rights(user_id, chat['chat_id'], chat_id) and check_user_rights(
                    bot.get_bot_user_id(), chat['chat_id'], chat_id):
                channels.append(chat)
        if 'marker' not in chats or chats['marker'] is None:
            break
        else:
            chats = bot.get_all_chats(marker=chats['marker'])
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
    """
    Обновление статистики по всем постам в канале: запускается как фоновой процесс
    """
    messages = get_all_messages(channel_id)
    for msg in messages:
        add_post(msg['timestamp'], msg['stat']['views'], msg['body'], channel_id)


def get_post_statictics(chat_id, channel_id, time_gap, fr, to):
    msg = "Перешлите боту сообщение, статистику по которому необходимо получить"
    mid = None
    while (True):
        upd = bot.get_updates()
        mid = get_fwd_message_id(upd)
        if mid is not None:
            break
    if time_gap == "day":
        res = get_post_stat_by_day_from_to(mid, fr, to)
    if time_gap == "week":
        res = get_post_stat_by_week_from_to(mid, fr, to)
    if time_gap == "month":
        res = get_post_stat_by_month_from_to(mid, fr, to)
    # прислать картинку


def get_ch_statictics(chat_id, channel_id, time_gap, fr, to):
    if time_gap == "day":
        res = get_post_stat_by_day_from_to(channel_id, fr, to)
    if time_gap == "week":
        res = get_post_stat_by_week_from_to(channel_id, fr, to)
    if time_gap == "month":
        res = get_post_stat_by_month_from_to(channel_id, fr, to)
    # прислать картинку


def get_channel_statistics(chat_id, channel_id):
    msg = "Выберите, хотите вы получить статистику по всему каналу или по определенному посту"
    buttons = [bot.button_callback("По каналу", "gcs~~channel", intent='default'),
               bot.button_callback("По посту", "gcs~~post", intent='default'),
               bot.button_callback("Выход", "gcs~~exit", intent='default')]

    bot.send_message(msg, chat_id, attachments=bot.attach_buttons(buttons))


def chat_callback(chat_id, channel_id, callback_id, callback_payload):
    command = callback_payload.split("~~")[0]
    if len(command) == 2:
        if command[0] == "gcs":
            if command[1] == "channel":
                gcs_get_stat(chat_id, channel_id, True)
            else:
                gcs_get_stat(chat_id, channel_id, False)
    if len(command) == 5:
        if command[0] == "gcstime":
            time_gap = command[1]
            fr = command[3]
            to = command[4]
            if command[2] == "ch":
                get_ch_statictics(chat_id, channel_id, time_gap, fr, to)
            else:
                get_post_statictics(chat_id, channel_id, time_gap, fr, to)


def gcs_get_stat(chat_id, channel_id, is_channel):
    """
    is_channel true if we need channel stat else false
    """
    msg = "Введите одну или две даты через пробел в формате ДД.ММ.ГГГГ, например 21.02.1930 \n" \
          "Первая дата - начало временного промежутка, вторая - конец (необязательный параметр) \n" \
          "Если вы хотите получить статистику за все доступное боту время, введите команду skip \n" \
          "Для выхода введите команду /exit"
    bot.send_message(msg, chat_id)
    upd = bot.get_updates()
    text = bot.get_text(upd)
    if text == "skip":
        gcs_params(chat_id, channel_id, is_channel)
    elif text == "exit":
        return
    elif len(text.split()) == 1:
        s = text.split('.')
        d = datetime(s[2], s[1], s[0])
        unixtime = time.mktime(d.timetuple())
        gcs_params(chat_id, channel_id, is_channel, int(unixtime))
    elif len(text.split()) == 2:
        s1 = text.split()[0].split('.')
        s2 = text.split()[1].split('.')
        d1 = datetime(s1[2], s1[1], s1[0])
        d2 = datetime(s2[2], s2[1], s2[0])
        unixtime1 = time.mktime(d1.timetuple())
        unixtime2 = time.mktime(d2.timetuple())
        gcs_params(chat_id, channel_id, is_channel, int(unixtime1), int(unixtime2))
    else:
        bot.send_message("Неправильный формат ввода", chat_id)


def gcs_params(chat_id, channel_id, is_channel, date1=0, date2=2147483647):
    msg = "Выберите временные отрезки, по которым вы хотите получать статистику"
    strings = ["gcstime~~day", "gcstime~~week", "gcstime~~month"]
    if is_channel:
        for s in strings:
            s += "~~ch"
    else:
        for s in strings:
            s += "~~pst"
    for s in strings:
        s += "~~" + str(date1) + "~~" + str(date2)

    buttons = [bot.button_callback("День", strings[0], intent='default'),
               bot.button_callback("Неделя", strings[1], intent='default'),
               bot.button_callback("Месяц", strings[2], intent='default')]
    bot.send_message(msg, chat_id, attachments=bot.attach_buttons(buttons))


def create_poll(chat_id, channel_id):
    """
    Создание опроса
    """
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
    """
    Закрытие опроса
    """
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
    """
    Получение результатов опроса: сколько голосов за каждый вариант. По запросу можно увидеть, кто голосовал
    """
    msg = "Выберите, по какому опросу вы хотите получить статистику:\n"
    i = 1
    tmp = []
    opened_polls = get_all_polls()
    for poll in opened_polls:
        msg += ("№" + str(i) + ". " + str(poll[1]) + "\n")
        i += 1
    bot.send_message(msg, chat_id)
    num = get_integer(chat_id)
    msg = "Варианты:\n"
    i = 1
    for v in get_poll_statistics_db(opened_polls[num - 1][0]):
        msg += ("\"" + str(v[0]) + "\": получено " + str(v[1]) + " голосов\n")
    bot.send_message(msg, chat_id)


def poll_callback(callback_id, callback_payload):
    """
    Реакция на клик пользователя по варианту ответа в опросе
    """
    opened_polls = get_all_polls()
    bot.send_answer_callback(callback_id, "Ваш голос засчитан")
    poll_id = callback_payload.split("~~")[0]
    num = callback_payload.split("~~")[1]
    rs = update_votes(poll_id, num)
    if rs is False:
        bot.send_answer_callback(callback_id, "Опрос закрыт")
    return


def clear_channel_followers(chat_id, channel_id):
    """
    Удаление неактивных подписчиков в канале
    """
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


# def send_timed_post(channel_id):


# def create_timed_post(chat_id):
# проверить, что пользователь админ


def main():
    channel_id = -1
    bot.edit_bot_info("TESTbot", commands=commands)

    while True:
        upd = bot.get_updates()
        if upd:
            chat_id = bot.get_chat_id(upd)
            chat_info = bot.get_chat(chat_id)
            upd_type = bot.get_update_type(upd)

            if not chat_info:
                continue
            elif chat_info['type'] == 'channel':
                if upd_type == "message_callback":
                    poll_callback(bot.get_callback_id(upd), bot.get_payload(upd))
            else:
                if channel_id == -1:
                    channel_id = set_channel(chat_id)
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
                    elif text == "/get_channel_statistics":
                        get_channel_statistics(channel_id, chat_id)
                    elif text == "/clear_members":
                        clear_channel_followers(chat_id, channel_id)
                    elif text == "/set_channel":
                        set_channel(chat_id)
                    else:
                        bot.send_message("Ваша команда не распознана", chat_id)
                if chat_info['type'] == 'chat':
                    if bot.get_chat_membership(chat_id)['is_admin'] is False:
                        bot.send_message(ask_for_perms_text, chat_id)
                    elif 'read_all_messages' not in bot.get_chat_membership(chat_id)['permissions']:
                        bot.send_message(ask_for_perms_text, chat_id)


if __name__ == '__main__':
    try:
        # connect()
        main()
        close()
    except KeyboardInterrupt:
        # disconnect()
        exit()
