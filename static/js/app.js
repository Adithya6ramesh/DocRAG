// App State Management
class DocRAGApp {
    constructor() {
        this.currentChatId = null;
        this.chats = this.loadChats();
        this.authToken = localStorage.getItem('auth_token'); // Fixed key name
        this.userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
        this.theme = localStorage.getItem('theme') || 'light';
        
        this.initializeApp();
        this.bindEvents();
    }

    // Initialize the application
    initializeApp() {
        this.applyTheme();
        this.renderChatHistory();
        this.updateAuthUI();
        
        // Create first chat if no chats exist
        if (this.chats.length === 0) {
            this.createNewChat();
        } else {
            this.loadChat(this.chats[0].id);
        }
    }

    // Event Bindings
    bindEvents() {
        // Sidebar toggle
        document.getElementById('sidebarToggle').addEventListener('click', this.toggleSidebar);
        
        // New chat button
        document.getElementById('newChatBtn').addEventListener('click', () => this.createNewChat());
        
        // Message input
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        
        // Upload button and menu
        document.getElementById('uploadBtn').addEventListener('click', this.toggleUploadMenu);
        document.getElementById('uploadFileBtn').addEventListener('click', () => this.triggerFileUpload('file'));
        document.getElementById('uploadImageBtn').addEventListener('click', () => this.triggerFileUpload('image'));
        
        // File inputs
        document.getElementById('fileInput').addEventListener('change', (e) => this.handleFileUpload(e, 'document'));
        document.getElementById('imageInput').addEventListener('change', (e) => this.handleFileUpload(e, 'image'));
        
        // Auth modal
        document.getElementById('authBtn').addEventListener('click', this.showAuthModal);
        document.getElementById('closeModal').addEventListener('click', this.hideAuthModal);
        
        // Auth tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchAuthTab(e.target.dataset.tab));
        });
        
        // Auth forms
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('signupForm').addEventListener('submit', (e) => this.handleSignup(e));
        
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
        
        // Close upload menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.upload-btn') && !e.target.closest('.upload-menu')) {
                this.hideUploadMenu();
            }
        });
        
        // Close modal when clicking outside
        document.getElementById('authModal').addEventListener('click', (e) => {
            if (e.target.id === 'authModal') {
                this.hideAuthModal();
            }
        });
    }

    // Chat Management
    createNewChat() {
        const newChat = {
            id: Date.now().toString(),
            title: 'New Chat',
            messages: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        
        this.chats.unshift(newChat);
        this.saveChats();
        this.renderChatHistory();
        this.loadChat(newChat.id);
    }

    loadChat(chatId) {
        this.currentChatId = chatId;
        const chat = this.chats.find(c => c.id === chatId);
        
        if (!chat) return;
        
        // Update active chat in sidebar
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.toggle('active', item.dataset.chatId === chatId);
        });
        
        // Render messages
        this.renderMessages(chat.messages);
    }

    renderChatHistory() {
        const chatHistory = document.getElementById('chatHistory');
        
        if (this.chats.length === 0) {
            chatHistory.innerHTML = '<div class="empty-state">No chats yet</div>';
            return;
        }
        
        chatHistory.innerHTML = this.chats.map(chat => `
            <div class="chat-item" data-chat-id="${chat.id}" onclick="app.loadChat('${chat.id}')">
                <div class="chat-item-title">${this.escapeHtml(chat.title)}</div>
                <div class="chat-item-preview">
                    ${chat.messages.length > 0 ? this.escapeHtml(chat.messages[chat.messages.length - 1].content.slice(0, 50) + '...') : 'No messages'}
                </div>
            </div>
        `).join('');
    }

    renderMessages(messages) {
        const chatMessages = document.getElementById('chatMessages');
        
        if (messages.length === 0) {
            chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h3>👋 Welcome to DocRAG!</h3>
                    <p>Upload documents and start asking questions about them.</p>
                </div>
            `;
            return;
        }
        
        chatMessages.innerHTML = messages.map(msg => `
            <div class="message ${msg.sender}">
                <div class="message-avatar">
                    <i class="fas ${msg.sender === 'user' ? 'fa-user' : 'fa-robot'}"></i>
                </div>
                <div class="message-content">
                    <div class="message-text">${this.formatMessage(msg.content)}</div>
                    <div class="message-time">${this.formatTime(msg.timestamp)}</div>
                    ${msg.sources ? this.renderSources(msg.sources) : ''}
                </div>
            </div>
        `).join('');
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    formatMessage(content) {
        // Convert markdown to HTML with proper formatting
        let html = content;
        
        // Handle code blocks first (```code```)
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Escape HTML but preserve our tags
        html = html.replace(/&/g, '&amp;')
                   .replace(/</g, '&lt;')
                   .replace(/>/g, '&gt;')
                   .replace(/&lt;pre&gt;/g, '<pre>')
                   .replace(/&lt;\/pre&gt;/g, '</pre>')
                   .replace(/&lt;code&gt;/g, '<code>')
                   .replace(/&lt;\/code&gt;/g, '</code>');
        
        // Handle headings (##, ###)
        html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
        
        // Handle bold text
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Handle italic text  
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Handle bullet points (-, *, •)
        html = html.replace(/^[\-\*•]\s+(.+)$/gm, '<li>$1</li>');
        
        // Handle numbered lists
        html = html.replace(/^\d+\.\s+(.+)$/gm, '<ol-li>$1</ol-li>');
        
        // Wrap list items
        html = html.replace(/(<li>.*?<\/li>\s*)+/gs, '<ul>$&</ul>');
        html = html.replace(/(<ol-li>.*?<\/ol-li>\s*)+/gs, function(match) {
            return '<ol>' + match.replace(/<ol-li>/g, '<li>').replace(/<\/ol-li>/g, '</li>') + '</ol>';
        });
        
        // Handle paragraphs - split by double newlines
        const parts = html.split(/\n\n+/);
        html = parts.map(part => {
            part = part.trim();
            // Don't wrap if it's already wrapped in a tag
            if (part.startsWith('<h') || part.startsWith('<ul') || 
                part.startsWith('<ol') || part.startsWith('<pre') ||
                part.length === 0) {
                return part;
            }
            // Replace single newlines with <br>
            part = part.replace(/\n/g, '<br>');
            return '<p>' + part + '</p>';
        }).join('\n');
        
        return html;
    }

    renderSources(sources) {
        if (!sources || sources.length === 0) return '';
        
        return `
            <div class="message-sources">
                <div class="sources-label">📚 Sources:</div>
                ${sources.map(source => `
                    <div class="source-item">
                        <span class="source-score">${Math.round(source.score * 100)}%</span>
                        <span class="source-text">${this.escapeHtml(source.text.slice(0, 100))}...</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Message Handling
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Add user message
        this.addMessage('user', message);
        messageInput.value = '';
        
        // Show loading
        this.showLoading(true);
        
        try {
            // Send to RAG API
            const response = await this.callRAGAPI(message);
            
            // Add bot response
            this.addMessage('assistant', response.message, response.sources);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error processing your request. Please try again.');
            this.showToast('Error processing message', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    addMessage(sender, content, sources = null) {
        const message = {
            id: Date.now().toString(),
            sender,
            content,
            sources,
            timestamp: new Date().toISOString()
        };
        
        const currentChat = this.chats.find(c => c.id === this.currentChatId);
        if (!currentChat) return;
        
        currentChat.messages.push(message);
        currentChat.updatedAt = new Date().toISOString();
        
        // Update title based on first message
        if (currentChat.messages.length === 1 && sender === 'user') {
            currentChat.title = content.slice(0, 30) + (content.length > 30 ? '...' : '');
        }
        
        this.saveChats();
        this.renderMessages(currentChat.messages);
        this.renderChatHistory();
    }

    async callRAGAPI(query) {
        const endpoint = this.authToken ? '/auth/search' : '/search';
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        } else {
            headers['X-Tenant-ID'] = 'demo-tenant';
        }
        
        const response = await fetch(`${endpoint}?query=${encodeURIComponent(query)}`, {
            method: 'POST',
            headers
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Format response - handle both new format with 'answer' and old format with 'results'
        let message = '';
        let sources = [];
        
        if (data.answer) {
            // New format with AI-generated answer
            message = data.answer;
            sources = data.sources || [];
        } else if (data.sources && data.sources.length > 0) {
            // Handle renamed 'results' to 'sources'
            const topResult = data.sources[0];
            message = `Based on your documents, here's what I found:\n\n${topResult.text}`;
            sources = data.sources;
        } else if (data.results && data.results.length > 0) {
            // Fallback to old 'results' format
            const topResult = data.results[0];
            message = `Based on your documents, here's what I found:\n\n${topResult.text}`;
            sources = data.results;
        } else {
            message = `I couldn't find specific information about "${query}" in your uploaded documents. Please make sure you've uploaded relevant documents first.`;
        }

        return {
            message,
            sources
        };
    }

    // File Upload Handling
    triggerFileUpload(type) {
        const inputId = type === 'image' ? 'imageInput' : 'fileInput';
        document.getElementById(inputId).click();
        this.hideUploadMenu();
    }

    async handleFileUpload(event, type) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;
        
        this.showLoading(true);
        
        // Show initial status
        this.addMessage('assistant', `📁 Processing ${files.length} file(s)...`);
        
        try {
            if (type === 'document') {
                // Use bulk upload endpoint for multiple files
                const success = await this.uploadMultipleFiles(files);
                if (success) {
                    this.showToast(`Successfully processed ${files.length} file(s)!`, 'success');
                } else {
                    this.showToast('Some files failed to upload. Check the chat for details.', 'warning');
                }
            } else if (type === 'image') {
                this.showToast('Image processing not implemented yet', 'warning');
            }
            
        } catch (error) {
            console.error('File upload error:', error);
            this.addMessage('assistant', `❌ Upload failed: ${error.message}`);
            this.showToast('Upload failed. Please try again.', 'error');
        } finally {
            this.showLoading(false);
            // Reset file inputs
            event.target.value = '';
        }
    }

    async uploadMultipleFiles(files) {
        try {
            // Check file types first
            const allowedTypes = ['.txt', '.md', '.pdf'];
            const invalidFiles = files.filter(file => {
                const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                return !allowedTypes.includes(fileExt);
            });
            
            if (invalidFiles.length > 0) {
                this.showToast(`Invalid file types detected. Only .txt, .md, and .pdf files are supported.`, 'warning');
                return false;
            }
            
            // Create FormData for bulk upload
            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });
            
            const endpoint = '/upload-files';
            const headers = {};
            
            if (this.authToken) {
                headers['Authorization'] = `Bearer ${this.authToken}`;
            } else {
                headers['X-Tenant-ID'] = 'demo-tenant';
            }
            
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                headers
            });
            
            const result = await response.json();
            
            if (response.ok && !result.error) {
                // Display detailed results
                this.addMessage('assistant', `📁 ${result.message}`);
                
                // Show individual file results if any failures
                if (result.failed_count > 0) {
                    const failedFiles = result.results.filter(r => r.error);
                    failedFiles.forEach(file => {
                        this.addMessage('assistant', `❌ ${file.filename}: ${file.error}`);
                    });
                }
                
                // Show successful files
                const successfulFiles = result.results.filter(r => !r.error);
                successfulFiles.forEach(file => {
                    this.addMessage('assistant', `✅ ${file.filename}: ${file.chunks_processed} chunks processed`);
                });
                
                return result.successful_count > 0;
            } else {
                throw new Error(result.error || 'Bulk upload failed');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            this.addMessage('assistant', `❌ Upload failed: ${error.message}`);
            return false;
        }
    }

    // Authentication
    async handleLogin(event) {
        event.preventDefault();
        
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            // This would integrate with your Supabase auth
            this.showToast('Login functionality coming soon!', 'info');
            this.hideAuthModal();
        } catch (error) {
            this.showToast('Login failed', 'error');
        }
    }

    async handleSignup(event) {
        event.preventDefault();
        
        const email = document.getElementById('signupEmail').value;
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (password !== confirmPassword) {
            this.showToast('Passwords do not match', 'error');
            return;
        }
        
        try {
            // This would integrate with your Supabase auth
            this.showToast('Signup functionality coming soon!', 'info');
            this.hideAuthModal();
        } catch (error) {
            this.showToast('Signup failed', 'error');
        }
    }

    updateAuthUI() {
        const authBtn = document.getElementById('authBtn');
        const userEmail = document.getElementById('userEmail');
        
        if (this.authToken && this.userInfo.email) {
            authBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
            userEmail.textContent = this.userInfo.email;
        } else {
            authBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
            userEmail.textContent = 'Guest User';
        }
    }

    // UI Helpers
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        
        sidebar.classList.toggle('open');
        mainContent.classList.toggle('sidebar-open');
    }

    toggleUploadMenu() {
        const uploadMenu = document.getElementById('uploadMenu');
        uploadMenu.classList.toggle('show');
    }

    hideUploadMenu() {
        document.getElementById('uploadMenu').classList.remove('show');
    }

    showAuthModal() {
        document.getElementById('authModal').classList.add('show');
    }

    hideAuthModal() {
        document.getElementById('authModal').classList.remove('show');
    }

    switchAuthTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        
        // Update forms
        document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
        document.getElementById('signupForm').classList.toggle('hidden', tab !== 'signup');
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        localStorage.setItem('theme', this.theme);
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        const themeIcon = document.querySelector('#themeToggle i');
        themeIcon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.classList.toggle('show', show);
        
        const sendBtn = document.getElementById('sendBtn');
        sendBtn.disabled = show;
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        }, 3000);
    }

    // Data Persistence
    loadChats() {
        const chats = localStorage.getItem('docrag_chats');
        return chats ? JSON.parse(chats) : [];
    }

    saveChats() {
        localStorage.setItem('docrag_chats', JSON.stringify(this.chats));
    }

    // Utilities
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize the app
const app = new DocRAGApp();