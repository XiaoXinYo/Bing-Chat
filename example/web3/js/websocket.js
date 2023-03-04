const WS = new WebSocket('ws://127.0.0.1:5000/ws_stream');//使用https时需要wss协议，使用http仅需要ws协议
let ANSWER_SPAN = null;

WS.onopen = function () {
    console.log('连接成功');
    mdui.snackbar({
        message: '连接成功',
        position: 'right-top'
    });
}

WS.onclose = function () {
    console.log('断开连接');
    mdui.snackbar({
        message: '连接已断开',
        position: 'right-top'
    });
}

window.onbeforeunload = function () {
    WS.close();
}

WS.onmessage = function (e) {
    if (ANSWER_SPAN.innerHTML == '正在回复...') {
        ANSWER_SPAN.innerHTML = '';
    }

    let data = JSON.parse(e.data);
    if (data['code'] == 200) {
        if (data.data.done === false) {
            ANSWER_SPAN.innerHTML += data['data']['answer'];
        } else {
            document.getElementById('send').disabled = false;
        }
    } else {
        ANSWER_SPAN.innerHTML = data['message'];
        document.getElementById('send').disabled = false;
    }
}

document.getElementById('send').onclick = function () {
    if (WS.readyState != 1) {
        mdui.snackbar({
            message: '连接已断开',
            position: 'right-top'
        });
        return;
    }
    let input = document.getElementById('editor');
    let content = input.innerHTML;
    if (content == '') {
        mdui.snackbar({
            message: '请输入内容',
            position: 'right-top'
        });
        return;
    }

    let div = document.createElement('div');
    div.innerHTML = "<div class='cright cmsg'><img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/me.jpg'><span class='name'><span>You</span></span><span class='content'>" + content + "</span></div>";
    document.getElementById('messagesdiv').appendChild(div);

    let answer_div = document.createElement('div');
    answer_div.className = 'cleft cmsg';
    answer_div.innerHTML = "<img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/bing2.png'><span class='name'><span>EdgeGPT</span></span>";
    ANSWER_SPAN = document.createElement('span');
    ANSWER_SPAN.className = 'content';
    ANSWER_SPAN.innerHTML = '正在回复...';
    answer_div.appendChild(ANSWER_SPAN);
    document.getElementById('messagesdiv').appendChild(answer_div);

    WS.send(content);
    input.innerHTML = '';
    document.getElementById('send').disabled = true;
}