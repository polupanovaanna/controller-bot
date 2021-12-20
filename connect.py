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
    cur.execute(
        "CREATE TABLE post_stat2 (timestamp integer PRIMARY KEY NOT NULL, "
        "time integer, views integer);")


def add_post(timestamp: int, views: int):
    cur.execute("INSERT INTO post_stat2 (timestamp, time, views) VALUES (%s, %s, %s);",
                (timestamp, tm(), views))


# def update_post(timestamp: int, views: int):
    #cur.execute(f"SELECT * from post_stat WHERE timestamp={timestamp};")
    #rows = cur.fetchone()
    #rows[1].append(int(tm()))
    #rows[2].append(views)
    #cur.execute("UPDATE post_stat SET time = \'{}\', views = \'{}\' WHERE timestamp={};".format(str(rows[1]).replace('[','{').replace(']','}'),
                                                                                         #str(rows[2]).replace('[','{').replace(']','}'),
                                                                                                #timestamp))


def create_poll_info():
    """
    Create table for poll.
    """
    cur.execute(
        "CREATE TABLE poll_info (id integer PRIMARY KEY NOT NULL, "
        "poll_name varchar, answers varchar ARRAY, voted integer ARRAY);")


def convert_poll_results(answers_):
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

    answers_ : [[answer, voted], ...]
    """
    answers, voted = convert_poll_results(answers_)

    cur.execute("INSERT INTO poll_info (id, poll_name, answers, voted) VALUES (%s, %s, %s, %s);",
                (id, name, answers, voted))
    cur.execute("SELECT * FROM poll_info;")
    print(cur.fetchone())
    print(answers)


def update_votes(id: int, index: int):
    cur.execute("SELECT * FROM poll_info WHERE id = {};".format(id))
    res = cur.fetchone()
    voted = res[3]
    voted[index] += 1
    voted = str(voted).replace('[', '{').replace(']', '}')
    cur.execute("UPDATE poll_info SET voted = \'{}\' WHERE id={};".format(voted, id))
    cur.execute("SELECT * FROM poll_info WHERE id={};".format(id))
    print(cur.fetchone())


def close():
    cur.close()
    conn.close()

def get_poll_statistics_db(id: int):
    cur.execute("SELECT * FROM poll_info WHERE id={};".format(id))
    res = cur.fetchone()
    return list(zip(res[2], res[3]))

if __name__ == "__main__":
    # update_votes(15, "name", [('ans', 14),('ans', 14),('ans', 14)])
    # exit(0)
    # create_post_stat()
    # add_post(5843, 15)
    # add_poll(23432, "test", [['dfas', 0], ['fdk', 0]])
    update_votes(23432, 0)
    print(func(23432))
    close()

