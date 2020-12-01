import psycopg2
import datetime
import threading

class chatDB:
    def __init__(self, database, user, password, host, port):
        self.connection = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        self.cursor = self.connection.cursor()
        self.proc_lock = threading.Lock()

    def create_table(self):
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS MESSAGE
                            (MSGID INT PRIMARY KEY NOT NULL,
                            CHATID INT NOT NULL,
                            SENDER CHAR(255) NOT NULL,
                            MESSAGE TEXT NOT NULL,
                            DATETIME DATE NOT NULL);""")
        self.connection.commit()

    def get_messages_in_chat(self, chat):
        self.cursor.execute("""SELECT *
                            FROM MESSAGE
                            WHERE CHATID = '{chat}'
                            ORDER BY DATETIME""".format(chat=chat))
        result = self.cursor.fetchall()
        # print(result)
        return result

    def add_message(self, msg_id, chat_id, sender, message):
        self.proc_lock.acquire()

        # print("Starting the entry of {name}: {msg}".format(name=msg_id, msg=message))

        time = datetime.datetime.utcnow().isoformat()
        self.cursor.execute("""INSERT INTO MESSAGE (MSGID, CHATID, SENDER, MESSAGE, DATETIME) VALUES({mid}, {cid}, '{s}', '{m}', '{t}') ON CONFLICT(MSGID) DO NOTHING;""".format(mid=msg_id, cid=chat_id, s=sender.replace("\'", "\'\'"), m=message.replace("\'", "\'\'"), t=time))
        self.connection.commit()

        self.proc_lock.release()

    def close_connection(self):
        # Commit all the changes made to the database
        self.connection.commit()

        # Close the actual connection to the database
        self.connection.close()
