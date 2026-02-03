let currentChatId = null;
let chats = [];
let attachedFile = null;
let extractedText = null;

// Auto-resize textarea
const messageInput = document.getElementById('messageInput');
messageInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

// Send on Enter (Shift+Enter for new line)
messageInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Load chats on page load
window.addEventListener('DOMContentLoaded', loadChats);

async function loadChats() {
    try {
        const response = await fetch('/get_chats');
        const data = await response.json();
        chats = data.chats;
        renderChatsList();

        if (chats.length > 0) {
            loadChat(chats[0].id);
        }
    } catch (error) {
        console.error('Error loading chats:', error);
    }
}

function renderChatsList() {
    const chatsList = document.getElementById('chatsList');
    chatsList.innerHTML = '';

    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item' + (chat.id === currentChatId ? ' active' : '');
        chatItem.innerHTML = `
            <div class="chat-item-title">${chat.title}</div>
            <div class="chat-item-actions">
                <button class="chat-action-btn" onclick="deleteChat('${chat.id}', event)" title="Delete">🗑️</button>
            </div>
        `;
        chatItem.onclick = (e) => {
            if (!e.target.classList.contains('chat-action-btn')) {
                loadChat(chat.id);
            }
        };
        chatsList.appendChild(chatItem);
    });
}

async function createNewChat() {
    try {
        const response = await fetch('/create_chat', { method: 'POST' });
        const data = await response.json();
        await loadChats();
        loadChat(data.chat.id);
        closeSidebar();
    } catch (error) {
        console.error('Error creating chat:', error);
    }
}

async function loadChat(chatId) {
    try {
        const response = await fetch(`/get_chat/${chatId}`);
        const data = await response.json();
        currentChatId = chatId;
        renderMessages(data.chat.messages, false);
        document.getElementById('chatTitle').textContent = data.chat.title;
        renderChatsList();
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

function renderMessages(messages, append = false) {
    const chatMessages = document.getElementById('chatMessages');
    const emptyState = document.getElementById('emptyState');

    if (!append) {
        chatMessages.innerHTML = '';
    }

    if (emptyState) { 
        if (!append && messages.length === 0) {
            console.log('Showing empty state');
            emptyState.style.display = 'flex';
            return;
        }
        console.log('Showing normal state');
        emptyState.style.display = 'none';
    }

    messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.role}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const roleDiv = document.createElement('div');
        roleDiv.className = 'message-role';
        roleDiv.textContent = msg.role === 'user' ? 'You' : 'AI Assistant';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        // Parse Markdown and sanitize HTML
        const rawHtml = marked.parse(msg.content);
        textDiv.innerHTML = DOMPurify.sanitize(rawHtml);

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = msg.timestamp;

        messageContent.append(roleDiv, textDiv, timeDiv);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Typing indicator for AI
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');

    const messageGroup = document.createElement('div');
    messageGroup.className = 'message assistant typing-message';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const avatar = document.createElement('div');
    avatar.className = 'avatar assistant';
    avatar.textContent = 'AI';

    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator active';
    typingIndicator.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    messageContent.appendChild(avatar);
    messageContent.appendChild(typingIndicator);
    messageGroup.appendChild(messageContent);

    chatMessages.appendChild(messageGroup);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageGroup;
}

async function sendMessage() {
    const input = messageInput;
    const text = input.value.trim();
    const sendBtn = document.getElementById('sendBtn');

    if (!text && !attachedFile) return;

    input.disabled = true;
    sendBtn.disabled = true;

    // Display message with file indicator if file attached
    let displayContent = text;
    if (attachedFile) {
        displayContent += `\n\n📎 Attached: ${attachedFile.name}`;
    }

    const userMessage = {
        role: 'user',
        content: displayContent,
        timestamp: new Date().toLocaleTimeString() 
    };

    renderMessages([userMessage], true); 

    input.value = '';
    input.style.height = 'auto';

    // Show typing indicator
    const typingDiv = showTypingIndicator();

    try {
        // Create chat if it doesn't exist
        if (!currentChatId) {
            const createResp = await fetch('/create_chat', { method: 'POST' });
            const createData = await createResp.json();
            currentChatId = createData.chat.id;
        }

        // Prepare request body with file content if available
        const requestBody = { 
            chat_id: currentChatId, 
            message: text || `Analyze this ${attachedFile?.type || 'document'}`
        };
        
        if (extractedText) {
            requestBody.file_content = extractedText;
        }

        // Send message to backend
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        typingDiv.remove(); // Remove typing indicator

        // Clear attached file
        if (attachedFile) {
            removeFile();
        }

        // Append only new messages
        if (data.assistant_message) renderMessages([data.assistant_message], true);

        await loadChats(); // refresh sidebar

    } catch (error) {
        console.error('Error sending message:', error);
        typingDiv.remove();

        const errorMsg = {
             role: 'assistant',
             content: 'Sorry, an error occurred. Please try again.',
             timestamp: new Date().toLocaleTimeString()
        };
        renderMessages([errorMsg], true);
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }
}

async function deleteChat(chatId, event) {
    event.stopPropagation();
    if (!confirm('Delete this chat?')) return;

    try {
        await fetch(`/delete_chat/${chatId}`, { method: 'DELETE' });

        await loadChats();

        if (currentChatId === chatId) {
            currentChatId = null;

            if (chats.length > 0) {
                loadChat(chats[0].id);
            } else {
                document.getElementById('chatMessages').innerHTML = '';
                document.getElementById('chatTitle').textContent = 'AI Assistant';

                const emptyState = document.getElementById('emptyState');
                if (emptyState) {
                    emptyState.style.display = 'flex';
                }
            }
        }
    } catch (error) {
        console.error('Error deleting chat:', error);
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
}

document.getElementById('overlay').addEventListener('click', closeSidebar);

// File handling functions
async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const sendBtn = document.getElementById('sendBtn');

    // Show loading state
    fileName.textContent = `Processing ${file.name}...`;
    filePreview.style.display = 'block';
    sendBtn.disabled = true;

    // Create FormData and upload file
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/process_file', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            // Store file info and extracted text
            attachedFile = {
                name: file.name,
                type: result.file_type,
                metadata: result.metadata
            };
            extractedText = result.text;

            // Update preview
            fileName.textContent = `📄 ${file.name} (${result.file_type})`;
            sendBtn.disabled = false;
        } else {
            alert(`Error: ${result.error}`);
            removeFile();
        }
    } catch (error) {
        console.error('Error processing file:', error);
        alert('Failed to process file. Please try again.');
        removeFile();
    }

    // Clear file input
    event.target.value = '';
}

function removeFile() {
    attachedFile = null;
    extractedText = null;
    document.getElementById('filePreview').style.display = 'none';
    document.getElementById('fileName').textContent = '';
    document.getElementById('fileInput').value = '';
}
