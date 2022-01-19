import time

import psycopg2
from config import host, user, password, db_name
from time import time as tm

time.sleep(10)
conn = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)
conn.autocommit = True
cur = conn.cursor()


def create_channel_list():
    """
    Private
    channel - user
    """
    cur.execute(
        "CREATE TABLE user_active_channel (user_id BIGINT, "
        "chat_id BIGINT);")


def get_active_channel(user_id: int):
    cur.execute(f"SELECT chat_id FROM user_active_channel WHERE user_id={user_id};")
    res = cur.fetchone()
    if res == None:
        return None
    return res[0]


def check_user(user_id: int):
    """
    Private
    """
    cur.execute(f"SELECT EXISTS(SELECT 1 FROM user_active_channel WHERE user_id={user_id});")
    return cur.fetchone()[0]


def set_active_channel(user_id: int, chat_id: int):
    if check_user(user_id):
        cur.execute(f"UPDATE user_active_channel SET chat_id={chat_id} WHERE user_id={user_id};")
        return

    cur.execute("INSERT INTO user_active_channel (user_id, chat_id) VALUES (%s, %s);",
                (user_id, chat_id))


def create_user_stat():
    """
    Private
    Create table for users.
    """
    cur.execute(
        "CREATE TABLE user_stat (timestamp BIGINT, "
        "user_cnt BIGINT, chat_id BIGINT);")


def exists_chat(chat_id: int):
    cur.execute(f"SELECT EXISTS(SELECT 1 FROM user_stat WHERE chat_id={chat_id});")
    return cur.fetchone()[0]


def get_all_chats():
    """
    returns all chat id's
    """
    cur.execute("SELECT DISTINCT chat_id FROM user_stat;")

    res = []
    tmp = cur.fetchone()
    while tmp != None:
        res.append(tmp[0])
        tmp = cur.fetchone()

    return res


def add_chat_stat(time: int, count: int, chat_id: int):
    """
    give time and chat_id and cnt to write stat.
    """
    cur.execute(f"SELECT SUM(user_cnt) AS view FROM user_stat WHERE chat_id='{chat_id}';")

    tmp = cur.fetchone()[0]
    if tmp is None:
        old = 0
        cur.execute("INSERT INTO user_stat (timestamp, user_cnt, chat_id) VALUES (%s, %s, %s);",
                    (time, count, chat_id))
    else:
        old = int(tmp)

    cur.execute("INSERT INTO user_stat (timestamp, user_cnt, chat_id) VALUES (%s, %s, %s);",
                (time, count - old, chat_id))


def get_chat_stat_by_day_from_to(chat_id: int, fr=0, to=2147483647):
    """
    TODO
    """
    return get_chat_stat(chat_id, 'day', fr, to)


def get_chat_stat_by_week_from_to(chat_id: int, fr=0, to=2147483647):
    """
    TODO
    """
    return get_chat_stat(chat_id, 'week', fr, to)


def get_chat_stat_by_month_from_to(chat_id: int, fr=0, to=2147483647):
    """
    TODO
    """
    return get_chat_stat(chat_id, 'month', fr, to)


def get_chat_stat(chat_id: int, wtf: str, fr: int, to: int):
    """
    Private
    user_stat by wtf.
    """
    cur.execute(
        f"SELECT DATE_TRUNC('{wtf}',to_timestamp(timestamp)::date) AS month, SUM(user_cnt) AS user_sum FROM user_stat WHERE chat_id={chat_id} GROUP BY month ORDER BY month;")

    res = []
    tmp = cur.fetchone()
    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def create_post_stat():
    """
    Private
    Call to create table for posts.
    """
    cur.execute(
        "CREATE TABLE post_stat (timestamp BIGINT, "
        "time BIGINT, views BIGINT, message_id varchar);")


def add_post(timestamp: int, views: int, message_id: str, chat_id: int):
    """
    Add's note about post at this moment.
    """
    cur.execute(f"SELECT SUM(views) AS view FROM post_stat WHERE message_id='{message_id}';")

    tmp = cur.fetchone()[0]
    if tmp is None:
        old = 0
        add_message(chat_id, message_id)
    else:
        old = int(tmp)

    cur.execute("INSERT INTO post_stat (timestamp, time, views, message_id) VALUES (%s, %s, %s, %s);",
                (timestamp, tm(), views - old, message_id))


