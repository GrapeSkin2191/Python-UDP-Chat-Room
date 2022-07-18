# Python-UDP-Chat-Room
A chat room using UDP in Python.

## About the client
The client will generate a log when running and a txt file which contains the chat when closing properly.

Note that *udpclient.ini* is required. And *udpclient.ico* is recommended (in order to show the icon).  

Also note that the server will not know the client is exiting if you end the client process in the task manager, so this is **not** recommended.

## About the server
The server will generate a log when running.

## How to change the config (both the client and the server)
To the client, the config can provide the address of the server. To the server, it can provide the address it uses.   
The config is also used to configure the logger.   
### To change the address
The default config should be like this *(if it is not, it is a bug, lol)*:
```
[socket]
Host=127.0.0.1
Port=14514
```
Just change *Host* and *Port*.
### To configure the logger
Look at <https://docs.python.org/zh-cn/3.9/library/logging.config.html#logging-config-fileformat>
