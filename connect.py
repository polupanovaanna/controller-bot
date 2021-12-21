# TODO check is poll closed
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
    Call to create table for posts.
    """
    cur.execute(
        "CREATE TABLE post_stat (timestamp integer, "
        "time integer, views integer);")


def add_post(timestamp: int, views: int):
    """
    Add's note about post at this moment.
    """
    cur.execute("INSERT INTO post_stat (timestamp, time, views) VALUES (%s, %s, %s);",
                (timestamp, tm(), views))
    

def get_post_stat_by_day_db(id: int):
    """
    Give id and u will get get max of views in each weak.
    """
    return get_post_stat_by_db(id, 'day')


def get_post_stat_by_weak_db(id: int):
    """
    Give id and u will get get max of views in each weak.
    """
    return get_post_stat_by_db(id, 'weak')


def get_post_stat_by_month_db(id: int):
    """
    Give id and u will get get max of views in each mounth.
    """
    return get_post_stat_by_db(id, 'month')


def get_post_stat_by_db(id: int, wtf: str):
    """
    Private function to not copy paste.
    """

    cur.execute(f"SELECT DATE_TRUNC('{wtf}',to_timestamp(time)::date) AS month, MAX(views) AS views_sum FROM post_stat GROUP BY month;")


    res = []
    tmp = cur.fetchone()
    while tmp != None:
        res.append(tmp)
        tmp = cur.fetchone()

    return res


def create_poll_info():
    """
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
    Call on create poll.

    answers_ : [[answer: str, voted: int], ...]
    """
    answers, voted = convert_poll_results(answers_)

    cur.execute("INSERT INTO poll_info (id, poll_name, answers, voted, closed) VALUES (%s, %s, %s, %s, FALSE);",
                (id, name, answers, voted))
    #cur.execute("SELECT * FROM poll_info;")


def update_votes(id: int, index: int):
    """
    Add one vote to index ans.
    """
    cur.execute("SELECT * FROM poll_info WHERE id = {};".format(id))
    res = cur.fetchone()

    if res[4]:
        return False

    voted = res[3]
    voted[index] += 1
    voted = str(voted).replace('[', '{').replace(']', '}')
    cur.execute("UPDATE poll_info SET voted = \'{}\' WHERE id={};".format(voted, id))
    return True


def close():
    """
    Close postgresql connections.
    """
    cur.close()
    conn.close()

#TODO
def db_close_poll(id: int):
    """
    Finaly close poll.
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
        res = cur.fetchone()
    return res

if __name__ == "__main__":
    # add_poll(12, 'name', [['fds', 0], ['dssa', 0]])
    create_post_stat()
    create_poll_info()
    close()

