from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.chains import LLMChain
import chainlit as cl
from pymongo import MongoClient
from typing import Optional

import sockets
atlas_uri = "mongodb://m001-student:nani@sandbox-shard-00-00.4bigd.mongodb.net:27017,sandbox-shard-00-01.4bigd.mongodb.net:27017,sandbox-shard-00-02.4bigd.mongodb.net:27017/?replicaSet=atlas-q5gnca-shard-0&ssl=true&authSource=admin"

client = MongoClient(atlas_uri)
database = client["chainlit"]

# Access a specific collection within the database
collection = database["chat_conversations"]

@cl.on_chat_start
async def on_chat_start():
    model = ChatOpenAI(streaming=True)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You're a knowledgeable assistant able to answer questions."),
        ("human", "{question}"),
    ])
    chain = LLMChain(llm=model, prompt=prompt, output_parser=StrOutputParser())
    cl.user_session.set("chain", chain)
    cl.user_session.set("chat_history",[] )  


@cl.on_message
async def on_message(message: cl.Message): 

    chain = cl.user_session.get("chain")  
    chat_history = cl.user_session.get("chat_history")   
    
    res = await chain.arun(
        question=message.content,
        callbacks=[cl.LangchainCallbackHandler()]
    )
    # Create a dictionary to represent the message and its feedback
    message_with_feedback = {
        "id": len(chat_history),  # Unique identifier for the message
        "user": message.content,
        "bot": res,
        "feedback": None
    }
    chat_history.append(message_with_feedback)
    cl.user_session.set("chat_history", chat_history)
    
    # chat_history.append({"user": message.content, "bot": res, "feedback": None})  
    # cl.user_session.set("chat_history", chat_history)   
    # actions = [
    #     cl.Action(name="positive_feedback", value="positive", label="Good 👍"),
    #     cl.Action(name="negative_feedback", value="negative", label="Bad 👎")
    # ]
    actions = [
        cl.Action(name="positive_feedback", value=str(message_with_feedback["id"]), label="Good 👍"),
        cl.Action(name="negative_feedback", value=str(message_with_feedback["id"]), label="Bad 👎")
    ]
    # print(f"User: {message.content}\nBot: {res}")   
    # await cl.Message(content=res,actions=actions).send()
    await cl.Message(
        content=res,actions=actions,
        elements=[
            cl.Text(
                name="instructions",
                content="See instructions",
                display="side",
            )
        ]
    ).send()




@cl.action_callback("positive_feedback")
async def handle_positive_feedback(action: cl.Action):
    # Retrieve the message id from the action value and update feedback
    update_feedback(int(action.value), "positive")

@cl.action_callback("negative_feedback")
async def handle_negative_feedback(action: cl.Action):
    # Retrieve the message id from the action value and update feedback
    update_feedback(int(action.value), "negative")

def update_feedback(message_id, feedback_type):
    chat_history = cl.user_session.get("chat_history", )
    if message_id < len(chat_history):
        chat_history[message_id]["feedback"] = feedback_type
        cl.user_session.set("chat_history", chat_history)



from fastapi import HTTPException
@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    if username == "taranesh" and password == "password1":
        # First user with permissions to view chat history
        return cl.User(
            identifier="Taranesh",
            metadata={"role": "user", "permissions": ["view_chat_history"]}
        )
    elif username == "vani" and password == "password2":
        # Second user without permissions to view chat history
        return cl.User(
            identifier="Vani",
            metadata={"role": "user", "permissions": ""}
        )
    elif username == "admin" and password == "password3":
        # New user you want to add
        return cl.User(
            identifier="Admin",
            metadata={"role": "user", "additional_metadata": "value"}
        )
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

@cl.on_chat_end
def on_chat_end():
    chat_history = cl.user_session.get("chat_history")
    if chat_history:
        session_id = cl.user_session.get("id")
        chat_history_archive = {}
        chat_history_archive[session_id] = chat_history
        documents_to_insert = [chat_history_archive]
        result = collection.insert_many(documents_to_insert)
        # print(documents_to_insert)
    








    # @cl.action_callback("positive_feedback")
# async def handle_positive_feedback(action: cl.Action):
#     # Custom logic to store positive feedback
#     chat_history = cl.user_session.get("chat_history", )
#     if chat_history:
#         chat_history[-1]["feedback"] = "positive"
#         cl.user_session.set("chat_history", chat_history)
#     return "Thank you for your positive feedback!"

# @cl.action_callback("negative_feedback")
# async def handle_negative_feedback(action: cl.Action):
#     # Custom logic to store negative feedback
#     chat_history = cl.user_session.get("chat_history", )
#     if chat_history:
#         chat_history[-1]["feedback"] = "negative"
#         cl.user_session.set("chat_history", chat_history)
#     return "Thank you for your feedback, we will work to improve."