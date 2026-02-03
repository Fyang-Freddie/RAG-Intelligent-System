from app.constants import LOG_PIPELINE_SUCCESS, LOG_PREFIX_PIPELINE
from app.utils.profiler import print_performance_summary
import logging
from app.controller.pipeline import run_search_pipeline
from app.services.document_processor import get_document_processor
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import json
import os
import time
import random
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

# File to store chat data (inside app/data/)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATA_FILE = os.path.join(DATA_DIR, 'chat_data.json')

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'chats': []}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/get_chats', methods=['GET'])
def get_chats():
    data = load_data()
    return jsonify({'chats': data['chats']})


@main.route('/create_chat', methods=['POST'])
def create_chat():
    data = load_data()
    new_chat_id = str(int(time.time() * 1000)) + str(random.randint(100, 999))
    new_chat = {
        'id': new_chat_id,
        'title': 'New Chat',
        'created_at': datetime.now().isoformat(),
        'messages': []
    }
    data['chats'].insert(0, new_chat)
    save_data(data)
    return jsonify({'chat': new_chat})


@main.route('/get_chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    data = load_data()
    chat = next((c for c in data['chats'] if c['id'] == chat_id), None)
    if chat:
        return jsonify({'chat': chat})
    return jsonify({'error': 'Chat not found'}), 404


@main.route('/send_message', methods=['POST'])
def send_message():
    req_data = request.get_json()
    chat_id = req_data.get('chat_id')
    message_text = req_data.get('message')
    file_content = req_data.get('file_content')  # Extracted text from file

    data = load_data()
    chat = next((c for c in data['chats'] if c['id'] == chat_id), None)

    if not chat:
        return jsonify({'error': 'Chat not found'}), 404

    # Combine message text with file content if provided
    full_message = message_text
    if file_content:
        full_message = f"{message_text}\n\n[Attached Document Content]:\n{file_content}"

    # Add user message
    user_message = {
        'role': 'user',
        'content': message_text,  # Store original message without file content
        'timestamp': datetime.now().strftime('%I:%M %p')
    }
    if file_content:
        user_message['has_attachment'] = True
        
    chat['messages'].append(user_message)

    # Update chat title if it's the first message
    if len(chat['messages']) == 1:
        chat['title'] = message_text[:50] + ('...' if len(message_text) > 50 else '')

    pipeline_start = time.time()
    
    # Generate AI response using full message (with file content if available)
    ai_response = run_search_pipeline(full_message)
    
    pipeline_time = time.time() - pipeline_start
    logger.info(f"{LOG_PREFIX_PIPELINE} {LOG_PIPELINE_SUCCESS} (⏱️ Total: {pipeline_time:.3f}s)")
        
    # Print performance summary after pipeline completes
    
    print_performance_summary()
    
    assistant_message = {
        'role': 'assistant',
        'content': ai_response,
        'timestamp': datetime.now().strftime('%I:%M %p')
    }
    chat['messages'].append(assistant_message)

    save_data(data)
    return jsonify({'success': True, 'chat': chat})


@main.route('/delete_chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    data = load_data()
    data['chats'] = [c for c in data['chats'] if c['id'] != chat_id]
    save_data(data)
    return jsonify({'status': 'success'})


@main.route('/rename_chat/<chat_id>', methods=['POST'])
def rename_chat(chat_id):
    req_data = request.get_json()
    new_title = req_data.get('title')

    data = load_data()
    chat = next((c for c in data['chats'] if c['id'] == chat_id), None)

    if chat:
        chat['title'] = new_title
        save_data(data)
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Chat not found'}), 404


@main.route('/process_file', methods=['POST'])
def process_file():
    """
    Process uploaded file (PDF, DOCX, TXT, images) and extract text content
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400
    
    # Get document processor
    processor = get_document_processor()
    
    # Check if file type is supported
    if not processor.is_supported(file.filename):
        supported = ', '.join(processor.get_supported_extensions())
        return jsonify({
            'success': False, 
            'error': f'Unsupported file type. Supported: {supported}'
        }), 400
    
    try:
        # Read file data
        file_data = file.read()
        
        # Process the file
        result = processor.process_file(file_data, secure_filename(file.filename))
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }), 500