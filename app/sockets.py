import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Literal

from chainlit.action import Action
from chainlit.auth import get_current_user, require_login
from chainlit.config import config
from chainlit.context import init_ws_context
from chainlit.data import get_data_layer
from chainlit.logger import logger
from chainlit.message import ErrorMessage, Message
from chainlit.server import socket
from chainlit.session import WebsocketSession
from chainlit.telemetry import trace_event
from chainlit.types import UIMessagePayload
from chainlit.user_session import user_sessions
# print("xsacsac")
def restore_existing_session(sid, session_id, emit_fn, emit_call_fn):
    """Restore a session from the sessionId provided by the client."""
    if session := WebsocketSession.get_by_id(session_id):
        session.restore(new_socket_id=sid)
        session.emit = emit_fn
        session.emit_call = emit_call_fn
        trace_event("session_restored")
        return True
    return False


async def persist_user_session(thread_id: str, metadata: Dict):
    if data_layer := get_data_layer():
        await data_layer.update_thread(thread_id=thread_id, metadata=metadata)


async def resume_thread(session: WebsocketSession):
    data_layer = get_data_layer()
    if not data_layer or not session.user or not session.thread_id_to_resume:
        return
    thread = await data_layer.get_thread(thread_id=session.thread_id_to_resume)
    if not thread:
        return

    author = thread.get("user").get("identifier") if thread["user"] else None
    user_is_author = author == session.user.identifier

    if user_is_author:
        metadata = thread.get("metadata", {})
        user_sessions[session.id] = metadata.copy()
        if chat_profile := metadata.get("chat_profile"):
            session.chat_profile = chat_profile
        if chat_settings := metadata.get("chat_settings"):
            session.chat_settings = chat_settings

        trace_event("thread_resumed")

        return thread


def load_user_env(user_env):
    # Check user env
    if config.project.user_env:
        # Check if requested user environment variables are provided
        if user_env:
            user_env = json.loads(user_env)
            for key in config.project.user_env:
                if key not in user_env:
                    trace_event("missing_user_env")
                    raise ConnectionRefusedError(
                        "Missing user environment variable: " + key
                    )
        else:
            raise ConnectionRefusedError("Missing user environment variables")
    return user_env


def build_anon_user_identifier(environ):
    scope = environ.get("asgi.scope", {})
    client_ip, _ = scope.get("client")
    ip = environ.get("HTTP_X_FORWARDED_FOR", client_ip)

    try:
        headers = scope.get("headers", {})
        user_agent = next(
            (v.decode("utf-8") for k, v in headers if k.decode("utf-8") == "user-agent")
        )
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, user_agent + ip))

    except StopIteration:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, ip))


@socket.on("connect")
async def connect(sid, environ, auth):
    if not config.code.on_chat_start and not config.code.on_message:
        logger.warning(
            "You need to configure at least an on_chat_start or an on_message callback"
        )
        return False
    user = None
    token = None
    login_required = require_login()
    try:
        # Check if the authentication is required
        if login_required:
            authorization_header = environ.get("HTTP_AUTHORIZATION")
            token = authorization_header.split(" ")[1] if authorization_header else None
            user = await get_current_user(token=token)
    except Exception as e:
        logger.info("Authentication failed")
        return False

    # Session scoped function to emit to the client
    def emit_fn(event, data):
        if session := WebsocketSession.get(sid):
            if session.should_stop:
                session.should_stop = False
                raise InterruptedError("Task stopped by user")
        return socket.emit(event, data, to=sid)

    # Session scoped function to emit to the client and wait for a response
    def emit_call_fn(event: Literal["ask", "call_fn"], data, timeout):
        if session := WebsocketSession.get(sid):
            if session.should_stop:
                session.should_stop = False
                raise InterruptedError("Task stopped by user")
        return socket.call(event, data, timeout=timeout, to=sid)

    session_id = environ.get("HTTP_X_CHAINLIT_SESSION_ID")
    if restore_existing_session(sid, session_id, emit_fn, emit_call_fn):
        return True

    user_env_string = environ.get("HTTP_USER_ENV")
    user_env = load_user_env(user_env_string)

    client_type = environ.get("HTTP_X_CHAINLIT_CLIENT_TYPE")

    ws_session = WebsocketSession(
        id=session_id,
        socket_id=sid,
        emit=emit_fn,
        emit_call=emit_call_fn,
        client_type=client_type,
        user_env=user_env,
        user=user,
        token=token,
        chat_profile=environ.get("HTTP_X_CHAINLIT_CHAT_PROFILE"),
        thread_id=environ.get("HTTP_X_CHAINLIT_THREAD_ID"),
    )


    trace_event("connection_successful")
    return True


