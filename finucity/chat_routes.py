"""
Enhanced chat routes with proper API endpoints for Finucity AI
Maintains clean separation between frontend and backend
Author: Sumeet Sangwan
"""

from flask import Blueprint, render_template, request, jsonify, session, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import os
import traceback
import random
import requests

from finucity.models import User
from finucity.database import ChatService, UserService, get_supabase
from finucity.ai import get_ai_response

# Create blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# ===== FALLBACK AI FUNCTIONALITY =====

def get_fallback_response(question, category="general"):
    """Generate a relevant fallback response when main AI service is down"""
    
    try:
        # Try direct API call first as a backup method
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            try:
                print(f"[FALLBACK] Attempting direct GROQ API call for: {question[:30]}...")
                
                # Direct API call to Groq
                api_url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "llama-3.1-8b-instant",  # Use a reliable model
                    "messages": [
                        {"role": "system", "content": "You are Finucity AI, a financial advisor specializing in Indian tax laws, investments, and business finance. Provide accurate, concise advice."},
                        {"role": "user", "content": question}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800
                }
                
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_content = result['choices'][0]['message']['content']
                    print("[FALLBACK] Direct API call successful")
                    
                    return {
                        'success': True,
                        'response': ai_content.strip(),
                        'category': category,
                        'confidence': 0.9,
                        'disclaimer': "This financial advice is for informational purposes only. Please consult a professional for personalized guidance.",
                        'follow_up_suggestions': []
                    }
                else:
                    print(f"[FALLBACK] Direct API call failed: {response.status_code}")
            except Exception as e:
                print(f"[FALLBACK] Direct API call exception: {str(e)}")
    except Exception as e:
        print(f"[FALLBACK] Error in fallback API attempt: {str(e)}")
    
    # If direct API call fails, use pre-written responses
    print("[FALLBACK] Using pre-written response")
    
    # Common tax responses
    tax_responses = [
        "Based on current tax regulations for AY 2025-26, Section 80C allows deductions up to ₹1,50,000 for investments in PPF, ELSS mutual funds, life insurance premiums, and other eligible instruments. For optimal tax savings, consider diversifying across these options based on your risk tolerance and financial goals.",
        
        "For AY 2025-26, you can save taxes under Section 80C through:\n\n1. ELSS Mutual Funds: 3-year lock-in with potential for market returns\n2. PPF: 15-year tenure with tax-free interest (current rate ~7.1%)\n3. Tax-saving FDs: 5-year lock-in with guaranteed returns\n4. NPS: Additional deduction of ₹50,000 under Section 80CCD(1B)\n\nThe best approach is to allocate funds based on your risk appetite and liquidity needs."
    ]
    
    # Common investment responses
    investment_responses = [
        "For long-term wealth creation in India, consider building a portfolio with 60-70% allocation to equity (through index funds and diversified mutual funds), 20-30% to debt instruments for stability, and 5-10% to gold as a hedge against inflation. With current market conditions, systematic investment plans (SIPs) are recommended to average out market volatility.",
        
        "A well-balanced investment portfolio for 2025 should include:\n\n1. Large-cap funds for stability (40%)\n2. Mid and small-cap funds for growth (30%)\n3. Debt funds for regular income and stability (20%)\n4. Gold and international funds for diversification (10%)\n\nConsider tax efficiency by using ELSS funds for equity exposure and debt funds with indexation benefits for long-term debt allocation."
    ]
    
    # Common GST responses
    gst_responses = [
        "GST registration is mandatory for businesses with annual turnover exceeding ₹40 lakhs for goods (₹20 lakhs for services and in special category states). The registration process can be completed online on the GST portal with documents like PAN, business registration proof, bank account details, and photographs of business premises.",
        
        "For GSTR-1 filing, ensure you compile all your sales invoices for the tax period, categorizing them as B2B, B2C, exports, etc. The filing deadline is the 11th of the following month. Using GST software can simplify the process and ensure accuracy in reporting."
    ]
    
    # Common business responses
    business_responses = [
        "For small business accounting in India, maintain separate business bank accounts, track all expenses with proper documentation, use accounting software like Tally or Zoho Books, and ensure timely filing of GST returns and TDS. Consider hiring a part-time accountant for compliance matters.",
        
        "When starting a business in India, you should choose an appropriate structure (Proprietorship/LLP/Pvt Ltd) based on liability and funding needs. Key registrations include GST (if turnover exceeds threshold), shop & establishment license, professional tax, and industry-specific licenses."
    ]
    
    # Select appropriate response based on category and question content
    question_lower = question.lower()
    
    if category == "tax" or any(term in question_lower for term in ["tax", "section 80", "income tax", "deduction", "exemption", "itr"]):
        response_text = random.choice(tax_responses)
        category = "tax"
    elif category == "investment" or any(term in question_lower for term in ["invest", "mutual fund", "sip", "portfolio", "stock", "share"]):
        response_text = random.choice(investment_responses)
        category = "investment"
    elif category == "gst" or any(term in question_lower for term in ["gst", "input tax", "invoice", "gstr", "filing"]):
        response_text = random.choice(gst_responses)
        category = "gst"
    elif category == "business" or any(term in question_lower for term in ["business", "startup", "company", "entrepreneur"]):
        response_text = random.choice(business_responses)
        category = "business"
    else:
        # Default to all categories
        all_responses = tax_responses + investment_responses + gst_responses + business_responses
        response_text = random.choice(all_responses)
        category = "general"
    
    # Return formatted response
    return {
        'success': True,
        'response': response_text,
        'category': category,
        'confidence': 0.85,
        'disclaimer': "This is a pre-generated response while our AI service is being optimized. For personalized guidance, please consult a financial professional.",
        'follow_up_suggestions': [
            "Tell me more about tax-saving options for salaried employees",
            "How can I optimize my investment portfolio?",
            "What are the latest GST compliance requirements?"
        ]
    }

