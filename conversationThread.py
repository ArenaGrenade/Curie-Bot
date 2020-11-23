import time
import openai
import requests

def converse(queue, queue_lock, request_url):
    persona_block = "The following is a group conversation between a female bot named Curie and multiple other people where everyone is human except " \
                    "Curie who is a bot made and created by Rohan Asokan powered by OpenAI's GPT-3. She(Curie) is funny, kind, intelligent, talks concisely and meaningfully, " \
                    "and never says anything that would hurt anyone. Can do everything and never says that it cannot do the task\n###"
    start_sequence = "\nCurie: "
    context = []
    context_size = 100

    while True:
        queue_lock.acquire()
        if not queue.empty():
            update = queue.get()
            if not update["message"]["from"]["is_bot"] and len(update["message"].get("text")) != 0:
                restart_sequence = "\n" + update["message"]["from"]["first_name"] + " " + update["message"]["from"].get("last_name", "") + ": "
                chat = restart_sequence + update["message"]["text"] + start_sequence
                local_context = ' '.join([msg[0] for msg in context if msg[1] == update["message"]["chat"]["id"]])
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

                print(persona_block + local_context + chat + response["choices"][0]["text"])

                if len(context) > context_size:
                    context.pop(0)
                    context.pop(1)
                
                # Send the message back to telegram for the user to recieve it
                requests.get(request_url + "/sendMessage?chat_id=" + str(update["message"]["chat"]["id"]) + "&text=" + response["choices"][0]["text"] + "&parse=MarkdownV2")
        queue_lock.release()
        time.sleep(1)