import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get('OPEN_AI_KEY')

prompt = "Once upon a time"

completion = openai.Completion.create(
    engine="davinci",
    prompt=prompt,
    max_tokens=10,
    temperature=1,
    stop="\n"
)

print(prompt + completion["choices"][0]["text"])