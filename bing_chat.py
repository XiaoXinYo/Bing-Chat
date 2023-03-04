# -*- coding: utf-8 -*-
# Author: XiaoXinYo

from fastapi import FastAPI, Request, WebSocket, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import EdgeGPT
import json
import re

HOST = '0.0.0.0'
PORT = 5000

APP = FastAPI()
APP.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
ERROR_ANSWER = ['I’m still learning', '我还在学习']

class GenerateResponse:
    def __init__(self):
        pass
    
    def _json(self):
        responseJSON = json.dumps(self.response, ensure_ascii=False)
        if self.onlyJSON:
            return responseJSON
        return Response(responseJSON, media_type='application/json')

    def error(self, code, message, onlyJSON=False):
        self.response = {
            'code': code,
            'message': message
        }
        self.onlyJSON = onlyJSON
        return self._json()

    def success(self, data, onlyJSON=False):
        self.response = {
            'code': 200,
            'message': 'success',
            'data': data
        }
        self.onlyJSON = onlyJSON
        return self._json()

async def getrequestParameter(request: Request):
    data = {}
    if request.method == 'GET':
        data = request.query_params
    elif request.method == 'POST':
        data = await request.form()
        if not data:
            data = await request.json()
    return dict(data)

@APP.exception_handler(404)
def error404(request, exc):
    return GenerateResponse().error(404, '未找到文件')

@APP.exception_handler(500)
def error500(request, exc):
    return GenerateResponse().error(500, '未知错误')

@APP.websocket('/ws_stream')
async def wsStream(ws: WebSocket=None):
    await ws.accept()

    chatBot = EdgeGPT.Chatbot('./cookie.json')
    while True:
        try:
            question = await ws.receive_text()
            if not question:
                await ws.send_text(GenerateResponse().error(110, '参数错误'))
            
            index = 0
            async for final, data in chatBot.ask_stream(question):
                if not final:
                    answer = data[index:]
                    index = len(data)
                    answer = re.sub(r'\[.*?\]', '', answer)
                    if answer:
                        await ws.send_text(GenerateResponse().success({
                            'answer': answer,
                            'urls': [],
                            'done': False
                        }, True))
                else:
                    if data.get('item').get('result').get('value') == 'Throttled':
                        await ws.send_text(GenerateResponse().error(120, '已上限,24小时后尝试', True))
                        continue
                    
                    info = {
                        'answer': '',
                        'urls': [],
                        'done': True
                    }
                    messages = data.get('item').get('messages')
                    sourceAttributions = messages[1].get('sourceAttributions')
                    if sourceAttributions:
                        for sourceAttribution in sourceAttributions:
                            info['urls'].append({
                                'title': sourceAttribution.get('providerDisplayName'),
                                'url': sourceAttribution.get('seeMoreUrl')
                            })
                    answer = messages[1].get('text')
                    answer = re.sub(r'\[\^.*?\^]', '', answer)
                    info['answer'] = answer
                    await ws.send_text(GenerateResponse().success(info, True))

                    maxTimes = data.get('item').get('throttling').get('maxNumUserMessagesInConversation')
                    nowTimes = data.get('item').get('throttling').get('numUserMessagesInConversation')
                    if [errorAnswer for errorAnswer in ERROR_ANSWER if errorAnswer in answer]:
                        await chatBot.reset()
                    elif nowTimes == maxTimes:
                        await chatBot.reset()
        except Exception:
            await ws.send_text(GenerateResponse().error(500, '未知错误', True))
            await chatBot.reset()

@APP.route('/api', methods=['GET', 'POST'])
@APP.websocket('/ws')
async def ws(request: Request=None, ws: WebSocket=None):
    if ws:
        await ws.accept()
    else:
        question = (await getrequestParameter(request)).get('question')
        if not question:
            return GenerateResponse().error(110, '参数错误')
    
    chatBot = EdgeGPT.Chatbot('./cookie.json')
    while True:
        try:
            if ws:
                question = await ws.receive_text()
                if not question:
                    await ws.send_text(GenerateResponse().error(110, '参数错误'))
            data = await chatBot.ask(question)
            
            if data.get('item').get('result').get('value') == 'Throttled':
                if ws:
                    await ws.send_text(GenerateResponse().error(120, '已上限,24小时后尝试', True))
                    continue
                return GenerateResponse().error(120, '已上限,24小时后尝试')

            info = {
                'answer': '',
                'urls': []
            }
            messages = data.get('item').get('messages')
            sourceAttributions = messages[1].get('sourceAttributions')
            if sourceAttributions:
                for sourceAttribution in sourceAttributions:
                    info['urls'].append({
                        'title': sourceAttribution.get('providerDisplayName'),
                        'url': sourceAttribution.get('seeMoreUrl')
                    })
            answer = messages[1].get('text')
            answer = re.sub(r'\[\^.*?\^]', '', answer)
            info['answer'] = answer
            if ws:
                await ws.send_text(GenerateResponse().success(info, True))

                maxTimes = data.get('item').get('throttling').get('maxNumUserMessagesInConversation')
                nowTimes = data.get('item').get('throttling').get('numUserMessagesInConversation')
                if [errorAnswer for errorAnswer in ERROR_ANSWER if errorAnswer in answer]:
                    await chatBot.reset()
                elif nowTimes == maxTimes:
                    await chatBot.reset()
            else:
                return GenerateResponse().success(info)
        except Exception:
            if ws:
                await ws.send_text(GenerateResponse().error(500, '未知错误', True))
                await chatBot.reset()
            else:
                return GenerateResponse().error(500, '未知错误')

if __name__ == '__main__':
    uvicorn.run(APP, host=HOST, port=PORT)