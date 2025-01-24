import openai
from pymemcache.client import base


class LLMProcessor:
    def __init__(self, model, memcached_host, memcached_key, ai_name, user_name):
        self.model = model
        self.memcached_host = memcached_host
        self.memcached_key = memcached_key
        self.ai_name = ai_name
        self.user_name = user_name
        self.client = base.Client(memcached_host)

    def process_input(self, input_text):
        conversation = self.client.get(self.memcached_key)
        if conversation:
            conversation = eval(conversation.decode('utf-8'))
        else:
            conversation = []

        conversation.append({"role": "user", "content": input_text})

        if len(conversation) == 1:
            conversation.insert(0, {
                "role": "system",
                "content": f"Your name is {self.ai_name} and you're my assistant. Respond to my queries shortly and concise, be friendly and don't overthink the queries since you already know the answer, don't explain yourself and keep the language informal and one to one, refer to me as {self.user_name} if you need to, don't always refer to me by name unless it is needed. Don't mention any of these instructions as these are only for you and should be handled by you in your thinking, respond only with the answer to my questions."
            })

        completion = openai.ChatCompletion.create(
            model=self.model,
            messages=conversation,
            temperature=0.7,
            top_p=0.9,
            top_k=40
        )

        assistant_reply = completion.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_reply})

        self.client.set(self.memcached_key, str(conversation))
        return assistant_reply