@socket.on("connection_successful")
async def connection_successful(sid):
    context = init_ws_context(sid)

    if context.session.restored:
        return

    await context.emitter.task_end()
    await context.emitter.clear("clear_ask")
    await context.emitter.clear("clear_call_fn")

    if context.session.thread_id_to_resume and config.code.on_chat_resume:
        thread = await resume_thread(context.session)
        if thread:
            context.session.has_first_interaction = True
            await context.emitter.emit("first_interaction", "resume")
            await context.emitter.resume_thread(thread)
            await config.code.on_chat_resume(thread)
            return

    if config.code.on_chat_start:
        await config.code.on_chat_start()


@socket.on("clear_session")
async def clean_session(sid):
    await disconnect(sid, force_clear=True)


@socket.on("disconnect")
async def disconnect(sid, force_clear=False):
     
    session = WebsocketSession.get(sid)
    if session:
        context = init_ws_context(session) 

    if config.code.on_chat_end and session:
        await config.code.on_chat_end()

    if session and session.thread_id and session.has_first_interaction:
        await persist_user_session(session.thread_id, session.to_persistable())
        # current_conversation = [step.to_dict() for step in context.active_steps] 
        # if data_layer := get_data_layer():
        #     await data_layer.update_thread(
        #         thread_id=session.thread_id,
        #         history=current_conversation
        #     )
    def clear():
        if session := WebsocketSession.get(sid):
            # Clean up the user session
            if session.id in user_sessions:
                user_sessions.pop(session.id)
            # Clean up the session
            session.delete()

    async def clear_on_timeout(sid):
        await asyncio.sleep(config.project.session_timeout)
        clear()

    if force_clear:
        clear()
    else:
        asyncio.ensure_future(clear_on_timeout(sid))


@socket.on("stop")
async def stop(sid):
    if session := WebsocketSession.get(sid):
        trace_event("stop_task")

        init_ws_context(session)
        await Message(
            author="System", content="Task stopped by the user.", disable_feedback=True
        ).send()

        session.should_stop = True

        if config.code.on_stop:
            await config.code.on_stop()


async def process_message(session: WebsocketSession, payload: UIMessagePayload):
    """Process a message from the user."""
    try:
        context = init_ws_context(session)
        await context.emitter.task_start()
        message = await context.emitter.process_user_message(payload)
 
        if config.code.on_message:
            await config.code.on_message(message)
    except InterruptedError:
        pass
    except Exception as e:
        logger.exception(e)
        await ErrorMessage(
            author="Error", content=str(e) or e.__class__.__name__
        ).send()
    finally:
        await context.emitter.task_end()


@socket.on("ui_message")
async def message(sid, payload: UIMessagePayload):
    """Handle a message sent by the User."""
    session = WebsocketSession.require(sid)
    session.should_stop = False

    await process_message(session, payload)


async def process_action(action: Action):
    callback = config.code.action_callbacks.get(action.name)
    if callback:
        res = await callback(action)
        return res
    else:
        logger.warning("No callback found for action %s", action.name)


