from random import randint
from datetime import datetime
import matplotlib.pyplot as plt

import requests
from connect import *
from threading import Thread

from botapitamtam import BotHandler, logger
from token_file import token
from text import *

url = 'https://botapi.tamtam.chat/'
bot = BotHandler(token)

max_time = 2147483647


class State:
    def __init__(self):
        self.state = "empty"
        self.next = "empty"
        self.params = []
        self.cur_suggestion = 0


user_states = {}


# bot_state = State()

def reset_state(user_id):
    user_states[user_id].state = "empty"
    user_states[user_id].next = "empty"
    user_states[user_id].params = []


commands = [{"name": '/create_poll', "description": "Создание опроса"},
            {"name": '/poll_statistics', "description": "Результаты опроса"},
            {"name": '/close_poll', "description": "Закрытие опроса"},
            {"name": '/get_channel_views_statistics', "description": "Получить статистику по просмотрам на постах"},
            {"name": '/get_channel_members_statistics', "description": "Получить статистику по подписчикам канала"},
            {"name": '/clear_members', "description": "Удалить неактивных участников канала"},
            {"name": '/set_channel', "description": "Выбор канала для работы с ботом"},
            {"name": '/setup_timed', "description": "Отправка отложенного поста или опроса"},
            {"name": '/get_channel_mentions', "description": "Получение числа упоминаний канала"},
            {"name": '/exit', "description": "Возвращает бота в исходное состояние"}]


def draw_statistics(dates, param, text, filename):
    plt.bar(dates, param)
    plt.ylabel(text)
    plt.xlabel("Дата")
    plt.savefig(filename)
    plt.close()


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
        messages = None
    return messages


def get_message_by_id(msg_id):
    message = None
    method = 'messages/{}'.format(msg_id)
    params = [('access_token', token)]
    try:
        response = requests.get(url + method, params)
        if response.status_code == 200:
            message = response.json()
        else:
            logger.error("Error get chat info: {}".format(response.status_code))
            message = None
    except Exception as e:
        logger.error("Error connect get chat info: %s.", e)
        message = None
    if message is None:
        return None
    ans = [message['body']['text']]
    if 'attachments' in message['body']:
        ans.append(message['body']['attachments'])
    else:
        ans.append(None)
    return ans


def get_all_channel_members(channel_id, marker=None):
    """
    Дополнение к библиотеке. Возвращает список всех участников канала.
    """
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


def get_chat_by_link(link):
    """
    Дополнение к библиотеке. Получает ссылку на чат, возвращает chat_id
    """
    method = 'chats/{}'.format(link)
    params = {
        "access_token": token,
    }
    try:
        response = requests.get(url + method, params)
        if response.status_code == 200:
            chat = response.json()
        else:
            logger.error("Error get chat info: {}".format(response.status_code))
            chat = None
    except Exception as e:
        logger.error("Error connect get chat info: %s.", e)
        chat = None
    if chat is not None and "chat_id" in chat.keys():
        chat_id = chat["chat_id"]
    else:
        chat_id = None
    return chat_id


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


def get_integer(chat_id, user_id, maxval, upd):
    """
    Получение числа в корректном диапазоне от пользователя
    """
    number_of_ans = -1
    text = bot.get_text(upd)
    if text == '/exit':
        reset_state(user_id)
        return None
    try:
        number_of_ans = int(text)
    except ValueError:
        bot.send_message("Неправильно введено число. Попробуйте еще раз.", chat_id)
        return None

    if 0 < number_of_ans <= maxval:
        return number_of_ans
    else:
        bot.send_message("Вы ввели число вне допустимого диапазона. Попробуйте еще раз.", chat_id)


def get_date(chat_id, user_id, text):
    """
    Возвращает массив с одной или двумя датами в формате unix timestamp. Если пользователь вводит команду
    skip, возвращаются дефолтные значения - 0 и maxint (до 2030 года это бесконечность)
    """
    msg = "Неверно введен формат даты. Попробуйте еще раз."
    if text == "skip":
        return [0, max_time]
    elif text == "/exit":
        reset_state(user_id)
        return None
    elif len(text.split()) == 1:
        try:
            d1 = datetime.strptime(text, '%d.%m.%Y')
            return [d1, max_time]
        except ValueError:
            bot.send_message(msg, chat_id)
            return None
    elif len(text.split()) == 2:
        try:
            d1 = datetime.strptime(text.split()[0], '%d.%m.%Y')
            d2 = datetime.strptime(text.split()[1], '%d.%m.%Y')
            return [d1, d2]
        except ValueError:
            bot.send_message(msg, chat_id)
            return None
    else:
        bot.send_message(msg, chat_id)
        return None


