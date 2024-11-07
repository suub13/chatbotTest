function setupEventListeners(typeNum) {
    document.getElementById(`send-button${typeNum}`).addEventListener('click', () => sendMessage(typeNum));
    
    // 'Enter' 버튼을 누르면 버튼 클릭과 동일한 기능 수행
    document.getElementById(`chat-input${typeNum}`).addEventListener('keydown', (event) => handleKeyDown(event, typeNum));
    
    // Reload 버튼 리스너
    document.getElementById(`reload-button${typeNum}`).addEventListener('click', () => reloadChat(typeNum));

    document.addEventListener('DOMContentLoaded', () => startLoadingModel(typeNum));
}

// 처음 로딩 페이지 추가하려면 아래 function 에서 comment 처리 된 부분 해지 해야 함.
function startLoadingModel(typeNum) {
    sessionStorage.clear();
    toggleInput(typeNum, false); 
    document.getElementById('loading-overlay').style.display = 'block';

    const urlParams = new URLSearchParams(window.location.search);
    const userid = urlParams.get('userid'); 

    sessionStorage.setItem('userid',userid); 

    fetch('/create_agent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ userid, typeNum }) // Include both userid and typeNum in the request body
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            console.log(data.message);
            // Enable chat input once the agent is ready
            toggleInput(typeNum, true);
            document.getElementById('loading-overlay').style.display = 'none';
            displayMessage(typeNum, 'start bot', "저는 여권 분실 관련 상담 도우미입니다. &#128512; \n현재 위치하신 곳 또는 처한 상황에 대해 구체적으로 말씀해 주시면 더욱더 정확한 도움을 드릴 수 있습니다.");
        }
    })
    .catch(error => {
        console.error('Error creating chat agent:', error);
        document.getElementById('loading-overlay').style.display = 'none';
    });
}


function handleKeyDown(event, typeNum) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevent new line
        sendMessage(typeNum);
    }
}

function sendMessage(typeNum) {
    userid = sessionStorage.getItem('userid');

    const inputField = document.getElementById(`chat-input${typeNum}`);
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage(typeNum, 'user', message);
        userMessageDB(userid, typeNum, message);
        inputField.value = ''; // inputField 리셋
        toggleInput(typeNum, false); // 입력 필드 비활성화
        getChatbotResponse(userid, typeNum, message); // 챗봇 응답 요청
    }
}


function displayMessage(typeNum, sender, message, messageId = null, isTyping = false) {
    const messagesContainer = document.getElementById(`messages${typeNum}`);
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;

    if (isTyping) {
        messageElement.innerHTML = `<span class="typing-dots">&middot &middot &middot</span>`;
        messageElement.dataset.messageId = messageId;  // 데이터 ID 설정
        messagesContainer.appendChild(messageElement);
    } else if (sender === 'feedback'){
        const feedbackElement = document.createElement('div');
        feedbackElement.classList.add('message', 'feedback');
        feedbackElement.dataset.messageId = messageId; // data-message-id 추가
        feedbackElement.innerHTML = `
            <i class="fa-regular fa-thumbs-up"></i>
            <i class="fa-regular fa-thumbs-down"></i>
        `;
        messagesContainer.appendChild(feedbackElement);
    }
    else  {
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
        messagesContainer.appendChild(messageElement);
    }    

    messagesContainer.scrollTop = messagesContainer.scrollHeight; // Scroll to bottom
}


