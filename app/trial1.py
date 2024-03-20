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

chat_message_history = MongoDBChatMessageHistory(
    session_id="test_session",
    connection_string="mongodb://m001-student:nani@sandbox-shard-00-00.4bigd.mongodb.net:27017,sandbox-shard-00-01.4bigd.mongodb.net:27017,sandbox-shard-00-02.4bigd.mongodb.net:27017/?replicaSet=atlas-q5gnca-shard-0&ssl=true&authSource=admin",
    database_name="my_db",
    collection_name="chat_histories",
)
atlas_uri = "mongodb://m001-student:nani@sandbox-shard-00-00.4bigd.mongodb.net:27017,sandbox-shard-00-01.4bigd.mongodb.net:27017,sandbox-shard-00-02.4bigd.mongodb.net:27017/?replicaSet=atlas-q5gnca-shard-0&ssl=true&authSource=admin"

client = MongoClient(atlas_uri)
database = client["chainlit"]

# Access a specific collection within the database
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
  # type: List[cl_data.ThreadDict]

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
    print(memory)
    # chat_history.append({"user": message.content, "bot": res})  
    cl.user_session.set("chat_history", chat_history)   
    memory.chat_memory.add_user_message(message.content)
    memory.chat_memory.add_ai_message(res.content) 
 


@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin")
    else:
        return None


@cl.on_chat_resume
async def on_chat_resume(thread: cl_data.ThreadDict):
    print(thread)
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

from ast import Dict
from operator import itemgetter
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory
from pymongo import MongoClient
from chainlit.types import ThreadDict
import chainlit as cl
from typing import Optional
import jwt
from datetime import datetime, timedelta
from chainlit.auth import create_jwt
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
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




import functools
import json
import os
from collections import deque
from typing import TYPE_CHECKING, Dict, List, Optional, Union

import aiofiles
from chainlit.config import config
from chainlit.context import context
from chainlit.logger import logger
from chainlit.session import WebsocketSession
from chainlit.types import Feedback, Pagination, ThreadDict, ThreadFilter
from chainlit.user import PersistedUser, User, UserDict
from literalai import Attachment
from literalai import Feedback as ClientFeedback
from literalai import PageInfo, PaginatedResponse
from literalai import Step as ClientStep
from literalai.step import StepDict as ClientStepDict
from literalai.thread import NumberListFilter, StringFilter, StringListFilter
from literalai.thread import ThreadFilter as ClientThreadFilter

if TYPE_CHECKING:
    from chainlit.element import Element, ElementDict
    from chainlit.step import FeedbackDict, StepDict

_data_layer = None


def queue_until_user_message():
    def decorator(method):
        @functools.wraps(method)
        async def wrapper(self, *args, **kwargs):
            if (
                isinstance(context.session, WebsocketSession)
                and not context.session.has_first_interaction
            ):
                # Queue the method invocation waiting for the first user message
                queues = context.session.thread_queues
                method_name = method.__name__
                if method_name not in queues:
                    queues[method_name] = deque()
                queues[method_name].append((method, self, args, kwargs))

            else:
                # Otherwise, Execute the method immediately
                return await method(self, *args, **kwargs)

        return wrapper

    return decorator


class BaseDataLayer:
    """Base class for data persistence."""

    async def get_user(self, identifier: str) -> Optional["PersistedUser"]:
        return None

    async def create_user(self, user: "User") -> Optional["PersistedUser"]:
        pass

    async def upsert_feedback(
        self,
        feedback: Feedback,
    ) -> str:
        return ""

    @queue_until_user_message()
    async def create_element(self, element_dict: "ElementDict"):
        pass

    async def get_element(
        self, thread_id: str, element_id: str
    ) -> Optional["ElementDict"]:
        pass

    @queue_until_user_message()
    async def delete_element(self, element_id: str):
        pass

    @queue_until_user_message()
    async def create_step(self, step_dict: "StepDict"):
        pass

    @queue_until_user_message()
    async def update_step(self, step_dict: "StepDict"):
        pass

    @queue_until_user_message()
    async def delete_step(self, step_id: str):
        pass

    async def get_thread_author(self, thread_id: str) -> str:
        return ""

    async def delete_thread(self, thread_id: str):
        pass

    async def list_threads(
        self, pagination: "Pagination", filters: "ThreadFilter"
    ) -> "PaginatedResponse[ThreadDict]":
        return PaginatedResponse(
            data=[], pageInfo=PageInfo(hasNextPage=False, endCursor=None)
        )

    async def get_thread(self, thread_id: str) -> "Optional[ThreadDict]":
        return None

    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ):
        pass

    async def delete_user_session(self, id: str) -> bool:
        return True


