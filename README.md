# Python-UDP-Chat-Room
A chat room using UDP in Python.

## About the client
Notice that *udpclient.ini* is required. And *udpclient.ico* is recommended(to show the icon).  
### How to use the config
The config is used to provide the address of the server, and to configure the logger.   
#### To change the address
The default config should be like this:
```
[socket]
Host=127.0.0.1
Port=14514
```
Just change *Host* and *Port*.
### To configure the logger
Look at <https://docs.python.org/zh-cn/3.9/library/logging.config.html#logging-config-fileformat>

---
Also note that the server will not know the client is exiting if you end the client process in the task manager, so this is **not** recommended.

## About the server
The server will print the addresses of the clients when a new client connects, ~~although it glitched sometimes~~.
