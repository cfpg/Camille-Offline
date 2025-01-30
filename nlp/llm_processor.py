import logging
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.schema import SystemMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode
from tools import get_all_tools
from config import OPENAI_API_BASE, OPENAI_KEY, DB_URI
from utils.colors import colors


logger = logging.getLogger(__name__)

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

        logger.debug("Initializing LLMProcessor with model=%s, ai_name=%s, user_name=%s", model, ai_name, user_name)

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
        logger.debug("System prompt initialized")

        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=self.model,
            temperature=0.7,
            openai_api_base=OPENAI_API_BASE,
            openai_api_key=OPENAI_KEY
        )
        logger.debug("LLM initialized with model_name=%s, temperature=0.7", self.model)

        # Initialize memory
        try:
            with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
                checkpointer.setup()

                self.workflow = StateGraph(MessagesState)
                self.workflow.add_node("agent", self._call_agent)
                self.workflow.add_edge(START, "agent")
                self.app = self.workflow.compile(checkpointer=checkpointer)
                self.checkpointer = checkpointer
        except Exception as e:
            logger.error("Failed to initialize PostgresSaver or StateGraph: %s", str(e), exc_info=True)
            raise

        # Initialize agent with all registered tools
        # self.agent = initialize_agent(
        #     get_all_tools(),
        #     self.llm,
        #     agent="chat-conversational-react-description",
        #     memory=self.memory,
        #     verbose=True,
        #     handle_parsing_errors=True
        # )
    
    def _call_agent(self, state: MessagesState):
        logger.debug("Calling agent with state: %s", state)

        try:
            messages = [self.system_prompt] + state["messages"]
            agent = initialize_agent(
                get_all_tools(),
                self.llm,
                agent="chat-conversational-react-description",
                verbose=True,
                handle_parsing_errors=True
            )
            response = agent.run(messages)
            return {"messages": [AIMessage(content=response)]}
        except Exception as e:
            logger.error("Error in _call_agent: %s", str(e), exc_info=True)
            raise
    
    def _add_system_message(self):
        """Add the system message to memory."""
        self.memory.chat_memory.add_message(
            SystemMessage(content=self.system_prompt))

    def clear_memory(self):
        """
        Clear the conversation memory.
        Useful for starting a new conversation context.
        """
        self.memory.clear()
        self._add_system_message()

    def process_input(self, input_text):
        """
        Process user input and generate a response using conversation history.

        Args:
            input_text (str): The user's input text.

        Returns:
            str: The AI's response.
        """
        print(f"{colors['cyan']}User input: {input_text}{colors['reset']}")
        config = {"configurable": {"thread_id": "1"}}
        input_message = HumanMessage(content=input_text)
        
        for event in self.app.stream(
            {"messages": [input_message]}, 
            config, 
            stream_mode="values"
        ):
            if "messages" in event:
                return event["messages"][-1].content
        return "Sorry, I couldn't process that request."