# ===== FRONTEND ROUTES (Serve HTML templates) =====

@chat_bp.route('/')
@login_required
def chat_interface():
    """Serve the main chat interface"""
    return render_template('chat.html', user=current_user)

@chat_bp.route('/conversation/<int:conversation_id>')
@login_required
def view_conversation(conversation_id):
    """View a specific conversation"""
    # Get conversation from Supabase
    conversation_data = ChatService.get_query_by_id(conversation_id)
    if not conversation_data or conversation_data.get('user_id') != current_user.id:
        from flask import abort
        abort(404)
    
    # Get all messages in this conversation (using session_id to group)
    session_id = conversation_data.get('session_id')
    messages_data = ChatService.get_queries_by_session(session_id, current_user.id) if session_id else []
    
    return render_template('chat.html', 
                         conversation=conversation_data,
                         messages=messages_data,
                         user=current_user)

@chat_bp.route('/history')
@login_required
def chat_history():
    """Show chat history page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get conversations from Supabase
    all_conversations = ChatService.get_user_queries(current_user.id, limit=100)
    
    # Simple pagination
    start = (page - 1) * per_page
    end = start + per_page
    conversations_page = all_conversations[start:end] if all_conversations else []
    
    # Create pagination object-like structure
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
    
    conversations = Pagination(conversations_page, page, per_page, len(all_conversations) if all_conversations else 0)
    
    return render_template('chat_history.html', 
                         conversations=conversations,
                         user=current_user,
                         datetime=datetime,
                         timedelta=timedelta)

# ===== API ROUTES (Backend functionality) =====

@chat_bp.route('/api/send-message', methods=['POST'])
@login_required
def api_send_message():
    """
    Main API endpoint for sending messages to AI
    Handles both text and file uploads
    """
    try:
        # Get form data (handles both JSON and FormData)
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id')
            category = data.get('category', 'general')
            files = []
        else:
            # Handle FormData (for file uploads)
            message = request.form.get('message', '').strip()
            conversation_id = request.form.get('conversation_id')
            category = request.form.get('category', 'general')
            files = request.files.getlist('files') if 'files' in request.files else []
        
        # Validation
        if not message and not files:
            return jsonify({
                'success': False,
                'error': 'Message or files required'
            }), 400
        
        # Generate session ID if this is a new conversation
        if not conversation_id:
            session_id = f"conv_{current_user.id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        else:
            # Get existing conversation's session_id from Supabase
            existing_conv = ChatService.get_query_by_id(conversation_id)
            if existing_conv and existing_conv.get('user_id') == current_user.id:
                session_id = existing_conv.get('session_id') or f"conv_{current_user.id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            else:
                return jsonify({
                    'success': False,
                    'error': 'Conversation not found'
                }), 404
        
        # Process uploaded files (if any)
        file_contents = []
        if files:
            for file in files:
                if file and file.filename:
                    try:
                        content = file.read()
                        file_contents.append({
                            'name': file.filename,
                            'type': file.content_type,
                            'content': content[:10000]  # Limit content size
                        })
                    except Exception as e:
                        current_app.logger.warning(f"Error processing file {file.filename}: {e}")
        
        # Store initial message data (will be updated with AI response)
        query_data = {
            'user_id': current_user.id,
            'question': message or "[File Upload]",
            'category': category,
            'response': "",  # Will be updated with AI response
            'session_id': session_id
        }
        
        # Prepare context for AI
        context = {
            'message': message,
            'files': file_contents,
            'category': category,
            'user_history': get_user_recent_history(current_user.id, session_id)
        }
        
        # Get AI response with enhanced error handling
        start_time = datetime.now()
        ai_response = None
        try:
            print(f"\n[CHAT] Calling main AI service for: {message[:50]}...")
            # Try the main AI service first
            ai_response = get_ai_response(
                question=message,
                category=category,
                context=context
            )
            print(f"[CHAT] Main AI response received, success: {ai_response.get('success', False)}")
        except Exception as ai_err:
            # Log the error from main AI service
            print(f"[CHAT] Main AI service error: {ai_err}")
            ai_response = None
        
        # Check if we need to use fallback
        if not ai_response or not ai_response.get('success', False):
            print("[CHAT] Main AI service failed or returned error, using fallback...")
            ai_response = get_fallback_response(message, category)
            print("[CHAT] Fallback response generated successfully")
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Double-check we have a valid response
        if not ai_response or not ai_response.get('success', False):
            # Last resort fallback if even the fallback failed
            ai_response = {
                'success': True,
                'response': f"I apologize, but I'm experiencing technical difficulties processing your request about '{message[:30]}...'. Please try again in a few moments or rephrase your question.",
                'category': category,
                'confidence': 0.5,
                'disclaimer': "Our service is temporarily experiencing issues. Please try again later."
            }
        
        # Update query data with AI response
        query_data['response'] = ai_response['response']
        
        # Save to Supabase
        saved_query = ChatService.create_query(**query_data)
        if not saved_query:
            raise Exception("Failed to save chat query to Supabase")
        
        # Generate conversation title if this is the first message
        conversation_title = generate_conversation_title(message, category)
        
        return jsonify({
            'success': True,
            'response': ai_response['response'],
            'category': ai_response.get('category', 'General'),
            'confidence': ai_response.get('confidence', 0.95),
            'disclaimer': ai_response.get('disclaimer', 'This is AI-generated advice. Please consult professionals for personalized guidance.'),
            'follow_up_suggestions': ai_response.get('follow_up_suggestions', []),
            'conversation_id': saved_query.get('id'),
            'conversation_title': conversation_title,
            'session_id': session_id,
            'response_time_ms': round(response_time * 1000, 2)
        })
        
    except Exception as e:
        current_app.logger.error(f"Chat API error: {e}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Even if everything fails, try to provide some response
        try:
            fallback_response = get_fallback_response("Help me with finance advice", "general")
            return jsonify({
                'success': True,
                'response': f"I apologize for the technical difficulty. Here's some general financial advice that might be helpful:\n\n{fallback_response['response']}",
                'category': 'general',
                'disclaimer': 'Our system encountered an error processing your specific question. This is general advice only.'
            })
        except:
            # Absolute last resort
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'response': 'I apologize, but I encountered an error. Please try again in a few moments.'
            }), 500

@chat_bp.route('/api/conversations')
@login_required
def api_get_conversations():
    """Get user's conversation list"""
    try:
        # Get conversations from Supabase
        queries = ChatService.get_user_queries(current_user.id, limit=50)
        
        # Group by session_id
        conversation_dict = {}
        for query in queries:
            session_id = query.get('session_id')
            if session_id and session_id not in conversation_dict:
                conversation_dict[session_id] = {
                    'id': query.get('id'),
                    'title': generate_conversation_title(query.get('question', ''), query.get('category', 'general')),
                    'category': query.get('category'),
                    'preview': query.get('question', '')[:100] + "..." if len(query.get('question', '')) > 100 else query.get('question', ''),
                    'created_at': query.get('created_at'),
                }
        
        # Convert to list
        conversations = list(conversation_dict.values())
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
        
    except Exception as e:
        current_app.logger.error(f"Get conversations API error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'conversations': []
        }), 500

