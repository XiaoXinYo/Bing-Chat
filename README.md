## 介绍
Bing Chat服务端,通过WebSocket/API实现通讯.
## 需求
1. 语言: Python3.8+.
2. 包: fastapi, uvicorn, python-multipart, EdgeGPT.
3. 其他: New Bing账户.
## 配置
地址和端口分别在第11行和第12行.
## 使用
1. 浏览器安装Cookie-Editor扩展.
2. 在[https://www.bing.com/chat](https://www.bing.com/chat)页面中点击扩展.
3. 点击扩展右下角的Export,将复制的内容粘贴到cookie.json.
4. 运行bing_chat.py.
## 参数
### 请求
名称|必填|中文名
---|---|---
style|是|风格,balanced代表平衡,creative代表创造,precise代表精确
question|是|问题

注:WebSocket发送需JSON格式.
### 响应
名称|中文名|说明
---|---|---
code|状态码|
message|消息|
data|数据|
answer|回答|
links|链接|
done|完成|部分传输是否完成,当连接/ws_stream时存在
reset|重置|下次对话是否被重置,当为WebSocket时存在(code为500时也会被重置)
### 整体传输
> 等待Bing Chat响应完后返回.

#### WebSocket
连接/ws.
```
{"code": 200, "message": "success", "data": {answer:"您好，这是必应。", urls:[{"title": "The New Bing - Learn More", "url": "https://www.bing.com/new"}], "reset": false}}
```
#### API
1. 请求方式: GET/POST.
2. 请求地址: /api.
```
{"code": 200, "message": "success", "data": {answer:"您好，这是必应。", urls:[{"title": "The New Bing - Learn More", "url": "https://www.bing.com/new"}]}}
```
### 流传输
> 一部分一部分返回.

1. WebSocket连接/ws_stream.
2. 当部分传输完成时,将会返回整体,done改为true,url才会有值.
```
{"code": 200, "message": "success", "data": {answer:"您。", urls:[], "done": false, "reset": false}}

{"code": 200, "message": "success", "data": {answer:"好", urls:[], "done": false, "reset": false}}

{"code": 200, "message": "success", "data": {answer:"，", urls:[], "done": false, "reset": false}}

{"code": 200, "message": "success", "data": {answer:"这。", urls:[], "done": false, "reset": false}}

{"code": 200, "message": "success", "data": {answer:"是", urls:[], "done": false, "reset": false}}

{"code": 200, "message": "success", "data": {answer:"必应", urls:[], "done": false, "reset": false}}

{"code": 200, "message": "success", "data": {answer:"。", urls:[], "done": false, "reset": false}}

{"code": 200, "message": "success", "data": {answer:"您好，这是必应。", urls:[{"title": "The New Bing - Learn More", "url": "https://www.bing.com/new"}], "done": true, "reset": false}}
```
## emm
1. 页面写的有点丑，有能力的大神，可以pull request一下，如果你有的example也可以提交.
2. 搭建好建议不要对外开放，因为目前Bing Chat24小时内有次数限制.
3. 至于反应快慢的问题，要看回答文本的长度，如果文本长度过长，回复时间会比较长.
4. 关于整体传输和流传输，整体传输由于要等待Bing完全响应才能开始传输，所以时间要久一点。流传输会先返回一部分，所以看起来比较快，但其实最终的完成时间都是一样的.