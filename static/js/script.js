function setupEventListeners(typeNum) {
    // 화면 켜질 때 startLoadingModel() 수행
    document.addEventListener('DOMContentLoaded', () => startLoadingModel(typeNum));

    // 'Enter' 버튼을 리스너 (버튼 클릭과 동일한 기능 수행)
    document.getElementById(`chat-input${typeNum}`).addEventListener('keydown', (event) => handleKeyDown(event, typeNum));

    // send-button 버튼 리스너
    document.getElementById(`send-button${typeNum}`).addEventListener('click', () => sendMessage(typeNum));
    
    // Reload 버튼 리스너
    document.getElementById(`reload-button${typeNum}`).addEventListener('click', () => reloadChat(typeNum));
}


function startLoadingModel(typeNum) {
    sessionStorage.clear();
    toggleInput(typeNum, false);
    document.getElementById('loading-overlay').style.display = 'block';

    const userid = new URLSearchParams(window.location.search).get('userid'); 
    sessionStorage.setItem('userid', userid);

    sessionStorage.setItem('shouldStoreBotMessage', true);

    fetch('/create_agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userid, typeNum })
    })
    .then(response => response.json())
    .then(data => data.error ? alert(data.error) : toggleInput(typeNum, true))
    .catch(console.error)
    .finally(() => document.getElementById('loading-overlay').style.display = 'none');
}


function handleKeyDown(event, typeNum) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage(typeNum);
    }
}


// function sendMessage(typeNum) {
//     const userid = sessionStorage.getItem('userid');
//     const inputField = document.getElementById(`chat-input${typeNum}`);
//     const message = inputField.value.trim();

//     if (message) {
//         displayMessage(typeNum, 'user', message); // display user message
//         storeUserMessage(userid, typeNum, message); // store user message in DB
//         inputField.value = ''; // empty input box
//         toggleInput(typeNum, false); // disable input-box & send-button
//         getChatbotResponse(userid, typeNum, message);
//         storeBotMessage(userid, typeNum, )

//         toggleInput(typeNum, true); // enable input-box & send-button
//     }
// }


function displayMessage(typeNum, sender, message, messageId = null) {
    const messagesContainer = document.getElementById(`messages${typeNum}`);
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;

    if (sender === 'bot') {
        // Add thumbs up/down buttons with a data attribute for message ID
        messageElement.innerHTML = `
                <div class="message-content">
                    ${message.replace(/\n/g, '<br>')}
                </div>
                <div class="feedback-buttons" data-message-id="${messageId}">
                    <i class="fa-solid fa-thumbs-up"></i>
                    <i class="fa-solid fa-thumbs-down"></i>
                </div>
        `;
    } else {
        messageElement.innerHTML = message.replace(/\n/g, '<br>');
    }

    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight; // Scroll to bottom
}


