# -*- coding: utf-8 -*-
# Author: XiaoXinYo

from typing import Union, Any, AsyncGenerator
from fastapi import FastAPI, Request, WebSocket, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import EdgeGPT
import uuid
import time
import json
import re
import BingImageCreator

HOST = '0.0.0.0'
PORT = 5000
COOKIE_FILE_PATH = './cookie.json'

APP = FastAPI()
APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
STYLES = ['balanced', 'creative', 'precise']
CHATBOT = {}

def getChatBot(token: str) -> tuple:
    global CHATBOT
    if token in CHATBOT:
        chatBot = CHATBOT[token]['chatBot']
        CHATBOT[token]['useTime'] = time.time()
    else:
        chatBot = EdgeGPT.Chatbot(COOKIE_FILE_PATH)
        token = str(uuid.uuid4())
        CHATBOT[token] = {}
        CHATBOT[token]['chatBot'] = chatBot
        CHATBOT[token]['useTime'] = time.time()
    return token, chatBot

def getStyleEnum(style: str) -> EdgeGPT.ConversationStyle:
    enum = EdgeGPT.ConversationStyle
    if style == 'balanced':
        enum = enum.balanced
    elif style == 'creative':
        enum = enum.creative
    elif style == 'precise':
        enum = enum.precise
    return enum

def getAnswer(data: dict) -> str:
    messages = data.get('item').get('messages')
    if 'text' in messages[1]:
        return messages[1].get('text')
    else:
        return messages[1].get('adaptiveCards')[0].get('body')[0].get('text')

def filterAnswer(answer: str) -> str:
    answer = re.sub(r'\[\^.*?\^]', '', answer)
    return answer

def getStreamAnswer(data: dict) -> str:
    messages = data.get('item').get('messages')
    if 'text' in messages[1]:
        answer = messages[1].get('text')
    else:
        answer = messages[1].get('adaptiveCards')[0].get('body')[0].get('text')
    answer = answer = filterAnswer(answer)
    return answer

def getUrl(data: dict) -> list:
    sourceAttributions = data.get('item').get('messages')[1].get('sourceAttributions')
    urls = []
    if sourceAttributions:
        for sourceAttribution in sourceAttributions:
            urls.append({
                'title': sourceAttribution.get('providerDisplayName'),
                'url': sourceAttribution.get('seeMoreUrl')
            })
    return urls

def needReset(data: dict, answer: str) -> bool:
    maxTimes = data.get('item').get('throttling').get('maxNumUserMessagesInConversation')
    nowTimes = data.get('item').get('throttling').get('numUserMessagesInConversation')
    errorAnswers = ['I’m still learning', '我还在学习']
    if [errorAnswer for errorAnswer in errorAnswers if errorAnswer in answer]:
        return True
    elif nowTimes == maxTimes:
        return True
    return False

async def getrequestParameter(request: Request) -> dict:
    data = {}
    if request.method == 'GET':
        data = request.query_params
    elif request.method == 'POST':
        data = await request.form()
        if not data:
            data = await request.json()
    return dict(data)

class GenerateResponse:
    TYPE = Union[str, Response]

    def __init__(self):
        self.response = {}
        self.onlyJSON = False
    
    def _json(self) -> TYPE:
        responseJSON = json.dumps(self.response, ensure_ascii=False)
        if self.onlyJSON:
            return responseJSON
        elif self.stream:
            return f'data: {responseJSON}\n\n'
        return Response(responseJSON, media_type='application/json')

    def error(self, code: int, message: str, onlyJSON: bool=False, stream=False) -> TYPE:
        self.response = {
            'code': code,
            'message': message
        }
        self.onlyJSON = onlyJSON
        self.stream = stream
        return self._json()

    def success(self, data: Any, onlyJSON: bool=False, stream=False) -> TYPE:
        self.response = {
            'code': 200,
            'message': 'success',
            'data': data
        }
        self.onlyJSON = onlyJSON
        self.stream = stream
        return self._json()

async def checkToken() -> None:
    global CHATBOT
    while True:
        for token in CHATBOT.copy():
            if time.time() - CHATBOT[token]['useTime'] > 5 * 60:
                await CHATBOT[token]['chatBot'].close()
                del CHATBOT[token]
        await asyncio.sleep(60)

@APP.on_event('startup')
async def startup() -> None:
    asyncio.get_event_loop().create_task(checkToken())

@APP.exception_handler(404)
def error404(request: Request, exc: Exception) -> Response:
    return GenerateResponse().error(404, '未找到文件')

@APP.exception_handler(500)
def error500(request: Request, exc: Exception) -> Response:
    return GenerateResponse().error(500, '未知错误')

@APP.websocket('/ws')
async def ws(ws: WebSocket) -> str:
    await ws.accept()

    chatBot = EdgeGPT.Chatbot(COOKIE_FILE_PATH)
    while True:
        try:
            parameters = await ws.receive_json()
            if not isinstance(parameters, dict):
                await ws.send_text(GenerateResponse().error(110, '格式错误', True))
                continue
            style = parameters.get('style')
            question = parameters.get('question')
            if not style or not question:
                await ws.send_text(GenerateResponse().error(110, '参数不能为空', True))
                continue
            elif style not in STYLES:
                await ws.send_text(GenerateResponse().error(110, 'style不存在', True))
                continue
            
            data = await chatBot.ask(question, conversation_style=getStyleEnum(style))
            
            if data.get('item').get('result').get('value') == 'Throttled':
                await ws.send_text(GenerateResponse().error(120, '已上限,24小时后尝试', True))
                continue
            
            info = {
                'answer': '',
                'urls': [],
                'reset': False
            }
            answer = getAnswer(data)
            answer = filterAnswer(answer)
            info['answer'] = answer
            info['urls'] = getUrl(data)
            
            if needReset(data, answer):
                await chatBot.reset()
                info['reset'] = True
            
            await ws.send_text(GenerateResponse().success(info, True))
        except FileExistsError:
            await ws.send_text(GenerateResponse().error(500, '未知错误', True))
            await chatBot.reset()