def get_date_time(chat_id, user_id, text):
    msg = "Неверный формат даты и времени. Попробуйте еще раз"
    if text == '/exit':
        reset_state(user_id)
        return
    try:
        vdt = datetime.strptime(text, '%d.%m.%Y %H:%M')
    except ValueError:
        bot.send_message(msg, chat_id)
        return None
    vdt_sec = vdt.timestamp()
    return vdt_sec


def get_fwd(chat_id, upd):
    mid = get_fwd_message_id(upd)
    if mid is None:
        bot.send_message("Перешлите боту сообщение, по которому необходимо получить статистику, либо введите /exit",
                         chat_id)
    return mid


def check_user_rights(user_id, channel_id):
    """
    Проверка, что пользователь является админом канала
    """
    members = bot.get_chat_admins(channel_id)
    if members is not None:
        for mem in members['members']:
            if mem['user_id'] == user_id:
                return True
    return False


def set_channel_1(chat_id, user_id):
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
            if chat['type'] == 'channel' and check_user_rights(user_id, chat['chat_id']):
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
            i += 1
        bot.send_message(msg, chat_id)
        user_states[user_id].state = "get_integer"
        user_states[user_id].next = "set_channel_2"
        user_states[user_id].params = [len(channels), channels]


def set_channel_2(chat_id, user_id, channels, num):
    msg = "Канал был успешно установлен!"
    bot.send_message(msg, chat_id)
    set_active_channel(user_id, channels[num - 1]['chat_id'])
    if not exists_chat(channels[num - 1]['chat_id']):
        th = Thread(target=update_channel_statistics, args=[channels[num - 1]['chat_id']])
        th.start()
    reset_state(user_id)
    return channels[num - 1]['chat_id']


def add_suggested_post_1(chat_id, user_id):
    msg = get_link_text
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_link"
    user_states[user_id].next = "add_suggested_post_2"


def add_suggested_post_2(chat_id, channel_id, user_id):
    msg = "Пришлите боту пост, который вы хотели бы предложить"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_msg_id"
    user_states[user_id].next = "add_suggested_post_3"
    user_states[user_id].params.append(channel_id)


def add_suggested_post_3(chat_id, channel_id, msg_id, user_id):
    add_suggestion(channel_id, chat_id, msg_id, int(datetime.now().timestamp()))
    bot.send_message("Пост был предложен в канал", chat_id)
    reset_state(user_id)


def see_suggested_posts_1(chat_id, channel_id):
    posts = get_suggestions(channel_id)
    # что вообще дальше происходит? Есть массив постов и индекс, между постами можно перемещаться вперед назад и
    # публиковать
    length = len(posts)
    if length == 0:
        bot.send_message("Предложенных постов пока нет", chat_id)
        return
    buttons = [
        bot.button_callback("Опубликовать", "publish~~" + posts[0][2], intent='default')]
    if length > 1:
        buttons.append(bot.button_callback("Вперед", "next", intent='default'))
    bot.send_message("Пост 1/" + str(length), chat_id, attachments=bot.attach_buttons(buttons))
    info = get_message_by_id(posts[0][2])
    bot.send_message(info[0], chat_id, attachments=info[1])


def publish_suggested(channel_id, msg_id):
    info = get_message_by_id(msg_id)
    bot.send_message(info[0], channel_id, attachments=info[1])
    pop_one_suggestion(msg_id)


def print_suggested(chat_id, channel_id, user_id, i, tpe):
    if tpe == "next":
        i += 1
    elif tpe == "prev":
        i -= 1
    posts = get_suggestions(channel_id)
    if len(posts) == 0:
        bot.send_message("Предложенных постов пока нет", chat_id)
        return
    if i >= len(posts) or i < 0:
        i = 0
    user_states[user_id].cur_suggestion = i
    buttons = []
    if i > 0:
        buttons.append(bot.button_callback("Назад", "prev", intent='default'))
    buttons.append(
        bot.button_callback("Опубликовать", "publish~~" + posts[i][2], intent='default'))
    if i != len(posts) - 1:
        buttons.append(bot.button_callback("Вперед", "next", intent='default'))
    info = get_message_by_id(posts[i][2])
    bot.send_message(info[0], chat_id, attachments=info[1])


def update_channel_statistics(channel_id):
    """
    Обновление статистики просмотров по всем постам в канале и статистики подписчиков: запускается как фоновой
    процесс ежедневно
    """
    while True:
        messages = get_all_messages(channel_id)
        for msg in messages['messages']:
            add_post(int(datetime.now().timestamp()), msg['stat']['views'], msg['body']['mid'], channel_id)
        cnt = bot.get_chat(channel_id)['participants_count']
        add_chat_stat(int(datetime.now().timestamp()), cnt, channel_id)
        time.sleep(86400)


