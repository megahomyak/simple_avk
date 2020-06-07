# simple_avk
Simple asynchronous VK API client framework by megahomyak.

It's so simple that it fits in one file.

It supports:
* VK API methods calling (with "call_method" method).
* Receiving events (with longpoll; "get_new_events" and "listen" methods).
* Errors raising if something went wrong (you can disable it in "\_\_init\_\_").

Warnings:
* Before receiving events with "get_new_events", you need to prepare longpoll (with "prepare_longpoll" method).
* In "listen" method "prepare_longpoll" is called automatically.

# How to use it
1. Create object of class "SimpleAVK", passing token, aiohttp session, maybe group id or other params to it
2. Here we go! Now you can call VK methods (with "call_method" method), listen to the longpoll ("listen" method) or get list of events ("get_new_events" method, but at first you need to prepare longpoll with "prepare_longpoll" method)

# Possible async problems
To respond truly asynchronously, you need to throw incoming events in handlers and then just forget about them, handler will do its work. Like this:
1. You got a response
2. It has type "message_new"
3. You throw it into a handler
4. Just forget about it; you don't need results (because there is no results in suchlike handlers)
5. When an event gives you control back, you scroll list of events further and throw events to their handlers (or do nothing)

How to do it:
1. Throw every handler into loop with asyncio.gather (it returns a Future object). You need to hang done callback function to returned Future (with "add_done_callback" method). When Future is done, it will be sent in the specified function.
2. In done callback you can get results of given handler or this handler's exception (with "exception" method of given Future). By default, all exceptions from futures are catched and don't show up. Now you can print them or even get their traceback (with "traceback" module), print it and stop the program (with sys.exit()). Asyncio catches any exception in the done callback too, so you can't just raise the received exception.