async function userMessageDB(userid, typeNum, userMessage) {
    let conv_id = sessionStorage.getItem(`convType${typeNum}`);

    try {
        const response = await fetch(`/api/userMessage${typeNum}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ 
                message: userMessage,
                userid: userid,
                conv_id: conv_id
            }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        // Extract conv_id from response
        const data = await response.json();
        conv_id = data.conv_id;

        // Save conv_id to sessionStorage
        sessionStorage.setItem(`convType${typeNum}`, conv_id);

    } catch (error) {
        console.error('Error fetching Python function result:', error);
    }
}


function getChatbotResponse(userid, typeNum, userMessage) {
    let conv_id = sessionStorage.getItem(`convType${typeNum}`);

    // 1. 로딩 메시지 ('...') 표시
    const loadingMessageId = `loading-${Date.now()}`;  // 고유 메시지 ID 생성
    displayMessage(typeNum, 'bot', '', loadingMessageId, true);  // 로딩 메시지 추가

    fetch(`/api/botResponse${typeNum}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ 
            message: userMessage,
            userid: userid,
            conv_id: conv_id,
         }),
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        const botResponse = data.response;
        const messageId = data.message_id;

        // 3. 로딩 메시지 교체 (data-message-id를 새 메시지 ID로 업데이트)
        const loadingMessageElement = document.querySelector(`#messages${typeNum} .message.bot[data-message-id="${loadingMessageId}"]`);
        if (loadingMessageElement) {
            // data-message-id 값을 새 메시지 ID로 변경
            loadingMessageElement.setAttribute('data-message-id', messageId);
            loadingMessageElement.innerHTML = botResponse.replace(/\n/g, '<br>'); // 텍스트 교체
            displayMessage(typeNum, "feedback", '', messageId, false);
        }

        toggleInput(typeNum, true); // 입력 필드 활성화

        conv_id = data.conv_id;
        sessionStorage.setItem(`convType${typeNum}`, conv_id);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

async function reloadChat(typeNum) {
    userid = sessionStorage.getItem('userid');
    console.log(`Reload button clicked for chatbot ${typeNum}. Messages are being reloaded.`);
    document.getElementById('loading-overlay').style.display = 'block';

    // 메시지 영역 리셋
    const messagesContainer = document.getElementById(`messages${typeNum}`);
    
    toggleInput(typeNum, false);
    await callReload(userid, typeNum);
    messagesContainer.innerHTML = '';
    toggleInput(typeNum, true);

    sessionStorage.removeItem(`convType${typeNum}`);
    document.getElementById('loading-overlay').style.display = 'none';
}

async function callReload(userid, typeNum) {
    try {
        const response = await fetch(`/api/chatReload/${typeNum}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ 
                userid: userid
             }),
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

    const inputField = document.getElementById(`chat-input${typeNum}`);
    inputField.disabled = !enable;
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




document.addEventListener('click', function(event) {
    const target = event.target;

    if (target.classList.contains('fa-thumbs-up') || target.classList.contains('fa-thumbs-down')) {
        const feedback = target.classList.contains('fa-thumbs-up') ? 'up' : 'down';
        const messageId = target.closest('.feedback').getAttribute('data-message-id');
        const feedbackContainer = target.closest('.feedback');
        const isSelected = target.classList.contains('selected');

        if (messageId) {
            if (feedback === 'up'){
                // up 버튼 더이상 누를 수 없게 
                feedbackContainer.querySelector('.fa-thumbs-up').classList.add('disabled');
                // up 버튼 선택
                feedbackContainer.querySelector('.fa-thumbs-up').classList.add('selected');

                // down 버튼 누름 가능
                feedbackContainer.querySelector('.fa-thumbs-down').classList.remove('disabled');
                // 선택 해제
                feedbackContainer.querySelector('.fa-thumbs-down').classList.remove('selected');

            } else {
                // up 버튼 더이상 누를 수 없게 
                feedbackContainer.querySelector('.fa-thumbs-down').classList.add('disabled');
                // up 버튼 선택
                feedbackContainer.querySelector('.fa-thumbs-down').classList.add('selected');

                // down 버튼 누름 가능
                feedbackContainer.querySelector('.fa-thumbs-up').classList.remove('disabled');
                // 선택 해제
                feedbackContainer.querySelector('.fa-thumbs-up').classList.remove('selected');

            }
            sendFeedback(messageId, feedback);
        }
    }
});


async function sendFeedback(messageId, feedback) {
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ message_id: messageId, feedback: feedback }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error sending feedback:', error);
    }
}

async function removeFeedback(messageId) {
    try {
        const response = await fetch('/api/feedback/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ message_id: messageId }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error removing feedback:', error);
    }
}
