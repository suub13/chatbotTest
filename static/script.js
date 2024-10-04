document.addEventListener('DOMContentLoaded', () => {
    initializeChatbot();
});

let messageHistory = []; // 메시지를 저장할 배열
let conversationId = null; // 대화 ID 저장

function initializeChatbot() {
    setupEventListeners();
}

function setupEventListeners() {
    document.getElementById('send-button1').addEventListener('click', sendMessage1);
    document.getElementById('send-button2').addEventListener('click', sendMessage2);
    document.getElementById('send-button3').addEventListener('click', sendMessage3);

    // 이건 'Enter' 버튼을 누르면 button click과 같은 기능을 함.
    document.getElementById('chat-input1').addEventListener('keydown', handleKeyDown1);
    document.getElementById('chat-input2').addEventListener('keydown', handleKeyDown2);
    document.getElementById('chat-input3').addEventListener('keydown', handleKeyDown3);

    document.getElementById('reload-button1').addEventListener('click', reloadChat1);
    document.getElementById('reload-button2').addEventListener('click', reloadChat2);
    document.getElementById('reload-button3').addEventListener('click', reloadChat3);

}

function handleKeyDown1(event) {
    if (event.key === 'Enter') {
        sendMessage1();
    }
}

function handleKeyDown2(event) {
    if (event.key === 'Enter') {
        sendMessage2();
    }
}

function handleKeyDown3(event) {
    if (event.key === 'Enter') {
        sendMessage3();
    }
}

function sendMessage1() {
    const inputField = document.getElementById('chat-input1');
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage1('user', message);
        // 메시지를 messageHistory에 저장
//        messageHistory.push({ sender: 'user', text: message });
        // inputField 리셋
        inputField.value = '';
        // 챗봇이 응답을 생성하는 중간에 사용자가 다른 질문을 할 수 없게 막는 기능
        toggleInput1(false);
        getChatbotResponse1(message);
    }
}

function sendMessage2() {
    const inputField = document.getElementById('chat-input2');
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage2('user', message);
        // 메시지를 messageHistory에 저장
//        messageHistory.push({ sender: 'user', text: message });
        // inputField 리셋
        inputField.value = '';
        // 챗봇이 응답을 생성하는 중간에 사용자가 다른 질문을 할 수 없게 막는 기능
        toggleInput2(false);
        getChatbotResponse2(message);
    }
}

function sendMessage3() {
    const inputField = document.getElementById('chat-input3');
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage3('user', message);
        // 메시지를 messageHistory에 저장
//        messageHistory.push({ sender: 'user', text: message });
        // inputField 리셋
        inputField.value = '';
        // 챗봇이 응답을 생성하는 중간에 사용자가 다른 질문을 할 수 없게 막는 기능
        toggleInput3(false);
        getChatbotResponse3(message);
    }
}

async function reloadChat1() {
    console.log('Reload button clicked. Messages are being reloaded.');

    // 메시지 영역 empty string을 대체하여 내용 리셋
    const messagesContainer = document.getElementById('messages1');
    messagesContainer.innerHTML = '';

    // model instance 다시 시작해서 로드하기.
    const newMessage = await reload1();
}

async function reloadChat2() {
    console.log('Reload button clicked. Messages are being reloaded.');

    // 메시지 영역 empty string을 대체하여 내용 리셋
    const messagesContainer = document.getElementById('messages2');
    messagesContainer.innerHTML = '';

    // model instance 다시 시작해서 로드하기.
    const newMessage = await reload2();
}

async function reloadChat3() {
    console.log('Reload button clicked. Messages are being reloaded.');

    // 메시지 영역 empty string을 대체하여 내용 리셋
    const messagesContainer = document.getElementById('messages3');
    messagesContainer.innerHTML = '';

    // model instance 다시 시작해서 로드하기.
    const newMessage = await reload3();
}

