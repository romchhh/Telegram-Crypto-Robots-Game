import sqlite3

con = sqlite3.connect('data/db.sqlite')
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS Squads (
                squad_id INTEGER PRIMARY KEY,
                leader_id INTEGER,
                group_name INTEGER,
                users_id TEXT,
                ton_balance INTEGER DEFAULT 0
);''')


def add_group_to_db(group_id, leader_id, group_name):
    print(f"Adding group to DB: group_id={group_id}, leader_id={leader_id}, group_name={group_name}")
    con = sqlite3.connect("data/db.sqlite")  # Использовать двойные кавычки для пути
    cur = con.cursor()
    cur.execute("""
        INSERT INTO Squads (squad_id, leader_id, group_name)
        VALUES (?, ?, ?)
        ON CONFLICT(squad_id) DO UPDATE SET leader_id=excluded.leader_id, group_name=excluded.group_name  
    """, (group_id, leader_id, group_name))
    con.commit()
    con.close()

def get_top_squads(limit):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('''
        SELECT squad_id, group_name, leader_id, ton_balance
        FROM Squads
        ORDER BY ton_balance DESC
        LIMIT ?
    ''', (limit,))
    result = cur.fetchall()
    con.close()
    return result

    
def add_user_to_squad(chat_id, user_id):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()

    # Проверяем, нет ли уже пользователя в других сквадах
    cur.execute('''
        SELECT squad_id FROM Squads WHERE users_id LIKE '%' || ? || '%'
    ''', (str(user_id),))
    if cur.fetchone():
        con.close()
        return False

    cur.execute('''
        INSERT INTO Squads (squad_id, users_id)
        VALUES (?, ?)
        ON CONFLICT(squad_id) DO UPDATE SET users_id=coalesce(users_id || ',' || ?, excluded.users_id)
    ''', (chat_id, str(user_id), str(user_id)))
    con.commit()
    con.close()
    return True

def check_user_in_squad(group_id, user_id):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('''
        SELECT users_id FROM Squads WHERE squad_id = ?
    ''', (group_id,))
    result = cur.fetchone()
    if result is None:
        return False
    elif user_id in [int(x) for x in result[0].split(',')]:
        return True
    else:
        return False

def get_squad_id_by_user_id(user_id):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('''
        SELECT squad_id FROM Squads WHERE users_id LIKE '%' || ? || '%'
    ''', (str(user_id),))
    result = cur.fetchone()
    con.close()
    if result:
        return result[0]
    else:
        return None

def add_squad_balance(squad_id, amount):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('''
        UPDATE Squads SET ton_balance = ton_balance + ? WHERE squad_id = ?
    ''', (amount, squad_id))
    con.commit()
    con.close()
        
def get_squad_with_highest_balance():
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('''
        SELECT squad_id, ton_balance FROM Squads ORDER BY ton_balance DESC LIMIT 1
    ''')
    result = cur.fetchone()
    con.close()
    if result:
        return result[0]
    else:
        return None

def get_total_squads_balance():
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('SELECT SUM(ton_balance) FROM Squads')
    result = cur.fetchone()
    con.close()
    if result is None:
        return 0
    else:
        return result[0]


async def get_squads_balance_sum():
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('SELECT SUM(ton_balance) FROM Squads')
    result = cur.fetchone()
    con.close()
    return result[0] if result else 0

def get_squad_leader(squad_id):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('SELECT leader_id FROM Squads WHERE squad_id = ?', (squad_id,))
    result = cur.fetchone()
    con.close()
    return result[0] if result else None


def get_all_squads():
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('SELECT * FROM Squads')
    squads = cur.fetchall()
    con.close()
    return squads


def get_all_admin_squads():
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()

    # Выполняем запрос для получения всех сквадов
    cur.execute('SELECT * FROM Squads')
    squads = cur.fetchall()

    # Добавляем информацию о пользователях для каждого сквада
    for squad in squads:
        squad_id = squad[0]  # Предполагаем, что squad_id - первый элемент кортежа

        # Выполняем запрос для получения всех пользователей в текущем скваде
        cur.execute('SELECT user_id FROM users_id WHERE squad_id=?', (squad_id,))
        members = cur.fetchall()

        # Преобразуем список кортежей в список идентификаторов пользователей
        members = [m[0] for m in members]

        # Добавляем список пользователей в кортеж сквада
        squad = squad + (members,)

    con.close()
    return squads

def delete_squad_from_db(squad_id):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()

    # Удаляем всех пользователей из сквада
    cur.execute('DELETE FROM Squads WHERE squad_id=?', (squad_id,))

    # Удаляем сам сквад
    cur.execute('DELETE FROM Squads WHERE squad_id=?', (squad_id,))

    con.commit()
    con.close()

    return True


def set_squad_balance(squad_id, balance):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('UPDATE Squads SET ton_balance = ? WHERE squad_id = ?', (balance, squad_id))
    con.commit()
    con.close()
    
    
def get_squads_count():
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM Squads')
    result = cur.fetchone()
    con.close()
    return result[0]


def is_group_blocked(group_id):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()
    cur.execute('SELECT EXISTS(SELECT 1 FROM Squads WHERE squad_id=? AND blocked=1)', (group_id,))
    result = cur.fetchone()[0]
    con.close()
    return bool(result)

def get_squad_admin_time():
    # Подключаемся к базе данных
    conn = sqlite3.connect('data/db.sqlite')  # Замените 'your_database.db' на имя вашей базы данных
    cursor = conn.cursor()

    # Извлекаем данные из таблицы squads_admin
    cursor.execute("SELECT day, hour, minute FROM squads_admin")
    result = cursor.fetchone()

    # Закрываем соединение с базой данных
    conn.close()

    return result


def update_squad_admin_time(day, hour, minute):
    # Подключаемся к базе данных
    conn = sqlite3.connect('data/db.sqlite')  # Замените 'your_database.db' на имя вашей базы данных
    cursor = conn.cursor()

    # Изменяем данные в таблице squads_admin
    cursor.execute("UPDATE squads_admin SET day=?, hour=?, minute=?", (day, hour, minute))
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()

    return True


def log_squad_payment(group_id: int, leader_id: int, prize: float):
    con = sqlite3.connect('data/db.sqlite')
    cur = con.cursor()

    # Retrieve group_name using group_id
    cur.execute('SELECT group_name FROM Squads WHERE squad_id = ?', (group_id,))
    result = cur.fetchone()

    if result:
        group_name = result[0]

        # Insert the payment record into squads_payments
        cur.execute('''
            INSERT INTO squads_payments (group_id, leader_id, group_name, prize)
            VALUES (?, ?, ?, ?)
        ''', (group_id, leader_id, group_name, prize))

        con.commit()
    else:
        print(f"Group with ID {group_id} not found")

    con.close()


def get_top_payments(limit):
        con = sqlite3.connect('data/db.sqlite')
        cur = con.cursor()
        cur.execute('''
            SELECT group_id, leader_id, group_name, prize 
            FROM squads_payments 
            ORDER BY prize DESC 
            LIMIT ?
        ''', (limit,))
        result = cur.fetchall()
        con.close()
        return result