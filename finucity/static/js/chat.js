/**
 * Finucity AI - Advanced Professional Chat Interface
 * Frontend JavaScript for chat functionality
 * Created by: Sumeet Sangwan (@Sumeet-01)
 * Last Updated: 2025-11-12 15:37:09 UTC
 * Version: 2.2.0
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- STATE MANAGEMENT ---
    let currentConversationId = initialConversationId || null;
    let isLoading = false;
    let conversations = [];
    let currentTheme = localStorage.getItem('finucity-theme') || 'wine';
    let isInitialLoad = true;
    
    // --- DOM ELEMENTS ---
    const elements = {
        body: document.body,
        appContainer: document.querySelector('.app-container'),
        splashScreen: document.querySelector('.splash-screen'),
        sidebar: document.getElementById('sidebar'),
        sidebarOverlay: document.getElementById('sidebarOverlay'),
        conversationsList: document.getElementById('conversationsList'),
        conversationSearch: document.getElementById('conversationSearch'),
        clearSearch: document.getElementById('clearSearch'),
        filterOptions: document.querySelectorAll('.filter-option'),
        chatForm: document.getElementById('chatForm'),
        messageInput: document.getElementById('messageInput'),
        sendButton: document.getElementById('sendButton'),
        messagesContainer: document.getElementById('messagesContainer'),
        welcomeMessage: document.getElementById('welcomeMessage'),
        chatTitle: document.getElementById('chatTitle'),
        chatSubtitle: document.getElementById('chatSubtitle'),
        typingStatus: document.getElementById('typingStatus'),
        newChatBtn: document.getElementById('newChatBtn'),
        refreshConversations: document.getElementById('refreshConversations'),
        
        // Header Dropdown Menu
        optionsMenuBtn: document.getElementById('optionsMenuBtn'),
        optionsDropdown: document.getElementById('optionsDropdown'),
        
        // Action Buttons
        exportButton: document.getElementById('exportButton'),
        infoButton: document.getElementById('infoButton'),
        attachButton: document.getElementById('attachButton'),
        templateButton: document.getElementById('templateButton'),
        emojiButton: document.getElementById('emojiButton'),
        
        // Modals
        settingsModal: document.getElementById('settingsModal'),
        closeSettings: document.getElementById('closeSettings'),
        saveSettingsBtn: document.getElementById('saveSettingsBtn'),
        restoreDefaultsBtn: document.getElementById('restoreDefaultsBtn'),
        templatesModal: document.getElementById('templatesModal'),
        closeTemplates: document.getElementById('closeTemplates'),
        templateSearch: document.getElementById('templateSearch'),
        templateCategories: document.querySelectorAll('.template-category'),
        useTemplateButtons: document.querySelectorAll('.use-template-btn'),
        
        // Font Size Controls
        fontButtons: document.querySelectorAll('.font-btn'),
        
        // Suggestion Chips
        suggestionChips: document.querySelectorAll('.suggestion-chip'),
        popularQueries: document.querySelectorAll('.popular-query'),
        
        // Toast Container
        toastContainer: document.getElementById('toastContainer')
    };

    // --- API FUNCTIONS ---
    const api = {
        async sendMessage(message, conversationId = null) {
            try {
                const response = await fetch('/chat/api/send-message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: conversationId,
                        category: 'general'
                    })
                });
    
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Network error');
                }
    
                return await response.json();
            } catch (error) {
                console.error('Send message error:', error);
                throw error;
            }
        },

        async getConversations() {
            try {
                const response = await fetch('/chat/api/conversations');
                if (!response.ok) throw new Error('Failed to fetch conversations');
                return await response.json();
            } catch (error) {
                console.error('Error fetching conversations:', error);
                return { success: false, conversations: [] };
            }
        },

        async getConversation(conversationId) {
            try {
                const response = await fetch(`/chat/api/conversation/${conversationId}`);
                if (!response.ok) throw new Error('Failed to fetch conversation');
                return await response.json();
            } catch (error) {
                console.error('Error fetching conversation:', error);
                return { success: false, messages: [] };
            }
        },
        
        async deleteConversation(conversationId) {
            try {
                const response = await fetch(`/chat/api/conversation/${conversationId}`, {
                    method: 'DELETE'
                });
                if (!response.ok) throw new Error('Failed to delete conversation');
                return await response.json();
            } catch (error) {
                console.error('Error deleting conversation:', error);
                return { success: false };
            }
        }
    };

    // --- UI FUNCTIONS ---
    const ui = {
        addMessage(role, content, options = {}) {
            // Hide welcome message if it exists
            if (elements.welcomeMessage && elements.welcomeMessage.style.display !== 'none') {
                elements.welcomeMessage.style.display = 'none';
            }

            // Create message container
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            // Generate avatar content (letter or icon)
            let avatarContent = role === 'user' 
                ? (currentUser && currentUser.first_name ? currentUser.first_name[0].toUpperCase() : 'U')
                : 'A';
            
            // Use marked for assistant messages, plain text for user messages
            const processedContent = role === 'assistant' && window.marked 
                ? marked.parse(content) 
                : this.escapeHtml(content);
            
            // Create timestamp
            const now = new Date();
            const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            // Build message HTML
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatarContent}</div>
                <div class="message-bubble">
                    <div class="message-content">
                        ${processedContent}
                        ${options.disclaimer ? `<div class="message-disclaimer">${options.disclaimer}</div>` : ''}
                    </div>
                    <div class="message-footer">
                        <div class="message-time">
                            <i class="far fa-clock"></i>
                            <span>${timeString}</span>
                        </div>
                        <div class="message-actions">
                            <button class="message-action-btn copy-btn" title="Copy to clipboard">
                                <i class="far fa-copy"></i>
                            </button>
                            ${role === 'assistant' ? `
                                <button class="message-action-btn like-btn" title="Mark as helpful">
                                    <i class="far fa-thumbs-up"></i>
                                </button>
                                <button class="message-action-btn dislike-btn" title="Mark as unhelpful">
                                    <i class="far fa-thumbs-down"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            
            // Add event listeners to message action buttons
            const copyBtn = messageDiv.querySelector('.copy-btn');
            if (copyBtn) {
                copyBtn.addEventListener('click', () => {
                    const textToCopy = role === 'assistant' ? content : messageDiv.querySelector('.message-content').textContent;
                    navigator.clipboard.writeText(textToCopy)
                        .then(() => this.showToast('Content copied to clipboard!', 'success'))
                        .catch(err => this.showToast('Failed to copy content', 'error'));
                });
            }
            
            const likeBtn = messageDiv.querySelector('.like-btn');
            if (likeBtn) {
                likeBtn.addEventListener('click', (e) => {
                    e.target.closest('.like-btn').classList.toggle('active');
                    const dislikeBtn = e.target.closest('.message-actions').querySelector('.dislike-btn');
                    if (dislikeBtn.classList.contains('active')) {
                        dislikeBtn.classList.remove('active');
                    }
                    this.showToast('Feedback recorded. Thank you!', 'success');
                });
            }
            
            const dislikeBtn = messageDiv.querySelector('.dislike-btn');
            if (dislikeBtn) {
                dislikeBtn.addEventListener('click', (e) => {
                    e.target.closest('.dislike-btn').classList.toggle('active');
                    const likeBtn = e.target.closest('.message-actions').querySelector('.like-btn');
                    if (likeBtn.classList.contains('active')) {
                        likeBtn.classList.remove('active');
                    }
                    this.showToast('Feedback recorded. Thank you!', 'success');
                });
            }

            // Add to messages container and scroll into view
            elements.messagesContainer.appendChild(messageDiv);
            this.scrollToBottom();
            
            return messageDiv;
        },

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        showTypingIndicator() {
            if (document.querySelector('.typing-indicator')) return;
            
            const indicator = document.createElement('div');
            indicator.className = 'typing-indicator';
            indicator.innerHTML = `
                <div class="message-avatar">A</div>
                <div class="message-bubble">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            elements.messagesContainer.appendChild(indicator);
            this.scrollToBottom();
            
            // Update typing status
            if (elements.typingStatus) {
                elements.typingStatus.textContent = 'Finucity AI is typing...';
            }
        },

        removeTypingIndicator() {
            const indicator = document.querySelector('.typing-indicator');
            if (indicator) {
                indicator.remove();
            }
            
            // Clear typing status
            if (elements.typingStatus) {
                elements.typingStatus.textContent = '';
            }
        },

        scrollToBottom() {
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        },

        updateChatTitle(title, subtitle = '') {
            if (elements.chatTitle) {
                elements.chatTitle.textContent = title || 'Finucity AI Assistant';
            }
            if (subtitle && elements.chatSubtitle) {
                elements.chatSubtitle.textContent = subtitle;
            }
            
            // Update page title
            document.title = `${title || 'Finucity AI'} | Chat`;
        },

        toggleLoading(loading) {
            isLoading = loading;
            elements.sendButton.disabled = loading || !elements.messageInput.value.trim();
            elements.messageInput.disabled = loading;
            
            if (loading) {
                elements.sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            } else {
                elements.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            }
        },

        renderConversations(conversationList) {
            elements.conversationsList.innerHTML = '';
            
            if (!conversationList || conversationList.length === 0) {
                elements.conversationsList.innerHTML = `
                    <div class="conversations-placeholder">
                        <div class="placeholder-icon">
                            <i class="fas fa-comments"></i>
                        </div>
                        <p>No conversations yet. Start chatting to create one!</p>
                    </div>
                `;
                return;
            }

            conversationList.forEach(conv => {
                // Create conversation item
                const item = document.createElement('div');
                item.className = `conversation-item ${conv.id == currentConversationId ? 'active' : ''}`;
                item.dataset.id = conv.id;
                item.dataset.category = conv.category || 'general';
                
                // Format timestamp
                const timestamp = new Date(conv.created_at || Date.now());
                const timeString = timestamp.toLocaleDateString([], {
                    month: 'short',
                    day: 'numeric'
                });
                
                item.innerHTML = `
                    <div class="conversation-header">
                        <div class="conversation-title">${conv.title || 'New Conversation'}</div>
                        <div class="conversation-actions">
                            <button class="btn-delete-conversation" title="Delete conversation" aria-label="Delete conversation">
                                <i class="far fa-trash-alt"></i>
                            </button>
                        </div>
                    </div>
                    <div class="conversation-preview">${conv.preview || 'Click to view conversation'}</div>
                    <div class="conversation-meta">
                        <span class="conversation-date">
                            <i class="far fa-clock"></i>
                            ${timeString}
                        </span>
                        ${conv.category ? `<span class="conversation-category">${conv.category}</span>` : ''}
                    </div>
                `;
                
                // Event listeners
                item.addEventListener('click', (e) => {
                    // Don't trigger if the delete button was clicked
                    if (e.target.closest('.btn-delete-conversation')) return;
                    
                    loadConversation(conv.id);
                    
                    // Close sidebar on mobile
                    if (window.innerWidth <= 768) {
                        elements.sidebar.classList.remove('open');
                        elements.sidebarOverlay.classList.remove('show');
                    }
                });
                
                // Delete button
                const deleteBtn = item.querySelector('.btn-delete-conversation');
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showConfirmDialog(
                        'Delete Conversation',
                        'Are you sure you want to delete this conversation? This cannot be undone.',
                        () => deleteConversation(conv.id)
                    );
                });
                
                elements.conversationsList.appendChild(item);
            });
        },
        
        filterConversations(filter = 'all', query = '') {
            const items = document.querySelectorAll('.conversation-item');
            
            items.forEach(item => {
                const title = item.querySelector('.conversation-title').textContent.toLowerCase();
                const preview = item.querySelector('.conversation-preview').textContent.toLowerCase();
                const category = item.dataset.category;
                
                const matchesFilter = filter === 'all' || category === filter;
                const matchesQuery = !query || 
                    title.includes(query.toLowerCase()) || 
                    preview.includes(query.toLowerCase());
                
                item.style.display = matchesFilter && matchesQuery ? 'block' : 'none';
            });
            
            // Show placeholder if no results
            const hasVisibleItems = [...items].some(item => item.style.display !== 'none');
            const placeholder = elements.conversationsList.querySelector('.conversations-placeholder');
            
            if (!hasVisibleItems) {
                if (!placeholder) {
                    const noResults = document.createElement('div');
                    noResults.className = 'conversations-placeholder';
                    noResults.innerHTML = `
                        <div class="placeholder-icon">
                            <i class="fas fa-search"></i>
                        </div>
                        <p>No conversations found matching your filters</p>
                    `;
                    elements.conversationsList.appendChild(noResults);
                }
            } else if (placeholder) {
                placeholder.remove();
            }
        },

        showError(message) {
            this.addMessage('assistant', `⚠️ Error: ${message}`);
            this.showToast(message, 'error');
        },

        clearMessages() {
            elements.messagesContainer.innerHTML = '';
            if (elements.welcomeMessage) {
                elements.welcomeMessage.style.display = 'block';
            }
        },
        
        showToast(message, type = 'info', duration = 3000) {
            // Create toast element
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            // Set icon based on type
            let icon = 'fa-info-circle';
            if (type === 'success') icon = 'fa-check-circle';
            if (type === 'error') icon = 'fa-exclamation-circle';
            if (type === 'warning') icon = 'fa-exclamation-triangle';
            
            // Build toast HTML
            toast.innerHTML = `
                <div class="toast-icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="toast-content">
                    <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
                    <div class="toast-message">${message}</div>
                </div>
                <button class="toast-close">&times;</button>
            `;
            
            // Add to container
            elements.toastContainer.appendChild(toast);
            
            // Close button event
            toast.querySelector('.toast-close').addEventListener('click', () => {
                toast.remove();
            });
            
            // Auto remove after duration
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(30px)';
                
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }, duration);
        },
        
        showConfirmDialog(title, message, onConfirm) {
            // Create modal element
            const modal = document.createElement('div');
            modal.className = 'modal show';
            
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 400px;">
                    <div class="modal-header">
                        <h3><i class="fas fa-question-circle"></i> ${title}</h3>
                        <button class="close-btn">&times;</button>
                    </div>
                    <div class="modal-body">
                        <p>${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="cancelBtn">Cancel</button>
                        <button class="btn btn-primary" id="confirmBtn">Confirm</button>
                    </div>
                </div>
            `;
            
            // Add to body
            document.body.appendChild(modal);
            
            // Event listeners
            const closeModal = () => {
                modal.classList.remove('show');
                setTimeout(() => {
                    modal.remove();
                }, 300);
            };
            
            modal.querySelector('.close-btn').addEventListener('click', closeModal);
            modal.querySelector('#cancelBtn').addEventListener('click', closeModal);
            
            modal.querySelector('#confirmBtn').addEventListener('click', () => {
                closeModal();
                onConfirm();
            });
            
            // Close when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }
    };

    // --- CORE FUNCTIONS ---
    async function sendMessage(messageText) {
        if (!messageText.trim() || isLoading) return;
        
        try {
            // Add user message to UI
            ui.addMessage('user', messageText);
            ui.showTypingIndicator();
            ui.toggleLoading(true);
            
            // Clear input and resize if it's the input field
            if (elements.messageInput.value === messageText) {
                elements.messageInput.value = '';
                autoResizeTextarea();
            }
            
            // Send message to API
            const response = await api.sendMessage(messageText, currentConversationId);
            
            ui.removeTypingIndicator();

            if (response.success) {
                // Add AI response
                ui.addMessage('assistant', response.response, {
                    disclaimer: response.disclaimer
                });

                // Update conversation state if this was a new conversation
                if (!currentConversationId && response.conversation_id) {
                    currentConversationId = response.conversation_id;
                    
                    // Update URL without page reload
                    const newUrl = `/chat/conversation/${currentConversationId}`;
                    window.history.pushState({ conversationId: currentConversationId }, '', newUrl);
                    
                    // Update chat title
                    ui.updateChatTitle(response.conversation_title || 'New Conversation');
                    
                    // Refresh conversations list
                    await loadConversations();
                }
            } else {
                ui.showError(response.error || 'Failed to get AI response');
            }
        } catch (error) {
            console.error('Send message error:', error);
            ui.removeTypingIndicator();
            ui.showError('Failed to send message. Please try again.');
        } finally {
            ui.toggleLoading(false);
            elements.messageInput.focus();
            checkSendButtonState();
        }
    }

    async function loadConversation(conversationId) {
        if (conversationId === currentConversationId) return;

        currentConversationId = conversationId;
        ui.clearMessages();
        ui.showTypingIndicator();

        try {
            const response = await api.getConversation(conversationId);
            ui.removeTypingIndicator();

            if (response.success && response.messages) {
                // Update chat title
                ui.updateChatTitle(response.conversation.title || 'Conversation');

                // Add all messages to UI
                response.messages.forEach(msg => {
                    ui.addMessage(msg.role, msg.content);
                });

                // Update URL
                const newUrl = `/chat/conversation/${conversationId}`;
                window.history.pushState({ conversationId: conversationId }, '', newUrl);

                // Update active conversation in sidebar
                document.querySelectorAll('.conversation-item').forEach(item => {
                    item.classList.remove('active');
                });
                const activeItem = document.querySelector(`[data-id="${conversationId}"]`);
                if (activeItem) {
                    activeItem.classList.add('active');
                }
            } else {
                ui.showError('Failed to load conversation');
            }
        } catch (error) {
            console.error('Load conversation error:', error);
            ui.removeTypingIndicator();
            ui.showError('Failed to load conversation');
        }
    }

    async function loadConversations() {
        try {
            const response = await api.getConversations();
            if (response.success) {
                conversations = response.conversations || [];
                ui.renderConversations(conversations);
            } else {
                ui.showToast('Failed to load conversations', 'error');
            }
        } catch (error) {
            console.error('Load conversations error:', error);
        }
    }
    
    async function deleteConversation(conversationId) {
        try {
            const response = await api.deleteConversation(conversationId);
            
            if (response.success) {
                // Remove from UI
                const item = document.querySelector(`.conversation-item[data-id="${conversationId}"]`);
                if (item) {
                    item.remove();
                }
                
                // Show toast
                ui.showToast('Conversation deleted successfully', 'success');
                
                // If current conversation was deleted, start a new one
                if (conversationId === currentConversationId) {
                    startNewChat();
                }
                
                // Refresh conversations list
                await loadConversations();
            } else {
                ui.showToast('Failed to delete conversation', 'error');
            }
        } catch (error) {
            console.error('Delete conversation error:', error);
            ui.showToast('Error deleting conversation', 'error');
        }
    }
    
    async function exportConversation() {
        if (!currentConversationId) {
            ui.showToast('No active conversation to export', 'warning');
            return;
        }
        
        try {
            const response = await api.getConversation(currentConversationId);
            
            if (response.success && response.messages) {
                // Format conversation for export
                let exportText = `# ${response.conversation.title || 'Conversation'}\n`;
                exportText += `# Date: ${new Date().toLocaleString()}\n`;
                exportText += `# Exported from Finucity AI\n\n`;
                
                response.messages.forEach(msg => {
                    const role = msg.role === 'assistant' ? 'Finucity AI' : 'You';
                    exportText += `## ${role}:\n${msg.content}\n\n`;
                });
                
                // Create and download file
                const blob = new Blob([exportText], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `finucity-chat-${response.conversation.id}.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                ui.showToast('Conversation exported successfully', 'success');
            } else {
                ui.showToast('Failed to export conversation', 'error');
            }
        } catch (error) {
            console.error('Export conversation error:', error);
            ui.showToast('Error exporting conversation', 'error');
        }
    }

    function startNewChat() {
        currentConversationId = null;
        ui.clearMessages();
        ui.updateChatTitle('Finucity AI Assistant', 'Your AI Chartered Accountant');
        
        // Update URL
        window.history.pushState({}, '', '/chat/');
        
        // Remove active state from all conversations
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        
        elements.messageInput.focus();

        // Close sidebar on mobile
        if (window.innerWidth <= 768 && elements.sidebar && elements.sidebarOverlay) {
            elements.sidebar.classList.remove('open');
            elements.sidebarOverlay.classList.remove('show');
        }
    }

    function checkSendButtonState() {
        const hasText = elements.messageInput.value.trim().length > 0;
        elements.sendButton.disabled = !hasText || isLoading;
    }

    function autoResizeTextarea() {
        const el = elements.messageInput;
        if (!el) return;
        
        el.style.height = 'auto';
        const maxHeight = 150; // Max height in pixels
        const scrollHeight = el.scrollHeight;
        el.style.height = Math.min(scrollHeight, maxHeight) + 'px';
    }
    
    function toggleModal(modalElement, show) {
        if (!modalElement) return;
        
        if (show) {
            modalElement.classList.add('show');
            document.body.style.overflow = 'hidden';
        } else {
            modalElement.classList.remove('show');
            document.body.style.overflow = '';
        }
    }

    // --- FILE UPLOAD FUNCTION ---
    async function uploadFiles(files) {
        try {
            const formData = new FormData();
            files.forEach((file, index) => {
                formData.append(`file${index}`, file);
            });
            
            ui.showToast('Uploading files...', 'info');
            
            const response = await fetch('/chat/api/upload-files', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('Upload failed');
            
            const result = await response.json();
            ui.showToast('Files uploaded successfully!', 'success');
            
            // Add uploaded files info to chat
            const fileList = files.map(f => `📎 ${f.name}`).join('\n');
            elements.messageInput.value += `\n\nAttached files:\n${fileList}`;
            autoResizeTextarea();
            checkSendButtonState();
            
        } catch (error) {
            console.error('Upload error:', error);
            ui.showToast('Failed to upload files. Please try again.', 'error');
        }
    }

    // --- EVENT LISTENERS ---
    
    // Form submission
    elements.chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageText = elements.messageInput.value.trim();
        if (messageText && !isLoading) {
            await sendMessage(messageText);
        }
    });

    // Input handling
    elements.messageInput.addEventListener('input', () => {
        checkSendButtonState();
        autoResizeTextarea();
    });

    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            elements.chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // New chat button
    if (elements.newChatBtn) {
        elements.newChatBtn.addEventListener('click', startNewChat);
    }
    
    // Refresh conversations
    if (elements.refreshConversations) {
        elements.refreshConversations.addEventListener('click', async () => {
            elements.refreshConversations.classList.add('rotating');
            await loadConversations();
            setTimeout(() => {
                elements.refreshConversations.classList.remove('rotating');
            }, 1000);
        });
    }
    
    // Search conversations
    if (elements.conversationSearch && elements.clearSearch) {
        elements.conversationSearch.addEventListener('input', () => {
            const query = elements.conversationSearch.value.trim();
            const activeFilter = document.querySelector('.filter-option.active')?.dataset.filter || 'all';
            ui.filterConversations(activeFilter, query);
            
            // Show/hide clear button
            elements.clearSearch.style.opacity = query.length ? '1' : '0';
            elements.clearSearch.style.pointerEvents = query.length ? 'auto' : 'none';
        });
        
        // Clear search
        elements.clearSearch.addEventListener('click', () => {
            elements.conversationSearch.value = '';
            elements.clearSearch.style.opacity = '0';
            elements.clearSearch.style.pointerEvents = 'none';
            const activeFilter = document.querySelector('.filter-option.active')?.dataset.filter || 'all';
            ui.filterConversations(activeFilter);
        });
    }
    
    // Filter conversations
    elements.filterOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Update active state
            elements.filterOptions.forEach(o => o.classList.remove('active'));
            option.classList.add('active');
            
            // Apply filter
            const filter = option.dataset.filter;
            const query = elements.conversationSearch?.value.trim() || '';
            ui.filterConversations(filter, query);
        });
    });

    // Suggestion chips
    if (elements.messagesContainer) {
        elements.messagesContainer.addEventListener('click', (e) => {
            // Check for suggestion chips or popular queries
            const chip = e.target.closest('.suggestion-chip, .popular-query');
            if (chip) {
                const suggestion = chip.dataset.suggestion;
                if (suggestion) {
                    elements.messageInput.value = suggestion;
                    elements.messageInput.focus();
                    checkSendButtonState();
                    autoResizeTextarea();
                    
                    // Smooth scroll to input
                    const inputContainer = document.querySelector('.input-container');
                    if (inputContainer) {
                        inputContainer.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            }
        });
    }

    // Sidebar overlay click (mobile)
    if (elements.sidebarOverlay) {
        elements.sidebarOverlay.addEventListener('click', () => {
            if (elements.sidebar) {
                elements.sidebar.classList.remove('open');
            }
            elements.sidebarOverlay.classList.remove('show');
        });
    }
    
    // ========== HEADER OPTIONS DROPDOWN MENU ==========
    if (elements.optionsMenuBtn && elements.optionsDropdown) {
        console.log('✅ Initializing header options menu...');
        
        // Toggle dropdown on button click
        elements.optionsMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            
            // Toggle this dropdown
            const isShowing = elements.optionsDropdown.classList.contains('show');
            
            if (isShowing) {
                elements.optionsDropdown.classList.remove('show');
                elements.optionsDropdown.style.display = 'none';
            } else {
                elements.optionsDropdown.style.display = 'block';
                // Force reflow
                elements.optionsDropdown.offsetHeight;
                elements.optionsDropdown.classList.add('show');
            }
            
            console.log('Options dropdown', isShowing ? 'closed' : 'opened');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (elements.optionsDropdown.classList.contains('show') &&
                !elements.optionsMenuBtn.contains(e.target) &&
                !elements.optionsDropdown.contains(e.target)) {
                elements.optionsDropdown.classList.remove('show');
                elements.optionsDropdown.style.display = 'none';
                console.log('Options dropdown closed (click outside)');
            }
        });
        
        // Handle dropdown item clicks
        const dropdownItems = elements.optionsDropdown.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const itemId = item.id;
                console.log('✅ Dropdown item clicked:', itemId);
                
                // Close the dropdown
                elements.optionsDropdown.classList.remove('show');
                elements.optionsDropdown.style.display = 'none';
                
                // Handle the action based on the item clicked
                switch(itemId) {
                    case 'settingsBtn':
                        if (elements.settingsModal) {
                            toggleModal(elements.settingsModal, true);
                        }
                        break;
                    
                    case 'exportBtn':
                        exportConversation();
                        break;
                    
                    case 'clearHistoryBtn':
                        ui.showConfirmDialog(
                            'Clear All History',
                            'Are you sure you want to clear all conversation history? This action cannot be undone.',
                            async () => {
                                // Clear all conversations
                                for (const conv of conversations) {
                                    await deleteConversation(conv.id);
                                }
                                ui.showToast('All conversations cleared', 'success');
                                startNewChat();
                            }
                        );
                        break;
                    
                    case 'aboutBtn':
                        ui.showToast('Finucity AI v2.2.0 - Built by Sumeet-01', 'info', 5000);
                        break;
                    
                    default:
                        console.log('Unknown dropdown item:', itemId);
                }
            });
        });
        
        console.log('✅ Header options menu initialized successfully');
    }
    
    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
        const path = window.location.pathname;
        const conversationMatch = path.match(/\/chat\/conversation\/(\d+)/);
        
        if (conversationMatch) {
            const conversationId = parseInt(conversationMatch[1]);
            loadConversation(conversationId);
        } else if (path === '/chat/' || path === '/chat') {
            startNewChat();
        }
    });
    
    // Export Button in Header
    if (elements.exportButton) {
        elements.exportButton.addEventListener('click', exportConversation);
    }
    
    // Info Button
    if (elements.infoButton) {
        elements.infoButton.addEventListener('click', () => {
            if (!currentConversationId) {
                ui.showToast('No active conversation to show info', 'warning');
                return;
            }
            
            const conv = conversations.find(c => c.id == currentConversationId);
            if (conv) {
                const created = new Date(conv.created_at).toLocaleString();
                ui.showToast(`Created: ${created} | Category: ${conv.category || 'General'}`, 'info', 5000);
            }
        });
    }
    
    // Template button
    if (elements.templateButton && elements.templatesModal && elements.closeTemplates) {
        elements.templateButton.addEventListener('click', () => {
            toggleModal(elements.templatesModal, true);
        });
        
        elements.closeTemplates.addEventListener('click', () => {
            toggleModal(elements.templatesModal, false);
        });
        
        // Template categories
        elements.templateCategories.forEach(category => {
            category.addEventListener('click', () => {
                elements.templateCategories.forEach(c => c.classList.remove('active'));
                category.classList.add('active');
                
                const filter = category.dataset.category;
                const templates = document.querySelectorAll('.template-card');
                
                templates.forEach(template => {
                    const showTemplate = filter === 'all' || template.dataset.category === filter;
                    template.style.display = showTemplate ? 'block' : 'none';
                });
            });
        });
        
        // Template search
        if (elements.templateSearch) {
            elements.templateSearch.addEventListener('input', () => {
                const query = elements.templateSearch.value.toLowerCase().trim();
                const templates = document.querySelectorAll('.template-card');
                
                templates.forEach(template => {
                    const title = template.querySelector('h4').textContent.toLowerCase();
                    const description = template.querySelector('p').textContent.toLowerCase();
                    const isMatch = title.includes(query) || description.includes(query);
                    
                    const activeCategory = document.querySelector('.template-category.active');
                    const categoryFilter = activeCategory?.dataset.category || 'all';
                    const matchesCategory = categoryFilter === 'all' || template.dataset.category === categoryFilter;
                    
                    template.style.display = (isMatch && matchesCategory) ? 'block' : 'none';
                });
            });
        }
        
        // Use template
        document.querySelectorAll('.use-template-btn').forEach(button => {
            button.addEventListener('click', () => {
                const template = button.closest('.template-card').querySelector('p').textContent;
                elements.messageInput.value = template;
                elements.messageInput.focus();
                checkSendButtonState();
                autoResizeTextarea();
                
                toggleModal(elements.templatesModal, false);
            });
        });
    }
    
    // Settings
    if (elements.settingsModal && elements.closeSettings) {
        elements.closeSettings.addEventListener('click', () => {
            toggleModal(elements.settingsModal, false);
        });
        
        // Font size
        elements.fontButtons.forEach(button => {
            button.addEventListener('click', () => {
                elements.fontButtons.forEach(b => b.classList.remove('active'));
                button.classList.add('active');
                
                const size = button.dataset.size;
                document.documentElement.style.fontSize = 
                    size === 'small' ? '14px' : 
                    size === 'large' ? '18px' : '16px';
                
                localStorage.setItem('font-size', size);
            });
        });
        
        // Save settings
        if (elements.saveSettingsBtn) {
            elements.saveSettingsBtn.addEventListener('click', () => {
                toggleModal(elements.settingsModal, false);
                ui.showToast('Settings saved successfully', 'success');
            });
        }
        
        // Restore defaults
        if (elements.restoreDefaultsBtn) {
            elements.restoreDefaultsBtn.addEventListener('click', () => {
                // Reset font size
                document.documentElement.style.fontSize = '16px';
                elements.fontButtons.forEach(b => {
                    b.classList.toggle('active', b.dataset.size === 'medium');
                });
                localStorage.removeItem('font-size');
                
                ui.showToast('Settings restored to defaults', 'success');
            });
        }
    }
    
    // Emoji button
    if (elements.emojiButton) {
        elements.emojiButton.addEventListener('click', () => {
            // Simple emoji picker
            const commonEmojis = ['😊', '👍', '❤️', '🎉', '🤔', '👏', '💰', '📈', '💼', '📊'];
            
            // Create and show emoji picker
            const picker = document.createElement('div');
            picker.className = 'emoji-picker';
            picker.style.cssText = `
                position: absolute;
                bottom: 80px;
                right: 10px;
                background: var(--bg-alt);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: var(--border-radius-md);
                padding: 10px;
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 10px;
                z-index: 100;
                box-shadow: var(--shadow-lg);
            `;
            
            commonEmojis.forEach(emoji => {
                const emojiBtn = document.createElement('button');
                emojiBtn.type = 'button';
                emojiBtn.className = 'emoji-btn';
                emojiBtn.textContent = emoji;
                emojiBtn.style.cssText = `
                    font-size: 20px;
                    padding: 5px;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    border-radius: var(--border-radius-sm);
                    transition: all 0.2s ease;
                `;
                
                emojiBtn.addEventListener('mouseover', () => {
                    emojiBtn.style.background = 'rgba(255, 255, 255, 0.1)';
                    emojiBtn.style.transform = 'scale(1.2)';
                });
                
                emojiBtn.addEventListener('mouseout', () => {
                    emojiBtn.style.background = 'transparent';
                    emojiBtn.style.transform = 'scale(1)';
                });
                
                emojiBtn.addEventListener('click', () => {
                    // Insert emoji at cursor position
                    const input = elements.messageInput;
                    const startPos = input.selectionStart;
                    const endPos = input.selectionEnd;
                    input.value = input.value.substring(0, startPos) + emoji + input.value.substring(endPos);
                    
                    // Set cursor position after the inserted emoji
                    input.selectionStart = startPos + emoji.length;
                    input.selectionEnd = startPos + emoji.length;
                    
                    // Focus back on the input
                    input.focus();
                    checkSendButtonState();
                    autoResizeTextarea();
                    
                    // Remove the picker
                    document.body.removeChild(picker);
                });
                
                picker.appendChild(emojiBtn);
            });
            
            // Add to body
            document.body.appendChild(picker);
            
            // Click outside to close
            const closeEmojiPicker = (e) => {
                if (!picker.contains(e.target) && e.target !== elements.emojiButton) {
                    if (document.body.contains(picker)) {
                        document.body.removeChild(picker);
                    }
                    document.removeEventListener('click', closeEmojiPicker);
                }
            };
            
            setTimeout(() => {
                document.addEventListener('click', closeEmojiPicker);
            }, 100);
        });
    }
    
    // Attach files button - WORKING VERSION
    if (elements.attachButton) {
        elements.attachButton.addEventListener('click', () => {
            // Create file input
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.csv,.xlsx';
            fileInput.multiple = true;
            
            fileInput.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                
                if (files.length === 0) return;
                
                // Show selected files
                const fileNames = files.map(f => f.name).join(', ');
                ui.showToast(`Selected: ${fileNames}`, 'success');
                
                // Here you can add file upload logic
                console.log('Files selected:', files);
                
                // Uncomment when backend is ready:
                // uploadFiles(files);
            });
            
            // Trigger file picker
            fileInput.click();
        });
    }

    // --- INITIALIZATION ---
    async function initialize() {
        console.log('🚀 Initializing Finucity AI Chat Interface v2.2.0...');
        
        // Remove loading class after animation completes
        setTimeout(() => {
            if (elements.body) {
                elements.body.classList.remove('loading');
            }
        }, 2000);
        
        // Initialize AOS library for animations
        if (window.AOS) {
            AOS.init({
                duration: 800,
                once: true,
                offset: 50
            });
        }
        
        console.log('✅ Finucity Chat initialized successfully');
        console.log('Current theme:', currentTheme);
        console.log('Is authenticated:', isAuthenticated);
        console.log('Initial conversation ID:', initialConversationId);
        
        // Apply saved theme
        document.documentElement.className = `theme-${currentTheme}`;
        
        // Apply saved font size
        const savedFontSize = localStorage.getItem('font-size');
        if (savedFontSize) {
            document.documentElement.style.fontSize = 
                savedFontSize === 'small' ? '14px' : 
                savedFontSize === 'large' ? '18px' : '16px';
            
            elements.fontButtons.forEach(button => {
                button.classList.toggle('active', button.dataset.size === savedFontSize);
            });
        }
        
        // Check if user is authenticated
        if (!isAuthenticated) {
            ui.addMessage('assistant', 'Please log in to use the chat feature. <a href="/auth/login">Click here to login</a>');
            return;
        }

        // Load conversations
        await loadConversations();

        // If there's an initial conversation ID, load it
        if (initialConversationId) {
            await loadConversation(parseInt(initialConversationId));
        }

        // Focus on input
        elements.messageInput.focus();
        checkSendButtonState();
        
        // If this is first visit, show welcome animation
        if (isInitialLoad) {
            setTimeout(() => {
                if (elements.welcomeMessage && !currentConversationId) {
                    elements.welcomeMessage.style.opacity = '1';
                }
            }, 500);
            
            isInitialLoad = false;
        }
    }

    // Start the app
    initialize();
    
    // --- UTILS ---
    // Add to window for debugging
    window.finucityChat = {
        startNewChat,
        ui,
        loadConversation,
        sendMessage,
        exportConversation,
        elements,
        conversations
    };
});

// CSS animations
document.head.insertAdjacentHTML('beforeend', `
<style>
@keyframes rotating {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
.rotating {
    animation: rotating 1s linear infinite;
}

/* Message action button active states */
.message-action-btn.active {
    color: var(--accent-primary) !important;
    background: rgba(139, 58, 71, 0.1);
}
</style>
`);

// Debug tools
window.debugFinucity = {
    testOptionsMenu: function() {
        console.log('🧪 Testing options menu...');
        const btn = document.getElementById('optionsMenuBtn');
        const dropdown = document.getElementById('optionsDropdown');
        
        console.log('Button found:', !!btn);
        console.log('Dropdown found:', !!dropdown);
        
        if (btn && dropdown) {
            dropdown.classList.toggle('show');
            dropdown.style.display = dropdown.classList.contains('show') ? 'block' : 'none';
            console.log('Dropdown toggled. Is visible:', dropdown.classList.contains('show'));
        }
    },
    
    showAllConversations: function() {
        console.log('📋 Current conversations:', window.finucityChat.conversations);
        return window.finucityChat.conversations;
    },
    
    testExport: function() {
        console.log('📤 Testing export function...');
        if (window.finucityChat && window.finucityChat.exportConversation) {
            window.finucityChat.exportConversation();
        }
    }
};

console.log('%c🚀 Finucity AI Chat v2.2.0 Loaded Successfully!', 'color: #8B3A47; font-size: 18px; font-weight: bold;');
console.log('%c✨ Built by: Sumeet-01 | Date: 2025-11-12', 'color: #4CAF50; font-size: 12px;');
console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #8B3A47;');
console.log('%c🛠️ Debug tools available:', 'color: #FBA002; font-weight: bold;');
console.log('  • window.debugFinucity.testOptionsMenu()');
console.log('  • window.debugFinucity.showAllConversations()');
console.log('  • window.debugFinucity.testExport()');
console.log('  • window.finucityChat (access to all chat functions)');
console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #8B3A47;');