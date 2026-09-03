import sqlite3

class Database:
    def __init__(self, db_path='linguaforge.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS common_words (
                words_id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_word TEXT UNIQUE NOT NULL,
                russian_word TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_words (
                userwords_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                english_word TEXT NOT NULL,
                russian_word TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, english_word)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                correct INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        self.conn.commit()

    def get_or_create_user(self, username):
        self.cursor.execute('INSERT OR IGNORE INTO users (username) VALUES (?)', (username,))
        self.conn.commit()
        self.cursor.execute('SELECT user_id, username FROM users WHERE username = ?', (username,))
        row = self.cursor.fetchone()
        # Если пользователь только что создан – добавим запись в статистику
        self.cursor.execute('INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)', (row[0],))
        self.conn.commit()
        return {'user_id': row[0], 'username': row[1]}

    def add_user_word(self, user_id, english, russian):
        try:
            self.cursor.execute('''
                INSERT INTO user_words (user_id, english_word, russian_word)
                VALUES (?, ?, ?)
            ''', (user_id, english, russian))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_words(self, user_id):
        self.cursor.execute('''
            SELECT userwords_id, english_word, russian_word
            FROM user_words WHERE user_id = ?
        ''', (user_id,))
        rows = self.cursor.fetchall()
        return [{'userwords_id': r[0], 'english_word': r[1], 'russian_word': r[2]} for r in rows]

    def delete_user_word(self, user_id, word_id):
        self.cursor.execute('DELETE FROM user_words WHERE user_id = ? AND userwords_id = ?', (user_id, word_id))
        self.conn.commit()

    def get_common_words(self):
        self.cursor.execute('SELECT words_id, english_word, russian_word FROM common_words')
        rows = self.cursor.fetchall()
        return [{'words_id': r[0], 'english_word': r[1], 'russian_word': r[2]} for r in rows]

    def update_stats(self, user_id, correct):
        if correct:
            self.cursor.execute('''
                UPDATE user_stats SET correct = correct + 1, total = total + 1
                WHERE user_id = ?
            ''', (user_id,))
        else:
            self.cursor.execute('''
                UPDATE user_stats SET total = total + 1
                WHERE user_id = ?
            ''', (user_id,))
        self.conn.commit()

    def get_stats(self, user_id):
        self.cursor.execute('SELECT correct, total FROM user_stats WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        return {'correct': row[0] or 0, 'total': row[1] or 0} if row else {'correct': 0, 'total': 0}

    def get_all_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in self.cursor.fetchall()]

    def get_table_schema(self, table_name):
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        return self.cursor.fetchall()  # список кортежей (cid, name, type, notnull, dflt_value, pk)

    def close(self):
        self.conn.close()