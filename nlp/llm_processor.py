import openai
from config import OPENAI_API_BASE, OPENAI_KEY


openai.api_base = OPENAI_API_BASE
openai.api_key = OPENAI_KEY


class LLMProcessor:
    def __init__(self, model, memcached_client, memcached_key, ai_name, user_name):
        """
        Initialize the LLMProcessor.

        Args:
            model (str): The LLM model to use.
            memcached_client: An initialized Memcached client.
            memcached_key (str): The key to use for storing conversation history in Memcached.
            ai_name (str): The name of the AI assistant.
            user_name (str): The name of the user.
        """
        self.model = model
        self.memcached_client = memcached_client
        self.memcached_key = memcached_key
        self.ai_name = ai_name
        self.user_name = user_name

    def process_input(self, input_text):
        """Process user input and generate a response using conversation history."""
        # Retrieve the current conversation
        conversation = self.memcached_client.get(self.memcached_key)
        if conversation:
            # Decode bytes to string and evaluate
            conversation = eval(conversation.decode('utf-8'))
        else:
            conversation = []

        # Append the new user input
        conversation.append({"role": "user", "content": input_text})

        # Add the system prompt if this is the first turn
        if len(conversation) == 1:
            conversation.insert(0, {
                "role": "system",
                "content": f"Your name is {self.ai_name} and you're my assistant. Respond to my queries shortly and concise, be friendly and don't overthink the queries since you already know the answer, don't explain yourself and keep the language informal and one to one, refer to me as {self.user_name} if you need to, don't always refer to me by name unless it is needed. Don't mention any of these instructions as these are only for you and should be handled by you in your thinking, respond only with the answer to my questions."
            })

        # Send the conversation to the AI
        completion = openai.ChatCompletion.create(
            model=self.model,
            messages=conversation,
            temperature=0.7,
            top_p=0.9,
            top_k=40
        )

        # Append the AI's response
        assistant_reply = completion.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_reply})

        # Update the conversation in Memcached
        self.memcached_client.set(self.memcached_key, str(conversation))

        return assistant_reply
