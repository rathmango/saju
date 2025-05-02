"""
UI 스타일 및 챗봇 인터페이스 관련 헬퍼 함수
"""
import streamlit as st
import html
import json
import requests
import re

def add_styles():
    """스타일시트를 추가합니다."""
    st.markdown("""
    <style>
    /* 버튼 스타일 강화 */
    .stButton > button {
        background-color: #4F46E5;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    }

    .stButton > button:hover {
        background-color: #6366F1;
        box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
    }

    /* 버튼 강조 (사주 계산하기, 대화하기 등) */
    .highlight-button {
        transform: scale(1.05);
    }

    /* 다크모드 대응 */
    [data-theme="dark"] .stButton > button {
        background-color: #6366F1;
        color: white;
    }

    [data-theme="dark"] .stButton > button:hover {
        background-color: #818CF8;
    }

    /* 컬러풀한 강조 효과 */
    .title-gradient {
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        font-weight: bold;
    }

    /* 폼 영역 강화 */
    [data-testid="stForm"] {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 20px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* 헤더 스타일 강화 */
    h1, h2, h3 {
        font-weight: 600;
    }

    /* 채팅 컨테이너 스타일 */
    .chat-container {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        background-color: var(--background-color, white);
        color: var(--text-color, black);
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    
    /* 라이트 모드 */
    [data-theme="light"] .chat-container {
        background-color: white;
        color: #333333;
    }
    
    /* 다크 모드 */
    [data-theme="dark"] .chat-container {
        background-color: #262730;
        color: #ffffff;
        border: 1px solid #555555;
    }
    
    .user-message {
        border-left: 5px solid #1890ff;
    }
    .assistant-message {
        border-left: 5px solid #7c7c7c;
    }
    .chat-msg-content {
        white-space: pre-wrap;
        overflow-wrap: break-word;
        font-size: 16px;
        line-height: 1.7;
        margin-top: 8px;
    }
    .stTextArea textarea {
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

def stream_response(response, message_placeholder, in_chat_container=False):
    """스트림 응답을 더 부드럽게 표시하는 함수"""
    full_response = ""
    
    # 단일 텍스트 영역 생성
    response_area = message_placeholder.empty()
    
    # 응답이 문자열인 경우 (오류 메시지 등)
    if isinstance(response, str):
        # HTML 태그를 완전히 이스케이프
        escaped_response = html.escape(response)
        response_area.text(escaped_response)
        return response
    
    # 스트리밍 응답인 경우 (requests 스트리밍 응답)
    try:
        # requests의 스트림 응답 처리
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                # Server-Sent Events 형식에서 데이터 추출
                if line.startswith('data: ') and not line.startswith('data: [DONE]'):
                    json_str = line[6:]  # 'data: ' 부분 제거
                    try:
                        chunk = json.loads(json_str)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            if 'delta' in chunk['choices'][0] and 'content' in chunk['choices'][0]['delta']:
                                content = chunk['choices'][0]['delta']['content']
                                if content:
                                    full_response += content
                                    # HTML 태그를 완전히 이스케이프
                                    escaped_response = html.escape(full_response)
                                    response_area.text(escaped_response)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        error_msg = f"응답 처리 중 오류가 발생했습니다: {str(e)}\n\n원본 응답: {response.text if hasattr(response, 'text') else '응답 내용 없음'}"
        escaped_error = html.escape(error_msg)
        response_area.text(escaped_error)
    
    return full_response

def preprocess_markdown(text):
    """마크다운 텍스트를 전처리하여 줄바꿈 등의 문제를 해결합니다."""
    if not text:
        return ""
    
    # 타입 체크
    if not isinstance(text, str):
        try:
            text = str(text)
        except:
            return ""
        
    # HTML 태그 이스케이프
    text = html.escape(text)
    
    # 줄바꿈 처리 개선
    text = text.replace('\n\n\n', '\n\n')  # 과도한 줄바꿈 줄이기
    
    # 목록 앞 여백 줄이기
    text = re.sub(r'\n\n- ', '\n- ', text)
    text = re.sub(r'\n\n\d+\. ', '\n\d+\. ', text)
    
    # 특수문자 처리
    text = text.replace('•', '&#8226;')  # 불릿 포인트 처리
    
    return text 