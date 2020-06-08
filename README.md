# simple_avk
Simple asynchronous VK API client framework by megahomyak.

For Python 3.5+ (because it uses typing)!

It's so simple that it fits in one file.

It supports:
* VK API methods calling (with `call_method` method)
* Receiving events (with longpoll; `get_new_events` and `listen` methods)
* Errors raising if something went wrong

Warnings:
* Before receiving events with `get_new_events`, you need to prepare longpoll (with `prepare_longpoll` method)
* In `listen` method `prepare_longpoll` is called automatically

## How to use it
1. Install the library
   
       pip install simple_avk
   and import it (you need only `SimpleAVK` class)
   
       from simple_avk import SimpleAVK
3. Create object of class `SimpleAVK` (`simple_avk.SimpleAVK`), passing token, aiohttp session, maybe group id or other params to it
   
       vk = SimpleAVK(aiohttp_session=session, token="your token", group_id=1234567890)
4. Here we go! Now you can call VK methods (with `call_method` method), listen to the longpoll (`listen` method) or get list of events (`get_new_events` method, but at first you need to prepare longpoll with `prepare_longpoll` method)
   
   Listening example:
   
       async for event in vk.listen():
           ...
   Getting list of events example:
   
       vk.prepare_longpoll()  # You need to do it once
       events = vk.get_new_events()

## How to respond asynchronously well
To respond truly asynchronously, you need to throw incoming events in handlers and then just forget about them, handler will do its work. Like this:
1. You got a response
2. It has type `message_new`
3. You throw it into a handler
4. Just forget about it; you don't need results (because there is no results in suchlike handlers)
5. When an event gives you control back, you scroll list of events further and throw events to their handlers (or do nothing)

**How to do it:**
1. Throw every handler into loop with `asyncio.gather` (it returns a `Future` object). You need to hang done callback function to returned `Future` (with `add_done_callback` method). When Future is done, it will be sent in the specified function.
2. In done callback you can get results of given handler or this handler's exception (with `exception` method of given `Future`). By default, all exceptions from `Futures` are catched and don't show up. Now you can print them or even get their traceback (with `traceback` module), print it and stop the program (with `sys.exit()`). Asyncio catches any exception in the done callback too, so you can't just raise the received exception.
   
   How to get `Future`'s exception, print traceback and stop the program:
   
   Some imports:
   
       import traceback
       import sys
       import asyncio
   Somewhere in code:
   
       async for event in vk.listen():
           if event["type"] == "message_new":
               asyncio.gather(
                   message_handler(event["object"]["message"])
               ).add_done_callback(
                   check_for_exceptions
               )
   Also somewhere in code:
   
       def check_for_exceptions(future):
           exc = future.exception()
           if exc:
               print(get_traceback_as_str(exc))
               sys.exit()
       
       
       def get_traceback_as_str(exc):
           tb = traceback.TracebackException.from_exception(exc)
           return "".join(tb.format())
