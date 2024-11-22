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

    const urlParams = new URLSearchParams(window.location.search);
    const userid = urlParams.get('userid'); 

    sessionStorage.setItem('userid',userid); 

    displayMessage(typeNum, 'start bot', "저는 여권 관련 상담 도우미입니다. &#128512; \n현재 위치하신 곳 또는 처한 상황에 대해 구체적으로 말씀해 주시면 더욱더 정확한 도움을 드릴 수 있습니다.");
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




function getChatbotResponse(userid, typeNum, userMessage) {
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
            userid: userid
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

    })
    .catch(error => {
        console.error('Error:', error);
    });
}

async function reloadChat(typeNum) {
    userid = sessionStorage.getItem('userid');
    if (!userid) {
        console.error('User ID is missing in session.');
        alert('세션에 User ID가 없습니다. 페이지를 새로고침하세요.');
        return;
    }
    document.getElementById('loading-overlay').style.display = 'block';

    // 입력 비활성화 및 메시지 리셋
    toggleInput(typeNum, false);
    const messagesContainer = document.getElementById(`messages${typeNum}`);
    messagesContainer.innerHTML = '';

    try {
        // API 호출
        await callReload(userid, typeNum);
        displayMessage(typeNum, 'start bot', 
            "저는 여권 관련 상담 도우미입니다. 😊\n현재 위치하신 곳 또는 처한 상황에 대해 구체적으로 말씀해 주시면 더욱 정확한 도움을 드릴 수 있습니다."
        );
    } catch (error) {
        console.error('Error during reload:', error);
        alert('챗봇을 다시 로드하는 중 오류가 발생했습니다.');
    } finally {
        // 입력 활성화 및 로딩 종료
        toggleInput(typeNum, true);
        document.getElementById('loading-overlay').style.display = 'none';
    }
}


async function callReload(userid, typeNum) {
    const response = await fetch(`/api/chatReload/${typeNum}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userid }),
    });

    if (!response.ok) {
        const errorMessage = await response.text();
        throw new Error(`Reload failed: ${errorMessage}`);
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


document.addEventListener('click', function (event) {
    const target = event.target;

    if (target.classList.contains('fa-thumbs-up') || target.classList.contains('fa-thumbs-down')) {
        const feedbackContainer = target.closest('.feedback');
        const messageId = feedbackContainer?.getAttribute('data-message-id');
        const isThumbsUp = target.classList.contains('fa-thumbs-up');
        const isThumbsDown = target.classList.contains('fa-thumbs-down');
        const selectedFeedback = getSelectedFeedback(feedbackContainer);

        if (messageId) {
            if (
                (isThumbsUp && selectedFeedback === 'UP') ||
                (isThumbsDown && selectedFeedback === 'DOWN')
            ) {
                // If the same button is clicked again, deselect it
                toggleFeedbackButtons(feedbackContainer, 'NONE');
                sendFeedback(messageId, 'NONE'); // Send null feedback to indicate deselection
            } else {
                // Otherwise, select the clicked button
                const feedback = isThumbsUp ? 'UP' : 'DOWN';
                toggleFeedbackButtons(feedbackContainer, feedback);
                sendFeedback(messageId, feedback);
            }
        }
    }
});

function getSelectedFeedback(container) {
    const upButton = container.querySelector('.fa-thumbs-up');
    const downButton = container.querySelector('.fa-thumbs-down');

    if (upButton.classList.contains('selected')) {
        return 'UP';
    } else if (downButton.classList.contains('selected')) {
        return 'DOWN';
    } else {
        return null; // No feedback is selected
    }
}

function toggleFeedbackButtons(container, feedback) {
    const upButton = container.querySelector('.fa-thumbs-up');
    const downButton = container.querySelector('.fa-thumbs-down');

    if (feedback === 'UP') {
        upButton.classList.add('selected');
        downButton.classList.remove('selected');
    } else if (feedback === 'DOWN') {
        downButton.classList.add('selected');
        upButton.classList.remove('selected');
    } else {
        // Deselect both buttons
        upButton.classList.remove('selected');
        downButton.classList.remove('selected');
    }
}

async function sendFeedback(messageId, feedback) {
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ message_id: messageId, feedback }),
        });

        if (!response.ok) throw new Error('Failed to send feedback');
    } catch (error) {
        console.error('Error:', error);
    }
}