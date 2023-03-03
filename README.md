## 介绍
Bing Chat服务端,通过WebSocket/API实现通讯.
## 需求
1. 语言: Python.
2. 包: fastapi, uvicorn, python-multipart, EdgeGPT.
3. 其他: New Bing账户.
## 使用
1. 浏览器安装Cookie-Editor扩展.
2. 在[https://www.bing.com/chat](https://www.bing.com/chat)页面中点击扩展.
3. 点击扩展右下角的Export,将复制的内容粘贴到cookie.json.
4. 运行bing_chat.py.
5. WebSocket连接/ws,API请求/api(请求参数为question).
## 配置
地址和端口分别在第11行和第12行.
## 响应参数
名称|说明
---|---
code|状态码
message|消息
data|数据
answer|答复
links|链接
## emm
1. 页面写的有点丑，有能力的大神，可以pull request一下，如果你有的example也可以提交.
2. 搭建好建议不要对外开放，因为目前Bing Chat24小时内有次数限制.
3. 至于反应快慢的问题，要看回答文本的长度，如果文本长度过长，回复时间会比较长.