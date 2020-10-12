## simple_avk
Simple asynchronous VK API client library by megahomyak.

For Python 3.5+ (because it uses typing)!

It's so simple it fits in one file.

It supports:
* VK API methods calling (with `call_method` method)
* Receiving events (with longpoll; `get_new_events` and `listen` methods)
* Errors raising if something went wrong

## How to use it
1. Install the library and import it (you need only `SimpleAVK` class)

    Install it:

       pip install simple_avk

    Import it:

       from simple_avk import SimpleAVK

3. Create an object of class `SimpleAVK` (`simple_avk.SimpleAVK`), passing token, aiohttp session, maybe group id or other params to it

       vk = SimpleAVK(aiohttp_session=session, token="your token", group_id=1234567890)

4. Here we go! Now you can call VK methods with `call_method` method, listen to the longpoll with `listen` method or get list of events with `get_new_events` method:

   Listening example:

       async for event in vk.listen():
           ...

   Getting list of events example:

       events = vk.get_new_events()