def send_stat_pic(chat_id, text, res):
    """
    Отправка сообщения с информацией о собранной статистике пользователю
    """
    dates = []
    param = []
    for r in res:
        dates.append(r[0].strftime("%m/%d/%Y"))
        param.append(int(r[1]))
    draw_statistics(dates, param, text, "tmp.png")
    a = bot.attach_image("tmp.png")
    bot.send_message("Статистика:", chat_id, attachments=a)


def get_members_statistics_1(chat_id, user_id):
    """
    Получение статистики прироста подписчиков в канале за различные промежутки времени
    """
    msg = get_stat_text
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_date"
    user_states[user_id].next = "gms_params"


def gms_params(chat_id, date1, date2):
    msg = "Выберите временные отрезки, по которым вы хотите получать статистику"
    strings = ["gms~~day", "gms~~week", "gms~~month"]
    for i in range(len(strings)):
        strings[i] += "~~" + str(date1) + "~~" + str(date2)

    buttons = [bot.button_callback("День", strings[0], intent='default'),
               bot.button_callback("Неделя", strings[1], intent='default'),
               bot.button_callback("Месяц", strings[2], intent='default')]
    bot.send_message(msg, chat_id, attachments=bot.attach_buttons(buttons))


def gms_get_stat(chat_id, channel_id, user_id, time_gap, fr, to):
    res = []
    if time_gap == "day":
        res = get_chat_stat_by_day_from_to(channel_id, fr, int(to))
    elif time_gap == "week":
        res = get_chat_stat_by_week_from_to(channel_id, fr, int(to))
    elif time_gap == "month":
        res = get_chat_stat_by_month_from_to(channel_id, fr, int(to))
    send_stat_pic(chat_id, "Количество новых пользователей", res)
    reset_state(user_id)


def get_post_statistics_1(chat_id, user_id, time_gap, fr, to):
    msg = "Перешлите боту сообщение, статистику по которому необходимо получить"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_fwd"
    user_states[user_id].next = "get_post_statistics_2"
    user_states[user_id].params = [time_gap, fr, to]


def get_post_statistics_2(chat_id, user_id, mid, time_gap, fr, to):
    res = []
    if time_gap == "day":
        res = get_post_stat_by_day_from_to(mid, fr, to)
    if time_gap == "week":
        res = get_post_stat_by_week_from_to(mid, fr, to)
    if time_gap == "month":
        res = get_post_stat_by_month_from_to(mid, fr, to)
    send_stat_pic(chat_id, "Количество просмотров", res)
    reset_state(user_id)


def get_ch_statictics(chat_id, channel_id, user_id, time_gap, fr, to):
    res = []
    if time_gap == "day":
        res = get_channel_stat_by_day_from_to(channel_id, fr, to)
    if time_gap == "week":
        res = get_channel_stat_by_week_from_to(channel_id, fr, to)
    if time_gap == "month":
        res = get_channel_stat_by_month_from_to(channel_id, fr, to)
    send_stat_pic(chat_id, "Количество просмотров", res)
    reset_state(user_id)


def get_channel_statistics(chat_id):
    """
    Вспомогательная функция для получения информации от пользователя (статистика по каналу)
    """
    msg = "Выберите, хотите вы получить статистику по всему каналу или по определенному посту"
    buttons = [bot.button_callback("По каналу", "gcs~~channel", intent='default'),
               bot.button_callback("По посту", "gcs~~post", intent='default'),
               bot.button_callback("Выход", "gcs~~exit", intent='default')]

    bot.send_message(msg, chat_id, attachments=bot.attach_buttons(buttons))


def get_post_top_1(chat_id, user_id):
    msg = "Выберите, сколько постов в рейтинге вы хотите вывести"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_integer"
    user_states[user_id].next = "get_post_top_2"


def get_post_top_2(chat_id, num, user_id):
    msg = "Выберите временной промежуток, за который будет выведен топ постов\n" + get_stat_text
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_date"
    user_states[user_id].next = "get_post_top_3"
    user_states[user_id].params.append(num)


def get_post_top_3(chat_id, channel_id, user_id, num, date1, date2):
    posts = get_top_from_channel(channel_id, num, date1, date2)
    i = 1
    for post in posts:
        bot.send_message("№" + str(i) + ". " + str(post[0]) + " просмотров", chat_id)
        bot.send_forward_message(None, post[1], chat_id)
        i += 1
    reset_state(user_id)


