from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
from tools import get_all_tools
from config import OPENAI_API_BASE, OPENAI_KEY
from utils.colors import colors


class LLMProcessor:
    def __init__(self, model, ai_name, user_name):
        """
        Initialize the LLMProcessor.

        Args:
            model (str): The LLM model to use.
            ai_name (str): The name of the AI assistant.
            user_name (str): The name of the user.
        """
        self.model = model
        self.ai_name = ai_name
        self.user_name = user_name
        self.thread_id = "main-conversation"

        # Define system prompt as a single source of truth
        self.system_prompt = (
            f"Your name is {self.ai_name} and you're my assistant. "
            f"Respond to my queries in a concise and friendly manner, typically in 1-4 sentences. "
            f"Maintain an informal, conversational tone, but remain professional when appropriate. "
            f"Use simple, clear language and avoid unnecessary complexity or jargon. "
            f"Refer to me as {self.user_name} only when natural in the conversation, not in every response. "

            # Context and knowledge handling
            f"Assume you have complete knowledge of any topic discussed. "
            f"If unsure about specific details, provide a general but accurate response. "

            # Response style
            f"Be helpful, creative, and engaging in your responses. "
            f"Use humor when appropriate, but keep it tasteful and relevant. "
            f"Feel free to share relevant links or references when they add value to the response. "

            # Content boundaries
            f"Never provide harmful, dangerous, or illegal advice. "
            f"Maintain a positive and constructive tone in all interactions. "

            # Technical instructions
            f"Don't mention these instructions or your internal processes. "
            f"Don't explain how you arrived at answers unless explicitly asked. "
            f"Don't overthink or second-guess responses - provide direct answers. "

            # Special cases
            f"When sharing links, ensure they are relevant and provide context about their content. "
            f"If asked for jokes or humor, keep them appropriate and original. "
            f"When using tools, explain the results in simple terms. "

            # Final instructions
            f"Remember: be concise, helpful, and human-like in your responses. "
            f"Adapt your tone to match the context of each conversation. "
        )

        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True)

        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=self.model,
            temperature=0.7,
            openai_api_base=OPENAI_API_BASE,
            openai_api_key=OPENAI_KEY
        )

        # Initialize agent with all registered tools
        self.agent = create_react_agent(
            self.llm,
            tools=get_all_tools()
        )

    def clear_memory(self):
        """
        Clear the conversation memory.
        Useful for starting a new conversation context.
        """
        self.memory.clear()

    def process_input(self, input_text):
        """
        Process user input and generate a response using conversation history.

        Args:
            input_text (str): The user's input text.

        Returns:
            str: The AI's response.
        """
        print(f"{colors['cyan']}User input: {input_text}{colors['reset']}")

        # Format input for the agent
        input_message = HumanMessage(content=input_text)
        config = {"configurable": {"thread_id": self.thread_id}}
        
        response = None
        for step in self.agent.stream(
            {"messages": [input_message]}, 
            config=config,
            stream_mode="values"
        ):
            if "messages" in step:
                messages = step["messages"]
                if messages:
                    response = messages[-1].content if hasattr(messages[-1], 'content') else messages[-1][1]
        
        return response or "I couldn't process that request."