function displayMessage1(sender, message) {
    const messagesContainer = document.getElementById('messages1');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
//    messageElement.textContent = message;
    // Replace \n with <br> to handle line breaks
    messageElement.innerHTML = message.replace(/\n/g, '<br>');
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


function displayMessage2(sender, message) {
    const messagesContainer = document.getElementById('messages2');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
//    messageElement.textContent = message;
    // Replace \n with <br> to handle line breaks
    messageElement.innerHTML = message.replace(/\n/g, '<br>');
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


function displayMessage3(sender, message) {
    const messagesContainer = document.getElementById('messages3');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
//    messageElement.textContent = message;
    // Replace \n with <br> to handle line breaks
    messageElement.innerHTML = message.replace(/\n/g, '<br>');
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


function linkifyText(text) {
    const urlRegex = /(https?:\/\/[^\s]+)/g; // URL 패턴을 찾는 정규 표현식
    return text.replace(urlRegex, function(url) {
      return `<a href="${url}" target="_blank">${url}</a>`; // URL을 <a> 태그로 감쌈
    });
  }



function getChatbotResponse1(userMessage) {
    fetch('http://localhost:5000/api/botResponse1', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
    })
    .then(response => response.json())
    .then(data => {
        const botResponse = data.response;
        const organizedResponse = linkifyText(botResponse);
        console.log('Result:', organizedResponse); // 결과 출력
        displayMessage1('bot', organizedResponse);
        toggleInput1(true);

    })
    .catch(error => {
        console.error('Error:', error);
    });

}


function getChatbotResponse2(userMessage) {
    fetch('http://localhost:5000/api/botResponse2', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
    })
    .then(response => response.json())
    .then(data => {
        const botResponse = data.response;
        console.log('Result:', botResponse); // 결과 출력
        displayMessage2('bot', botResponse);
        toggleInput2(true);

    })
    .catch(error => {
        console.error('Error:', error);
    });

}

function getChatbotResponse3(userMessage) {
    fetch('http://localhost:5000/api/botResponse3', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
    })
    .then(response => response.json())
    .then(data => {
        const botResponse = data.response;
        console.log('Result:', botResponse); // 결과 출력
        displayMessage3('bot', botResponse);
        toggleInput3(true);

    })
    .catch(error => {
        console.error('Error:', error);
    });

}

