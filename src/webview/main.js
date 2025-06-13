// @ts-ignore
const vscode = acquireVsCodeApi();

const messageList = document.getElementById('message-list');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

function addMessage(text, type) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message ' + type;
    messageElement.textContent = text;
    messageList.appendChild(messageElement);
    messageList.scrollTop = messageList.scrollHeight; // Auto-scroll
}

sendButton.addEventListener('click', () => {
    const text = messageInput.value;
    if (text) {
        addMessage(text, 'user-message');
        vscode.postMessage({ command: 'userMessage', text: text });
        messageInput.value = '';
    }
});

messageInput.addEventListener('keyup', (event) => {
    if (event.key === 'Enter') {
        sendButton.click();
    }
});

let backendReady = false;

window.addEventListener('message', event => {
    const message = event.data;
    if (message.text.includes("--- The system is now ready for prompts. ---")) {
        backendReady = true;
        addMessage("MCP Agent is ready. Please enter your request.", 'system-message');

    }
    if (backendReady)
    {
        switch (message.command) {
        case 'agentMessage':
            addMessage(message.text, 'agent-message');
            break;
        case 'systemError':
            addMessage('ERROR: ' + message.text, 'system-error');
            break;
        case 'systemStatus':
            addMessage('STATUS: ' + message.text, 'system-message');
            break;
    }
    }   
});