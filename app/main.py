from operator import itemgetter

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory

from chainlit.types import ThreadDict
import chainlit as cl
from operator import itemgetter
from pymongo import MongoClient
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory
from chainlit.types import ThreadDict
import chainlit as cl
# MongoDB connection setup
# atlas_uri = "mongodb://your-mongodb-uri"
atlas_uri = "mongodb://m001-student:nani@sandbox-shard-00-00.4bigd.mongodb.net:27017,sandbox-shard-00-01.4bigd.mongodb.net:27017,sandbox-shard-00-02.4bigd.mongodb.net:27017/?replicaSet=atlas-q5gnca-shard-0&ssl=true&authSource=admin"

client = MongoClient(atlas_uri)
database = client["your_database"]
collection = database["chat_conversations"]
def store_chat_history(user_id, conversation):
    # Store conversation history in MongoDB
    collection.insert_one({"user_id": user_id, "content": conversation})

def retrieve_chat_history(user_id):
    # Retrieve conversation history from MongoDB
    history = collection.find({"user_id": user_id}).sort("timestamp", 1)

    # Reassemble conversation context from retrieved messages
    conversation_context = []
    for message in history:
        conversation_context.append(message["content"])

    return conversation_context
def setup_runnable():
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory
    model = ChatOpenAI(streaming=True)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful chatbot"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    runnable = (
        RunnablePassthrough.assign(
            history=RunnableLambda(memory.load_memory_variables) | itemgetter("history")
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable)


@cl.password_auth_callback
def auth():
    return cl.User(identifier="test")


@cl.on_chat_start
async def on_chat_start():
    user_id = "123"  # Replace with actual user identifier
    # Retrieve chat history from MongoDB
    conversation_history = retrieve_chat_history(user_id)
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True, chat_history=conversation_history))
    setup_runnable()


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    user_id = "123"  # Replace with actual user identifier
    # Retrieve chat history from MongoDB
    conversation_history = retrieve_chat_history(user_id)
    memory = ConversationBufferMemory(return_messages=True, chat_history=conversation_history)
    root_messages = [m for m in thread["steps"] if m["parentId"] == None]
    for message in root_messages:
        if message["type"] == "USER_MESSAGE":
            memory.chat_memory.add_user_message(message["output"])
        else:
            memory.chat_memory.add_ai_message(message["output"])

    cl.user_session.set("memory", memory)

    setup_runnable()


@cl.on_message
async def on_message(message: cl.Message):
    user_id = "123"
    memory = cl.user_session.get("memory")  # type: ConversationBufferMemory

    runnable = cl.user_session.get("runnable")  # type: Runnable

    res = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await res.stream_token(chunk)

    await res.send()

    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content) 