def get_post_stat_by_day_db(id: int):
    """
    Needs post id, returns post views last day.
    """
    return get_post_stat_by_db(id, 'day')


def get_post_stat_by_week_db(id: int):
    """
     Needs post id, returns post views last week.
    """
    return get_post_stat_by_db(id, 'week')


def get_post_stat_by_month_db(id: int):
    """
    Needs post id, returns post views last month.
    """
    return get_post_stat_by_db(id, 'month')


def get_channel_stat_by_day_from_to(chat_id: int, fr=0, to=2147483647):
    """
    Views stat for all posts from channel with precision day.
    You can add 'from' and 'to'.
    """
    return get_channel_stat_from_to(chat_id, 'day', fr, to)


def get_channel_stat_by_week_from_to(chat_id: int, fr=0, to=2147483647):
    """
    Views stat for all posts from channel with precision week.
    You can add 'from' and 'to'.
    """
    return get_channel_stat_from_to(chat_id, 'week', fr, to)


def get_channel_stat_by_month_from_to(chat_id: int, fr=0, to=2147483647):
    """
    Views stat for all posts from channel with precision month.
    You can add 'from' and 'to'.
    """
    return get_channel_stat_from_to(chat_id, 'month', fr, to)


def get_channel_stat_from_to(chat_id: int, wtf: str, fr: int, to: int):
    """
    Private
    Returns count of new views between fr and to in channel, with precision wtf.
    """
    cur.execute(
        f"SELECT DATE_TRUNC('{wtf}',to_timestamp(time)::date) AS month, SUM(views) AS views_sum FROM post_stat INNER JOIN channel_post ON post_stat.message_id=channel_post.message_id WHERE channel_post.chat_id={chat_id} AND post_stat.time BETWEEN {fr} AND {to} GROUP BY month ORDER BY month;")

    res = []
    tmp = cur.fetchone()
    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def get_post_stat_by_day_from_to(message_id: str, fr=0, to=2147483647):
    """
    Returns count of new views between fr and to for post, with precision day.
    """
    return get_post_stat_from_to(message_id, 'day', fr, to)


def get_post_stat_by_week_from_to(message_id: str, fr=0, to=2147483647):
    """
    Returns count of new views between fr and to for post, with precision week.
    """
    return get_post_stat_from_to(message_id, 'week', fr, to)


def get_post_stat_by_month_from_to(message_id: str, fr=0, to=2147483647):
    """
    Returns count of new views between fr and to for post, with precision month.
    """
    return get_post_stat_from_to(message_id, 'month', fr, to)


def get_post_stat_from_to(message_id: str, wtf: str, fr, to):
    """
    Private
    Returns count of new views between fr and to for post, with precision wtf.
    """
    cur.execute(
        f"SELECT DATE_TRUNC('day',to_timestamp(time)::date) AS month, SUM(views) AS views_sum FROM post_stat WHERE message_id='{message_id}' AND time BETWEEN {fr} AND {to} GROUP BY month ORDER BY month;")

    res = []
    tmp = cur.fetchone()
    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def get_post_stat_by_db(id: int, wtf: str):
    """
    Private function to not copy paste.
    """
    cur.execute(
        f"SELECT DATE_TRUNC('{wtf}',to_timestamp(time)::date) AS month, SUM(views) AS views_sum FROM post_stat INNER JOIN channel_post ON post_stat.chat_id=channel_post.chat_id GROUP BY month;")

    res = []
    tmp = cur.fetchone()
    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def create_channel_to_post():
    """
    Private
    Creates table from channel to post_id
    """
    cur.execute(
        "CREATE TABLE channel_post (chat_id BIGINT, "
        "message_id varchar);")


def add_message(chat_id: int, message_id: str):
    """
    Private
    Add's message to table channel-post.
    """
    cur.execute("INSERT INTO channel_post (chat_id, message_id) VALUES (%s, %s)", (chat_id, message_id))


def create_poll_info():
    """
    Private
    Create table for poll.
    """
    cur.execute(
        "CREATE TABLE poll_info (id BIGINT PRIMARY KEY NOT NULL, "
        "poll_name varchar, answers varchar ARRAY, voted BIGINT ARRAY, closed boolean, chat_id BIGINT);")


