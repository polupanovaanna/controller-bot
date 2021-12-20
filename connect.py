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
    # answers_ : [[answer, voted], ...]
    answers, voted = convert_poll_results(answers_)

    cur.execute("INSERT INTO poll_info (id, poll_name, answers, voted) VALUES (%s, %s, %s, %s);",
                (id, name, answers, voted))
    cur.execute("SELECT * FROM poll_info;")
    print(cur.fetchone())
    print(answers)


def update_votes(id: int, name: str, answers_):
    answers, voted = convert_poll_results(answers_)
    cur.execute("UPDATE poll_info SET voted = \'{}\' WHERE id={};".format(voted, id))


if __name__ == "__main__":
    # update_votes(15, "name", [('ans', 14),('ans', 14),('ans', 14)])
    # exit(0)
    create_post_stat()
    add_post(5843, 15)

def close():
    cur.close()
    conn.close()
