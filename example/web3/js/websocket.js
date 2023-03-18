const DEFAULT_SRV_URL = "ws://127.0.0.1:5000/ws_stream";
function get_src_url() {
    const protocol = window.location.protocol
    if (protocol != "http:" && protocol != "https:") {
        // use default url
        return DEFAULT_SRV_URL;
    }
    const host = window.location.hostname

    let port = "5000"
    try {
        port = srv_port
    }catch (error){
        console.log(error.message)
    }
    // ws://127.0.0.1:5000/ws_stream
    return "ws://" + host + ":" + port + "/ws_stream"
}
const target_url = get_src_url()
console.log("connecting to " + target_url)
const WS = new WebSocket(target_url);//使用https时需要wss协议，使用http仅需要ws协议
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

        if (data['data']['reset']) {
            let answerDiv = document.createElement('div');
            answerDiv.innerHTML = "<div class='cleft cmsg'><img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/bing2.png'><span class='name'><span>EdgeGPT</span></span><span class='content'>对话已被重置</span></div>";
            document.getElementById('messagesdiv').appendChild(answerDiv);
        }
    } else {
        ANSWER_SPAN.innerHTML = data['message'];

        if (data['code'] == 500) {
            let answerDiv = document.createElement('div');
            answerDiv.innerHTML = "<div class='cleft cmsg'><img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/bing2.png'><span class='name'><span>EdgeGPT</span></span><span class='content'>对话已被重置</span></div>";
            document.getElementById('messagesdiv').appendChild(answerDiv);
        }

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

    var radio = document.getElementsByName("style");
    for (var i = 0; i < radio.length; i++) {
        if (radio[i].checked) {
            var radioValue = radio[i].value;
        }
    }

    let input = document.getElementById('editor');
    let question = input.innerHTML;
    if (question == '') {
        mdui.snackbar({
            message: '请输入内容',
            position: 'right-top'
        });
        return;
    }

    let div = document.createElement('div');
    div.innerHTML = "<div class='cright cmsg'><img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/me.jpg'><span class='name'><span>You</span></span><span class='content'>" + question + "</span></div>";
    document.getElementById('messagesdiv').appendChild(div);

    let answer_div = document.createElement('div');
    answer_div.className = 'cleft cmsg';
    answer_div.innerHTML = "<img class='headIcon radius' ondragstart='return false;' oncontextmenu='return false;'src='../images/bing2.png'><span class='name'><span>EdgeGPT</span></span>";
    ANSWER_SPAN = document.createElement('span');
    ANSWER_SPAN.className = 'content';
    ANSWER_SPAN.innerHTML = '正在回复...';
    answer_div.appendChild(ANSWER_SPAN);
    document.getElementById('messagesdiv').appendChild(answer_div);

    WS.send(JSON.stringify({"style": radioValue, "question": question}));
    input.innerHTML = '';
    document.getElementById('send').disabled = true;
}