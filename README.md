# simple_avk
Simple asynchronous VK API client framework by megahomyak.

It's so simple that it fits in one file.

It supports:
    VK API methods calling (with "call_method" method).
    Receiving events (with longpoll; "get_new_events" and "listen" methods).
    Errors raising if something went wrong (you can disable it in "__init__").

Warnings:
    Before receiving events with "get_new_events", you need to prepare longpoll (with "prepare_longpoll" method).
    In "listen" method "prepare_longpoll" is called automatically.

Further docs is in code, because I'm lazy
