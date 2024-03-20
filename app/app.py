from datetime import datetime
from typing import List, Optional
from typing import Optional, Union
import aiofiles
import chainlit.data as cl_data
from chainlit.step import StepDict
from bson import ObjectId
import chainlit as cl
from pymongo import MongoClient
from typing import Optional
from langchain_community.chat_message_histories import MongoDBChatMessageHistory
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from operator import itemgetter
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
import sockets
from chainlit import sync
chat_message_history = MongoDBChatMessageHistory(
    session_id="test_session",
    connection_string="mongodb://m001-student:nani@sandbox-shard-00-00.4bigd.mongodb.net:27017,sandbox-shard-00-01.4bigd.mongodb.net:27017,sandbox-shard-00-02.4bigd.mongodb.net:27017/?replicaSet=atlas-q5gnca-shard-0&ssl=true&authSource=admin",
    database_name="my_db",
    collection_name="chat_histories",
)
atlas_uri = "mongodb://m001-student:nani@sandbox-shard-00-00.4bigd.mongodb.net:27017,sandbox-shard-00-01.4bigd.mongodb.net:27017,sandbox-shard-00-02.4bigd.mongodb.net:27017/?replicaSet=atlas-q5gnca-shard-0&ssl=true&authSource=admin"
client = MongoClient(atlas_uri)
database = client["chainlit"]
collection = database["chat_conversations"]
now = datetime.utcnow().isoformat()
user_dict = {"id": "test", "createdAt": now, "identifier": "admin"}


thread_history = [
    {
        "createdAt": now,
        "id": "ba9d6d84-41b4-4554-ac0d-5df989d793c2",
        "name": "hi",
        "steps": [
            {
                "createdAt": now,
                "id": "7899f391-bb6d-402f-828c-a7b4c8721c02",
                "threadId": "ba9d6d84-41b4-4554-ac0d-5df989d793c2",
                "parentId": None,
                "feedback": None,
                "start": now,
                "end": now,
                "type": "user_message",
                "name": "admin",
                "generation": None,
                "input": "",
                "output": "hi",
                "showInput": None,
                "disableFeedback": False,
                "indent": None,
                "language": None,
                "isError": False,
                "waitForAnswer": False
            },
            {
                "createdAt": now,
                "id": "3d504777-a35d-4416-a72d-b816c835e7af",
                "threadId": "ba9d6d84-41b4-4554-ac0d-5df989d793c2",
                "parentId": "7899f391-bb6d-402f-828c-a7b4c8721c02",
                "feedback": None,
                "start": now,
                "end": now,
                "type": "run",
                "name": "load_memory_variables",
                "generation": None,
                "input": '{"input": ""}',
                "output": "[]",
                "showInput": False,
                "disableFeedback": True,
                "indent": None,
                "language": "text",
                "isError": False,
                "waitForAnswer": None
            },
            {
                "createdAt": now,
                "id": "74f3e14e-3589-4950-8030-ff507b45a158",
                "threadId": "ba9d6d84-41b4-4554-ac0d-5df989d793c2",
                "parentId": "7899f391-bb6d-402f-828c-a7b4c8721c02",
                "feedback": None,
                "start": now,
                "end": now,
                "type": "llm",
                "name": "ChatOpenAI",
                "generation": {
                    "provider": "openai-chat",
                    "model": "gpt-3.5-turbo",
                    "error": None,
                    "settings": {
                        "n": 1,
                        "stop": None,
                        "model": "gpt-3.5-turbo",
                        "stream": True,
                        "streaming": True,
                        "model_name": "gpt-3.5-turbo",
                        "temperature": 0.7
                    },
                    "variables": {
                        "input": ""
                    },
                    "tags": [],
                    "tools": None,
                    "tokenCount": 16,
                    "inputTokenCount": 7,
                    "outputTokenCount": 9,
                    "ttFirstToken": 1248.6145496368408,
                    "tokenThroughputInSeconds": 8.104821363950968,
                    "duration": 1.3572168350219727,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful chatbot"
                        },
                        {
                            "role": "user",
                            "content": "hi"
                        }
                    ],
                    "messageCompletion": None,
                    "type": "CHAT"
                },
                "input": '{"prompts": ["System: You are a helpful chatbot\\nHuman: hi"]}',
                "output": '{"role": "assistant", "content": "Hello! How can I help you today?"}',
                "showInput": False,
                "disableFeedback": False,
                "indent": None,
                "language": "json",
                "isError": False,
                "waitForAnswer": None
            },
            {
                "createdAt": now,
                "id": "079cc241-a70d-4ecf-b1b5-2c7c95136758",
                "threadId": "ba9d6d84-41b4-4554-ac0d-5df989d793c2",
                "parentId": None,
                "feedback": None,
                "start": now,
                "end": now,
                "type": "assistant_message",
                "name": "Chatbot",
                "generation": None,
                "input": "",
                "output": "Hello! How can I help you today?",
                "showInput": None,
                "disableFeedback": False,
                "indent": None,
                "language": None,
                "isError": False,
                "waitForAnswer": False
            }
        ],
        "elements": [],
        "metadata": {
            "id": "39db0c21-44f6-4110-a0c0-b52c7237fbb2",
            "env": "{}",
            "user": None,
            "memory": None,
            "runnable": None,
            "chat_profile": "",
            "root_message": None,
            "chat_settings": {}
        },
        "user": user_dict,
        "tags": []
    }
]
create_step_counter = 0

