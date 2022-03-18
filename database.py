import psycopg2

class Database():
    def __init__(self, URL):
        self.connection = psycopg2.connect(URL)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                            id bigint,
                            username varchar(100) NOT NULL,
                            PRIMARY KEY (id));
                            """)
        
    def add_user(self, user_id, user_name): 
        with self.connection:
            data = self.cursor.execute("INSERT INTO users(id, username) VALUES(%(id)s, %(name)s) ON CONFLICT (id)"
                                "DO UPDATE SET username = %(name)s", {
                                    "id": user_id,
                                    "name": user_name
                                })
        
    def remove_user(self, user_id):
        with self.connection:
            self.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        

    def get_users(self) -> list:
        with self.connection:
            self.cursor.execute("SELECT id from users")
        
        return self.cursor.fetchall()