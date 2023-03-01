## 介绍
Bing Chat服务端,通过API/WebSocket实现通讯.
## 需求
1. 语言: Python.
2. 包:  
   API版: gevent,flask,flask_cors,EdgeGPT.  
   WebSocket版: asyncio,websockets,EdgeGPT.
3. 其他: New Bing账户.
## 使用
1. 浏览器安装Cookie-Editor扩展.
2. 在[https://www.bing.com/chat](https://www.bing.com/chat)页面中点击扩展.
3. 点击扩展右下角的Export,将复制的内容粘贴到cookie.json.
4. 运行bing_chat_api.py/bing_chat_ws.py
## 配置
API版: API地址和端口分别在第14行和第15行.
WebSocket版: WebSocket地址和端口分别在第10行和第11行.
## 响应参数
名称|说明
---|---
code|状态码
message|消息
data|数据
text|文本
links|链接
注: API版的请求参数为message.
## emm
1. 页面写的有点丑，有能力的大神，可以pull request一下，如果你有的example也可以提交.
2. 搭建好建议不要对外开放，因为目前Bing Chat24小时内有次数限制.