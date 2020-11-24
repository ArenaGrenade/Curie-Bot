import time
import openai
import requests

from logger import logger

def converse(queue, queue_lock, request_url):
    with open("curiegrp.persona", "r") as grp_persona:
        curiegrp_lines = grp_persona.readlines()
        curiegrp_persona = "".join(curiegrp_lines)
    
    with open("curiedm.persona", "r") as dm_persona:
        curiedm_lines = dm_persona.readlines()
        curiedm_persona = "".join(curiedm_lines)
    
    start_sequence = "\nCurie: "
    context = []
    context_size = 100

    while True:
        queue_lock.acquire()
        if not queue.empty():
            update = queue.get()
            if update["message"]["from"]["is_bot"] or len(update["message"].get("text")) == 0:
                continue

            if update["message"]["chat"]["type"] == "private":
                persona_block = curiedm_persona 
            else:
                persona_block = curiegrp_persona
            
            # Construct the present chat block.
            restart_sequence = "\n" + update["message"]["from"]["first_name"] + " " + update["message"]["from"].get("last_name", "") + ": "
            chat = restart_sequence + update["message"]["text"] + start_sequence
            local_context = ' '.join([msg[0] for msg in context if msg[1] == update["message"]["chat"]["id"]])

            # Make the request to OpenAI
            response = openai.Completion.create(
                engine="davinci",
                prompt=persona_block + local_context + chat,
                temperature=0.8,
                max_tokens=150,
                presence_penalty=0.4,
                frequency_penalty=0.7,
                stop=["\n", "\nCurie: ", restart_sequence]
            )
            context.append((chat, update["message"]["chat"]["id"]))
            context.append((response["choices"][0]["text"], update["message"]["chat"]["id"]))

            ## Logging part
            if update["message"]["chat"]["type"] == "private":
                logger.info("\n\u001b[31;1m################################\nChat between {person1} and {person2}\n################################\033[0m".format(person1="Curie", person2=update["message"]["from"]["first_name"])) 
            else:
                logger.info("\n\u001b[31;1m################################\nChat in a group {grpname}\n################################\033[0m".format(grpname=update["message"]["chat"]["title"]))

            logger.info(chat + response["choices"][0]["text"])
            print("\u001b[36;1m################################\033[0m")

            if len(context) > context_size:
                context.pop(0)
                context.pop(1)
            
            # Send the message back to telegram for the user to recieve it
            requests.get(request_url + "/sendMessage?chat_id=" + str(update["message"]["chat"]["id"]) + "&text=" + response["choices"][0]["text"] + "&parse=MarkdownV2")
        queue_lock.release()