def chat_callback(chat_id, channel_id, user_id, callback_payload):
    """
    Обработка нажатий на кнопку, поступающих от пользователя
    """
    command = callback_payload.split("~~")
    if len(command) == 1:
        if command == "prev":
            print_suggested(chat_id, channel_id, user_id, user_states[user_id].cur_suggestion, "prev")
        elif command == "next":
            print_suggested(chat_id, channel_id, user_id, user_states[user_id].cur_suggestion, "next")
    if len(command) == 2:
        if command[0] == "gcs":
            if command[1] == "channel":
                gcs_get_stat_1(chat_id, True, user_id)
            else:
                gcs_get_stat_1(chat_id, False, user_id)
        elif command[0] == "setup":
            if command[1] == "create":
                create_timed_post_or_poll_1(chat_id, user_id)
            if command[1] == "delete":
                delete_timed_post_1(chat_id, user_id)
            if command[1] == "pin":
                pin_timed_post_1(chat_id, user_id)
            if command[1] == "unpin":
                unpin_timed_post_1(chat_id, user_id)
        elif command[0] == "publish":
            publish_suggested(channel_id, command[1])
    if len(command) == 3:
        if command[0] == "timed":
            if command[1] == "poll":
                create_poll_1(chat_id, channel_id, int(command[2]))
            else:
                create_timed_post_1(chat_id, int(command[2]), user_id)
    if len(command) == 4:
        if command[0] == "gms":
            gms_get_stat(chat_id, channel_id, user_id, command[1], command[2], command[3])
    if len(command) == 5:
        if command[0] == "gcstime":
            time_gap = command[1]
            fr = command[3]
            to = command[4]
            if command[2] == "ch":
                get_ch_statictics(chat_id, channel_id, user_id, time_gap, fr, to)
            else:
                get_post_statistics_1(chat_id, user_id, time_gap, fr, to)


def gcs_get_stat_1(chat_id, is_channel, user_id):
    """
    Получение статистики по одному или всем постам канала. По всем постам: если параметр is_channel = True
    """
    msg = get_stat_text
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_date"
    user_states[user_id].next = "gcs_params"
    user_states[user_id].params = [is_channel]


def gcs_params(chat_id, user_id, is_channel, date1, date2):
    msg = "Выберите временные отрезки, по которым вы хотите получать статистику"
    strings = ["gcstime~~day", "gcstime~~week", "gcstime~~month"]
    if is_channel:
        for i in range(len(strings)):
            strings[i] += "~~ch"
    else:
        for i in range(len(strings)):
            strings[i] += "~~pst"
    for i in range(len(strings)):
        strings[i] += "~~" + str(date1) + "~~" + str(date2)

    buttons = [bot.button_callback("День", strings[0], intent='default'),
               bot.button_callback("Неделя", strings[1], intent='default'),
               bot.button_callback("Месяц", strings[2], intent='default')]
    bot.send_message(msg, chat_id, attachments=bot.attach_buttons(buttons))
    reset_state(user_id)


def create_poll_1(chat_id, user_id, timeto=0):
    """
    Создание опроса
    """
    bot.send_message(create_poll_intro, chat_id)
    user_states[user_id].state = "get_text"
    user_states[user_id].next = "create_poll_2"
    user_states[user_id].params.append(timeto)


def create_poll_2(chat_id, user_id):
    bot.send_message(create_poll_ask_num, chat_id)
    user_states[user_id].state = "get_integer"
    user_states[user_id].next = "create_poll_3"


def create_poll_3(chat_id, user_id):
    poll_id = randint(0, 100000)
    user_states[user_id].params.append(poll_id)
    user_states[user_id].params.append(1)
    user_states[user_id].params.append([])
    bot.send_message("Введите вариант ответа №" + str(1), chat_id)
    user_states[user_id].state = "get_text"
    user_states[user_id].next = "create_poll_4"
    user_states[user_id].params[4] += 1


def create_poll_4(chat_id, channel_id, number_of_ans, i, user_id):
    if i <= number_of_ans:
        bot.send_message("Введите вариант ответа №" + str(i), chat_id)
        user_states[user_id].state = "get_text"
        user_states[user_id].next = "create_poll_4"
        user_states[user_id].params[4] += 1
    else:
        create_poll_5(chat_id, channel_id, user_id, user_states[user_id].params[1], user_states[user_id].params[3],
                      user_states[user_id].params[5],
                      user_states[user_id].params[0])


def create_poll_5(chat_id, channel_id, user_id, poll_text_main, poll_id, answers, timeto):
    add_poll(poll_id, poll_text_main, answers, channel_id)
    buttons = []
    i = 1
    for var in answers:
        buttons.append(bot.button_callback(var[0], str(poll_id) + "~~" + str(i), intent='default'))
        i += 1
    if timeto != 0:
        bot.send_message("Опрос будет опубликован в указанное время", chat_id)
    reset_state(user_id)
    th = Thread(target=send_poll_to_channel, args=(channel_id, poll_text_main, bot.attach_buttons(buttons), timeto))
    th.start()
    reset_state(user_id)
    return