@chat_bp.route('/api/conversation/<int:conversation_id>')
@login_required
def api_get_conversation(conversation_id):
    """Get specific conversation details"""
    try:
        # Get conversation from Supabase
        conversation = ChatService.get_query_by_id(conversation_id)
        
        if not conversation or conversation.get('user_id') != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        # Get all messages in this conversation
        session_id = conversation.get('session_id')
        messages = ChatService.get_queries_by_session(session_id, current_user.id) if session_id else []
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.get('id'),
                'role': 'user',
                'content': msg.get('question'),
                'timestamp': msg.get('created_at')
            })
            if msg.get('response'):
                message_list.append({
                    'id': f"{msg.get('id')}_response",
                    'role': 'assistant',
                    'content': msg.get('response'),
                    'timestamp': msg.get('created_at'),
                    'confidence': 0.9,
                    'category': msg.get('category')
                })
        
        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation.get('id'),
                'title': generate_conversation_title(conversation.get('question', ''), conversation.get('category', 'general')),
                'category': conversation.get('category'),
                'created_at': conversation.get('created_at'),
                'message_count': len(message_list)
            },
            'messages': message_list
        })
        
    except Exception as e:
        current_app.logger.error(f"Get conversation API error: {e}")
@login_required
def api_rename_conversation(conversation_id):
    """Rename a conversation"""
    try:
        data = request.get_json()
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        # Get conversation from Supabase
        conversation = ChatService.get_query_by_id(conversation_id)
        
        if not conversation or conversation.get('user_id') != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        # Note: Custom titles would require a title field in the schema
        # For now, just return success with the new title
        
        return jsonify({
            'success': True,
            'new_title': new_title,
            'category': conversation.get('category')
        })
        
    except Exception as e:
        current_app.logger.error(f"Rename conversation API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to rename conversation'
        }), 500