async function reload1() {
    try {
        const response = await fetch('/api/chatReload1', {
            method: 'GET', // 또는 POST 등 필요한 메서드를 사용
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        return data.message; // Python 함수의 결과를 반환
    } catch (error) {
        console.error('Error fetching Python function result:', error);
        return 'Error: Unable to load data';
    }
}

async function reload2() {
    try {
        const response = await fetch('/api/chatReload2', {
            method: 'GET', // 또는 POST 등 필요한 메서드를 사용
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        return data.message; // Python 함수의 결과를 반환
    } catch (error) {
        console.error('Error fetching Python function result:', error);
        return 'Error: Unable to load data';
    }
}

async function reload3() {
    try {
        const response = await fetch('/api/chatReload3', {
            method: 'GET', // 또는 POST 등 필요한 메서드를 사용
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        return data.message; // Python 함수의 결과를 반환
    } catch (error) {
        console.error('Error fetching Python function result:', error);
        return 'Error: Unable to load data';
    }
}

function toggleInput1(enable) {
//    const inputField = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button1');
    if (enable) {
//        inputField.disabled = false;
        sendButton.disabled = false;
//        inputField.focus();
    } else {
//        inputField.disabled = true;
        sendButton.disabled = true;
    }
}

function toggleInput2(enable) {
//    const inputField = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button2');
    if (enable) {
//        inputField.disabled = false;
        sendButton.disabled = false;
//        inputField.focus();
    } else {
//        inputField.disabled = true;
        sendButton.disabled = true;
    }
}

function toggleInput3(enable) {
//    const inputField = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button3');
    if (enable) {
//        inputField.disabled = false;
        sendButton.disabled = false;
//        inputField.focus();
    } else {
//        inputField.disabled = true;
        sendButton.disabled = true;
    }
}


function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto'; // Reset the height
    let newHeight = textarea.scrollHeight;
    const maxHeight = parseInt(window.getComputedStyle(textarea).getPropertyValue('max-height'), 10);

    if (newHeight > maxHeight) {
        newHeight = maxHeight;
        textarea.style.overflowY = 'auto'; // Enable vertical scroll when max height is reached
    } else {
        textarea.style.overflowY = 'hidden'; // Hide overflow before max height is reached
    }

    textarea.style.height = newHeight + 'px'; // Set the height to match the content
}

const chatInput1 = document.getElementById('chat-input1');
const chatInput2 = document.getElementById('chat-input2');
const chatInput3 = document.getElementById('chat-input3');

chatInput1.addEventListener('input1', function() {
    adjustTextareaHeight(chatInput1);
});

chatInput2.addEventListener('input2', function() {
    adjustTextareaHeight(chatInput2);
});

chatInput3.addEventListener('input3', function() {
    adjustTextareaHeight(chatInput3);
});

// Adjust height on page load in case there is already content
adjustTextareaHeight(chatInput1);
adjustTextareaHeight(chatInput2);
adjustTextareaHeight(chatInput3);







//document.addEventListener('DOMContentLoaded', () => {
//    initializeChatbot();
//});
//
//let messageHistory = []; // 메시지를 저장할 배열
//let conversationId = null; // 대화 ID 저장
//
//function initializeChatbot() {
//    setupEventListeners();
//}
//
//function setupEventListeners() {
//    document.getElementById('send-button').addEventListener('click', sendMessage);
//    document.getElementById('chat-input').addEventListener('keydown', handleKeyPress);
//}
//
//function handleKeyPress(event) {
//    if (event.key === 'Enter') {
//        sendMessage();
//    }
//}
//
//function sendMessage() {
//    const inputField = document.getElementById('chat-input');
//    const message = inputField.value.trim();
//    if (message !== '') {
//        displayMessage('user', message);
//        messageHistory.push({ sender: 'user', text: message }); // 메시지를 배열에 저장
//        inputField.value = '';
//        toggleInput(false); // 메시지 전송 후 입력 필드 비활성화
//        getChatbotResponse();
//    }
//}
//
//function displayMessage(sender, message) {
//    const messagesContainer = document.getElementById('messages');
//    const messageElement = document.createElement('div');
//    messageElement.className = `message ${sender}`;
//    messageElement.textContent = message;
//    messagesContainer.appendChild(messageElement);
//    messagesContainer.scrollTop = messagesContainer.scrollHeight;
//}
//
//function getChatbotResponse() {
//    // 메시지 히스토리를 서버로 전송
//    fetch('/message', {
//        method: 'POST',
//        headers: {
//            'Content-Type': 'application/json',
//        },
//        body: JSON.stringify({ history: messageHistory, conversation_id: conversationId }),
//    })
//    .then(response => response.json())
//    .then(data => {
//        const botResponse = data.response; // 서버에서 받은 응답
//        conversationId = data.conversation_id; // 서버에서 받은 대화 ID 저장
//        displayMessage('bot', botResponse);
//        messageHistory.push({ sender: 'bot', text: botResponse }); // 챗봇 응답을 배열에 저장
//        toggleInput(true); // 챗봇 응답 후 입력 필드 활성화
//    })
//    .catch(error => {
//        console.error('Error:', error);
//        displayMessage('bot', '챗봇 응답을 가져오는 데 실패했습니다.');
//        toggleInput(true); // 에러 발생 시에도 입력 필드 활성화
//    });
//}
//
//function toggleInput(enable) {
//    const inputField = document.getElementById('chat-input');
//    const sendButton = document.getElementById('send-button');
//    if (enable) {
//        inputField.disabled = false;
//        sendButton.disabled = false;
//        inputField.focus();
//    } else {
//        inputField.disabled = true;
//        sendButton.disabled = true;
//    }
//}