def send_poll_to_channel(channel_id, text, attachments, timeto):
    time.sleep(timeto)
    bot.send_message(text, channel_id, attachments=attachments)


def close_poll_1(chat_id, channel_id, user_id):
    """
    Закрытие опроса
    """
    opened_polls = get_all_polls(channel_id)
    if len(opened_polls) == 0:
        msg = "В данный момент в канале нет открытых опросов\n"
        bot.send_message(msg, chat_id)
        return
    msg = "Выберите, какой опрос вы хотите закрыть:\n"
    i = 1
    for poll in opened_polls:
        msg += ("№" + str(i) + ". " + poll[1] + "\n")
        i += 1
    msg += "Обратите внимание, что после закрытия по опросу нельзя будет получить статистику"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_integer"
    user_states[user_id].next = "close_poll_2"
    user_states[user_id].params.append(opened_polls)


def close_poll_2(chat_id, user_id, opened_polls, num):
    db_close_poll(opened_polls[num - 1][0])
    bot.send_message("Опрос был успешно закрыт", chat_id)
    reset_state(user_id)


def get_poll_statistics_1(chat_id, channel_id, user_id):
    """
    Получение результатов опроса: сколько голосов за каждый вариант. По запросу можно увидеть, кто голосовал
    """
    msg = "Выберите, по какому опросу вы хотите получить статистику:\n"
    i = 1
    opened_polls = get_all_polls(channel_id)
    for poll in opened_polls:
        msg += ("№" + str(i) + ". " + str(poll[1]) + "\n")
        i += 1
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_integer"
    user_states[user_id].next = "get_poll_statistics_2"
    user_states[user_id].params.append(opened_polls)


def get_poll_statistics_2(chat_id, opened_polls, num, user_id):
    user_states[user_id].params.append(num)
    msg = "Варианты:\n"
    i = 1
    for v in get_poll_statistics_db(opened_polls[num - 1][0]):
        msg += ("№" + str(i) + "\"" + str(v[0]) + "\": получено " + str(v[1]) + " голосов\n")
        i += 1
    user_states[user_id].params.append(i)
    bot.send_message(msg, chat_id)
    msg = "Если вы хотите получить статистику по определенным вариантам, введите номер варианта," \
          " для окончания работы выберите команду /exit \n"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_integer"
    user_states[user_id].next = "get_poll_statistics_3"


def get_poll_statistics_3(chat_id, user_id, opened_polls, num, i):
    stat = who_voted(opened_polls[num - 1][0], i)
    msg = ' '
    for i in range(len(stat) - 1):
        msg += stat[i][1] + ', '
    if len(stat) > 0:
        msg += stat[len(stat) - 1][1]
    else:
        bot.send_message('За вариант №' + str(i) + ' никто не проголосовал', chat_id)
        return
    bot.send_message('За вариант №' + str(i) + ' проголосовали: ' + msg, chat_id)
    reset_state(user_id)


def poll_callback(callback_id, callback_payload, user_id, username):
    """
    Реакция на клик пользователя по варианту ответа в опросе
    """
    poll_id = callback_payload.split("~~")[0]
    num = callback_payload.split("~~")[1]
    rs = update_votes(poll_id, num, user_id, username)
    if rs is False:
        bot.send_answer_callback(callback_id, "Вы уже голосовали в этом опросе или опрос закрыт")
    else:
        bot.send_answer_callback(callback_id, "Ваш голос засчитан")
    return


def clear_channel_followers_1(chat_id, user_id):
    """
    Удаление неактивных подписчиков в канале
    """
    bot.send_message("Укажите, какое время (в днях) пользователь должен быть не активным, чтобы быть удаленным ботом",
                     chat_id)
    user_states[user_id].state = "get_integer"
    user_states[user_id].next = "clear_channel_followers_2"


def clear_channel_followers_2(chat_id, user_id, channel_id, duration):
    members = get_all_channel_members(channel_id)
    while True:
        if members is None:
            break
        for mem in members['members']:
            if int(datetime.now().timestamp()) - duration * 24 * 60 * 60 > mem['last_activity_time']:
                bot.remove_member(channel_id, mem['user_id'])
        if 'marker' not in members:
            break
        else:
            members = get_all_channel_members(channel_id, marker=members['marker'])
    bot.send_message("Пользователи были удалены", chat_id)
    reset_state(user_id)


def send_timed_post(channel_id, timeto, text, attachments):
    """
    Непосредственно отложенная отправка поста
    """
    time.sleep(timeto)
    bot.send_message(text, channel_id, attachments=attachments)


