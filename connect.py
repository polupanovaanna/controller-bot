import psycopg2
from config import host, user, password, db_name
from time import time as tm

conn = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)

conn.autocommit = True
cur = conn.cursor()


def create_post_stat():
    """
    Private
    Call to create table for posts.
    """
    cur.execute(
        "CREATE TABLE post_stat (timestamp integer, "
        "time integer, views integer, message_id integer);")


def add_post(timestamp: int, views: int, message_id: int, chat_id: int):
    """
    Add's note about post at this moment.
    """

    cur.execute(f"SELECT SUM(views) AS view FROM post_stat WHERE message_id={message_id};")

    tmp = cur.fetchone()[0]
    if tmp is None:
        old = 0
        add_message(chat_id, message_id)
    else:
        old = int(tmp)

    cur.execute("INSERT INTO post_stat (timestamp, time, views, message_id) VALUES (%s, %s, %s, %s);",
                (timestamp, 1000000, views - old, message_id))


def get_post_stat_from_channel(channel_id: int):
    """
    TODO
    """
    cur.execute(
        f"SELECT DATE_TRUNC('month',to_timestamp(time)::date) AS month, MAX(views) AS views_sum FROM post_stat INNER JOIN channel_post ON post_stat.message_id=channel_post.message_id WHERE chat_id={channel_id} GROUP BY month;")

    res = []
    tmp = cur.fetchone()

    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()
    return res


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


def get_channel_stat_by_day_from_to(chat_id: int, fr = 0, to = 2147483647):
    """
    TODO
    """
    
    cur.execute(f"SELECT DATE_TRUNC('day',to_timestamp(time)::date) AS month, SUM(views) AS views_sum FROM post_stat INNER JOIN channel_post ON post_stat.message_id=channel_post.message_id WHERE channel_post.chat_id={chat_id} AND post_stat.time BETWEEN {fr} AND {to} GROUP BY month ORDER BY month;")

    res = []
    tmp = cur.fetchone()
    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def get_post_stat_by_day_from_to(message_id: int, fr = 0, to = 2147483647):
    """
    TODO
    """
    
    cur.execute(f"SELECT DATE_TRUNC('day',to_timestamp(time)::date) AS month, SUM(views) AS views_sum FROM post_stat WHERE message_id={message_id} AND time BETWEEN {fr} AND {to} GROUP BY month ORDER BY month;")

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
        f"SELECT DATE_TRUNC('{wtf}',to_timestamp(time)::date) AS month, MAX(views) AS views_sum FROM post_stat INNER JOIN channel_post ON post_stat.chat_id=channel_post.chat_id GROUP BY month;")

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
        "CREATE TABLE channel_post (chat_id integer, "
        "message_id integer);")


def add_message(chat_id: int, message_id: int):
    """
    Private
    Add's message
    """
    cur.execute("INSERT INTO channel_post (chat_id, message_id) VALUES (%s, %s)", (chat_id, message_id))


def create_poll_info():
    """
    Private
    Create table for poll.
    """

    cur.execute(
        "CREATE TABLE poll_info (id integer PRIMARY KEY NOT NULL, "
        "poll_name varchar, answers varchar ARRAY, voted integer ARRAY, closed boolean);")


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


def add_poll(id: int, name: str, answers_):
    """
    Private
    Call on create poll.

    answers_ : [[answer: str, voted: int], ...]
    """
    answers, voted = convert_poll_results(answers_)

    cur.execute("INSERT INTO poll_info (id, poll_name, answers, voted, closed) VALUES (%s, %s, %s, %s, FALSE);",
                (id, name, answers, voted))


def update_votes(id: int, index: int):
    """
    Add one vote to index ans.
    """
    cur.execute("SELECT * FROM poll_info WHERE id = {};".format(id))
    res = cur.fetchone()

    if res[4]:
        return False

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


def get_all_polls():
    """
    Return [(id: int, name: str), ...]
    """
    cur.execute(f"SELECT id, poll_name FROM poll_info WHERE closed=FALSE;")

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

    create_post_stat()
    create_poll_info()
    create_channel_to_post()


if __name__ == "__main__":
    #add_post(15, 5, 0, 0)
    print(get_post_stat_by_day_from_to(0))
    print(get_post_stat_by_day_from_to(1))
    print(get_channel_stat_by_day_from_to(0))

    close()
