import psycopg2

conn = psycopg2.connect("dbname=mydb user=megaserg01 password=123")
conn.autocommit = True
cur = conn.cursor()


def create_poll_info():
    cur.execute(
        "CREATE TABLE poll_info (id integer PRIMARY KEY NOT NULL, poll_name varchar, answers varchar ARRAY, voted integer ARRAY);")

def debug():
    conn.commit()
    cur.execute("SELECT * FROM poll_info;")
    row = cur.fetchone()
    while(row is not None):
        print(row)
        row = cur.fetchone()
def convert_poll_results(answers_):
    answers = '{'
    voted = '{'
    for variant in answers_:
        answers += variant[0] + ','
        voted += str(variant[1]) + ','
    answers = answers[0:-1] + '}'
    voted = voted[0:-1] + '}'
    return (answers, voted)

def add_poll(id: int, name: str, answers_):
    # answers_ : [[answer, voted], ...]
    answers, voted = convert_poll_results(answers_)
    cur.execute("INSERT INTO poll_info (id, poll_name, answers, voted) VALUES (%s, %s, %s, %s);",
                (id, name, answers, voted))

def update_votes(id: int, name : str, answers_):
    answers, voted = convert_poll_results(answers_)
    cur.execute("UPDATE poll_info SET voted = \'{}\' WHERE id={};".format(voted, id))
    conn.commit()
debug()
cur.close()
conn.close()