class ChainlitDataLayer:
    def  __init__(self, mongodb_uri: str): 
        logger.info("Chainlit data layer initialized")
        self.client = MongoClient(mongodb_uri)
        self.db = self.client["your_database_name"]

    def attachment_to_element_dict(self, attachment: Attachment) -> "ElementDict":
        metadata = attachment.metadata or {}
        return {
            "chainlitKey": None,
            "display": metadata.get("display", "side"),
            "language": metadata.get("language"),
            "page": metadata.get("page"),
            "size": metadata.get("size"),
            "type": metadata.get("type", "file"),
            "forId": attachment.step_id,
            "id": attachment.id or "",
            "mime": attachment.mime,
            "name": attachment.name or "",
            "objectKey": attachment.object_key,
            "url": attachment.url,
            "threadId": attachment.thread_id,
        }

    def feedback_to_feedback_dict(
        self, feedback: Optional[ClientFeedback]
    ) -> "Optional[FeedbackDict]":
        if not feedback:
            return None
        return {
            "id": feedback.id or "",
            "forId": feedback.step_id or "",
            "value": feedback.value or 0,  # type: ignore
            "comment": feedback.comment,
            "strategy": "BINARY",
        }

    def step_to_step_dict(self, step: ClientStep) -> "StepDict":
        metadata = step.metadata or {}
        input = (step.input or {}).get("content") or (
            json.dumps(step.input) if step.input and step.input != {} else ""
        )
        output = (step.output or {}).get("content") or (
            json.dumps(step.output) if step.output and step.output != {} else ""
        )
        return {
            "createdAt": step.created_at,
            "id": step.id or "",
            "threadId": step.thread_id or "",
            "parentId": step.parent_id,
            "feedback": self.feedback_to_feedback_dict(step.feedback),
            "start": step.start_time,
            "end": step.end_time,
            "type": step.type or "undefined",
            "name": step.name or "",
            "generation": step.generation.to_dict() if step.generation else None,
            "input": input,
            "output": output,
            "showInput": metadata.get("showInput", False),
            "disableFeedback": metadata.get("disableFeedback", False),
            "indent": metadata.get("indent"),
            "language": metadata.get("language"),
            "isError": metadata.get("isError", False),
            "waitForAnswer": metadata.get("waitForAnswer", False),
            "feedback": self.feedback_to_feedback_dict(step.feedback),
        }
