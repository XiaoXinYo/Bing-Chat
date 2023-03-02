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

class GenerateResponse:
    def __init__(self):
        pass
    
    def _json(self):
        resultJSON = json.dumps(self.result, ensure_ascii=False)
        if self.onlyJSON:
            return resultJSON
        return Response(resultJSON, media_type='application/json')

    def success(self, data, onlyJSON=False):
        result = {
            'code': 200,
            'message': 'success',
            'data': data
        }
        self.result = result
        self.onlyJSON = onlyJSON
        return self._json()

    def error(self, code, message, onlyJSON=False):
        result = {
            'code': code,
            'message': message
        }
        self.result = result
        self.onlyJSON = onlyJSON
        return self._json()

def getrequestParameter(request):
    data = {}
    if request.method == 'GET':
        data = request.query_params
    elif request.method == 'POST':
        data = request.form()
        if not data:
            data = request.json()
    return dict(data)

@APP.websocket('/ws')
@APP.route('/api', methods=['GET', 'POST'])
async def ws(request: Request=None, ws: WebSocket=None):
    if ws:
        await ws.accept()
    else:
        message = getrequestParameter(request).get('message')
        if not message:
            return GenerateResponse().error(110, '参数错误')
    
    chatBot = EdgeGPT.Chatbot(cookiePath='./cookie.json')
    while True:
        try:
            if ws:
                message = await ws.receive_text()
            data = await chatBot.ask(message)
            
            if data.get('item').get('result').get('value') == 'Throttled':
                if ws:
                    await ws.send_text(GenerateResponse().error(120, '已上限,24小时后尝试', True))
                    break
                return GenerateResponse().error(120, '已上限,24小时后尝试')
            
            info = {
                'text': '',
                'urls': []
            }
            messages = data.get('item').get('messages')
            if len(messages) == 1 or 'New topic' in json.dumps(messages):
                await chatBot.reset()
                data = await chatBot.ask(message)
                messages = data.get('item').get('messages')
            else:
                sourceAttributions = messages[1].get('sourceAttributions')
                if sourceAttributions:
                    for sourceAttribution in sourceAttributions:
                        info['urls'].append({
                            'title': sourceAttribution.get('providerDisplayName'),
                            'url': sourceAttribution.get('seeMoreUrl')
                        })
            text = messages[1].get('text')
            text = re.sub(r'\[\^.*?\^]', '', text)
            info['text'] = text

            if ws:
                await ws.send_text(GenerateResponse().success(info, True))
            else:
                return GenerateResponse().success(info)
        except Exception:
            if ws:
                await ws.send_text(GenerateResponse().error(500, '未知错误', True))
            else:
                return GenerateResponse().error(500, '未知错误')

if __name__ == '__main__':
    uvicorn.run(APP, host=HOST, port=PORT)