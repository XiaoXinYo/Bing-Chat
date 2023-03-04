## 介绍
Bing Chat服务端,通过WebSocket/API实现通讯.
## 需求
1. 语言: Python.
2. 包: fastapi, uvicorn, python-multipart, EdgeGPT.
3. 其他: New Bing账户.
## 配置
地址和端口分别在第11行和第12行.
## 使用
1. 浏览器安装Cookie-Editor扩展.
2. 在[https://www.bing.com/chat](https://www.bing.com/chat)页面中点击扩展.
3. 点击扩展右下角的Export,将复制的内容粘贴到cookie.json.
4. 运行bing_chat.py.
### 整体传输
> 等待Bing Chat响应完后返回.

1. WebSocket连接/ws.
2. API请求/api
```
{"code": 200, "message": "success", "data": {answer:"您好，这是必应。", urls:[{"title": "The New Bing - Learn More", "url": "https://www.bing.com/new"}]}}
```
### 流传输
> 一部分一部分返回.

1. WebSocket连接/ws_stream.
2. 当部分返回完成时,将会返回整体,done改为true,url才会有值.
```
{"code": 200, "message": "success", "data": {answer:"您。", urls:[], "done": false}}

{"code": 200, "message": "success", "data": {answer:"好", urls:[], "done": false}}

{"code": 200, "message": "success", "data": {answer:"，", urls:[], "done": false}}

{"code": 200, "message": "success", "data": {answer:"这。", urls:[], "done": false}}

{"code": 200, "message": "success", "data": {answer:"是", urls:[], "done": false}}

{"code": 200, "message": "success", "data": {answer:"必应", urls:[], "done": false}}

{"code": 200, "message": "success", "data": {answer:"。", urls:[], "done": false}}

{"code": 200, "message": "success", "data": {answer:"您好，这是必应。", urls:[{"title": "The New Bing - Learn More", "url": "https://www.bing.com/new"}], "done": true}}
```
## 响应参数
| 名称      | 说明   |
|---------|------|
| code    | 状态码  |
| message | 消息   |
| data    | 数据   |
| text    | 文本   |
| links   | 链接   |
| done    | 是否完成 |

## emm
1. 页面写的有点丑，有能力的大神，可以pull request一下，如果你有的example也可以提交.
2. 搭建好建议不要对外开放，因为目前Bing Chat24小时内有次数限制.
3. 至于反应快慢的问题，要看回答文本的长度，如果文本长度过长，回复时间会比较长.
4. 关于整体传输和流传输，，整体传输由于要等待完全响应所以时间要久，流传输会先返回一部分，所以看起来比较快，但其实最终的完成时间都是一样的.