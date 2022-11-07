import sqlite3 as sq
import time


def sql_start():
    global base, cur
    base = sq.connect('users.db')
    cur = base.cursor()
    if base:
        print("data base 'users.db' connected")
    base.execute('CREATE TABLE IF NOT EXISTS USERS(users TEXT PRIMARY KEY, promo TEXT, end_time TEXT)')
    base.execute('CREATE TABLE IF NOT EXISTS PROMO(PROMO TEXT PRIMARY KEY)')
    base.commit()


async def check_time(id):
    return float(cur.execute("SELECT end_time FROM USERS WHERE users == ?", (id, )).fetchone()[0])


async def add_new_member(id):
    try:
        cur.execute("INSERT INTO USERS VALUES (?, ?, ?)", (id, "0", ""))
    except:
        pass
    finally:
        base.commit()


async def add_new_promo(promo):
    cur.execute("INSERT INTO PROMO VALUES (?)", (promo,))
    base.commit()


async def use_promo(id, promo):
    if str(promo) in str(cur.execute("SELECT * FROM PROMO").fetchall()):
        cur.execute("DELETE FROM PROMO WHERE PROMO == ?", (promo,))
        cur_time = time.time()
        cur.execute("UPDATE USERS SET promo == ? WHERE users == ?", (promo, id))
        cur.execute("UPDATE USERS SET end_time == ? WHERE users == ?", (cur_time, id))
        base.commit()
        return 1
    else:
        return 0
