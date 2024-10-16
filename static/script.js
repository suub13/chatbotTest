function setupEventListeners(typeNum) {
    document.getElementById(`send-button${typeNum}`).addEventListener('click', () => sendMessage(typeNum));

    document.getElementById(`send-button${typeNum}`).addEventListener('click', () => sendMessage(typeNum));
    
    // 'Enter' 버튼을 누르면 버튼 클릭과 동일한 기능 수행
    document.getElementById(`chat-input${typeNum}`).addEventListener('keydown', (event) => MessageHandleKeyDown(event, typeNum));
    
    // Reload 버튼 리스너
    document.getElementById(`reload-button${typeNum}`).addEventListener('click', () => reloadChat(typeNum));
}


function MessageHandleKeyDown(event, typeNum) {
    if (event.key === 'Enter'&& !event.shiftKey) {
        sendMessage(typeNum);
    }
}

function sendMessage(typeNum) {
    console.log(typeNum);
    const inputField = document.getElementById(`chat-input${typeNum}`);
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage(typeNum, 'user', message);
        userMessageDB(typeNum, message);
        inputField.value = ''; // inputField 리셋
        toggleInput(typeNum, false); // 입력 필드 비활성화
        getChatbotResponse(typeNum, message); // 챗봇 응답 요청
    }
}

async function userMessageDB(typeNum, userMessage){
    try {
        const response = await fetch(`/api/userMessage${typeNum}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: userMessage }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error fetching Python function result:', error);
    }
}

function displayMessage(typeNum, sender, message) {
    const messagesContainer = document.getElementById(`messages${typeNum}`);
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    
    // 메시지를 HTML에 추가 (개행 처리)
    console.log(message)
    messageElement.innerHTML = message.replace(/\n/g, '<br>');
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight; // 스크롤 아래로
}

function getChatbotResponse(typeNum, userMessage) {
    fetch(`/api/botResponse${typeNum}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        const botResponse = data.response;
        console.log('Result:', botResponse); // 결과 출력
        displayMessage(typeNum, 'bot', botResponse); // 봇 응답 출력
        toggleInput(typeNum, true); // 입력 필드 활성화
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

async function reloadChat(typeNum) {
    console.log(`Reload button clicked for chatbot ${typeNum}. Messages are being reloaded.`);

    // 메시지 영역 리셋
    const messagesContainer = document.getElementById(`messages${typeNum}`);
    
    toggleInput(typeNum, false);
    await callReload(typeNum);
    messagesContainer.innerHTML = '';
    toggleInput(typeNum, true);
}

async function callReload(typeNum) {
    try {
        const response = await fetch(`/api/chatReload/${typeNum}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error fetching Python function result:', error);
    }
}

function toggleInput(typeNum, enable) {
    const sendButton = document.getElementById(`send-button${typeNum}`);
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


function setupTextareaAdjustment(typeNum) {
    const chatInput = document.getElementById(`chat-input${typeNum}`);
    chatInput.addEventListener('input', function() {
        adjustTextareaHeight(chatInput);
    });
    adjustTextareaHeight(chatInput); // 초기 높이 조정
}

document.getElementById('template-form').addEventListener('submit', function(event) {
    event.preventDefault();  // 폼의 기본 동작(페이지 리로드)을 막음

    const responseMessage = document.getElementById('response-message');
    responseMessage.innerText = '';
    
    const template = document.getElementById('template').value;  // textarea 값 가져오기

    fetch('/update_template', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',  // 폼 데이터 전송 방식
        },
        body: new URLSearchParams({
            'template': template
        })
    })
    .then(response => {
        if (response.ok) {
            return response.text();  // 200일 때 응답 본문 처리
        } else {
            throw new Error('400 error: Missing userid or typeNum');
        }
    })
    .then(data => {
        document.getElementById('response-message').innerText = 'Template 수정 완료';  // 성공 메시지 표시
    })
    .catch(error => {
        document.getElementById('response-message').innerText = '오류가 발생했습니다: ' + error.message;  // 에러 메시지 표시
    });
});
document.getElementById('template').addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {  // Enter 키를 누르면 제출 (Shift + Enter는 줄바꿈)
        event.preventDefault();
        document.getElementById('template-form').dispatchEvent(new Event('submit'));  // 폼 제출 트리거
    }
});