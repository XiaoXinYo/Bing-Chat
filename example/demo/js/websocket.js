const WS = new WebSocket('wss://你的域名/ws');//使用https时需要wss，使用http仅需要ws

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
    document.getElementById('send').disabled = false;
    let data = JSON.parse(e.data);
    let content = document.getElementById('editor');
    let div = document.createElement('div');
    if (data['code'] == 200) {
        div.innerHTML = "<div class='cleft cmsg'><img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/bing2.png'><span class='name'><span>EdgeGPT</span></span><span class='content'>" + data['data']['text'] + "</span></div>";
    } else {
        div.innerHTML = "<div class='cleft cmsg'><img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/bing2.png'><span class='name'><span>EdgeGPT</span></span><span class='content'>" + data['message'] + "</span></div>";
    }
    document.getElementById('messagesdiv').appendChild(div);
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

    WS.send(content);
    input.innerHTML = '';
    document.getElementById('send').disabled = true;
}