async function storeUserMessage(userid, typeNum, userMessage) {
    let conv_id = sessionStorage.getItem(`convType${typeNum}`);

    try {
        const response = await fetch(`/api/userMessage${typeNum}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ userMessage, userid, conv_id }),
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


// function getChatbotResponse(userid, typeNum, userMessage) {
//     let conv_id = sessionStorage.getItem(`convType${typeNum}`);

//     fetch(`/api/botResponse${typeNum}`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         credentials: 'include',
//         body: JSON.stringify({ userMessage, userid, conv_id }),
//     })
//     .then(response => response.json())
//     .then(data => {
//         displayMessage(typeNum, 'bot', data.response, data.message_id);
//         sessionStorage.setItem(`convType${typeNum}`, data.conv_id);
//     })
//     .catch(error => {
//         console.error('Error:', error);
//     });
// }

function sendMessage(typeNum) {
    const userid = sessionStorage.getItem('userid');
    const inputField = document.getElementById(`chat-input${typeNum}`);
    const message = inputField.value.trim();

    if (message) {
        displayMessage(typeNum, 'user', message);
        storeUserMessage(userid, typeNum, message);
        inputField.value = '';
        toggleInput(typeNum, false);

        // Generate a unique request ID and store it in sessionStorage
        const requestId = Date.now();  // Use timestamp as unique ID
        sessionStorage.setItem(`requestId${typeNum}`, requestId);
        sessionStorage.setItem('shouldStoreBotMessage', 'true');

        getChatbotResponse(userid, typeNum, message, requestId)
            .then(botResponse => {
                const shouldStoreBotMessage = sessionStorage.getItem('shouldStoreBotMessage') === 'true';
                const latestRequestId = sessionStorage.getItem(`requestId${typeNum}`);

                // Only process this response if the request ID matches and shouldStoreBotMessage is true
                if (shouldStoreBotMessage && latestRequestId == requestId) {
                    console.log("왜들어와");
                    displayMessage(typeNum, 'bot', botResponse.response);
                    storeBotMessage(userid, typeNum, botResponse.response, botResponse.conv_id);
                }
            })
            .finally(() => toggleInput(typeNum, true));
    }
}

async function getChatbotResponse(userid, typeNum, userMessage, requestId) {
    let conv_id = sessionStorage.getItem(`convType${typeNum}`);
    console.log(conv_id);

    return fetch(`/api/botResponse${typeNum}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ userMessage, userid, conv_id, requestId }),
    })
    .then(response => response.json())
    .then(data => {
        sessionStorage.setItem(`convType${typeNum}`, data.conv_id);
        console.log(data.conv_id);
        return data;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

async function reloadChat(typeNum) {
    sessionStorage.setItem('shouldStoreBotMessage', 'false');
    
    // Generate a new unique request ID to cancel any pending responses
    const newRequestId = Date.now();
    sessionStorage.setItem(`requestId${typeNum}`, newRequestId);

    userid = sessionStorage.getItem('userid');
    console.log(`Reload button clicked for chatbot ${typeNum}. Messages are being reloaded.`);
    document.getElementById('loading-overlay').style.display = 'block';

    // Clear message area
    const messagesContainer = document.getElementById(`messages${typeNum}`);
    toggleInput(typeNum, false);
    await callReload(userid, typeNum);
    messagesContainer.innerHTML = '';
    toggleInput(typeNum, true);

    sessionStorage.removeItem(`convType${typeNum}`);
    document.getElementById('loading-overlay').style.display = 'none';
}


// function sendMessage(typeNum) {
//     const userid = sessionStorage.getItem('userid');
//     const inputField = document.getElementById(`chat-input${typeNum}`);
//     const message = inputField.value.trim();

//     if (message) {
//         displayMessage(typeNum, 'user', message);
//         storeUserMessage(userid, typeNum, message);
//         inputField.value = '';
//         toggleInput(typeNum, false);

//         sessionStorage.setItem('shouldStoreBotMessage',true);
//         getChatbotResponse(userid, typeNum, message)
//             .then(botResponse => {
//                 const shouldStoreBotMessage = sessionStorage.getItem('shouldStoreBotMessage') === 'true';
//                 console.log(shouldStoreBotMessage);
//                 if (shouldStoreBotMessage) {
//                     console.log("왜들어와")
//                     displayMessage(typeNum, 'bot', botResponse.response);
//                     storeBotMessage(userid, typeNum, botResponse.response, botResponse.conv_id);
//                 }
//             })
//             .finally(() => toggleInput(typeNum, true));
//     }
// }

// async function getChatbotResponse(userid, typeNum, userMessage) {
//     let conv_id = sessionStorage.getItem(`convType${typeNum}`);
//     console.log(conv_id);

//     return fetch(`/api/botResponse${typeNum}`, {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         credentials: 'include',
//         body: JSON.stringify({ userMessage, userid, conv_id }),
//     })
//     .then(response => response.json())
//     .then(data => {
//         sessionStorage.setItem(`convType${typeNum}`, data.conv_id);
//         console.log(data.conv_id);
//         return data;
//     })
//     .catch(error => {
//         console.error('Error:', error);
//     });
// }

function storeBotMessage(userid, typeNum, response, conv_id) {
    fetch('/api/storeBotMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userid, typeNum, response, conv_id }),
    })
    .catch(error => console.error('Error:', error));
}

// async function reloadChat(typeNum) {
//     sessionStorage.setItem('shouldStoreBotMessage', false);

//     userid = sessionStorage.getItem('userid');
//     console.log(`Reload button clicked for chatbot ${typeNum}. Messages are being reloaded.`);
//     document.getElementById('loading-overlay').style.display = 'block';

//     // 메시지 영역 리셋
//     const messagesContainer = document.getElementById(`messages${typeNum}`);
    
//     toggleInput(typeNum, false);
//     await callReload(userid, typeNum);
//     messagesContainer.innerHTML = '';
//     toggleInput(typeNum, true);

//     sessionStorage.removeItem(`convType${typeNum}`);
//     document.getElementById('loading-overlay').style.display = 'none';
// }

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
    // send-button, chat-input 활성화/비활성화
    const sendButton = document.getElementById(`send-button${typeNum}`);
    sendButton.disabled = !enable; 

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
        const messageId = target.closest('.feedback-buttons').getAttribute('data-message-id');
        const feedbackContainer = target.closest('.feedback-buttons');
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