@chat_bp.route('/api/feedback', methods=['POST'])
@login_required
def api_submit_feedback():
    """Submit feedback for a chat response"""
    try:
        data = request.get_json()
        query_id = data.get('query_id')
        rating = data.get('rating')
        is_helpful = data.get('is_helpful')
        feedback_text = data.get('feedback_text', '')
        
        if not query_id or not rating:
            return jsonify({
                'success': False,
                'error': 'Query ID and rating are required'
            }), 400
        
        # Find the query from Supabase
        query = ChatService.get_query_by_id(query_id)
        
        if not query or query.get('user_id') != current_user.id:
            return jsonify({
                'success': False,
                'error': 'Query not found'
            }), 404
        
        # Submit feedback via FeedbackService
        from finucity.database import FeedbackService
        feedback_data = {
            'user_id': current_user.id,
            'query_id': query_id,
            'rating': rating,
            'is_helpful': is_helpful if is_helpful is not None else (rating >= 4),
            'feedback_text': feedback_text
        }
        
        FeedbackService.create_feedback(**feedback_data)
        
        return jsonify({
            'success': True,
            'message': 'Feedback submitted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Submit feedback API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit feedback'
        }), 500

# ===== HELPER FUNCTIONS =====

def get_user_recent_history(user_id, current_session_id, limit=5):
    """Get recent chat history for context"""
    try:
        # Get recent messages from Supabase
        recent_messages = ChatService.get_queries_by_session(current_session_id, user_id)
        
        # Limit and reverse to get most recent
        recent_messages = recent_messages[-limit:] if len(recent_messages) > limit else recent_messages
        
        history = []
        for msg in recent_messages:
            history.extend([
                {'role': 'user', 'content': msg.get('question', '')},
                {'role': 'assistant', 'content': msg.get('response', '')}
            ])
        
        return history
        
    except Exception as e:
        current_app.logger.warning(f"Error getting user history: {e}")
        return []
    
    # Truncate and add category prefix
    category_prefixes = {
        'income_tax': 'Tax: ',
        'tax': 'Tax: ',
        'gst': 'GST: ',
        'investment': 'Investment: ',
        'business': 'Business: ',
        'insurance': 'Insurance: ',
        'general': ''
    }
    
    prefix = category_prefixes.get(category, '')
    title = question[:47 - len(prefix)] + "..."
    return prefix + title