@socket.on("action_call")
async def call_action(sid, action):
    """Handle an action call from the UI."""
    context = init_ws_context(sid)

    action = Action(**action)

    try:
        res = await process_action(action)
        await context.emitter.send_action_response(
            id=action.id, status=True, response=res if isinstance(res, str) else None
        )

    except InterruptedError:
        await context.emitter.send_action_response(
            id=action.id, status=False, response="Action interrupted by the user"
        )
    except Exception as e:
        logger.exception(e)
        await context.emitter.send_action_response(
            id=action.id, status=False, response="An error occured"
        )


@socket.on("chat_settings_change")
async def change_settings(sid, settings: Dict[str, Any]):
    """Handle change settings submit from the UI."""
    context = init_ws_context(sid)

    for key, value in settings.items():
        context.session.chat_settings[key] = value

    if config.code.on_settings_update:
        await config.code.on_settings_update(settings)


import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union, cast

from chainlit.data import get_data_layer
from chainlit.element import Element, File
from chainlit.logger import logger
from chainlit.message import Message
from chainlit.session import BaseSession, WebsocketSession
from chainlit.step import StepDict
from chainlit.types import (
    AskActionResponse,
    AskSpec,
    FileDict,
    FileReference,
    ThreadDict,
    UIMessagePayload,
)
from chainlit.user import PersistedUser
from socketio.exceptions import TimeoutError


class BaseChainlitEmitter:
    """
    Chainlit Emitter Stub class. This class is used for testing purposes.
    It stubs the ChainlitEmitter class and does nothing on function calls.
    """

    session: BaseSession

    def __init__(self, session: BaseSession) -> None:
        """Initialize with the user session."""
        self.session = session

    async def emit(self, event: str, data: Any):
        """Stub method to get the 'emit' property from the session."""
        pass

    async def emit_call(self):
        """Stub method to get the 'emit_call' property from the session."""
        pass

    async def resume_thread(self, thread_dict: ThreadDict):
        """Stub method to resume a thread."""
        pass

    async def send_step(self, step_dict: StepDict):
        """Stub method to send a message to the UI."""
        pass

    async def update_step(self, step_dict: StepDict):
        """Stub method to update a message in the UI."""
        pass

    async def delete_step(self, step_dict: StepDict):
        """Stub method to delete a message in the UI."""
        pass

    def send_timeout(self, event: Literal["ask_timeout", "call_fn_timeout"]):
        """Stub method to send a timeout to the UI."""
        pass

    def clear(self, event: Literal["clear_ask", "clear_call_fn"]):
        pass

    async def init_thread(self, interaction: str):
        pass

    async def process_user_message(self, payload: UIMessagePayload) -> Message:
        """Stub method to process user message."""
        return Message(content="")

    async def send_ask_user(
        self, step_dict: StepDict, spec: AskSpec, raise_on_timeout=False
    ) -> Optional[Union["StepDict", "AskActionResponse", List["FileDict"]]]:
        """Stub method to send a prompt to the UI and wait for a response."""
        pass

    async def send_call_fn(
        self, name: str, args: Dict[str, Any], timeout=300, raise_on_timeout=False
    ) -> Optional[Dict[str, Any]]:
        """Stub method to send a call function event to the copilot and wait for a response."""
        pass

    async def update_token_count(self, count: int):
        """Stub method to update the token count for the UI."""
        pass

    async def task_start(self):
        """Stub method to send a task start signal to the UI."""
        pass

    async def task_end(self):
        """Stub method to send a task end signal to the UI."""
        pass

    async def stream_start(self, step_dict: StepDict):
        """Stub method to send a stream start signal to the UI."""
        pass

    async def send_token(self, id: str, token: str, is_sequence=False):
        """Stub method to send a message token to the UI."""
        pass

    async def set_chat_settings(self, settings: dict):
        """Stub method to set chat settings."""
        pass

    async def send_action_response(
        self, id: str, status: bool, response: Optional[str] = None
    ):
        """Send an action response to the UI."""
        pass


