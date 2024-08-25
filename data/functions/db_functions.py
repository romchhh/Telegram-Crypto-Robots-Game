import sqlite3


class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    # MARKET

    def create_market_tables(self):
        with self.connection:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS market (
                robot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                health INTEGER,
                damage INTEGER,
                heal INTEGER,
                armor INTEGER,
                price INTEGER
            );''')

    def get_count_robots(self):
        with self.connection:
            return self.cursor.execute('SELECT COUNT(robot_id) FROM market;').fetchone()[0]

    def create_robot(self, name, health, damage, heal, armor, price):
        with self.connection:
            self.cursor.execute('''
                INSERT INTO market (
                    name,
                    health,
                    damage,
                    heal,
                    armor,
                    price
                ) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, health, damage, heal, armor, price))

            last_inserted_id = self.cursor.lastrowid
            return last_inserted_id

    def get_robots(self):
        with self.connection:
            return self.cursor.execute('SELECT * FROM market;').fetchall()
        
    def get_bazar_robots(self):
        with self.connection:
            return self.cursor.execute('SELECT * FROM bazar WHERE bought = 0;').fetchall()


    def get_one_robot(self, robot_id):
        with self.connection:
            return self.cursor.execute('SELECT * FROM market WHERE robot_id = ?', (robot_id,)).fetchone()

    def delete_robot(self, robot_id):
        with self.connection:
            self.cursor.execute('''DELETE FROM market WHERE robot_id = ?''', (robot_id,))

    # GAME

    def create_game_tables(self):
        with self.connection:
            return self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS games (
        game_id INTEGER PRIMARY KEY,
        bet INTEGER,
        status TEXT DEFAULT 'expectation',
        player_1 INTEGER,
        player_2 INTEGER DEFAULT 0,
        winner INTEGER DEFAULT 0,
        date TEXT,
        last_attack INTEGER DEFAULT 0,
        turn INTEGER
);''')

    def add_game(self, game_id, bet, player_1, date):
        with self.connection:
            self.cursor.execute('''
                INSERT INTO games (
                    game_id,
                    bet,
                    player_1,
                    date,
                    turn
                ) 
                VALUES (?, ?, ?, ?, ?)
            ''', (game_id, bet, player_1, date, player_1))

    def start_game(self, game_id, player_2):
        with self.connection:
            self.cursor.execute('''UPDATE games SET status = 'started', player_2 = ? WHERE game_id = ?''',
                                (player_2, game_id,))

    def finish_game(self, game_id, winner):
        with self.connection:
            self.cursor.execute('''UPDATE games SET status = 'finished', winner = ? WHERE game_id = ?''',
                                (winner, game_id,))

    def delete_game(self, game_id):
        with self.connection:
            self.cursor.execute('''UPDATE games SET status = 'deleted' WHERE game_id = ?''', (game_id,))

    def update_turn(self, player_id, game_id):
        with self.connection:
            self.cursor.execute('''UPDATE games SET turn = ? WHERE game_id = ?''', (player_id, game_id))

    def update_last_attack(self, time, game_id):
        with self.connection:
            self.cursor.execute('''UPDATE games SET last_attack = ? WHERE game_id = ?''', (time, game_id))

    def get_game_count(self):
        with self.connection:
            return self.cursor.execute('SELECT COUNT(game_id) FROM games;').fetchone()[0]

    def get_user_all_games(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT * FROM games WHERE (player_1 = ? OR player_2 = ?)",
                                       (user_id, user_id,)).fetchall()

    def get_active_games(self):
        with self.connection:
            return self.cursor.execute("SELECT * FROM games WHERE status = 'expectation'").fetchall()

    def get_user_active_games(self, user_id):
        with self.connection:
            return self.cursor.execute("SELECT * FROM games WHERE player_1 = ? AND status = 'expectation'",
                                       (user_id,)).fetchall()

    def get_game(self, game_id):
        with self.connection:
            return self.cursor.execute("SELECT * FROM games WHERE game_id = ?", (game_id,)).fetchmany(1)[0]

    def check_user_playable(self, user_id):
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM games WHERE (player_1 = ? OR player_2 = ?) AND (status = 'started' OR status = 'expectation')",
                (user_id, user_id,)).fetchmany(1)
            return bool(len(result))

    def check_user_game_create(self, user_id):
        with self.connection:
            result = self.cursor.execute(
                "SELECT * FROM games WHERE player_1 = ? AND status = 'expectation'",
                (user_id,)).fetchmany(1)
            return bool(len(result))

    # USER ROBOTS

    def create_robots_tables(self):
        with self.connection:
            return self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS user_robots (
        user_id INTEGER,
        robot_id INTEGER,
        name TEXT,
        health INTEGER,
        damage INTEGER,
        heal INTEGER,
        armor INTEGER,
        status TEXT DEFAULT 'unselected',
        max_health INTEGER,
        lvl INTEGER DEFAULT 0,
        experience INTEGER DEFAULT 0
);''')

    def add_robot(self, user_id, robot_id, name, health, damage, heal, armor):
        with self.connection:
            self.cursor.execute('''
                INSERT INTO user_robots (
                    user_id,
                    robot_id,
                    name,
                    health,
                    max_health,
                    damage,
                    heal,
                    armor
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, robot_id, name, health, health, damage, heal, armor))

    def update_robot(self, user_id, robot_id, upd_type, amount, increase=True):
        with self.connection:
            if increase:
                return self.cursor.execute(
                    f'''UPDATE user_robots SET {upd_type} = {upd_type} + ? WHERE user_id = ? and robot_id = ?''',
                    (amount, user_id, robot_id)
                )

            return self.cursor.execute(
                f'''UPDATE user_robots SET {upd_type} = {upd_type} - ? WHERE user_id = ? and robot_id = ?''',
                (amount, user_id, robot_id)
            )

    def update_robot_status(self, user_id, robot_id):
        with self.connection:
            self.cursor.execute(
                f'''UPDATE user_robots SET status = 'unselected' WHERE user_id = ?''',
                (user_id,)
            )

            return self.cursor.execute(
                f'''UPDATE user_robots SET status = 'selected' WHERE user_id = ? and robot_id = ?''',
                (user_id, robot_id)
            )

    def heal_full_robot(self, user_id, robot_id):
        with self.connection:
            return self.cursor.execute(
                'UPDATE user_robots SET health = max_health WHERE user_id = ? and robot_id = ?', (user_id, robot_id)
            )

    def get_user_robots(self, user_id):
        with self.connection:
            return self.cursor.execute('SELECT * FROM user_robots WHERE user_id = ?', (user_id,)).fetchall()

    def get_user_active_robot(self, user_id):
        with self.connection:
            return self.cursor.execute('''SELECT * FROM user_robots WHERE user_id = ? AND status = 'selected' ''',
                                       (user_id,)).fetchall()[0]

    def get_unhealthy_robots(self):
        with self.connection:
            return self.cursor.execute(
                '''SELECT * FROM user_robots WHERE health != max_health'''
            ).fetchall()

    def check_robot_health(self, user_id):
        with self.connection:
            robot = self.cursor.execute('''SELECT * FROM user_robots WHERE user_id = ? AND status = 'selected' ''',
                                        (user_id,)).fetchall()[0]

            return robot[3] == robot[8]

    def check_robot_exist(self, user_id, robot_id):
        with self.connection:
            result = self.cursor.execute(
                'SELECT * FROM user_robots WHERE user_id = ? AND robot_id = ?',
                (user_id, robot_id,)).fetchmany(1)
            return bool(len(result))
        
        
    def get_opponents_robot(self, game_id):
        with self.connection:
            # First, find the player1_id using the game_id
            result = self.cursor.execute('SELECT player_1 FROM games WHERE game_id = ? ', (game_id,)).fetchone()
            if result is None:
                return None
            player1_id = result[0]

            # Then, fetch the robot information for the player1_id
            return self.cursor.execute('''SELECT * FROM user_robots WHERE user_id = ? AND status = 'selected' ''', (player1_id,)).fetchall()
        
        
    def sell_robot_bazar(self, user_id, robot_id, price):
        with self.connection:
            # Вибірка конкретного робота з таблиці user_robots
            self.cursor.execute(
                '''SELECT user_id, robot_id, name, max_health, damage, heal, armor, lvl FROM user_robots WHERE user_id = ? AND robot_id = ?''',
                (user_id, robot_id)
            )
            robot_record = self.cursor.fetchone()

            if robot_record is None:
                print("Robot not found")
                return 0

            # Добавляем параметр price в запрос INSERT
            self.cursor.execute(
                '''INSERT INTO bazar (seller, robot_id, name, health, damage, heal, armor, lvl, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                robot_record + (price,)
            )

            return 1
        
        
    def check_robot_status(self, robot_id, user_id):
        with self.connection:
            self.cursor.execute(
                '''SELECT status FROM user_robots WHERE user_id = ? AND robot_id = ?''',
                (user_id, robot_id)
            )
            status = self.cursor.fetchone()

            if status:
                return status[0]
            else:
                return None
            
            
    def check_bazar_robot_exist(self, robot_id, user_id):
        with self.connection:
            self.cursor.execute(
                '''SELECT COUNT(*) FROM bazar WHERE seller = ? AND robot_id = ? AND bought = 0''',
                (user_id, robot_id)  
            )
            count = self.cursor.fetchone()[0]

            if count > 0:
                return True
            else:
                return False
            

        
    def get_user_bazar_robots(self, user_id):
        with self.connection:
            self.cursor.execute(
                '''SELECT robot_id, name, health, damage, heal, armor, price FROM bazar WHERE seller = ? AND bought = 0''',
                (user_id,)
            )
            robots = self.cursor.fetchall()

            return robots
        
    def delete_robot_from_bazar(self,user_id, robot_id):
        with self.connection:
            self.cursor.execute('DELETE FROM bazar WHERE seller = ? AND robot_id =? ', (user_id, robot_id))
            
    def get_bazar_robot(self, robot_id, robot_seller):
        with self.connection:
            return self.cursor.execute('SELECT * FROM bazar WHERE robot_id = ? AND seller = ?', (robot_id, robot_seller)).fetchone()
        
    def transport_robot_from_seller_to_buyer(self, robot_seller, robot_id, user_id):
        with self.connection:
            self.cursor.execute("""
                UPDATE user_robots
                SET user_id = ?, status = 'unselected'
                WHERE user_id = ? AND robot_id = ?
            """, (user_id, robot_seller, robot_id))
            self.connection.commit()
            return self.cursor.rowcount > 0


    def set_bought_status(self, user_id, robot_seller, robot_id):
        with self.connection:
            self.cursor.execute("""
                UPDATE bazar
                SET bought = 1, buyer = ?
                WHERE seller = ? AND robot_id = ? AND bought = 0
            """, (user_id, robot_seller, robot_id))
            self.connection.commit()
            return self.cursor.rowcount > 0
        
        
    def add_improve_lvl(self, robot_id, user_id):
        with self.connection:
            self.cursor.execute("""
                UPDATE user_robots
                SET lvl = lvl + 1
                WHERE robot_id = ? AND user_id = ?
            """, (robot_id, user_id))
            self.connection.commit()
            return self.cursor.rowcount > 0


        


