# -*- coding: utf-8 -*-
"""
Simple asynchronous VK API client framework by megahomyak.

Class SimpleAVK is what you need.
"""
from typing import Union, AsyncGenerator, Optional, List, Dict, Any
import aiohttp
JsonContents = Union[dict, list, str, int]
Json = Union[Dict[str, JsonContents], List[JsonContents]]

GROUPS_LONGPOLL_METHOD = "groups.getLongPollServer"
USERS_LONGPOLL_METHOD = "messages.getLongPollServer"
LONGPOLL_ERROR_DESCRIPTIONS = {
    1: (
        "Events history is outdated or partially lost, app "
        "can get further events using new ts value from server response."),
    2: (
        "Key is outdated, you need to get new key "
        "using method {}."),
    3: (
        "Information about user is lost, you need to request "
        "new key and ts using method {}."),
    4: (
        "Invalid version number passed in 'version' parameter.")
}
LONGPOLL_ERROR_MSG = "Error in longpoll with code {}: {}"
VK_METHOD_ERROR_MSG = "Error in method {} with code {}: {}"
VK_METHOD_LINK = "https://api.VK.com/method/{}"


class SimpleAVK:
    (
        """
        Main class of simple_avk framework.
        
        It supports:
            VK API methods calling (with "call_method" method).
            Receiving events (with longpoll; "get_new_events" and "listen" methods).
            Errors raising if something went wrong (you can disable it in "__init__").

        Warnings:
            Before receiving events with "get_new_events", you need to prepare longpoll"""
        """ (with "prepare_longpoll" method).
            In "listen" method "prepare_longpoll" is called automatically.
        """
    )

    def __init__(
            self, aiohttp_session: aiohttp.ClientSession,
            token: str = "", group_id: Optional[int] = None,
            api_version: str = "5.103", wait: int = 25,
            vk_errors_handling_type: str = "raise",
            user_longpoll_mode: int = 2,
            user_longpoll_version: int = 3) -> None:
        (
            """
            Setting aiohttp session, token, group id and api version.
            If your bot is on user account, you don't need to specify group id.

            It's synchronous method.

            Arguments:
                aiohttp_session {aiohttp.ClientSession}

            Keyword Arguments:
                token {str} -- token of your VK bot (default "")
                group_id {int} -- id of your VK group (default None; not necessary for user-bots)
                api_version {str} (default "5.103")
                wait {int} -- server waiting time in seconds (default 25)
                vk_errors_handling_type {str} -- what to do with VK errors"""
            """ (default "raise"; "raise" or "print", else do nothing)
                user_longpoll_mode {int} -- VK longpoll mode (default 2; used in user longpoll)
                user_longpoll_version {int} -- VK longpoll version"""
            """ (default 3; used in user longpoll)

            Returns:
                {None}
            """
        )
        self.aiohttp_session = aiohttp_session
        self.token = token
        self.group_id = group_id
        self.api_version = api_version
        self.vk_wait = wait
        self.vk_errors_handling_type = vk_errors_handling_type.lower()
        self.user_longpoll_mode = user_longpoll_mode
        self.user_longpoll_version = user_longpoll_version
        self.longpoll_method = ""
        self.longpoll_server_link = ""
        self.longpoll_params: Dict[str, JsonContents] = {}

    async def prepare_longpoll(self) -> None:
        """
        Getting longpoll server to receive events.

        It's asynchronous method.

        Arguments:
            None

        Returns:
            {None}

        Raises:
            {VKError} (from this module) -- any error from VK response
        """
        if self.group_id:
            self.longpoll_method = GROUPS_LONGPOLL_METHOD
            longpoll_params = {"group_id": self.group_id}
        else:
            # If group id isn't specified - it's user longpoll
            self.longpoll_method = USERS_LONGPOLL_METHOD
            longpoll_params = {}
        resp = await self.call_method(
            self.longpoll_method,
            params=longpoll_params
        )
        vk_last_event_id = resp["ts"]
        vk_secret_key = resp["key"]
        vk_longpoll_server = resp["server"]
        if self.group_id:
            self.longpoll_server_link = vk_longpoll_server
        else:
            self.longpoll_server_link = f"https://{vk_longpoll_server}"
        self.longpoll_params = {
            "act": "a_check",  # What a_check means lol, they didn't explained it in docs
            "key": vk_secret_key,
            "ts": vk_last_event_id,
            "wait": self.vk_wait
        }
        if not self.group_id:
            # If group id isn't specified - it's user longpoll
            self.longpoll_params.update(
                {
                    "version": self.user_longpoll_version,
                    "mode": self.user_longpoll_mode
                }
            )

    async def get_new_events(self) -> List[Json]:
        """
        Get new events (also called updates) from longpoll.

        It's asynchronous method.

        Arguments:
            None

        Returns:
            {list} -- new events catched by longpoll

        Raises:
            {VKError} (from this module) -- any error from VK longpoll
        """
        resp = await self.aiohttp_session.get(
            self.longpoll_server_link,
            params=self.longpoll_params
        )
        resp_json = await resp.json()
        if not "failed" in resp_json:
            if "ts" in resp_json:
                self.longpoll_params["ts"] = resp_json["ts"]
            return resp_json["updates"]
        error_num = resp_json["failed"]
        error_desc = LONGPOLL_ERROR_DESCRIPTIONS[error_num].format(
            self.longpoll_method
        )
        full_error_msg = LONGPOLL_ERROR_MSG.format(
            error_num,
            error_desc
        )
        self.handle_vk_error(full_error_msg)

    async def listen(self) -> AsyncGenerator[Json, None]:
        """
        Catches new events from VK with infinite loop.
        Method "prepare_longpoll" is called here before infinite loop.
        Can be used in "async for" loop.

        It's asynchronous method.

        Arguments:
            None

        Yields:
            {json (dict or list)} -- event catched by longpoll

        Raises:
            {VKError} (from this module) -- any error from VK longpoll
        """
        await self.prepare_longpoll()
        while True:
            events = await self.get_new_events()
            for event in events:
                yield event

    async def call_method(
            self, method_name: str, params: Optional[Dict[Union[str, int], Any]] = None,
            method_type: str = "post") -> Union[Json, None]:
        """
        Calls VK API method.

        It's asynchronous method.

        Arguments:
            method_name {str} -- name of method (format: "METHODS_GROUP.METHOD")

        Keyword Arguments:
            params {dict} -- parameters passed to method (default dict())
            method_type {str} -- "post" or "get" (default "post")

        Returns:
            {json (dict or list)} or {None} -- VK response (or None if there is an error)

        Raises:
            {VKError} (from this module) -- any error from VK response
        """
        if not params:
            params = {}
        full_params = {
            **params,
            "access_token": self.token,
            "v": self.api_version
        }
        method_type = method_type.lower()
        link = VK_METHOD_LINK.format(method_name)
        if method_type == "post":
            resp = await self.aiohttp_session.post(link, params=full_params)
        if method_type == "get":
            resp = await self.aiohttp_session.get(link, params=full_params)
        resp_json = await resp.json()
        if "error" not in resp_json:
            return resp_json["response"]
        error = resp_json["error"]
        error_code = error["error_code"]
        error_msg = error["error_msg"]
        full_error_msg = VK_METHOD_ERROR_MSG.format(
            method_name,
            error_code,
            error_msg
        )
        self.handle_vk_error(full_error_msg)

    def handle_vk_error(self, error_text: str) -> None:
        """
        Special method to handle VK errors.
        Depends on vk_errors_handling_type argument from __init__.

        It's synchronous method.

        Arguments:
            error_text {str} -- text of your error

        Returns:
            {None}

        Raises:
            {VKError} (from this module) -- any error from VK response
        """
        if self.vk_errors_handling_type == "raise":
            raise VKError(error_text)
        if self.vk_errors_handling_type == "print":
            print(error_text)


class VKError(Exception):
    """
    Exception.
    Raised when an error is received from the VK response.
    """
    ...