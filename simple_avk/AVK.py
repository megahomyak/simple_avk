from typing import AsyncGenerator, Optional, Any

import aiohttp

from simple_avk import exceptions

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

VK_METHOD_LINK = "https://api.VK.com/method/{}"


class SimpleAVK:
    """
    Main class of the simple_avk library.

    It supports:
        VK API methods calling (with "call_method" method)
        Receiving events (with longpoll; "get_new_events" and "listen" methods)
        Errors raising if something went wrong
    """

    def __init__(
            self, aiohttp_session: aiohttp.ClientSession,
            token: str = "", group_id: Optional[int] = None,
            api_version: str = "5.103", wait: int = 25,
            user_longpoll_mode: int = 2,
            user_longpoll_version: int = 3) -> None:
        """
        Setting aiohttp session, token, group id and api version.
        If your bot is on user account, you don't need to specify group id.

        Args:
            aiohttp_session:
                ClientSession of the aiohttp to make asynchronous requests
            token:
                token of your VK bot (default "")
            group_id:
                id of your VK group (default None; not necessary for user-bots)
            api_version:
                version of VK api to use (default "5.103")
            wait:
                server waiting time in seconds (default 25)
            user_longpoll_mode:
                VK longpoll mode (default 2; used in user longpoll)
            user_longpoll_version:
                VK longpoll version (default 3; used in user longpoll)
        """
        self.aiohttp_session = aiohttp_session
        self.token = token
        self.group_id = group_id
        self.api_version = api_version
        self.vk_wait = wait
        self.user_longpoll_mode = user_longpoll_mode
        self.user_longpoll_version = user_longpoll_version
        self.longpoll_method = ""
        self.longpoll_server_link = ""
        self.longpoll_params = {}

    async def _get_new_longpoll_info(self) -> dict:
        return await self.call_method(
            self.longpoll_method,
            # Line too long cuz pep8 symbol limit sucks
            params={} if self.group_id is None else {"group_id": self.group_id}
        )

    async def _prepare_longpoll(self) -> None:
        """
        Getting longpoll server to receive events.

        Raises:
           VKError: any error from VK response
        """
        # If group id isn't specified - it's user longpoll
        self.longpoll_method = (
            GROUPS_LONGPOLL_METHOD if self.group_id else USERS_LONGPOLL_METHOD
        )
        resp = await self._get_new_longpoll_info()
        vk_last_event_id = resp["ts"]
        vk_secret_key = resp["key"]
        vk_longpoll_server = resp["server"]
        if self.group_id:
            self.longpoll_server_link = vk_longpoll_server
        else:
            self.longpoll_server_link = f"https://{vk_longpoll_server}"
        self.longpoll_params = {
            "act": "a_check",
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

    async def _real_get_new_events(self) -> list:
        updates = None
        while updates is None:
            resp = await self.aiohttp_session.get(
                self.longpoll_server_link,
                params=self.longpoll_params
            )
            resp_json = await resp.json()
            del resp
            if "failed" in resp_json:
                error_code = resp_json["failed"]
                if error_code == 1:  # Events are partially lost or outdated
                    # This error gives a new ts
                    self.longpoll_params["ts"] = resp_json["ts"]
                elif error_code in (2, 3):  # 2 - key is outdated
                    new_server_info = await self._get_new_longpoll_info()
                    self.longpoll_params["key"] = new_server_info["key"]
                    if error_code == 3:  # User info lost
                        # This error gives a new ts
                        self.longpoll_params["ts"] = new_server_info["ts"]
                else:
                    raise exceptions.LongpollError(
                        error_code,
                        LONGPOLL_ERROR_DESCRIPTIONS[error_code].format(
                            self.longpoll_method
                        )
                    )
            else:
                self.longpoll_params["ts"] = resp_json["ts"]
                updates = resp_json["updates"]
        return updates

    async def get_new_events(self) -> list:
        """
        Get new events (also called updates) from longpoll.

        Returns:
            list of new events caught by longpoll

        Raises:
            VKError: any error from VK longpoll
        """
        await self._prepare_longpoll()
        # noinspection PyAttributeOutsideInit
        # because I'm changing a function to make something like state pattern
        self.get_new_events = self._real_get_new_events
        return await self._real_get_new_events()

    async def listen(self) -> AsyncGenerator[Any, None]:
        """
        Catches new events from VK with infinite loop.
        Method "prepare_longpoll" is called here before infinite loop.
        Can be used in "async for" loop.

        Yields:
            event caught by longpoll

        Raises:
            VKError: any error from VK longpoll
        """
        while True:
            events = await self.get_new_events()
            for event in events:
                yield event

    async def call_method(self, method_name: str, params: dict = None) -> dict:
        """
        Calls VK API method (with POST request).

        Args:
            method_name: name of method (format: "METHODS_GROUP.METHOD")
            params: parameters passed to method (default None, later sets to {})

        Returns:
            VK response

        Raises:
            VKError: any error from VK response
        """
        if not params:
            params = {}
        full_params = {
            **params,
            "access_token": self.token,
            "v": self.api_version
        }
        link = VK_METHOD_LINK.format(method_name)
        resp = await self.aiohttp_session.post(link, data=full_params)
        resp_json = await resp.json()
        if "error" not in resp_json:
            return resp_json["response"]
        error = resp_json["error"]
        raise exceptions.MethodError(
            method_name, error["error_code"], error["error_msg"]
        )