deleted_thread_ids = []  # type: List[str]


class TestDataLayer(cl_data.BaseDataLayer):
    async def get_user(self, identifier: str):
        return cl.PersistedUser(id="test", createdAt=now, identifier=identifier)

    async def create_user(self, user: cl.User):
        return cl.PersistedUser(id="test", createdAt=now, identifier=user.identifier)

    @cl_data.queue_until_user_message()
    async def create_step(self, step_dict: StepDict):
        global create_step_counter
        create_step_counter += 1

    async def get_thread_author(self, thread_id: str):
        return "admin"

    async def list_threads(
        self, pagination: cl_data.Pagination, filter: cl_data.ThreadFilter
    ) -> cl_data.PaginatedResponse[cl_data.ThreadDict]:
        return cl_data.PaginatedResponse(
            data=[t for t in thread_history if t["id"] not in deleted_thread_ids],
            pageInfo=cl_data.PageInfo(hasNextPage=False, endCursor=None),
        )

    async def get_thread(self, thread_id: str):
        return next((t for t in thread_history if t["id"] == thread_id), None)

    async def delete_thread(self, thread_id: str):
        deleted_thread_ids.append(thread_id)


cl_data._data_layer = TestDataLayer()
 

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
@cl.on_chat_start
async def main():
    # await cl.Message("Hello, send me a message!", disable_feedback=True).send()
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True))
    cl.user_session.set("chat_history",[] )
    setup_runnable()
 

from langchain.schema.runnable.config import RunnableConfig
@cl.on_message
async def handle_message(message: cl.Message):
    chat_history = cl.user_session.get("chat_history")
    memory = cl.user_session.get("memory")   
    runnable = cl.user_session.get("runnable")   
    res = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await res.stream_token(chunk)

    await res.send()  
    # chat_history.append({"user": message.content, "bot": res})  
    cl.user_session.set("chat_history", chat_history)   
 
 


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin")
    else:
        return None


@cl.on_chat_resume
async def on_chat_resume(thread: cl_data.ThreadDict): 
    # await cl.Message(f"Welcome back to {thread['name']}").send()
    memory = cl.user_session.get("memory")  # Attempt to retrieve memory from user session
    if memory is None:
        # If memory is not set, instantiate it and save it in the user session
        memory = ConversationBufferMemory(return_messages=True) 
        cl.user_session.set("memory", memory)
    # conversation_list = []
    # Now that we have ensured memory is not None, proceed to add messages to chat_memory
    root_messages = [m for m in thread["steps"] if m["parentId"] is None]
    for message in root_messages:
        if message["parentId"] is None:
            message_data = {
                "id": message["id"],
                "type": message["type"],
                "content": message["output"]
            }
            # Add the message data dictionary to the list
            # conversation_list.append(message_data)
            if message["type"] == "USER_MESSAGE":
                memory.chat_memory.add_user_message(message["output"])
            else:
                memory.chat_memory.add_ai_message(message["output"])

    def format_thread(thread_history: List[Dict]) -> str:
        formatted_thread = []

        for thread in thread_history:
            thread_data = {
                "thread_id": thread['id'],
                "user": thread['user']['identifier'],
                "created_at": thread['createdAt'],
                "steps": []
            }

            for step in thread['steps']:
                step_data = {
                    "step_id": step['id'],
                    "type": step['type'],
                    "name": step['name'],
                    "start_time": step['start'],
                    "end_time": step['end']
                }

                if step['type'] == 'user_message':
                    step_data["user_input"] = step['output']
                    # Add user message to chat memory
                    memory.chat_memory.add_user_message(step['output'])
                elif step['type'] == 'assistant_message':
                    step_data["assistant_output"] = step['output']
                    # Add AI message to chat memory
                    memory.chat_memory.add_ai_message(step['output'])
                elif step['type'] == 'run':
                    step_data["run_input"] = step['input']
                    step_data["run_output"] = step['output']

                thread_data["steps"].append(step_data)

            formatted_thread.append(thread_data)

        return json.dumps(formatted_thread, indent=2)
    # Example usage
    formatted_thread_json = format_thread(thread_history)
    # print(formatted_thread_json)

    setup_runnable()


@cl.on_chat_end
def on_chat_end():
    chat_history = cl.user_session.get("chat_history")
    
    if chat_history:
        session_id = cl.user_session.get("id")
        chat_history_archive = {}
        chat_history_archive[session_id] = chat_history
        documents_to_insert = [chat_history_archive]
        result = collection.insert_many(documents_to_insert)
 


 
from typing import List, Dict
import json



import sockets