def create_poll_voted():
    """
    Private
    Create table for voted.
    """
    cur.execute(
        "CREATE TABLE poll_voted (user_id BIGINT, "
        "name varchar, id BIGINT, index BIGINT);")


def who_voted(id: int, index: int):
    """
    Returns array of voted for this answer.
    [(user_id: int, name: str)]
    """
    cur.execute(f"SELECT user_id, name FROM poll_voted WHERE id={id} AND index={index}")

    res = []
    tmp = cur.fetchone()

    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def is_voted(chel_id: int, id: int):
    """
    Private, but u can use it.
    """
    cur.execute(f"SELECT EXISTS(SELECT 1 FROM poll_voted WHERE id={id} AND user_id={chel_id});")
    return cur.fetchone()[0]


def add_vote(chel_id: int, name: str, poll_id: int, index: int):
    """
    Private
    Mark chel as voted.
    """
    cur.execute("INSERT INTO poll_voted (user_id, name, id, index) VALUES (%s, %s, %s, %s);",
                (chel_id, name, poll_id, index))


def convert_poll_results(answers_):
    """
    Private function.
    Parse answers_ : [[answer: str, voted: int], ...] to pair of [answers] and [votes]
    """
    answers = '{'
    voted = '{'
    for variant in answers_:
        answers += variant[0] + ','
        voted += str(variant[1]) + ','
    answers = answers[0:-1] + '}'
    voted = voted[0:-1] + '}'
    return answers, voted


def add_poll(id: int, name: str, answers_, chat_id: int):
    """
    Call on create poll.

    answers_ : [[answer: str, voted: int], ...]
    """
    answers, voted = convert_poll_results(answers_)

    cur.execute("INSERT INTO poll_info (id, poll_name, answers, voted, closed, chat_id) VALUES (%s, %s, %s, %s, FALSE, %s);",
                (id, name, answers, voted, chat_id))


def update_votes(id: int, index: int, chel_id: int, name: str):
    """
    Add one vote to index ans.
    """
    if is_voted(chel_id, id):
        return

    cur.execute("SELECT * FROM poll_info WHERE id = {};".format(id))
    res = cur.fetchone()

    if res[4]:
        return False

    add_vote(chel_id, name, id, index)

    voted = res[3]
    voted[int(index) - 1] += 1
    voted = str(voted).replace('[', '{').replace(']', '}')
    cur.execute("UPDATE poll_info SET voted = \'{}\' WHERE id={};".format(voted, id))
    return True


def close():
    """
    Close postgresql connections.
    """
    cur.close()
    conn.close()


def db_close_poll(id: int):
    """
    Finally closes poll.
    No chance to open.
    """
    cur.execute("UPDATE poll_info SET closed = TRUE WHERE id={};".format(id))


def get_poll_statistics_db(id: int):
    """
    Return's [[ans: str, votes: int], ...]
    """
    cur.execute(f"SELECT * FROM poll_info WHERE id={id};")
    res = cur.fetchone()
    return list(zip(res[2], res[3]))


def get_all_polls(chat_id: int):
    """
    Return [(id: int, name: str), ...]
    """
    cur.execute(f"SELECT id, poll_name FROM poll_info WHERE closed=FALSE AND chat_id={chat_id};")

    tmp = cur.fetchone()
    res = []
    while tmp is not None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def create_all():
    """
    Create all tables
    """
    create_poll_voted()
    create_post_stat()
    create_poll_info()
    create_channel_to_post()
    create_user_stat()
    create_channel_list()


def get_channel_mentions(chat_id: int):
    """
    :returns mention count for channel and 0 if channel is not mentioned
    """
    cur.execute("SELECT mentions from mention_info where channel_id={}".format(chat_id))
    res = cur.fetchone()
    if res is not None:
        return res
    else:
        return 0


try:
    create_all()
except:
    pass

if __name__ == "__main__":
    set_active_channel(0, 0)
    print(get_active_channel(0))
    print(get_channel_mentions(12345))
    set_active_channel(0, 5)
    print(get_active_channel(0))
    close()
