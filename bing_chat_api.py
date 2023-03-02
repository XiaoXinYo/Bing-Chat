# -*- coding: utf-8 -*-
# Author: XiaoXinYo

from gevent.pywsgi import WSGIServer
from gevent import monkey
monkey.patch_all()

from flask import Flask, request
import flask_cors
import EdgeGPT
import json
import re

HOST = '0.0.0.0'
PORT = 5000

APP = Flask(__name__)
flask_cors.CORS(APP, resources=r'/*')

class GenerateResponseResult:
    def __init__(self):
        pass
    
    def _json(self):
        return json.dumps(self.result, ensure_ascii=False)

    def success(self, data):
        result = {
            'code': 200,
            'message': 'success',
            'data': data
        }
        self.result = result
        return self._json()

    def error(self, code, message):
        result = {
            'code': code,
            'message': message
        }
        self.result = result
        return self._json()

def getRequestParameter(request):
    data = {}
    if request.method == 'GET':
        data = request.args
    elif request.method == 'POST':
        data = request.form
        if not data:
            data = request.get_json()
    return dict(data)

@APP.errorhandler(404)
def errorhandler_404(error):
    return GenerateResponseResult().error(404, '未找到文件')

@APP.errorhandler(500)
def errorhandler_500(error):
    return GenerateResponseResult().error(500, '未知错误')

@APP.route('/', methods=['GET', 'POST'])
async def index():
    message = getRequestParameter(request).get('message')
    chatBot = EdgeGPT.Chatbot(cookiePath='./cookie.json')
    try:
        data = await chatBot.ask(message)
        
        if data.get('item').get('result').get('value') == 'Throttled':
            return GenerateResponseResult().error(120, '已上限,24小时后尝试')
            
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
        return GenerateResponseResult().success(info)
    except Exception:
        return GenerateResponseResult().error(500, '未知错误')

if __name__ == '__main__':
    WSGIServer((HOST, PORT), APP).serve_forever()