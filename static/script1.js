function setupEventListeners(chatbotNumber) {
    document.getElementById(`send-button${chatbotNumber}`).addEventListener('click', () => sendMessage(chatbotNumber));
    
    // 'Enter' 버튼을 누르면 버튼 클릭과 동일한 기능 수행
    document.getElementById(`chat-input${chatbotNumber}`).addEventListener('keydown', (event) => handleKeyDown(event, chatbotNumber));
    
    // Reload 버튼 리스너
    document.getElementById(`reload-button${chatbotNumber}`).addEventListener('click', () => reloadChat(chatbotNumber));
}

function handleKeyDown(event, chatbotNumber) {
    if (event.key === 'Enter') {
        sendMessage(chatbotNumber);
    }
}

function sendMessage(chatbotNumber) {
    const inputField = document.getElementById(`chat-input${chatbotNumber}`);
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage(chatbotNumber, 'user', message);
        inputField.value = ''; // inputField 리셋
        toggleInput(chatbotNumber, false); // 입력 필드 비활성화
        getChatbotResponse(chatbotNumber, message); // 챗봇 응답 요청
    }
}

function displayMessage(chatbotNumber, sender, message) {
    const messagesContainer = document.getElementById(`messages${chatbotNumber}`);
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    
    // 메시지를 HTML에 추가 (개행 처리)
    console.log(message)
    messageElement.innerHTML = message.replace(/\n/g, '<br>');
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight; // 스크롤 아래로
}

function getChatbotResponse(chatbotNumber, userMessage) {
    fetch(`/api/botResponse/${chatbotNumber}`, {
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
        displayMessage(chatbotNumber, 'bot', botResponse); // 봇 응답 출력
        toggleInput(chatbotNumber, true); // 입력 필드 활성화
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

async function reloadChat(chatbotNumber) {
    console.log(`Reload button clicked for chatbot ${chatbotNumber}. Messages are being reloaded.`);

    // 메시지 영역 리셋
    const messagesContainer = document.getElementById(`messages${chatbotNumber}`);
    messagesContainer.innerHTML = '';

    // Python 백엔드와 통신하여 채팅 기록을 다시 불러옴
    const newMessage = await runPythonFunction(chatbotNumber);
}

async function runPythonFunction(chatbotNumber) {
    try {
        const response = await fetch(`/api/chatReload${chatbotNumber}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        return data.message; // Python 함수의 결과 반환
    } catch (error) {
        console.error('Error fetching Python function result:', error);
        return 'Error: Unable to load data';
    }
}

function toggleInput(chatbotNumber, enable) {
    const sendButton = document.getElementById(`send-button${chatbotNumber}`);
    sendButton.disabled = !enable; // 버튼 활성화/비활성화
}

function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto'; // 높이 초기화
    let newHeight = textarea.scrollHeight;
    const maxHeight = parseInt(window.getComputedStyle(textarea).getPropertyValue('max-height'), 10);

    if (newHeight > maxHeight) {
        newHeight = maxHeight;
        textarea.style.overflowY = 'auto'; // 최대 높이를 넘을 경우 스크롤 활성화
    } else {
        textarea.style.overflowY = 'hidden'; // 최대 높이를 넘지 않을 경우 스크롤 비활성화
    }

    textarea.style.height = newHeight + 'px'; // 텍스트 높이 설정
}

// 각 챗봇별로 이벤트 리스너 설정
setupEventListeners(1);
setupEventListeners(2);
setupEventListeners(3);

function setupTextareaAdjustment(chatbotNumber) {
    const chatInput = document.getElementById(`chat-input${chatbotNumber}`);
    chatInput.addEventListener('input', function() {
        adjustTextareaHeight(chatInput);
    });
    adjustTextareaHeight(chatInput); // 초기 높이 조정
}

// 각 챗봇에 대해 텍스트 입력 창 높이 조절 설정
setupTextareaAdjustment(1);
setupTextareaAdjustment(2);
setupTextareaAdjustment(3);

