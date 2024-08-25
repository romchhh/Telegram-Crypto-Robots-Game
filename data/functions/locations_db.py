import sqlite3
import random
from datetime import datetime, timedelta

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

def get_health(uid):
    if check_user(uid):
        cur.execute(f'SELECT health FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0


def get_pvehealth(uid):
    if check_user(uid):
        cur.execute(f'SELECT pvehealth FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0


def add_health(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET health = health + {amount} WHERE uid = {uid}')
        con.commit()


def add_pvehealth(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET pvehealth = pvehealth + {amount} WHERE uid = {uid}')
        con.commit()


def get_damage(uid):
    if check_user(uid):
        cur.execute(f'SELECT damage FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0


def add_damage(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET damage = damage + {amount} WHERE uid = {uid}')
        con.commit()


def get_heal(uid):
    if check_user(uid):
        cur.execute(f'SELECT heal FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0


def add_heal(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET heal = heal + {amount} WHERE uid = {uid}')
        con.commit()
        
        
def get_lvl(uid):
    if check_user(uid):
        cur.execute(f'SELECT lvl FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0


def add_lvl(uid, amount):
    if check_user(uid):
        lvl = get_lvl(uid) // 10
        cur.execute(f'UPDATE Users SET lvl = lvl + {amount} WHERE uid = {uid}')
        con.commit()
        newlvl = get_lvl(uid) // 10
        if newlvl > lvl:
            rand = random.randint(1, 4)
            if rand == 1:
                set_last_update(uid, 1)
                add_health(uid, 5)
                return 'Ты повысил свой уровень! В награду твоё здоровье увеличено на 5 единиц!'
            elif rand == 2:
                set_last_update(uid, 2)
                add_damage(uid, 2)
                return 'Ты повысил свой уровень! В награду твой урон увеличен на 2 единицы!'
            elif rand == 3:
                set_last_update(uid, 3)
                add_heal(uid, 2)
                return 'Ты повысил свой уровень! В награду сила твоего ремкомплекта увеличена на 2 единицы!'
            else:
                set_last_update(uid, 0)
                return None
        else:
            return None
    else:
        return 0


def decrease_lvl(uid, amount):
    if check_user(uid):
        flvl = get_lvl(uid) // 10
        cur.execute(f'UPDATE Users SET lvl = lvl - {amount} WHERE uid = {uid}')
        con.commit()
        nlvl = get_lvl(uid) // 10
        if nlvl < flvl:
            if get_last_update(uid) == 1:
                set_last_update(uid, 0)
                add_health(uid, -5)
            elif get_last_update(uid) == 2:
                set_last_update(uid, 0)
                add_damage(uid, -2)
            elif get_last_update(uid) == 3:
                set_last_update(uid, 0)
                add_heal(uid, -2)
            else:
                pass


def get_last_update(uid):
    if check_user(uid):
        cur.execute(f'SELECT lstup FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0


def set_last_update(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET lstup = {amount} WHERE uid = {uid}')
        con.commit()
        
        
def record_island_location(user_id, days):
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    end_time = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute("INSERT INTO island_location (uid, days, start_time, end_time) VALUES (?, ?, ?, ?)",
                (user_id, days, start_time, end_time))
    con.commit()
    
    
def check_user_in_island_location(user_id):
    cur.execute("SELECT end_time FROM island_location WHERE uid = ? AND end_time > ?", (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    user_data = cur.fetchone()
    if user_data:
        end_time = datetime.strptime(user_data[0], '%Y-%m-%d %H:%M:%S')
        remaining_time = end_time - datetime.now()
        return remaining_time

    return None

def check_user_in_atlantida_location(user_id):
    cur.execute("SELECT COUNT(*) FROM atlantida_location WHERE uid = ?", (user_id,))
    result = cur.fetchone()
    if result and result[0] > 0:
        return True  # User ID found in the database
    else:
        return False 

def record_atlantida_location(user_id):
    cur.execute("INSERT INTO atlantida_location (uid, active) VALUES (?, 1)",
                (user_id,))
    con.commit()


def get_atlantida_entrance_fee():
    cur.execute("SELECT value FROM atlantida_admin WHERE name = 'atlantida'")
    result = cur.fetchone()

    if result and result[0]:
        return float(result[0])  # Convert the value to float
    else:
        return 3

def update_boss_power(power):
    cur.execute("UPDATE atlantida_admin SET power = ?", (power,))
    con.commit()
    
def get_boss_power():
    cur.execute("SELECT power FROM atlantida_admin")
    result = cur.fetchone()
    if result:
        return result[0]
    else:
        return 0

def set_atlantida_started_to_zero():
    cur.execute("UPDATE atlantida_admin SET started = 0 WHERE name = 'atlantida'")
    con.commit()

    
def check_atlantida_started():
    cur.execute("SELECT started FROM atlantida_admin LIMIT 1")
    result = cur.fetchone()
    if result and result[0] == 1:
        return True
    else:
        return False
    
def get_atlantida_prize():
    cur.execute("SELECT prize FROM atlantida_admin WHERE name = 'atlantida'")
    result = cur.fetchone()

    if result:
        return result[0]
    else:
        return 2
    
def delete_all_atlantida_locations():
    cur.execute('DELETE FROM atlantida_location')  # выполняем SQL-запрос
    con.commit()  # фиксируем изменения

    
def set_atlantida_value(value):
    cur.execute("UPDATE atlantida_admin SET value = ? WHERE name = 'atlantida'", (value,))
    con.commit()

def set_atlantida_prize(prize):
    cur.execute("UPDATE atlantida_admin SET prize = ? WHERE name = 'atlantida'", (prize,))
    con.commit()

def set_boss_power(power):
        cur.execute("UPDATE atlantida_admin SET power = ? WHERE name = 'atlantida'", (power,))
        con.commit()

def set_atlantida_started_to_one():
    cur.execute("UPDATE atlantida_admin SET started = 1 WHERE name = 'atlantida'")
    con.commit()
    
def get_atlantida_fighters():
    try:
        # Выполняем запрос для извлечения uid из таблицы atlantida_location
        cur.execute("SELECT uid FROM atlantida_location")
        fighters_ids = [row[0] for row in cur.fetchall()]  # Извлекаем все uid и сохраняем их в список

        return fighters_ids

    except sqlite3.Error as e:
        print(f"Ошибка при извлечении данных из таблицы atlantida_location: {e}")
        return []

######################
def get_game_take_balance(uid):
    if check_user(uid):
        cur.execute(f'SELECT balance FROM Users WHERE uid = {uid}')
        balance = cur.fetchone()[0]
        return balance
    else:
        return 0
    
def add_game_take_balance(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET balance = balance + {amount} WHERE uid = {uid}')
        con.commit()
    else:
        return 0
    
def decrease_game_take_balance(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET balance = balance - {amount} WHERE uid = {uid}')
        con.commit()
        
        
        
def add_health_to_robot(user_id: int, health_points: int):
    cur.execute("SELECT * FROM user_robots WHERE user_id=? AND status='selected'", (user_id,))
    robot = cur.fetchone()

    if robot:
        new_health = max(min(int(robot[3]) + health_points, int(robot[8])), 1)
        if new_health != int(robot[3]):
            cur.execute("UPDATE user_robots SET health=? WHERE user_id=? AND status='selected'", (new_health, robot[0]))
            con.commit()



def add_health(uid, amount):
    if check_user(uid):
        cur.execute(f'UPDATE Users SET pvehealth = pvehealth + {amount} WHERE uid = {uid}')
        con.commit()
            
            
def get_robot_health(user_id: int) -> int:
    cur.execute("""
        SELECT health
        FROM user_robots
        WHERE user_id = ? AND status = 'selected'
    """, (user_id,))
    result = cur.fetchone()
    if result is None:
        health = 0
    else:
        health = result[0]
    return health

            
def get_robot_max_health(user_id: int) -> int:
    cur.execute("""
        SELECT max_health
        FROM user_robots
        WHERE user_id = ? AND status = 'selected'
    """, (user_id,))
    result = cur.fetchone()
    if result is None:
        max_health = 0
    else:
        max_health = result[0]
    return max_health