def create_timed_post_or_poll_1(chat_id, user_id):
    """
    Основная функция для создания отложенного поста, запускается первой. Содержит пользовательский интерфейс.
    """
    msg = "Введите дату и время, в которое пост будет выложен в канал в формате ДД.ММ.ГГГГ ЧЧ:ММ, например" \
          " 11.10.2024 16:33 \n" \
          "Для выхода выберите команду /exit"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_date_time"
    user_states[user_id].next = "create_timed_post_or_poll_2"


def create_timed_post_or_poll_2(chat_id, user_id, vdt_sec):
    dt_now = datetime.now().timestamp()
    timeto = int(vdt_sec) - int(dt_now)
    if timeto < 0:
        timeto = 0

    msg = "Вы хотите опубликовать пост или опрос?"
    buttons = [bot.button_callback("Пост", "timed~~post~~" + str(timeto), intent='default'),
               bot.button_callback("Опрос", "timed~~poll~~" + str(timeto), intent='default')]
    bot.send_message(msg, chat_id, attachments=bot.attach_buttons(buttons))
    reset_state(user_id)


def create_timed_post_1(chat_id, timeto, user_id):
    msg = "Отправьте боту пост, который вы хотите опубликовать в канале"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_msg"
    user_states[user_id].next = "create_timed_post_2"
    user_states[user_id].params.append(timeto)


def create_timed_post_2(chat_id, channel_id, user_id, timeto, text, atch):
    bot.send_message("Ваш пост будет опубликован в указанное время", chat_id)
    th = Thread(target=send_timed_post, args=(channel_id, timeto, text, atch))
    th.start()
    reset_state(user_id)


def delete_timed_post_1(chat_id, user_id):
    msg = "Перешлите боту сообщение, которое хотите удалить.\n" \
          "Для выхода выберите команду /exit"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_fwd"
    user_states[user_id].next = "delete_timed_post_2"


def delete_timed_post_2(chat_id, post_id, user_id):
    msg = "Введите дату и время, в которое пост будет удален в канал в формате ДД.ММ.ГГГГ ЧЧ:ММ, например" \
          " 11.10.2024 16:33 \n" \
          "Для выхода выберите команду /exit"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_date_time"
    user_states[user_id].next = "delete_timed_post_3"
    user_states[user_id].params.append(post_id)


def delete_timed_post_3(chat_id, channel_id, post_id, dtm):
    dt_now = datetime.now().timestamp()
    timeto = int(dtm) - int(dt_now)
    if timeto < 0:
        timeto = 0
    bot.send_message("Ваш пост будет удален в указанное время", chat_id)
    th = Thread(target=delete_post, args=(channel_id, timeto, post_id))
    th.start()


def delete_post(timeto, post_id):
    time.sleep(timeto)
    bot.delete_message(post_id)


def pin_timed_post_1(chat_id, user_id):
    msg = "Перешлите боту сообщение, которое хотите закрепить.\n" \
          "Для выхода выберите команду /exit"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_fwd"
    user_states[user_id].next = "pin_timed_post_2"


def pin_timed_post_2(chat_id, post_id, user_id):
    msg = "Введите дату и время, в которое пост будет удален в канал в формате ДД.ММ.ГГГГ ЧЧ:ММ, например" \
          " 11.10.2024 16:33 \n" \
          "Для выхода выберите команду /exit"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_date_time"
    user_states[user_id].next = "pin_timed_post_3"
    user_states[user_id].params.append(post_id)


def pin_timed_post_3(chat_id, channel_id, post_id, dtm):
    dt_now = datetime.now().timestamp()
    timeto = int(dtm) - int(dt_now)
    if timeto < 0:
        timeto = 0
    bot.send_message("Ваш пост будет закреплен в указанное время", chat_id)
    th = Thread(target=pin_post, args=(channel_id, timeto, post_id))
    th.start()


def pin_post(channel_id, timeto, post_id):
    time.sleep(timeto)
    bot.pin_message(channel_id, post_id)


def unpin_timed_post_1(chat_id, user_id):
    msg = "Введите дату и время, в которое закрепленный пост будет откреплен в формате ДД.ММ.ГГГГ ЧЧ:ММ, например" \
          " 11.10.2024 16:33 \n" \
          "Для выхода выберите команду /exit"
    bot.send_message(msg, chat_id)
    user_states[user_id].state = "get_date_time"
    user_states[user_id].next = "unpin_timed_post_2"


def unpin_timed_post_2(chat_id, channel_id, dtm):
    dt_now = datetime.now().timestamp()
    timeto = int(dtm) - int(dt_now)
    if timeto < 0:
        timeto = 0
    bot.send_message("В указанное время произойдет открепление закрепленного поста", chat_id)
    th = Thread(target=unpin_post, args=(channel_id, timeto))
    th.start()


