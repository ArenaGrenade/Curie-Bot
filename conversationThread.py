import time
import openai
import requests
import threading

from logger import logger

def converse(queue, queue_lock, request_url, db_obj):
    with open("curiegrp.persona", "r") as grp_persona:
        curiegrp_lines = grp_persona.readlines()
        curiegrp_persona = "".join(curiegrp_lines)
    
    with open("curiedm.persona", "r") as dm_persona:
        curiedm_lines = dm_persona.readlines()
        curiedm_persona = "".join(curiedm_lines)
    
    context = []
    context_size = 100

    while True:
        queue_lock.acquire()
        if not queue.empty():
            update = queue.get()
            if update["message"]["from"]["is_bot"] or len(update["message"].get("text")) == 0:
                queue_lock.release()
                continue

            if update["message"]["chat"]["type"] == "private":
                persona_block = curiedm_persona
            else:
                persona_block = curiegrp_persona

            # Some information about the message
            message = update["message"]
            name = message["from"]["first_name"] + " " + message["from"].get("last_name", "")
            chat_id = message["chat"]["id"]
            if update["message"]["chat"]["type"] != "private":
                chat_name = message["chat"]["title"]
            text = message["text"]

            # Initiate the store of user message
            user_msg_store_thread = threading.Thread(target=db_obj.add_message, args=(message["message_id"], chat_id, name, text))
            user_msg_store_thread.start()
            
            # Construct the present chat block.
            start_sequence = "\nCurie: "
            restart_sequence = "\n" + name + ": "

            chat = restart_sequence + text
            
            # Get the current chat's context.
            local_context = ' '.join([msg[0] for msg in context if msg[1] == chat_id])
            # db_obj.get_messages_in_chat(chat_id)

            # Make the request to OpenAI
            response = openai.Completion.create(
                engine="davinci",
                prompt=persona_block + local_context + chat + start_sequence,
                temperature=0.8,
                max_tokens=150,
                presence_penalty=0.4,
                frequency_penalty=0.7,
                stop=["\n", "\nCurie: ", restart_sequence]
            )
            response_text = response["choices"][0]["text"]

            # Add the message and the response to the chat's context
            context.append((chat, chat_id))
            context.append((start_sequence + response_text, chat_id))

            bot_msg_store_thread = threading.Thread(target=db_obj.add_message, args=(message["message_id"], chat_id, "Curie", response_text))
            bot_msg_store_thread.start()

            ## Logging the messages.
            if update["message"]["chat"]["type"] == "private":
                logger.info("\n\u001b[31;1m################################\nChat between {person1} and {person2}\n################################\033[0m".format(person1="Curie", person2=name)) 
            else:
                logger.info("\n\u001b[31;1m################################\nChat in a group {grpname}\n################################\033[0m".format(grpname=chat_name))

            logger.info(chat + start_sequence + response_text)
            print("\u001b[36;1m################################\033[0m")

            # Update so that max sizes works
            if len(context) > context_size:
                context.pop(0)
                context.pop(1)
            
            # Send the message back to telegram for the user to recieve it
            requests.get(request_url + "/sendMessage?chat_id=" + str(chat_id) + "&text=" + response_text + "&parse=MarkdownV2")

            user_msg_store_thread.join()
            bot_msg_store_thread.join()
        queue_lock.release()