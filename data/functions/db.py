import sqlite3

con = sqlite3.connect('data/db.sqlite')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS Users (
                uid INTEGER,
                balance INTEGER DEFAULT 0,
                refferal INTEGER DEFAULT 0,
                ton_balance INTEGER DEFAULT 0
);''')

cur.execute(f'''CREATE TABLE IF NOT EXISTS tournament (
        tour_id INTEGER PRIMARY KEY,
        status  INTEGER DEFAULT 1,
        created_at TEXT,
        end_date TEXT
);''')

cur.execute(f'''CREATE TABLE IF NOT EXISTS tour_users (
        tour_id INTEGER,
        user_id INTEGER,
        ball INTEGER DEFAULT 0
);''')

con.commit()


def check_user(uid):
    cur.execute(f'SELECT * FROM Users WHERE uid = {uid}')
    user = cur.fetchone()
    if user:
        return True
    return False


def add_user(uid, ref):
    if not check_user(uid):
        cur.execute(f'INSERT INTO Users (uid, refferal) VALUES (?, ?)', (uid, ref))
        con.commit()


def delete_user(uid):
    if check_user(uid):
        cur.execute("DELETE FROM Users WHERE uid=?", (uid,))
        con.commit()


def get_refferals(uid):
    if check_user(uid):
        cur.execute(f'SELECT COUNT(uid) FROM Users WHERE refferal = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0
    
def get_top_refferals():
    cur.execute("""
        SELECT refferal, COUNT(*) as refferal_count
        FROM Users
        WHERE refferal != 0
        GROUP BY refferal
        ORDER BY refferal_count DESC
        LIMIT 10;
    """)
    return cur.fetchall()


def set_zero_levels():
    cur.execute('''
        UPDATE user_robots
        SET lvl = 0
    ''')
    con.commit()


def get_auto_withdraw():
    cur.execute("SELECT auto FROM autowithdraw WHERE id = 1")
    result = cur.fetchone()
    if result is None:
        return False
    else:
        return bool(result[0])

def set_auto_withdraw(value):
    cur.execute("UPDATE autowithdraw SET auto = ? WHERE id = ?", (value, 1))
    con.commit()

def add_refferals(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET refferals = refferals + {amount} WHERE uid = {uid}')
        con.commit()

def add_refferal_balance(ref):
    if check_user(ref):
        cur.execute(f'UPDATE Users SET balance = balance + 0.03 WHERE uid = {ref}')
        con.commit()

def get_balance(uid):
    if check_user(uid):
        cur.execute(f'SELECT ton_balance FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0

def get_user_ref(uid):
    if check_user(uid):
        cur.execute(f'SELECT refferal FROM Users WHERE uid = {uid}')
        ref = cur.fetchone()[0]
        return ref
    else:
        return 0

def get_take_balance(uid):
    if check_user(uid):
        cur.execute(f'SELECT balance FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0
    



def get_user_ref_status(uid):
    cur.execute('SELECT checkref FROM Users WHERE uid = ?', (uid,))
    result = cur.fetchone()[0]

    return result


def get_user_ref(uid):
    cur.execute('SELECT refferal FROM Users WHERE uid = ?', (uid,))
    result = cur.fetchone()[0]

    return result


def add_balance(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET ton_balance = ton_balance + {amount} WHERE uid = {uid}')
        con.commit()
        
def add_balance_leader(uid, amount):
    if check_user(uid):
        cur.execute('UPDATE Users SET ton_balance = ton_balance + ? WHERE uid = ?', (amount, uid))
        con.commit()



def add_take_balance(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET balance = balance + {amount} WHERE uid = {uid}')
        con.commit()


def decrease_balance(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET ton_balance = ton_balance - {amount} WHERE uid = {uid}')
        con.commit()


def decrease_take_balance(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET balance = balance - {amount} WHERE uid = {uid}')
        con.commit()

def decrease_game_take_balance(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET balance = balance - {amount} WHERE uid = {uid}')
        con.commit()

def new_top_lvl():
    cur.execute("SELECT * FROM user_robots ORDER BY lvl DESC LIMIT 10")
    results = cur.fetchall()
    return results

def new_top_bet_games():
    cur.execute("""
        SELECT player, SUM(bet) as total_bet
        FROM (
            SELECT player_1 as player, bet
            FROM games
            UNION ALL
            SELECT player_2 as player, bet
            FROM games
        ) as combined
        GROUP BY player
        ORDER BY total_bet DESC
        LIMIT 10
    """)
    results = cur.fetchall()
    return results


def new_top_refs():
    cur.execute("SELECT * FROM Users ORDER BY checkref DESC LIMIT 10")
    results = cur.fetchall()
    return results

def get_user_wallet(user_id):
    cur.execute("SELECT wallet FROM Users WHERE uid = ?", (user_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return 0


def get_users():
    cur.execute("SELECT uid FROM users")
    results = cur.fetchall()
    return results


def get_tour(tour_id):
    cur.execute("SELECT * FROM tournament WHERE tour_id = ?", (tour_id,))
    result = cur.fetchone()
    return result


def get_active_tour():
    cur.execute("SELECT tour_id FROM tournament WHERE status = 1")
    result = cur.fetchone()
    return result


def get_tour_user_exist(user_id, tour_id):
    cur.execute("SELECT * FROM tour_users WHERE user_id = ? AND tour_id = ?", (user_id, tour_id,))
    result = cur.fetchone()
    if result is None:
        return False
    return True


def get_count_exist_tour():
    cur.execute("SELECT COUNT(tour_id) FROM tournament")
    result = cur.fetchone()[0]
    return result


def add_to_tour(tour_id, user_id):
    cur.execute('''INSERT INTO tour_users (
    tour_id,
    user_id
)
VALUES (
    ?,
    ?
)''', (tour_id, user_id,))
    con.commit()


def add_tour(tour_id, created_at, end_at):
    cur.execute('''INSERT INTO tournament (
    tour_id,
    created_at,
    end_date
)
VALUES (
    ?,
    ?,
    ?
)''', (tour_id, created_at, end_at))
    con.commit()


def get_tour_top_user(tour_id):
    cur.execute('''SELECT user_id, ball
                  FROM tour_users
                  WHERE tour_id = ?
                  ORDER BY ball DESC
                  LIMIT 3''', (tour_id,))

    result = cur.fetchall()
    return result


def get_count_tour_users(tour_id):
    cur.execute('SELECT COUNT(user_id) FROM tour_users WHERE tour_id = ?', (tour_id,))
    result = cur.fetchone()[0]
    return result


def get_user_place(tour_id, user_id):
    cur.execute('''SELECT user_id, ball
                      FROM tour_users
                      WHERE tour_id = ?
                      ORDER BY ball DESC''', (tour_id,))

    tour_data = cur.fetchall()

    user_place = next((i+1 for i, (u_id, _) in enumerate(tour_data) if u_id == user_id), None)

    return user_place


def get_user_tour_ball(tour_id, user_id):
    cur.execute('''SELECT ball
                      FROM tour_users
                      WHERE tour_id = ?
                      AND user_id = ?''', (tour_id, user_id))

    result = cur.fetchone()

    if result is None:
        return 0

    return result[0]

def get_user_nft_status(chat_id):
    cur.execute("SELECT NFT FROM Users WHERE uid=?", (chat_id,))
    result = cur.fetchone()

    if result is None:
        return 0
    else:
        return result[0]

def set_user_nft_status(chat_id, nft_status):
    cur.execute("UPDATE Users SET NFT=? WHERE uid=?", (nft_status, chat_id))
    con.commit()

def update_user_wallet(chat_id, value):
    cur.execute(f"UPDATE Users SET wallet =? WHERE uid=?", (value, chat_id))
    con.commit()



def update_tour_status(tour_id):
    cur.execute(f'UPDATE tournament SET status = 0 WHERE tour_id = ?', (tour_id,))
    con.commit()


def add_ball_to_tour_user(tour_id, user_id):
    cur.execute(f'UPDATE tour_users SET ball = ball + 1 WHERE user_id = ? AND tour_id = ?', (user_id, tour_id,))
    con.commit()


def get_all_tours():
    cur.execute('SELECT * FROM tournament')

    result = cur.fetchall()

    return result


def update_ref_status(uid):
    cur.execute('UPDATE Users SET checkref = 0 WHERE uid = ?', (uid,))

    con.commit()
    
def zero_bet_game_exist():
    cur.execute('''
        SELECT COUNT(*)
        FROM games
        WHERE bet = 0 AND status = 'expectation'
    ''')
    result = cur.fetchone()
    return result[0] > 0

    

def add_take_balance_bazar(uid, robot_price):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET balance = balance + {robot_price} WHERE uid = {uid}')
        con.commit()

# def get_all_user_robots():
#     cur.execute('SELECT uid, health, damage, heal, antidmg, lvl FROM Users')
#
#     result = cur.fetchall()
#
#     return result


def get_user_count():
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]

    return user_count

def get_battle_count():
    cur.execute("SELECT COUNT(*) FROM games")
    battle_count = cur.fetchone()[0]

    return battle_count

def get_robots_count():
    cur.execute("SELECT COUNT(*) FROM user_robots")
    battle_count = cur.fetchone()[0]

    return battle_count


    
def store_user_language(user_id, language):
    cur.execute("UPDATE Users SET lang=? WHERE uid=?", (language, user_id))
    con.commit()

def check_user_language(user_id):
    cur.execute('SELECT lang FROM users WHERE uid = ?', (user_id,))
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return None