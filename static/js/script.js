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
    toggleInput(typeNum, false); 
    document.getElementById('loading-overlay').style.display = 'block';

    fetch('/create_agent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
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
    const inputField = document.getElementById(`chat-input${chatbotNumber}`);
    const message = inputField.value.trim();
    if (message !== '') {
        displayMessage(chatbotNumber, 'user', message);
        userMessageDB(chatbotNumber, message);
        inputField.value = ''; // inputField 리셋
        toggleInput(chatbotNumber, false); // 입력 필드 비활성화
        getChatbotResponse(chatbotNumber, message); // 챗봇 응답 요청
    }
}

async function userMessageDB(chatbotNumber, userMessage){
    try {
        const response = await fetch(`/api/userMessage${chatbotNumber}`, {
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



function getChatbotResponse(chatbotNumber, userMessage) {
    fetch(`/api/botResponse${chatbotNumber}`, {
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
        const messageId = data.message_id;
        console.log('Result:', botResponse); // 결과 출력
        displayMessage(chatbotNumber, 'bot', botResponse, messageId); // 봇 응답 출력
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
    
    toggleInput(chatbotNumber, false);
    await callReload(chatbotNumber);
    messagesContainer.innerHTML = '';
    toggleInput(chatbotNumber, true);
}

async function callReload(chatbotNumber) {
    try {
        const response = await fetch(`/api/chatReload/${chatbotNumber}`, {
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


function displayMessage(chatbotNumber, sender, message, messageId = null) {
    const messagesContainer = document.getElementById(`messages${chatbotNumber}`);
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



document.addEventListener('click', function(event) {
    const target = event.target;

    if (target.classList.contains('fa-thumbs-up') || target.classList.contains('fa-thumbs-down')) {
        const feedback = target.classList.contains('fa-thumbs-up') ? 'up' : 'down';
        const messageId = target.closest('.feedback-buttons').getAttribute('data-message-id');
        const feedbackContainer = target.closest('.feedback-buttons');
        const isSelected = target.classList.contains('selected');

        // 선택 해지 후 다른 옵션 선택 가능 기능
        
        // if (messageId) {
        //     if (isSelected) {
        //         // If the clicked button is already selected, deselect it
        //         target.classList.remove('selected');
                
        //         // Re-enable both buttons after deselection
        //         feedbackContainer.querySelector('.fa-thumbs-up').classList.remove('disabled');
        //         feedbackContainer.querySelector('.fa-thumbs-down').classList.remove('disabled');

        //         // Remove the feedback
        //         removeFeedback(messageId);
        //     } else {
        //         // If no button is selected, select the clicked one and disable the other
        //         target.classList.add('selected');
                
        //         if (feedback === 'up') {
        //             // Disable thumbs-down but keep thumbs-up enabled for deselection
        //             feedbackContainer.querySelector('.fa-thumbs-down').classList.add('disabled');
        //             feedbackContainer.querySelector('.fa-thumbs-up').classList.remove('disabled');
        //         } else {
        //             // Disable thumbs-up but keep thumbs-down enabled for deselection
        //             feedbackContainer.querySelector('.fa-thumbs-up').classList.add('disabled');
        //             feedbackContainer.querySelector('.fa-thumbs-down').classList.remove('disabled');
        //         }

        //         // Send the feedback to the server
        //         sendFeedback(messageId, feedback);
        //     }
        // }

        // 무조건 선택: select one or the other once you choose.

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
            body: JSON.stringify({ message_id: messageId }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
    } catch (error) {
        console.error('Error removing feedback:', error);
    }
}
