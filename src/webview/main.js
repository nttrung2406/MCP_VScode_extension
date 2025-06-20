(function() {
    const vscode = acquireVsCodeApi();
    const sendButton = document.getElementById('send-button');
    const messageInput = document.getElementById('message-input');
    const messageList = document.getElementById('message-list');

    sendButton.addEventListener('click', () => {
        sendMessageToExtension();
    });

    messageInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            sendMessageToExtension();
        }
    });

    function sendMessageToExtension() {
        const prompt = messageInput.value;
        if (prompt) {
            addMessage('You', prompt);
            
            vscode.postMessage({
                command: 'userMessage',
                text: prompt
            });
            messageInput.value = ''; 
        }
    }

    window.addEventListener('message', event => {
        const message = event.data;
        switch (message.command) {
            case 'agentThinking':
            case 'agentResponse':
            case 'systemError':
            case 'systemStatus':
                addMessage('Agent', message.text, message.command === 'systemError');
                break;
        }
    });

    function addMessage(sender, text, isError = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender.toLowerCase()}`;
        if (isError) {
            messageElement.classList.add('error');
        }
        
        const senderElement = document.createElement('strong');
        senderElement.textContent = `${sender}: `;
        
        const textElement = document.createElement('pre');
        textElement.textContent = text;

        messageElement.appendChild(senderElement);
        messageElement.appendChild(textElement);
        messageList.appendChild(messageElement);
        messageList.scrollTop = messageList.scrollHeight; 
    }
}());