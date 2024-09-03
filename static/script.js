document.addEventListener('DOMContentLoaded', () => {
    initializeChatbot();
});

let messageHistory = []; // 메시지를 저장할 배열
let conversationId = null; // 대화 ID 저장

function initializeChatbot() {
    setupEventListeners();
}

function setupEventListeners() {
    document.getElementById('send-button').addEventListener('click', sendMessage);
    // 이건 'Enter' 버튼을 누르면 button click과 같은 기능을 함.
    document.getElementById('chat-input').addEventListener('keydown', handleKeyDown);
    document.getElementById('reload-button').addEventListener('click', reloadChat);
}

function handleKeyDown(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendMessage() {
    const inputField = document.getElementById('chat-input');
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage('user', message);
        // 메시지를 messageHistory에 저장
//        messageHistory.push({ sender: 'user', text: message });
        // inputField 리셋
        inputField.value = '';
        // 챗봇이 응답을 생성하는 중간에 사용자가 다른 질문을 할 수 없게 막는 기능
        toggleInput(false);
        getChatbotResponse(message);
    }
}

async function reloadChat() {
    console.log('Reload button clicked. Messages are being reloaded.');

    // 메시지 영역 empty string을 대체하여 내용 리셋
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';

    // model instance 다시 시작해서 로드하기.
    const newMessage = await runPythonFunction();

}

function displayMessage(sender, message) {
    const messagesContainer = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    messageElement.textContent = message;
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


function getChatbotResponse(userMessage) {
    fetch('http://localhost:5000/api/botResponse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
    })
    .then(response => response.json())
    .then(data => {
        const botResponse = data.response;
//        console.log('Result:', botResponse); // 결과 출력
        displayMessage('bot', botResponse);
        toggleInput(true);

    })
    .catch(error => {
        console.error('Error:', error);
    });

}

async function runPythonFunction() {
    try {
        const response = await fetch('/api/chatReload', {
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

function toggleInput(enable) {
//    const inputField = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
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

const chatInput = document.getElementById('chat-input');
chatInput.addEventListener('input', function() {
    adjustTextareaHeight(chatInput);
});

// Adjust height on page load in case there is already content
adjustTextareaHeight(chatInput);









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