# `````````````````````````````````````````````````````````````````````/`
    async def get_user(self, identifier: str) -> Optional[PersistedUser]:
        user_data = self.db.users.find_one({"identifier": identifier})
        if not user_data:
            return None
        return PersistedUser(
            id=str(user_data["_id"]),
            identifier=user_data["identifier"],
            metadata=user_data.get("metadata", {}),
            createdAt=user_data.get("created_at", ""),
        )

    async def create_user(self, user: User) -> Optional[PersistedUser]:
        existing_user = self.db.users.find_one({"identifier": user.identifier})
        if not existing_user:
            user_data = {
                "identifier": user.identifier,
                "metadata": user.metadata,
                "created_at": user.created_at,
            }
            result = self.db.users.insert_one(user_data)
            return PersistedUser(
                id=str(result.inserted_id),
                identifier=user.identifier,
                metadata=user.metadata,
                createdAt=user.created_at,
            )
        else:
            # User already exists, update metadata if needed
            self.db.users.update_one(
                {"_id": ObjectId(existing_user["_id"])},
                {"$set": {"metadata": user.metadata}},
            )
            return PersistedUser(
                id=str(existing_user["_id"]),
                identifier=user.identifier,
                metadata=user.metadata,
                createdAt=existing_user.get("created_at", ""),
            )

    async def upsert_feedback(
        self, feedback: Feedback,
    ):
        if feedback.id:
            self.db.feedback.update_one(
                {"_id": ObjectId(feedback.id)},
                {
                    "$set": {
                        "comment": feedback.comment,
                        "strategy": feedback.strategy,
                        "value": feedback.value,
                    }
                },
            )
            return feedback.id
        else:
            feedback_data = {
                "step_id": feedback.forId,
                "value": feedback.value,
                "comment": feedback.comment,
                "strategy": feedback.strategy,
            }
            result = self.db.feedback.insert_one(feedback_data)
            return str(result.inserted_id)
    async def create_element(self, element: "Element"):
        metadata = {
            "size": element.size,
            "language": element.language,
            "display": element.display,
            "type": element.type,
            "page": getattr(element, "page", None),
        }

        if not element.for_id:
            return

        object_key = None

        if not element.url:
            if element.path:
                async with aiofiles.open(element.path, "rb") as f:
                    content = await f.read()  # type: Union[bytes, str]
            elif element.content:
                content = element.content
            else:
                raise ValueError("Either path or content must be provided") 
            object_key = self.upload_file_to_mongodb(content, element.mime)

        # Simulate sending steps (replace with your own logic if needed)
        await self.send_steps_to_mongodb(element.for_id, element.thread_id, element.id, element.name, metadata, element.mime, element.url, object_key)

    @queue_until_user_message() 
    async def delete_element(self, element_id: str): 
        self.delete_attachment_from_mongodb(element_id) 
    
    @queue_until_user_message()
    async def update_step(self, step_dict: "StepDict"):
        await self.create_step(step_dict) 

    @queue_until_user_message()
    async def delete_step(self, step_id: str): 
        self.db.steps.delete_one({"_id": ObjectId(step_id)})

    async def get_thread_author(self, thread_id: str) -> str:
        thread = await self.get_thread(thread_id)
        if not thread:
            return ""
        user = thread.get("user")
        if not user:
            return ""
        return user.get("identifier") or ""

    async def delete_thread(self, thread_id: str): 
        await self.db.threads.delete_one({"_id": ObjectId(thread_id)})

    async def list_threads(
        self, pagination: "Pagination", filters: "ThreadFilter"
    ) -> "PaginatedResponse[ThreadDict]":
        if not filters.userIdentifier:
            raise ValueError("userIdentifier is required")

        query = {"user.identifier": filters.userIdentifier}
        if filters.search:
            query["name"] = {"$regex": filters.search, "$options": "i"}

        threads = self.db.threads.find(query).skip(pagination.cursor).limit(pagination.first)
        return [self.thread_document_to_thread_dict(thread) for thread in threads]

    async def get_thread(self, thread_id: str) -> Optional["ThreadDict"]:
        # Simulate retrieving thread data from MongoDB (replace with your actual logic)
        thread_data = self.get_thread_data_from_mongodb(thread_id)
        
        if not thread_data:
            return None

        elements = []  # List[ElementDict]
        steps = []  # List[StepDict]

        for step in thread_data.get("steps", []):
            if config.ui.hide_cot and step.get("parent_id"):
                continue
            for attachment in step.get("attachments", []):
                elements.append(self.attachment_to_element_dict(attachment))
            if not config.features.prompt_playground and step.get("generation"):
                step["generation"] = None
            steps.append(self.step_to_step_dict(step))

        user = None  # type: Optional["UserDict"]

        if thread_data.get("user"):
            user = {
                "id": thread_data["user"].get("id") or "",
                "identifier": thread_data["user"].get("identifier") or "",
                "metadata": thread_data["user"].get("metadata", {}),
            }

        return {
            "createdAt": thread_data.get("created_at") or "",
            "id": thread_data["id"],
            "name": thread_data.get("name") or None,
            "steps": steps,
            "elements": elements,
            "metadata": thread_data.get("metadata", {}),
            "user": user,
            "tags": thread_data.get("tags", []),
        }

    # Simulated method for MongoDB operations (replace with actual MongoDB logic)
    def get_thread_data_from_mongodb(self, thread_id: str) -> Optional[dict]: 
        return self.db.threads.find_one({"_id": ObjectId(thread_id)})

    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ): 
        update_data = {}
        if name:
            update_data["name"] = name
        if user_id:
            update_data["user.identifier"] = user_id
        if metadata:
            update_data["metadata"] = metadata
        if tags:
            update_data["tags"] = tags

        self.update_thread_data_in_mongodb(thread_id, update_data)
 
    def update_thread_data_in_mongodb(self, thread_id: str, update_data: dict): 
        self.db.threads.update_one({"_id": ObjectId(thread_id)}, {"$set": update_data})


if mongodb_uri := os.environ.get("mongodb_uri"): 
    _data_layer = ChainlitDataLayer(mongodb_uri=mongodb_uri )
    
def get_data_layer(): 
    return _data_layer
