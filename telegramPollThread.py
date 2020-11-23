import threading
import requests

def pollThread(queue, queue_lock, request_url):
    uid = 0
    while True:
        updates = requests.get(request_url + "/getUpdates?offset=" + str(uid)).json()
        if len(updates["result"]) > 0:
            queue_lock.acquire()
            for update in updates["result"]:
                pupdate = 0
                if "message" in update:
                    if "from" in update["message"]:
                        if (("first_name" in update["message"]["from"]) or ("last_name" in update["message"]["from"])) and ("is_bot" in update["message"]["from"]):
                            pupdate = pupdate + 1
                    if "text" in update["message"]:
                        pupdate = pupdate + 1
                if pupdate == 2:
                    q.put(update)
                uid = update["update_id"] + 1
            queue_lock.release()