class ChainlitEmitter(BaseChainlitEmitter):
    """
    Chainlit Emitter class. The Emitter is not directly exposed to the developer.
    Instead, the developer interacts with the Emitter through the methods and classes exposed in the __init__ file.
    """

    session: WebsocketSession

    def __init__(self, session: WebsocketSession) -> None:
        """Initialize with the user session."""
        self.session = session

    def _get_session_property(self, property_name: str, raise_error=True):
        """Helper method to get a property from the session."""
        if not hasattr(self, "session") or not hasattr(self.session, property_name):
            if raise_error:
                raise ValueError(f"Session does not have property '{property_name}'")
            else:
                return None
        return getattr(self.session, property_name)

    @property
    def emit(self):
        """Get the 'emit' property from the session."""

        return self._get_session_property("emit")

    @property
    def emit_call(self):
        """Get the 'emit_call' property from the session."""
        return self._get_session_property("emit_call")

    def resume_thread(self, thread_dict: ThreadDict):
        """Send a thread to the UI to resume it"""
        return self.emit("resume_thread", thread_dict)

    def send_step(self, step_dict: StepDict):
        """Send a message to the UI."""
        return self.emit("new_message", step_dict)

    def update_step(self, step_dict: StepDict):
        """Update a message in the UI."""
        return self.emit("update_message", step_dict)

    def delete_step(self, step_dict: StepDict):
        """Delete a message in the UI."""
        return self.emit("delete_message", step_dict)

    def send_timeout(self, event: Literal["ask_timeout", "call_fn_timeout"]):
        return self.emit(event, {})

    def clear(self, event: Literal["clear_ask", "clear_call_fn"]):
        return self.emit(event, {})

    async def flush_thread_queues(self, interaction: str):
        if data_layer := get_data_layer():
            if isinstance(self.session.user, PersistedUser):
                user_id = self.session.user.id
            else:
                user_id = None
            try:
                await data_layer.update_thread(
                    thread_id=self.session.thread_id,
                    name=interaction,
                    user_id=user_id,
                )
            except Exception as e:
                logger.error(f"Error updating thread: {e}")
            await self.session.flush_method_queue()

    async def init_thread(self, interaction: str):
        await self.flush_thread_queues(interaction)
        await self.emit("first_interaction", interaction)

    async def process_user_message(self, payload: UIMessagePayload):
        step_dict = payload["message"]
        file_refs = payload["fileReferences"]
        # UUID generated by the frontend should use v4
        assert uuid.UUID(step_dict["id"]).version == 4

        message = Message.from_dict(step_dict)
        # Overwrite the created_at timestamp with the current time
        message.created_at = datetime.utcnow().isoformat()

        asyncio.create_task(message._create())

        if not self.session.has_first_interaction:
            self.session.has_first_interaction = True
            asyncio.create_task(self.init_thread(message.content))

        if file_refs:
            files = [
                self.session.files[file["id"]]
                for file in file_refs
                if file["id"] in self.session.files
            ]
            file_elements = [Element.from_dict(file) for file in files]
            message.elements = file_elements

            async def send_elements():
                for element in message.elements:
                    await element.send(for_id=message.id)

            asyncio.create_task(send_elements())

        self.session.root_message = message

        return message

    async def send_ask_user(
        self, step_dict: StepDict, spec: AskSpec, raise_on_timeout=False
    ):
        """Send a prompt to the UI and wait for a response."""

        try:
            # Send the prompt to the UI
            user_res = await self.emit_call(
                "ask", {"msg": step_dict, "spec": spec.to_dict()}, spec.timeout
            )  # type: Optional[Union["StepDict", "AskActionResponse", List["FileReference"]]]

            # End the task temporarily so that the User can answer the prompt
            await self.task_end()

            final_res: Optional[
                Union["StepDict", "AskActionResponse", List["FileDict"]]
            ] = None

            if user_res:
                interaction: Union[str, None] = None
                if spec.type == "text":
                    message_dict_res = cast(StepDict, user_res)
                    await self.process_user_message(
                        {"message": message_dict_res, "fileReferences": None}
                    )
                    interaction = message_dict_res["output"]
                    final_res = message_dict_res
                elif spec.type == "file":
                    file_refs = cast(List[FileReference], user_res)
                    files = [
                        self.session.files[file["id"]]
                        for file in file_refs
                        if file["id"] in self.session.files
                    ]
                    final_res = files
                    interaction = ",".join([file["name"] for file in files])
                    if get_data_layer():
                        coros = [
                            File(
                                name=file["name"],
                                path=str(file["path"]),
                                mime=file["type"],
                                chainlit_key=file["id"],
                                for_id=step_dict["id"],
                            )._create()
                            for file in files
                        ]
                        await asyncio.gather(*coros)
                elif spec.type == "action":
                    action_res = cast(AskActionResponse, user_res)
                    final_res = action_res
                    interaction = action_res["value"]

                if not self.session.has_first_interaction and interaction:
                    self.session.has_first_interaction = True
                    await self.init_thread(interaction=interaction)

            await self.clear("clear_ask")
            return final_res
        except TimeoutError as e:
            await self.send_timeout("ask_timeout")

            if raise_on_timeout:
                raise e
        finally:
            await self.task_start()

    async def send_call_fn(
        self, name: str, args: Dict[str, Any], timeout=300, raise_on_timeout=False
    ) -> Optional[Dict[str, Any]]:
        """Stub method to send a call function event to the copilot and wait for a response."""
        try:
            call_fn_res = await self.emit_call(
                "call_fn", {"name": name, "args": args}, timeout
            )  # type: Dict

            await self.clear("clear_call_fn")
            return call_fn_res
        except TimeoutError as e:
            await self.send_timeout("call_fn_timeout")

            if raise_on_timeout:
                raise e
            return None

    def update_token_count(self, count: int):
        """Update the token count for the UI."""

        return self.emit("token_usage", count)

    def task_start(self):
        """
        Send a task start signal to the UI.
        """
        return self.emit("task_start", {})

    def task_end(self):
        """Send a task end signal to the UI."""
        return self.emit("task_end", {})

    def stream_start(self, step_dict: StepDict):
        """Send a stream start signal to the UI."""
        return self.emit(
            "stream_start",
            step_dict,
        )

    def send_token(self, id: str, token: str, is_sequence=False):
        """Send a message token to the UI."""
        return self.emit(
            "stream_token", {"id": id, "token": token, "isSequence": is_sequence}
        )

    def set_chat_settings(self, settings: Dict[str, Any]):
        self.session.chat_settings = settings

    def send_action_response(
        self, id: str, status: bool, response: Optional[str] = None
    ):
        return self.emit(
            "action_response", {"id": id, "status": status, "response": response}
        )


import sys
from typing import Any, Coroutine, TypeVar

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec

import asyncio
import threading

from asyncer import asyncify
from chainlit.context import context_var
from syncer import sync

make_async = asyncify

T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")
T = TypeVar("T")
print("`1111111111111111111111111")

def run_sync(co: Coroutine[Any, Any, T_Retval]) -> T_Retval:
    """Run the coroutine synchronously."""

    # Copy the current context
    current_context = context_var.get()
    print(current_context)
    # Define a wrapper coroutine that sets the context before running the original coroutine
    async def context_preserving_coroutine():
        # Set the copied context to the coroutine
        context_var.set(current_context)
        return await co

    # Execute from the main thread in the main event loop
    if threading.current_thread() == threading.main_thread():
        return sync(context_preserving_coroutine())
    else:  # Execute from a thread in the main event loop
        result = asyncio.run_coroutine_threadsafe(
            context_preserving_coroutine(), loop=current_context.loop
        )
        return result.result()