@APP.route('/api', methods=['GET', 'POST'])
async def api(request: Request) -> Response:
    parameters = await getrequestParameter(request)
    token = parameters.get('token')
    style = parameters.get('style')
    question = parameters.get('question')
    if not style or not question:
        return GenerateResponse().error(110, '参数不能为空')
    elif style not in STYLES:
        return GenerateResponse().error(110, 'style不存在')
    
    token, chatBot = getChatBot(token)
    data = await chatBot.ask(question, conversation_style=getStyleEnum(style))
    
    if data.get('item').get('result').get('value') == 'Throttled':
        return GenerateResponse().error(120, '已上限,24小时后尝试')

    info = {
        'answer': '',
        'urls': [],
        'reset': False,
        'token': token
    }
    answer = getAnswer(data)
    answer = filterAnswer(answer)
    info['answer'] = answer
    info['urls'] = getUrl(data)
    
    if needReset(data, answer):
        await chatBot.reset()
        info['reset'] = True
    
    return GenerateResponse().success(info)

@APP.websocket('/ws_stream')
async def wsStream(ws: WebSocket) -> str:
    await ws.accept()

    chatBot = EdgeGPT.Chatbot(COOKIE_FILE_PATH)
    while True:
        try:
            parameters = await ws.receive_json()
            if not isinstance(parameters, dict):
                await ws.send_text(GenerateResponse().error(110, '格式错误', True))
                continue
            style = parameters.get('style')
            question = parameters.get('question')
            if not style or not question:
                await ws.send_text(GenerateResponse().error(110, '参数不能为空', True))
                continue
            elif style not in STYLES:
                await ws.send_text(GenerateResponse().error(110, 'style不存在', True))
                continue
            
            index = 0
            info = {
                'answer': '',
                'urls': [],
                'done': False,
                'reset': False
            }
            async for final, data in chatBot.ask_stream(question, conversation_style=getStyleEnum(style)):
                if not final:
                    answer = data[index:]
                    index = len(data)
                    answer = filterAnswer(answer)
                    if answer:
                        info['answer'] = answer
                        await ws.send_text(GenerateResponse().success(info, True))
                else:
                    if data.get('item').get('result').get('value') == 'Throttled':
                        await ws.send_text(GenerateResponse().error(120, '已上限,24小时后尝试', True))
                        break
                    
                    messages = data.get('item').get('messages')
                    info['answer'] = getStreamAnswer(data)
                    if 'text' not in messages[1]:
                        await ws.send_text(GenerateResponse().success(info, True))
                    info['done'] = True
                    info['urls'] = getUrl(data)

                    if needReset(data, answer):
                        await chatBot.reset()
                        info['reset'] = True
                    
                    await ws.send_text(GenerateResponse().success(info, True))
        except Exception:
            await ws.send_text(GenerateResponse().error(500, '未知错误', True))
            await chatBot.reset()

@APP.route('/api_stream', methods=['GET', 'POST'])
async def apiStream(request: Request) -> Response:
    parameters = await getrequestParameter(request)
    token = parameters.get('token')
    style = parameters.get('style')
    question = parameters.get('question')
    if not style or not question:
        return GenerateResponse().error(110, '参数不能为空')
    elif style not in STYLES:
        return GenerateResponse().error(110, 'style不存在')
    
    token, chatBot = getChatBot(token)
    async def generator() -> AsyncGenerator:
        index = 0
        info = {
            'answer': '',
            'urls': [],
            'done': False,
            'reset': False,
            'token': token
        }
        async for final, data in chatBot.ask_stream(question, conversation_style=getStyleEnum(style)):
            if not final:
                answer = data[index:]
                index = len(data)
                answer = filterAnswer(answer)
                if answer:
                    info['answer'] = answer
                    yield GenerateResponse().success(info, stream=True)
            else:
                if data.get('item').get('result').get('value') == 'Throttled':
                    yield GenerateResponse().error(120, '已上限,24小时后尝试', stream=True)
                    break
                
                messages = data.get('item').get('messages')
                info['answer'] = getStreamAnswer(data)
                if 'text' not in messages[1]:
                    yield GenerateResponse().success(info, stream=True)
                info['done'] = True
                info['urls'] = getUrl(data)

                if needReset(data, answer):
                    await chatBot.reset()
                    info['reset'] = True
                
                yield GenerateResponse().success(info, stream=True)
    
    return StreamingResponse(generator(), media_type='text/event-stream')

@APP.route('/image', methods=['GET', 'POST'])
async def image(request: Request) -> Response:
    keyword = (await getrequestParameter(request)).get('keyword')
    if not keyword:
        return GenerateResponse().error(110, '参数不能为空')
    elif not re.match(r'[a-zA-Z]', keyword):
        return GenerateResponse().error(110, '仅支持英文')

    with open(COOKIE_FILE_PATH, encoding='utf-8') as file:
        cookies = json.load(file)
        for cookie in cookies:
            if cookie.get('name') == '_U':
                uCookie = cookie.get('value')
                break
    
    return GenerateResponse().success(BingImageCreator.ImageGen(uCookie).get_images(keyword))

if __name__ == '__main__':
    uvicorn.run(APP, host=HOST, port=PORT)