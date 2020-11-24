import openai

import requests
import queue
import time
import threading
import time

from telegramPollThread import pollThread
from conversationThread import converse

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Creds
openai.api_key = os.environ.get('OPENAI_KEY')
print("Connected to OpenAI API")

# Telegram Creds
http_request_url = "https://api.telegram.org/bot" + os.environ.get('TG_BOT_KEY')

# Function and data for the queue of bot messages
queue_lock = threading.Lock()

workQueue = queue.Queue(30)
threads = []

threads.append(threading.Thread(target=pollThread, args=[workQueue, queue_lock, http_request_url]))
print("Created polling thread")
threads.append(threading.Thread(target=converse, args=[workQueue, queue_lock, http_request_url]))
print("Created Conversation thread")

threads[0].start()
threads[1].start()

# Wait for all threads to complete
for t in threads:
    t.join()