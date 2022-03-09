import sqlite3

class Database():
    def __init__(self, file_path):
        self.connection = sqlite3.connect(file_path)
        self.cursor = self.connection.cursor()
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                            id integer PRIMARY KEY,
                            username text NOT NULL);
                            """)
        
    def add_user(self, user_id, user_name): 
        with self.connection:
            data = self.cursor.execute("INSERT INTO users(id, username) VALUES(?, ?) ON CONFLICT (id)"
                                "DO UPDATE SET username = ?", (user_id, user_name, user_name, ))
        
    def remove_user(self, user_id):
        with self.connection:
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        

    def get_users(self) -> list:
        with self.connection:
            data = self.cursor.execute("SELECT id from users").fetchall()
        
        return data