def unpin_post(channel_id, timeto):
    time.sleep(timeto)
    bot.unpin_message(channel_id)


def setup_timed(chat_id):
    msg = "Выберите, хотите вы создать отложенный пост/опрос, удалить пост или закрепить пост"
    buttons = [bot.button_callback("Создание", "setup~~create", intent='default'),
               bot.button_callback("Удаление", "setup~~delete", intent='default'),
               bot.button_callback("Закрепление", "setup~~pin", intent='default'),
               bot.button_callback("Открепление", "setup~~unpin", intent='default')]
    bot.send_message(msg, chat_id, attachments=bot.attach_buttons(buttons))


def channel_mentions_info(chat_id, channel_id):
    msg = "Данный канал был упомянут в "
    msg += str(get_channel_mentions(channel_id))
    msg += " источниках"
    bot.send_message(msg, chat_id)


def main():
    channel_id = -1
    bot.edit_bot_info("TESTbot", commands=commands)

    while True:
        upd = bot.get_updates()
        if upd:
            chat_id = bot.get_chat_id(upd)
            chat_info = bot.get_chat(chat_id)
            upd_type = bot.get_update_type(upd)
            user_id = bot.get_user_id(upd)
            if user_id not in user_states:
                user_states[user_id] = State()
            if not chat_info:
                continue
            elif chat_info['type'] == 'channel' and upd_type == "message_callback":
                poll_callback(bot.get_callback_id(upd), bot.get_payload(upd), user_id, bot.get_name(upd))
            else:
                if upd_type == "bot_started":
                    bot.send_message(greeting_text_0, chat_id)
                    set_active_channel(user_id, -1)
                channel_id = get_active_channel(user_id)
                if upd_type == "message_created":
                    text = bot.get_text(upd)
                    if text == "/set_channel":
                        set_channel_1(chat_id, user_id)
                        if channel_id != -1:
                            bot.send_message(greeting_text_1, chat_id)
                    elif text == "/suggest":
                        add_suggested_post_1(chat_id, user_id)
                    elif channel_id == -1 and user_states[user_id].next != "set_channel_2" and \
                            user_states[user_id].next != "add_suggested_post_2" and user_states[
                        user_id].next != "add_suggested_post_3":
                        bot.send_message("Пожалуйста, установите канал для работы с ботом", chat_id)
                        continue
                    elif text == "/create_poll":
                        create_poll_1(chat_id, channel_id, user_id)
                    elif text == "/close_poll":
                        close_poll_1(chat_id, channel_id, user_id)
                    elif text == "/poll_statistics":
                        get_poll_statistics_1(chat_id, channel_id, user_id)
                    elif text == "/get_channel_views_statistics":
                        get_channel_statistics(chat_id)
                    elif text == "/get_channel_members_statistics":
                        get_members_statistics_1(chat_id, user_id)
                    elif text == "/get_posts_top":
                        get_post_top_1(chat_id, user_id)
                    elif text == "/clear_members":
                        clear_channel_followers_1(chat_id, user_id)
                    elif text == "/setup_timed":
                        setup_timed(chat_id)
                    elif text == "/get_channel_mentions":
                        channel_mentions_info(chat_id, channel_id)
                    elif text == "/see_suggestions":
                        see_suggested_posts_1(chat_id, channel_id)
                    elif text == "/exit":
                        reset_state(user_id)
                    else:
                        # обработка в зависимости от состояния бота
                        if user_states[user_id].state == "empty":
                            bot.send_message("Ваша команда не распознана", chat_id)
                        elif user_states[user_id].state == "get_integer":
                            if user_states[user_id].next == "set_channel_2":
                                ans = get_integer(chat_id, user_id, user_states[user_id].params[0], upd)
                                if ans is not None:
                                    set_channel_2(chat_id, user_id, user_states[user_id].params[1], ans)
                                    reset_state(user_id)
                            elif user_states[user_id].next == "create_poll_3":
                                ans = get_integer(chat_id, user_id, 100000, upd)
                                if ans is not None:
                                    user_states[user_id].params.append(ans)
                                    create_poll_3(chat_id, user_id)
                            elif user_states[user_id].next == "close_poll_2":
                                num = get_integer(chat_id, user_id, len(user_states[user_id].params[0]), upd)
                                if num is not None:
                                    close_poll_2(chat_id, user_id, user_states[user_id].params[0], num)
                            elif user_states[user_id].next == "get_poll_statistics_2":
                                num = get_integer(chat_id, user_id, len(user_states[user_id].params[0]), upd)
                                if num is not None:
                                    get_poll_statistics_2(chat_id, user_states[user_id].params[0], num, user_id)
                            elif user_states[user_id].next == "get_poll_statistics_3":
                                num = get_integer(chat_id, user_id, user_states[user_id].params[2], upd)
                                if num is not None:
                                    get_poll_statistics_3(chat_id, user_id, user_states[user_id].params[0],
                                                          user_states[user_id].params[1], num)
                            elif user_states[user_id].next == "clear_channel_followers_2":
                                num = get_integer(chat_id, user_id, 10000000000, upd)
                                if num is not None:
                                    clear_channel_followers_2(chat_id, user_id, channel_id, num)
                            elif user_states[user_id].next == "get_post_top_2":
                                num = get_integer(chat_id, user_id, 100, upd)
                                if num is not None:
                                    get_post_top_2(chat_id, num, user_id)
                        elif user_states[user_id].state == "get_text":
                            if user_states[user_id].next == "create_poll_2":
                                user_states[user_id].params.append(text)
                                create_poll_2(chat_id, user_id)
                            elif user_states[user_id].next == "create_poll_4":
                                user_states[user_id].params[5].append([text, 0])
                                create_poll_4(chat_id, channel_id, user_states[user_id].params[2],
                                              user_states[user_id].params[4], user_id)
                        elif user_states[user_id].state == "get_date":
                            dates = get_date(chat_id, user_id, text)
                            if dates is not None:
                                if user_states[user_id].next == "gms_params":
                                    gms_params(chat_id, dates[0], dates[1])
                                elif user_states[user_id].next == "gcs_params":
                                    gcs_params(chat_id, user_id, user_states[user_id].params[0], dates[0],
                                               dates[1])
                                elif user_states[user_id].next == "get_post_top_3":
                                    get_post_top_3(chat_id, channel_id, user_id, user_states[user_id].params[0],
                                                   dates[0], dates[1])
                        elif user_states[user_id].state == "get_date_time":
                            date_time = get_date_time(chat_id, user_id, text)
                            if date_time is not None:
                                if user_states[user_id].next == "create_timed_post_or_poll_2":
                                    create_timed_post_or_poll_2(chat_id, user_id, date_time)
                                elif user_states[user_id].next == "delete_timed_post_3":
                                    delete_timed_post_3(chat_id, channel_id, user_states[user_id].params[0], date_time)
                                elif user_states[user_id].next == "pin_timed_post_3":
                                    pin_timed_post_3(chat_id, channel_id, user_states[user_id].params[0], date_time)
                                elif user_states[user_id].next == "unpin_timed_post_2":
                                    unpin_timed_post_2(chat_id, channel_id, date_time)
                        elif user_states[user_id].state == "get_fwd":
                            mid = get_fwd(chat_id, upd)
                            if mid is not None:
                                if user_states[user_id].next == "get_post_statistics_2":
                                    get_post_statistics_2(chat_id, user_id, mid,
                                                          user_states[user_id].params[0],
                                                          user_states[user_id].params[1],
                                                          user_states[user_id].params[2])
                                elif user_states[user_id].next == "delete_timed_post_2":
                                    delete_timed_post_2(chat_id, mid, user_id)
                                elif user_states[user_id].next == "pin_timed_post_2":
                                    pin_timed_post_2(chat_id, mid, user_id)
                        elif user_states[user_id].state == "get_link":
                            link = bot.get_text(upd)
                            if user_states[user_id].next == "add_suggested_post_2":
                                sug_channel_id = get_chat_by_link(link)
                                if sug_channel_id is not None:
                                    add_suggested_post_2(chat_id, sug_channel_id, user_id)
                        elif user_states[user_id].state == "get_msg":
                            text = bot.get_text(upd)
                            atch = bot.get_attachments(upd)
                            if user_states[user_id].next == "create_timed_post_2":
                                create_timed_post_2(chat_id, channel_id, user_id, user_states[user_id].params[0], text,
                                                    atch)
                        elif user_states[user_id].state == "get_msg_id":
                            msg_id = bot.get_message_id(upd)
                            if user_states[user_id].next == "add_suggested_post_3":
                                add_suggested_post_3(chat_id, user_states[user_id].params[0], msg_id, user_id)
                elif upd_type == 'message_callback':
                    chat_callback(chat_id, user_id, bot.get_callback_id(upd), bot.get_payload(upd))
                if chat_info['type'] == 'chat':
                    if bot.get_chat_membership(chat_id)['is_admin'] is False:
                        bot.send_message(ask_for_perms_text, chat_id)
                    elif 'read_all_messages' not in bot.get_chat_membership(chat_id)['permissions']:
                        bot.send_message(ask_for_perms_text, chat_id)


if __name__ == '__main__':
    try:
        # connect()
        # create_all()
        main()
        close()
    except KeyboardInterrupt:
        # disconnect()
        exit()
