/**
 * Finucity AI - Chat Debugging Script
 * This script checks for common issues and provides diagnostics
 */

console.log('🔍 Running Chat Diagnostics...');

// Check if DOM is ready
if (document.readyState === 'loading') {
    console.warn('⚠️ DOM not ready yet, waiting...');
} else {
    console.log('✅ DOM is ready');
}

// Check for required elements
const requiredElements = {
    'chatForm': document.getElementById('chatForm'),
    'messageInput': document.getElementById('messageInput'),
    'sendButton': document.getElementById('sendButton'),
    'newChatBtn': document.getElementById('newChatBtn'),
    'messagesContainer': document.getElementById('messagesContainer'),
    'conversationsList': document.getElementById('conversationsList'),
    'optionsMenuBtn': document.getElementById('optionsMenuBtn'),
    'exportButton': document.getElementById('exportButton'),
    'themeSelector': document.getElementById('themeSelector'),
    'currentThemeBtn': document.getElementById('currentThemeBtn')
};

console.group('📋 Element Check');
let missingCount = 0;
Object.entries(requiredElements).forEach(([name, element]) => {
    if (element) {
        console.log(`✅ ${name} found`);
    } else {
        console.error(`❌ ${name} MISSING!`);
        missingCount++;
    }
});
console.groupEnd();

if (missingCount > 0) {
    console.error(`❌ ${missingCount} required elements are missing!`);
} else {
    console.log('✅ All required elements found');
}

// Check for JavaScript variables
console.group('🔧 Variables Check');
console.log('currentUserId:', typeof currentUserId !== 'undefined' ? currentUserId : '❌ MISSING');
console.log('isAuthenticated:', typeof isAuthenticated !== 'undefined' ? isAuthenticated : '❌ MISSING');
console.log('initialConversationId:', typeof initialConversationId !== 'undefined' ? initialConversationId : '❌ MISSING');
console.log('currentUser:', typeof currentUser !== 'undefined' ? currentUser : '❌ MISSING');
console.groupEnd();

// Test button clicks
console.group('🖱️ Button Test');
if (requiredElements.sendButton) {
    console.log('Send button disabled:', requiredElements.sendButton.disabled);
    console.log('Send button click handler:', requiredElements.sendButton.onclick ? 'Set' : 'Not set');
}
if (requiredElements.newChatBtn) {
    console.log('New Chat button click handler:', requiredElements.newChatBtn.onclick ? 'Set' : 'Not set');
}
console.groupEnd();

console.log('🔍 Diagnostics complete. Check console for details.');
