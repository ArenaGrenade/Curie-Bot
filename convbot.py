import openai

import requests
import queue
import time
import threading
import time
import signal

from telegramPollThread import pollThread
from conversationThread import converse
from chatDB import chatDB

import os
from dotenv import load_dotenv

load_dotenv()

MAX_THREADS = 2

# OpenAI Creds
openai.api_key = os.environ.get('OPENAI_KEY')
print("Connected to OpenAI API")

# Telegram Creds
http_request_url = "https://api.telegram.org/bot" + os.environ.get('TG_BOT_KEY')

# Postgres database Creds
db_url = os.environ.get('DB_URL')
database_obj = chatDB(
    "dc4u58bklubius", 
    "hlybalsqrzybbi", 
    "54df3d4318e3db112b66d1c48a2dfff6f458fcf83408bc0eeffa33d02f30f803",
    "ec2-52-203-182-92.compute-1.amazonaws.com",
    5432
)
database_obj.create_table()

# Function and data for the queue of bot messages
queue_lock = threading.Lock()

workQueue = queue.Queue(30)
threads = []

threads.append(threading.Thread(target=pollThread, args=[workQueue, queue_lock, http_request_url]))
print("Created polling thread")
threads[0].start()

for threadID in range(1, MAX_THREADS):
    threads.append(threading.Thread(target=converse, args=[workQueue, queue_lock, http_request_url, database_obj]))
    threads[threadID].start()
    print("Created Conversation Thread {id}".format(id = threadID))

# Wait for all threads to complete
for t in threads:
    t.join()