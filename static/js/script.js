function setupEventListeners(chatbotNumber) {
    document.getElementById(`send-button${chatbotNumber}`).addEventListener('click', () => sendMessage(chatbotNumber));
    
    // 'Enter' 버튼을 누르면 버튼 클릭과 동일한 기능 수행
    document.getElementById(`chat-input${chatbotNumber}`).addEventListener('keydown', (event) => handleKeyDown(event, chatbotNumber));
    
    // Reload 버튼 리스너
    document.getElementById(`reload-button${chatbotNumber}`).addEventListener('click', () => reloadChat(chatbotNumber));

    document.addEventListener('DOMContentLoaded', () => startLoadingModel(chatbotNumber));
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
        }
    })
    .catch(error => {
        console.error('Error creating chat agent:', error);
        document.getElementById('loading-overlay').style.display = 'none';
    });
}


function handleKeyDown(event, chatbotNumber) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevent new line
        sendMessage(chatbotNumber);
    }
}

function sendMessage(chatbotNumber) {
    userid = sessionStorage.getItem('userid');

    const inputField = document.getElementById(`chat-input${chatbotNumber}`);
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage(chatbotNumber, 'user', message);
        userMessageDB(userid, chatbotNumber, message);
        inputField.value = ''; // inputField 리셋
        toggleInput(chatbotNumber, false); // 입력 필드 비활성화
        getChatbotResponse(userid, chatbotNumber, message); // 챗봇 응답 요청
    }
}


function displayMessage(chatbotNumber, sender, message, messageId = null) {
    const messagesContainer = document.getElementById(`messages${chatbotNumber}`);
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    messageElement.innerHTML = message.replace(/\n/g, '<br>');
    messagesContainer.appendChild(messageElement);

    if (sender === 'bot') {
        console.log("bot맞아?");
        // Add thumbs up/down buttons with a data attribute for message ID
        const feedbackElement = document.createElement('div');
        feedbackElement.innerHTML = `
                <div class="message feedback" data-message-id="${messageId}">
                    <i class="fa-regular fa-thumbs-up"></i>
                    <i class="fa-regular fa-thumbs-down"></i>
                </div>
        `;
        console.log(feedbackElement);
        messagesContainer.appendChild(feedbackElement);
        console.log(messagesContainer);
    } 

    messagesContainer.scrollTop = messagesContainer.scrollHeight; // Scroll to bottom
}


async function userMessageDB(userid, chatbotNumber, userMessage) {
    let conv_id = sessionStorage.getItem(`convType${chatbotNumber}`);

    try {
        const response = await fetch(`/api/userMessage${chatbotNumber}`, {
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
        sessionStorage.setItem(`convType${chatbotNumber}`, conv_id);

    } catch (error) {
        console.error('Error fetching Python function result:', error);
    }
}


function getChatbotResponse(userid, chatbotNumber, userMessage) {
    let conv_id = sessionStorage.getItem(`convType${chatbotNumber}`);

    fetch(`/api/botResponse${chatbotNumber}`, {
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
        console.log('Result:', botResponse); // 결과 출력
        displayMessage(chatbotNumber, 'bot', botResponse, messageId); // 봇 응답 출력
        toggleInput(chatbotNumber, true); // 입력 필드 활성화

        conv_id = data.conv_id;
        sessionStorage.setItem(`convType${chatbotNumber}`, conv_id);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

async function reloadChat(chatbotNumber) {
    userid = sessionStorage.getItem('userid');
    console.log(`Reload button clicked for chatbot ${chatbotNumber}. Messages are being reloaded.`);
    document.getElementById('loading-overlay').style.display = 'block';

    // 메시지 영역 리셋
    const messagesContainer = document.getElementById(`messages${chatbotNumber}`);
    
    toggleInput(chatbotNumber, false);
    await callReload(userid, chatbotNumber);
    messagesContainer.innerHTML = '';
    toggleInput(chatbotNumber, true);

    sessionStorage.removeItem(`convType${chatbotNumber}`);
    document.getElementById('loading-overlay').style.display = 'none';
}

async function callReload(userid, chatbotNumber) {
    try {
        const response = await fetch(`/api/chatReload/${chatbotNumber}`, {
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

function toggleInput(chatbotNumber, enable) {
    const sendButton = document.getElementById(`send-button${chatbotNumber}`);
    sendButton.disabled = !enable; // 버튼 활성화/비활성화

    const inputField = document.getElementById(`chat-input${chatbotNumber}`);
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


function setupTextareaAdjustment(chatbotNumber) {
    const chatInput = document.getElementById(`chat-input${chatbotNumber}`);
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
