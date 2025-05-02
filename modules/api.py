"""
외부 API 통신 관련 함수 (OpenAI API 등)
"""
import os
import requests
import json
import streamlit as st

def setup_openai_api():
    """OpenAI API 키를 가져옵니다."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        # 환경 변수에 없으면 streamlit secrets에서 가져오기
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    return api_key

def analyze_saju_with_llm(prompt, messages=None, stream=True):
    """OpenAI API를 사용하여 사주를 분석합니다."""
    try:
        api_key = setup_openai_api()
        if not api_key:
            return "API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."
        
        # 직접 HTTP 요청을 통해 OpenAI API 호출
        conversation = []
        
        # 시스템 메시지 설정
        system_message = {
            "role": "system", 
            "content": "당신은 사주명리학의 최고 전문가로서, 사주팔자를 깊이 있게 분석할 수 있습니다. 한국의 전통 사주 이론을 기반으로 정확하고 통찰력 있는 분석을 제공하세요. 사용자가 질문하지 않은 내용까지 너무 장황하게 설명하지 마세요. 또한 사용자가 질문한 내용에 맞게 좋은 말을 전달하려 애쓰지 마세요. 분석한 내용을 그대로 전달해야합니다."
        }
        conversation.append(system_message)
        
        # 이전 대화 내역이 있으면 추가
        if messages:
            conversation.extend(messages)
        
        # 사용자 메시지 추가
        conversation.append({"role": "user", "content": prompt})
        
        # OpenAI API 직접 호출
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": "gpt-4.1-mini",
                "messages": conversation,
                "temperature": 0.5,
                "max_tokens": 32768,
                "stream": stream
            }
            
            if not stream:
                # 스트리밍 없는 요청
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    return f"API 오류: {response.status_code} - {response.text}"
            else:
                # 스트리밍 요청
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    stream=True
                )
                
                if response.status_code == 200:
                    return response
                else:
                    return f"API 오류: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"API 직접 호출 오류: {str(e)}"
    
    except Exception as e:
        return f"분석 중 오류가 발생했습니다: {str(e)}"

def check_api_key():
    """API 키가 설정되어 있는지 확인합니다."""
    api_key = setup_openai_api()
    return bool(api_key) 