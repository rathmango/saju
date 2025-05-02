import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import openai
import json
import matplotlib.font_manager as fm
import platform
import re
import html  # HTML 이스케이프 라이브러리 추가
import uuid  # 고유 ID 생성 라이브러리 추가
from supabase import create_client  # Supabase 클라이언트 추가

# 지역별 시차 데이터 (동경 127.5도 기준, 분:초 형식)
REGION_TIME_OFFSET = {
    # 서울/경기
    "서울특별시": 2.05,    # 2분 5초
    "인천광역시": 5.22,
    "경기도 수원시": 2.54,
    "경기도 성남시": 2.10,
    "경기도 고양시": 3.10,
    "경기도 용인시": 1.45,
    "경기도 부천시": 4.10,
    "경기도 안산시": 3.50,
    "경기도 남양주시": 1.20,
    "경기도 안양시": 3.15,
    "경기도 화성시": 3.28,
    "경기도 평택시": 3.25,
    "경기도 의정부시": 1.50,
    "경기도 시흥시": 4.05,
    "경기도 파주시": 3.40,
    "경기도 김포시": 4.28,
    "경기도 광명시": 3.45,
    "경기도 광주시": 1.15,
    "경기도 군포시": 3.30,
    "경기도 이천시": 0.25,
    "경기도 오산시": 2.58,
    "경기도 하남시": 1.45,
    "경기도 양주시": 1.35,
    "경기도 구리시": 1.30,
    "경기도 안성시": 2.38,
    "경기도 포천시": 0.55,
    "경기도 의왕시": 3.05,
    "경기도 여주시": 0.10,
    "경기도 양평군": -0.20,
    "경기도 동두천시": 1.45,
    "경기도 과천시": 2.50,
    "경기도 가평군": -0.05,
    "경기도 연천군": 2.25,
    
    # 강원도
    "강원특별자치도 춘천시": -1.48,
    "강원특별자치도 원주시": -0.55,
    "강원특별자치도 강릉시": -5.25,
    "강원특별자치도 동해시": -5.58,
    "강원특별자치도 태백시": -4.40,
    "강원특별자치도 속초시": -4.20,
    "강원특별자치도 삼척시": -5.45,
    "강원특별자치도 홍천군": -2.20,
    "강원특별자치도 횡성군": -1.30,
    "강원특별자치도 영월군": -3.10,
    "강원특별자치도 평창군": -3.30,
    "강원특별자치도 정선군": -4.15,
    "강원특별자치도 철원군": 0.20,
    "강원특별자치도 화천군": -1.10,
    "강원특별자치도 양구군": -2.25,
    "강원특별자치도 인제군": -3.05,
    "강원특별자치도 고성군": -4.35,
    "강원특별자치도 양양군": -4.55,
    
    # 충청북도
    "충청북도 청주시": 0.45,
    "충청북도 충주시": -0.15,
    "충청북도 제천시": -1.25,
    "충청북도 보은군": 0.30,
    "충청북도 옥천군": 0.05,
    "충청북도 영동군": -0.40,
    "충청북도 증평군": 0.25,
    "충청북도 진천군": 1.10,
    "충청북도 괴산군": -0.30,
    "충청북도 음성군": 0.20,
    "충청북도 단양군": -2.10,
    
    # 충청남도
    "충청남도 천안시": 2.15,
    "충청남도 공주시": 2.55,
    "충청남도 보령시": 4.40,
    "충청남도 아산시": 2.45,
    "충청남도 서산시": 5.25,
    "충청남도 논산시": 2.35,
    "충청남도 계룡시": 2.30,
    "충청남도 당진시": 4.05,
    "충청남도 금산군": 1.45,
    "충청남도 부여군": 3.35,
    "충청남도 서천군": 4.20,
    "충청남도 청양군": 3.25,
    "충청남도 홍성군": 4.15,
    "충청남도 예산군": 3.50,
    "충청남도 태안군": 5.45,
    
    # 전라북도
    "전라북도 전주시": 4.12,
    "전라북도 군산시": 5.40,
    "전라북도 익산시": 4.55,
    "전라북도 정읍시": 5.20,
    "전라북도 남원시": 3.15,
    "전라북도 김제시": 5.05,
    "전라북도 완주군": 4.05,
    "전라북도 진안군": 3.25,
    "전라북도 무주군": 2.35,
    "전라북도 장수군": 2.55,
    "전라북도 임실군": 3.50,
    "전라북도 순창군": 4.05,
    "전라북도 고창군": 6.10,
    "전라북도 부안군": 5.45,
    
    # 전라남도
    "전라남도 목포시": 7.25,
    "전라남도 여수시": 4.15,
    "전라남도 순천시": 3.50,
    "전라남도 나주시": 6.15,
    "전라남도 광양시": 3.25,
    "전라남도 담양군": 5.10,
    "전라남도 곡성군": 4.35,
    "전라남도 구례군": 3.20,
    "전라남도 고흥군": 4.50,
    "전라남도 보성군": 5.05,
    "전라남도 화순군": 5.25,
    "전라남도 장흥군": 5.55,
    "전라남도 강진군": 6.25,
    "전라남도 해남군": 7.15,
    "전라남도 영암군": 6.35,
    "전라남도 무안군": 7.05,
    "전라남도 함평군": 6.45,
    "전라남도 영광군": 6.30,
    "전라남도 장성군": 5.45,
    "전라남도 완도군": 6.15,
    "전라남도 진도군": 7.45,
    "전라남도 신안군": 7.50,
    
    # 경상북도
    "경상북도 포항시": -5.10,
    "경상북도 경주시": -4.25,
    "경상북도 김천시": -0.50,
    "경상북도 안동시": -2.35,
    "경상북도 구미시": -1.45,
    "경상북도 영주시": -2.15,
    "경상북도 영천시": -3.45,
    "경상북도 상주시": -1.25,
    "경상북도 문경시": -1.10,
    "경상북도 경산시": -3.30,
    "경상북도 군위군": -2.55,
    "경상북도 의성군": -2.40,
    "경상북도 청송군": -3.55,
    "경상북도 영양군": -3.40,
    "경상북도 영덕군": -5.25,
    "경상북도 청도군": -3.15,
    "경상북도 고령군": -2.05,
    "경상북도 성주군": -1.55,
    "경상북도 칠곡군": -2.20,
    "경상북도 예천군": -1.50,
    "경상북도 봉화군": -2.45,
    "경상북도 울진군": -5.45,
    "경상북도 울릉군": -8.20,

    # 경상남도
    "경상남도 창원시": -2.05,
    "경상남도 진주시": -0.55,
    "경상남도 통영시": -1.50,
    "경상남도 사천시": -0.40,
    "경상남도 김해시": -2.35,
    "경상남도 밀양시": -2.50,
    "경상남도 거제시": -2.20,
    "경상남도 양산시": -3.05,
    "경상남도 의령군": -1.25,
    "경상남도 함안군": -1.40,
    "경상남도 창녕군": -2.15,
    "경상남도 고성군": -1.20,
    "경상남도 남해군": -0.30,
    "경상남도 하동군": -0.15,
    "경상남도 산청군": -0.05,
    "경상남도 함양군": 0.10,
    "경상남도 거창군": 0.25,
    "경상남도 합천군": -1.05,
    
    # 제주도
    "제주특별자치도 제주시": 8.35,
    "제주특별자치도 서귀포시": 8.25,
    
    # 광역시
    "부산광역시": -2.15,
    "대구광역시": -3.10,
    "광주광역시": 5.45,
    "대전광역시": 1.45,
    "울산광역시": -4.05,
    "세종특별자치시": 2.05,
}

# 입력 필드 초기화 상태 추가
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# 지역 시차 보정 함수
def adjust_birth_time_by_region(year, month, day, hour, minute, region):
    """지역별 시차를 고려하여 생시를 보정합니다 (동경 127.5도 기준)"""
    if region not in REGION_TIME_OFFSET:
        return hour, minute, day, month, year  # 지원되지 않는 지역은 보정하지 않음
    
    # 지역 오프셋 구하기 (분과 초)
    offset = REGION_TIME_OFFSET[region]
    offset_minutes = int(offset)
    offset_seconds = int((offset - offset_minutes) * 60)
    
    # datetime 객체 생성
    birth_datetime = datetime(year, month, day, hour, minute)
    
    # 오프셋 적용 (양수면 더하고, 음수면 빼기)
    adjusted_datetime = birth_datetime + timedelta(minutes=offset_minutes, seconds=offset_seconds)
    
    # 결과 반환
    return (adjusted_datetime.hour, 
            adjusted_datetime.minute, 
            adjusted_datetime.day, 
            adjusted_datetime.month, 
            adjusted_datetime.year)

# 보정 결과 표시용 함수
def format_time_adjustment(original_time, adjusted_time):
    """시간 보정 결과를 사용자 친화적으로 표시합니다"""
    orig_year, orig_month, orig_day, orig_hour, orig_minute = original_time
    adj_year, adj_month, adj_day, adj_hour, adj_minute = adjusted_time
    
    # 날짜/시간 형식으로 표시
    orig_str = f"{orig_year}년 {orig_month}월 {orig_day}일 {orig_hour:02d}시 {orig_minute:02d}분"
    adj_str = f"{adj_year}년 {adj_month}월 {adj_day}일 {adj_hour:02d}시 {adj_minute:02d}분"
    
    # 변경 여부 확인
    if orig_str == adj_str:
        return f"입력하신 시간: {orig_str}\n보정 필요 없음"
    else:
        return f"입력하신 시간: {orig_str}\n만세력 기준 보정된 시간: {adj_str} (동경 127.5도 기준)"

# .env 파일 로드
load_dotenv()

# OpenAI API 키 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Supabase 설정
def setup_supabase():
    """Supabase 클라이언트를 설정합니다."""
    try:
        # Streamlit Cloud에서는 st.secrets 사용
        supabase_url = st.secrets.get("SUPABASE_URL", None)
        supabase_key = st.secrets.get("SUPABASE_KEY", None)
        
        # 로컬 개발 환경에서는 환경 변수 사용 가능
        if not supabase_url or not supabase_key:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            # 설정이 없으면 None 반환, 로깅 비활성화
            return None
            
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Supabase 설정 오류: {str(e)}")
        return None

# 세션 ID 설정
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 대화 로깅 함수
def log_conversation(user_input, assistant_response):
    """사용자와 어시스턴트의 대화를 Supabase에 로깅합니다."""
    try:
        supabase = setup_supabase()
        if not supabase:
            return  # Supabase 연결 실패 시 조용히 반환
        
        # 사용자 정보 추출 (사주 데이터가 있는 경우)
        user_info = {}
        if 'saju_data' in st.session_state and st.session_state.saju_data:
            original_info = st.session_state.saju_data.get("원본정보", {})
            if isinstance(original_info, dict):
                user_info = {
                    "year": original_info.get("year", ""),
                    "month": original_info.get("month", ""),
                    "day": original_info.get("day", ""),
                    "hour": original_info.get("hour", ""),
                    "gender": original_info.get("gender", ""),
                    "is_lunar": original_info.get("is_lunar", False)
                }
        
        # 메타데이터 추가
        metadata = {
            "app_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Supabase에 데이터 삽입
        result = supabase.table("saju_conversations").insert({
            "session_id": st.session_state.session_id,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "user_info": user_info,
            "metadata": metadata
        }).execute()
        
        return result
    except Exception as e:
        print(f"로깅 오류: {str(e)}")
        return None

# API 키 없을 경우 안내 메시지 표시 함수
def check_api_key():
    if not OPENAI_API_KEY:
        st.warning("""
        OpenAI API 키가 설정되지 않았습니다. 다음 단계를 따라 설정해주세요:
        
        1. 프로젝트 폴더에 '.env' 파일을 생성하세요
        2. 파일에 다음 내용을 추가하세요: `OPENAI_API_KEY=your-api-key-here`
        3. 앱을 재시작하세요
        """)
        return False
    return True

# 애플리케이션 설정
st.set_page_config(page_title="사주 계산기", page_icon="🔮", layout="wide")

# 세션 상태 초기화
if 'saju_data' not in st.session_state:
    st.session_state.saju_data = None
    
# 메시지 세션 상태 초기화 및 마이그레이션
if 'messages' not in st.session_state:
    st.session_state.messages = []
else:
    # 기존 메시지가 있으면 필요한 필드 추가
    migrated_messages = []
    for i, msg in enumerate(st.session_state.messages):
        if isinstance(msg, dict):
            if "id" not in msg and "role" in msg and "content" in msg:
                msg["id"] = f"legacy_msg_{i}"
            migrated_messages.append(msg)
    st.session_state.messages = migrated_messages
    
if 'message_id_counter' not in st.session_state:
    st.session_state.message_id_counter = 0
if 'analysis_guide' not in st.session_state:
    # analysisguide.md 파일 읽기
    try:
        with open('analysisguide.md', 'r', encoding='utf-8') as file:
            st.session_state.analysis_guide = file.read()
    except Exception as e:
        st.session_state.analysis_guide = "분석 가이드를 불러오지 못했습니다: " + str(e)
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False

# 스트림 응답 개선 함수 - 상단에 함수 정의!
def stream_response(response, message_placeholder):
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

# 마크다운 전처리 함수
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

# ================ 사주 분석 함수 ================
def analyze_saju_with_llm(prompt, messages=None, stream=True):
    """OpenAI API를 사용하여 사주를 분석합니다."""
    try:
        if not OPENAI_API_KEY:
            return "API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."
        
        # API 키를 환경 변수로 설정
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # 직접 HTTP 요청을 통해 OpenAI API 호출
        conversation = []
        
        # 시스템 메시지 설정
        system_message = {
            "role": "system", 
            "content": "당신은 사주명리학의 최고 전문가로서, 사주팔자를 깊이 있게 분석할 수 있습니다. 한국의 전통 사주 이론을 기반으로 정확하고 통찰력 있는 분석을 제공하세요. 사용자가 질문하지 않은 내용까지 너무 장황하게 설명하지 마세요."
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
                "Authorization": f"Bearer {OPENAI_API_KEY}"
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

# ================ 유틸리티 함수 ================
def get_lunar_date(solar_year, solar_month, solar_day):
    """양력을 음력으로 변환"""
    url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo'
    params = {
        'serviceKey': 'lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X/gHbvyM+2W1DlEv3ViocMaq8+0YB1H2jkYPhnYlNl4hZQj23JnA==',
        'solYear': str(solar_year),
        'solMonth': str(solar_month).zfill(2),
        'solDay': str(solar_day).zfill(2)
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        result_code = root.find('.//resultCode').text
        
        if result_code != '00':
            result_msg = root.find('.//resultMsg').text
            return {'error': True, 'message': f"API 오류: {result_code} - {result_msg}"}
        
        items = root.findall('.//item')
        if not items:
            return {'error': True, 'message': "결과 없음"}
            
        item = items[0]
        
        result = {
            'error': False,
            'lunYear': item.find('lunYear').text,
            'lunMonth': item.find('lunMonth').text,
            'lunDay': item.find('lunDay').text,
            'lunLeapmonth': item.find('lunLeapmonth').text,
            'solWeek': item.find('solWeek').text,
            'lunSecha': item.find('lunSecha').text if item.find('lunSecha') is not None else "",
            'lunWolgeon': item.find('lunWolgeon').text if item.find('lunWolgeon') is not None else "",
            'lunIljin': item.find('lunIljin').text if item.find('lunIljin') is not None else "",
            'solJd': item.find('solJd').text if item.find('solJd') is not None else ""
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': True, 'message': f"요청 오류: {str(e)}"}
    except ET.ParseError:
        return {'error': True, 'message': "XML 파싱 오류"}
    except Exception as e:
        return {'error': True, 'message': f"오류 발생: {str(e)}"}

def get_solar_date(lunar_year, lunar_month, lunar_day, lunar_leap_month="0"):
    """음력을 양력으로 변환"""
    url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getSolCalInfo'
    params = {
        'serviceKey': 'lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X/gHbvyM+2W1DlEv3ViocMaq8+0YB1H2jkYPhnYlNl4hZQj23JnA==',
        'lunYear': str(lunar_year),
        'lunMonth': str(lunar_month).zfill(2),
        'lunDay': str(lunar_day).zfill(2),
        'lunLeapmonth': lunar_leap_month  # 평달:0, 윤달:1
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        result_code = root.find('.//resultCode').text
        
        if result_code != '00':
            result_msg = root.find('.//resultMsg').text
            return {'error': True, 'message': f"API 오류: {result_code} - {result_msg}"}
        
        items = root.findall('.//item')
        if not items:
            return {'error': True, 'message': "결과 없음"}
            
        item = items[0]
        
        result = {
            'error': False,
            'solYear': item.find('solYear').text,
            'solMonth': item.find('solMonth').text,
            'solDay': item.find('solDay').text,
            'solWeek': item.find('solWeek').text if item.find('solWeek') is not None else "",
            'solLeapyear': item.find('solLeapyear').text if item.find('solLeapyear') is not None else "",
            'lunSecha': item.find('lunSecha').text if item.find('lunSecha') is not None else "",
            'lunWolgeon': item.find('lunWolgeon').text if item.find('lunWolgeon') is not None else "",
            'lunIljin': item.find('lunIljin').text if item.find('lunIljin') is not None else "",
            'solJd': item.find('solJd').text if item.find('solJd') is not None else ""
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': True, 'message': f"요청 오류: {str(e)}"}
    except ET.ParseError:
        return {'error': True, 'message': "XML 파싱 오류"}
    except Exception as e:
        return {'error': True, 'message': f"오류 발생: {str(e)}"}

def get_stem_branch_year(year):
    """연도로부터 천간과 지지 계산"""
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    
    return stems[stem_idx], branches[branch_idx]

def get_stem_branch_month(year_stem, month):
    """연간과 월로부터 월주 천간지지 계산"""
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "자", "축"]
    
    # 월의 지지는 간단하게 계산됨
    branch = branches[month - 1]
    
    # 연간에 따른 월간 결정
    stem_map = {
        "갑": [2, 4, 6, 8, 0, 2, 4, 6, 8, 0, 2, 4],
        "을": [4, 6, 8, 0, 2, 4, 6, 8, 0, 2, 4, 6],
        "병": [6, 8, 0, 2, 4, 6, 8, 0, 2, 4, 6, 8],
        "정": [8, 0, 2, 4, 6, 8, 0, 2, 4, 6, 8, 0],
        "무": [0, 2, 4, 6, 8, 0, 2, 4, 6, 8, 0, 2],
        "기": [2, 4, 6, 8, 0, 2, 4, 6, 8, 0, 2, 4],
        "경": [4, 6, 8, 0, 2, 4, 6, 8, 0, 2, 4, 6],
        "신": [6, 8, 0, 2, 4, 6, 8, 0, 2, 4, 6, 8],
        "임": [8, 0, 2, 4, 6, 8, 0, 2, 4, 6, 8, 0],
        "계": [0, 2, 4, 6, 8, 0, 2, 4, 6, 8, 0, 2]
    }
    
    stem_idx = stem_map[year_stem][month - 1]
    stem = stems[stem_idx]
    
    return stem, branch

def get_stem_branch_day(year, month, day):
    """연월일로부터 일주 천간지지 계산"""
    # 1900년 1월 1일은 음력으로 경인년 12월 초하루
    # 이 날의 일간은 '경'
    base_date = date(1900, 1, 1)
    target_date = date(year, month, day)
    days_passed = (target_date - base_date).days
    
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    stem_idx = (days_passed % 10)
    branch_idx = (days_passed % 12)
    
    return stems[stem_idx], branches[branch_idx]

def get_stem_branch_hour(day_stem, hour):
    """일간과 시간으로부터 시주 천간지지 계산"""
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 시간에 따른 지지 결정
    branch_map = {
        0: 0, 1: 0,     # 23:00-01:59 자(子)
        2: 1, 3: 1,     # 02:00-03:59 축(丑)
        4: 2, 5: 2,     # 04:00-05:59 인(寅)
        6: 3, 7: 3,     # 06:00-07:59 묘(卯)
        8: 4, 9: 4,     # 08:00-09:59 진(辰)
        10: 5, 11: 5,   # 10:00-11:59 사(巳)
        12: 6, 13: 6,   # 12:00-13:59 오(午)
        14: 7, 15: 7,   # 14:00-15:59 미(未)
        16: 8, 17: 8,   # 16:00-17:59 신(申)
        18: 9, 19: 9,   # 18:00-19:59 유(酉)
        20: 10, 21: 10, # 20:00-21:59 술(戌)
        22: 11, 23: 11  # 22:00-22:59 해(亥)
    }
    
    branch_idx = branch_map[hour]
    branch = branches[branch_idx]
    
    # 일간에 따른 시간 천간 결정
    stem_map = {
        "갑": [0, 2, 4, 6, 8, 0, 2, 4, 6, 8, 0, 2],
        "을": [1, 3, 5, 7, 9, 1, 3, 5, 7, 9, 1, 3],
        "병": [2, 4, 6, 8, 0, 2, 4, 6, 8, 0, 2, 4],
        "정": [3, 5, 7, 9, 1, 3, 5, 7, 9, 1, 3, 5],
        "무": [4, 6, 8, 0, 2, 4, 6, 8, 0, 2, 4, 6],
        "기": [5, 7, 9, 1, 3, 5, 7, 9, 1, 3, 5, 7],
        "경": [6, 8, 0, 2, 4, 6, 8, 0, 2, 4, 6, 8],
        "신": [7, 9, 1, 3, 5, 7, 9, 1, 3, 5, 7, 9],
        "임": [8, 0, 2, 4, 6, 8, 0, 2, 4, 6, 8, 0],
        "계": [9, 1, 3, 5, 7, 9, 1, 3, 5, 7, 9, 1]
    }
    
    stem_idx = stem_map[day_stem][branch_idx]
    stem = stems[stem_idx]
    
    return stem, branch

def get_five_elements(stem_or_branch):
    """천간 또는 지지에 따른 오행 반환"""
    elements_map = {
        "갑": "목", "을": "목", 
        "병": "화", "정": "화", 
        "무": "토", "기": "토",
        "경": "금", "신": "금", 
        "임": "수", "계": "수",
        "자": "수", "해": "수", 
        "인": "목", "묘": "목",
        "사": "화", "오": "화", 
        "진": "토", "술": "토", "축": "토", "미": "토",
        "신": "금", "유": "금"
    }
    
    return elements_map.get(stem_or_branch, "")

def get_twelve_life_forces(day_stem, branch):
    """일간과 지지에 따른 십이운성 계산"""
    twelve_forces = ["장생", "목욕", "관대", "임관", "대왕", "쇠", "병", "사", "묘", "절", "태", "양"]
    
    # 일간별 장생 시작점
    start_points = {
        "갑": "해", "을": "해",  # 목 일간
        "병": "인", "정": "인",  # 화 일간
        "무": "묘", "기": "묘",  # 토 일간
        "경": "오", "신": "오",  # 금 일간
        "임": "신", "계": "신"   # 수 일간
    }
    
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 양간(陽干)은 순행, 음간(陰干)은 역행
    directions = {
        "갑": 1, "을": -1, "병": 1, "정": -1, "무": 1, 
        "기": -1, "경": 1, "신": -1, "임": 1, "계": -1
    }
    
    start_branch = start_points[day_stem]
    start_idx = branches.index(start_branch)
    branch_idx = branches.index(branch)
    direction = directions[day_stem]
    
    if direction > 0:
        force_idx = (branch_idx - start_idx) % 12
    else:
        force_idx = (start_idx - branch_idx) % 12
    
    return twelve_forces[force_idx]

def calculate_major_fortune(year_stem, month_stem, month_branch, birth_day, birth_month, birth_year, gender):
    """대운 계산"""
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 간지에서 양간(陽干)과 음간(陰干) 판별
    is_yang_stem = stems.index(year_stem) % 2 == 0
    
    # 성별과 양간/음간에 따른 방향 결정 (남양여음 순행, 남음여양 역행)
    direction = 1 if (gender == "남" and is_yang_stem) or (gender == "여" and not is_yang_stem) else -1
    
    # 대운 시작 나이 계산 (간단한 예시: 실제로는 절입일 계산 필요)
    # 실제 구현에서는 절입일 계산 로직 추가 필요
    start_age = 10  # 단순화: 10살부터 시작
    
    month_stem_idx = stems.index(month_stem)
    month_branch_idx = branches.index(month_branch)
    
    major_fortunes = []
    for i in range(10):  # 10개 대운 계산
        next_stem_idx = (month_stem_idx + i*direction) % 10
        next_branch_idx = (month_branch_idx + i*direction) % 12
        
        next_stem = stems[next_stem_idx]
        next_branch = branches[next_branch_idx]
        
        start_year = birth_year + start_age + i*10
        end_year = start_year + 9
        
        major_fortunes.append({
            "간지": next_stem + next_branch,
            "시작연령": start_age + i*10,
            "시작년도": start_year,
            "종료년도": end_year
        })
    
    return major_fortunes

def count_five_elements(saju):
    """사주에 포함된 오행 개수 계산"""
    elements = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    
    # 천간 오행 개수
    for stem in [saju["연주"][0], saju["월주"][0], saju["일주"][0], saju["시주"][0]]:
        element = get_five_elements(stem)
        if element:
            elements[element] += 1
    
    # 지지 오행 개수
    for branch in [saju["연주"][1], saju["월주"][1], saju["일주"][1], saju["시주"][1]]:
        element = get_five_elements(branch)
        if element:
            elements[element] += 1
    
    return elements

def calculate_saju(year, month, day, hour, gender, is_lunar=False):
    """사주 계산"""
    # 원본 날짜 정보 저장
    original_date = {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "gender": gender,
        "is_lunar": is_lunar
    }
    
    if is_lunar:
        # 음력일 경우 양력으로 변환
        solar_info = get_solar_date(year, month, day)
        if not solar_info.get('error', True):
            year = int(solar_info['solYear'])
            month = int(solar_info['solMonth'])
            day = int(solar_info['solDay'])
    
    # 연주 계산
    year_stem, year_branch = get_stem_branch_year(year)
    
    # 월주 계산
    month_stem, month_branch = get_stem_branch_month(year_stem, month)
    
    # 일주 계산
    day_stem, day_branch = get_stem_branch_day(year, month, day)
    
    # 시주 계산
    hour_stem, hour_branch = get_stem_branch_hour(day_stem, hour)
    
    # 일간 확인
    day_master = day_stem
    
    # 간지 조합
    year_pillars = year_stem + year_branch
    month_pillars = month_stem + month_branch
    day_pillars = day_stem + day_branch
    hour_pillars = hour_stem + hour_branch
    
    # 십이운성 계산
    year_life_force = get_twelve_life_forces(day_stem, year_branch)
    month_life_force = get_twelve_life_forces(day_stem, month_branch)
    day_life_force = get_twelve_life_forces(day_stem, day_branch)
    hour_life_force = get_twelve_life_forces(day_stem, hour_branch)
    
    # 대운 계산
    major_fortunes = calculate_major_fortune(
        year_stem, month_stem, month_branch, day, month, year, gender
    )
    
    saju = {
        "연주": year_pillars,
        "월주": month_pillars,
        "일주": day_pillars,
        "시주": hour_pillars,
        "일간": day_master,
        "십이운성": {
            "연주": year_life_force,
            "월주": month_life_force,
            "일주": day_life_force,
            "시주": hour_life_force
        },
        "대운": major_fortunes,
        "원본정보": original_date,  # 원본 날짜 정보 추가
        "양력정보": {  # 변환된 양력 정보 추가
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "gender": gender
        }
    }
    
    # 오행 개수 계산
    elements_count = count_five_elements(saju)
    saju["오행개수"] = elements_count
    
    return saju

# ================ Streamlit UI ================
# 사이드바에 설정 추가
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 상태 확인
    is_api_key_set = check_api_key()
    
    if is_api_key_set:
        st.success("✅ 사주 상세 분석이 가능한 상태입니다")
    
    st.markdown("---")
    st.markdown("### 📝 앱 정보")
    st.markdown("이 앱은 한국 전통 사주명리학을 기반으로 사주를 계산하고 분석합니다.")

# 탭 구조 제거 - 하나의 흐름으로 구성
st.title("🔮 사주 계산기 & 분석")

# 사주 계산 영역
st.markdown("### 📅 생년월일 입력")
st.markdown("생년월일시와 성별을 입력하면 사주의 모든 요소를 계산해줍니다.")

with st.form("birth_info_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        # 음력/양력 선택
        calendar_type = st.radio("날짜 유형", ["양력", "음력"])
        is_lunar = calendar_type == "음력"
        
        # 날짜 입력
        birth_date = st.date_input(
            "생년월일",
            datetime.now().date(),
            min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31)
        )
        
        # 음력 윤달 선택 (음력 선택 시)
        lunar_leap_month = "0"
        if is_lunar:
            is_leap_month = st.checkbox("윤달입니까?")
            if is_leap_month:
                lunar_leap_month = "1"
        
        # 시간 입력
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            birth_hour = st.selectbox(
                "태어난 시(時)",
                list(range(24)),
                format_func=lambda x: f"{x:02d}시"
            )
        with time_col2:
            birth_minute = st.selectbox(
                "태어난 분(分)",
                list(range(0, 60, 1)),
                format_func=lambda x: f"{x:02d}분"
            )
        
        # 지역 선택
        region_category = st.selectbox(
            "태어난 지역(광역)",
            [
                "서울/경기/인천",
                "강원도",
                "충청북도",
                "충청남도/세종",
                "전라북도",
                "전라남도",
                "경상북도",
                "경상남도/부산/울산",
                "제주도",
                "광역시"
            ]
        )
        
        # 선택한 카테고리에 따라 세부 지역 옵션 필터링
        filtered_regions = []
        if region_category == "서울/경기/인천":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() 
                              if region.startswith("서울") or region.startswith("경기도") or region.startswith("인천")]
        elif region_category == "강원도":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() if region.startswith("강원")]
        elif region_category == "충청북도":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() if region.startswith("충청북도")]
        elif region_category == "충청남도/세종":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() 
                              if region.startswith("충청남도") or region.startswith("세종")]
        elif region_category == "전라북도":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() if region.startswith("전라북도")]
        elif region_category == "전라남도":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() if region.startswith("전라남도")]
        elif region_category == "경상북도":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() if region.startswith("경상북도")]
        elif region_category == "경상남도/부산/울산":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() 
                              if region.startswith("경상남도") or region.startswith("부산") or region.startswith("울산")]
        elif region_category == "제주도":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() if region.startswith("제주")]
        elif region_category == "광역시":
            filtered_regions = [region for region in REGION_TIME_OFFSET.keys() 
                              if region.endswith("광역시") and not (region.startswith("부산") or region.startswith("울산"))]
            filtered_regions.append("세종특별자치시")
        
        birth_region = st.selectbox("태어난 지역(시/군)", filtered_regions)
        
        # 성별 입력
        gender = st.radio("성별", ["남", "여"])
        
    with col2:
        st.markdown("### 태어난 시간대")
        st.markdown("""
        - 자시(子時): 23:00 ~ 01:00 (쥐)
        - 축시(丑時): 01:00 ~ 03:00 (소)
        - 인시(寅時): 03:00 ~ 05:00 (호랑이)
        - 묘시(卯時): 05:00 ~ 07:00 (토끼)
        - 진시(辰時): 07:00 ~ 09:00 (용)
        - 사시(巳時): 09:00 ~ 11:00 (뱀)
        - 오시(午時): 11:00 ~ 13:00 (말)
        - 미시(未時): 13:00 ~ 15:00 (양)
        - 신시(申時): 15:00 ~ 17:00 (원숭이)
        - 유시(酉時): 17:00 ~ 19:00 (닭)
        - 술시(戌時): 19:00 ~ 21:00 (개)
        - 해시(亥時): 21:00 ~ 23:00 (돼지)
        """)
        
        st.markdown("### 지역별 시차 보정")
        st.info("""
        각 지역별 시차는 동경 127.5도를 기준으로 보정됩니다.
        이는 만세력 등의 전통 역법에서 사용하는 표준 경도로,
        현재 시차와는 다를 수 있습니다.
        
        지역에 따라 실제 출생 시간이 사주 계산에 사용되는 
        시간과 차이가 있을 수 있습니다.
        """)
    
    submit_button = st.form_submit_button("사주 계산하기")

# 사주 계산 처리
if submit_button:
    try:
        # 입력된 날짜 가져오기
        year = birth_date.year
        month = birth_date.month
        day = birth_date.day
        minute = birth_minute  # 분 값 추가
        region = birth_region  # 지역 값 추가
        
        # 원본 시간 저장
        original_time = (year, month, day, birth_hour, minute)
        
        # 지역에 따른 시간 보정 적용
        adjusted_hour, adjusted_minute, adjusted_day, adjusted_month, adjusted_year = adjust_birth_time_by_region(
            year, month, day, birth_hour, minute, region
        )
        
        # 보정된 시간 정보
        adjusted_time = (adjusted_year, adjusted_month, adjusted_day, adjusted_hour, adjusted_minute)
        
        # 보정 결과 안내 메시지
        adjustment_message = format_time_adjustment(original_time, adjusted_time)
        
        # 보정된 시간으로 사주 계산
        saju_data = calculate_saju(
            adjusted_year, adjusted_month, adjusted_day, adjusted_hour, gender, is_lunar
        )
        
        # 원본 시간과 보정된 시간 정보 추가
        saju_data["원본시간"] = {"year": year, "month": month, "day": day, "hour": birth_hour, "minute": minute}
        saju_data["보정시간"] = {"year": adjusted_year, "month": adjusted_month, "day": adjusted_day, "hour": adjusted_hour, "minute": adjusted_minute}
        saju_data["지역"] = region
        
        # 사주 데이터 세션 상태에 저장
        st.session_state.saju_data = saju_data
        
        # 결과 표시
        st.success("사주가 계산되었습니다.")
        
        # 시간 보정 결과 표시
        st.info(adjustment_message)
        
        # 사주 정보 테이블 표시
        st.markdown("### 사주팔자")
        st.markdown(f"**일간(일주 천간)**: {saju_data['일간']}")
        
        # 사주 팔자 표 생성
        saju_df = pd.DataFrame({
            "구분": ["천간", "지지", "십이운성"],
            "연주": [saju_data["연주"][0], saju_data["연주"][1], saju_data["십이운성"]["연주"]],
            "월주": [saju_data["월주"][0], saju_data["월주"][1], saju_data["십이운성"]["월주"]],
            "일주": [saju_data["일주"][0], saju_data["일주"][1], saju_data["십이운성"]["일주"]],
            "시주": [saju_data["시주"][0], saju_data["시주"][1], saju_data["십이운성"]["시주"]],
        })
        st.table(saju_df)
        
        # 오행 분포 그래프
        st.markdown("### 오행 분포")
        
        # 데이터 준비
        elements = saju_data["오행개수"]
        elements_labels = list(elements.keys())
        elements_values = list(elements.values())
        
        # 색상 매핑
        colors = {"목": "#00CC00", "화": "#FF0000", "토": "#FFCC00", "금": "#FFFF00", "수": "#0000FF"}
        chart_colors = [colors[element] for element in elements_labels]
        
        # Streamlit 내장 차트
        elements_df = pd.DataFrame({
            "오행": elements_labels,
            "개수": elements_values
        })
        
        st.bar_chart(elements_df.set_index("오행"))
        
        # 대운 표시
        st.markdown("### 대운")
        
        # 대운 정보를 데이터프레임으로 변환
        major_fortunes_df = pd.DataFrame(saju_data["대운"])
        # 나이대 열 추가
        major_fortunes_df["나이대"] = major_fortunes_df.apply(
            lambda row: f"{row['시작연령']} ~ {row['시작연령'] + 9}세", axis=1
        )
        # 필요한 열만 선택하고 순서 변경
        major_fortunes_df = major_fortunes_df[["나이대", "간지", "시작년도", "종료년도"]]
        # 테이블 표시
        st.table(major_fortunes_df)
    
    except Exception as e:
        st.error(f"사주 계산 중 오류가 발생했습니다: {str(e)}")
    
    st.markdown("""
    **참고 사항**:
    - 이 계산기는 한국 사주명리학의 기본 원리를 바탕으로 계산합니다.
    - 지역별 시차는 동경 127.5도를 기준으로 보정됩니다.
    - 실제 전문적인 사주 분석을 위해서는 더 많은 요소들이 고려되어야 합니다.
    """)

# 사주 분석 챗봇 영역
st.markdown("---")
st.markdown("## 💬 사주 분석 챗봇")

if not OPENAI_API_KEY:
    st.warning("사주 분석을 위해 OpenAI API 키가 필요합니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
elif st.session_state.saju_data is None:
    st.info("먼저 위에서 사주를 계산해주세요.")
else:
    # 메시지 제출 함수
    def submit_message(user_input):
        try:
            if not user_input.strip():
                return
            
            # 메시지 중복 방지를 위한 검사
            # 직전 메시지와 동일한 내용이면 무시
            if st.session_state.messages and len(st.session_state.messages) > 0:
                last_messages = [msg for msg in st.session_state.messages if msg.get("role") == "user"]
                if last_messages and last_messages[-1].get("content") == user_input:
                    return  # 직전 사용자 메시지와 동일하면 무시
            
            # 사용자 메시지 추가 (고유 ID 부여)
            st.session_state.message_id_counter += 1
            user_msg_id = f"msg_{st.session_state.message_id_counter}"
            st.session_state.messages.append({"role": "user", "content": user_input, "id": user_msg_id})
            
            # 분석 가이드와 사주 데이터를 포함한 시스템 컨텍스트
            saju_data = st.session_state.saju_data
            
            # 현재 날짜와 시간 정보 가져오기
            current_time = datetime.now()
            current_time_str = current_time.strftime("%Y년 %m월 %d일 %H시 %M분")
            
            # 생년월일 정보 가져오기
            birth_info = ""
            if "원본정보" in saju_data:
                info = saju_data["원본정보"]
                date_type = "음력" if info["is_lunar"] else "양력"
                birth_info = f"{info['year']}년 {info['month']}월 {info['day']}일 {info['hour']}시 ({date_type}), 성별: {info['gender']}"
            else:
                # 이전 버전 호환성
                양력정보 = saju_data["양력정보"]
                birth_info = f"{양력정보['year']}년 {양력정보['month']}월 {양력정보['day']}일 {양력정보['hour']}시 (양력), 성별: {양력정보['gender']}"
            
            # 지역 및 시간 보정 정보 추가
            region_info = ""
            time_adjustment_info = ""
            if "지역" in saju_data:
                region_info = f"출생지역: {saju_data['지역']}"
                
                # 보정 시간 정보가 있는 경우
                if "원본시간" in saju_data and "보정시간" in saju_data:
                    orig = saju_data["원본시간"]
                    adj = saju_data["보정시간"]
                    
                    # 원본 시간과 보정된 시간이 다른 경우에만 표시
                    if orig != adj:
                        orig_str = f"{orig['year']}년 {orig['month']}월 {orig['day']}일 {orig['hour']}시 {orig['minute']}분"
                        adj_str = f"{adj['year']}년 {adj['month']}월 {adj['day']}일 {adj['hour']}시 {adj['minute']}분"
                        time_adjustment_info = f"원본 시간: {orig_str}\n보정된 시간: {adj_str} (동경 127.5도 기준)"
            
            system_context = f"""
            현재 시간: {current_time_str}
            
            당신은 사주명리학의 최고 전문가입니다. 다음 사주 데이터를 기반으로 질문에 최대한 상세히 답변하세요:
            - 생년월일시: {birth_info}
            - {region_info}
            {time_adjustment_info}
            - 연주: {saju_data['연주']}
            - 월주: {saju_data['월주']}
            - 일주: {saju_data['일주']}
            - 시주: {saju_data['시주']}
            - 일간: {saju_data['일간']}
            - 오행 분포: {saju_data['오행개수']}
            - 십이운성: {saju_data['십이운성']}
            - 대운: {saju_data['대운']}
            
            반드시 아래의 '분석 가이드라인' 전체 내용을 참고하여 최대한 상세히 답변하세요:
            - 분석 가이드라인:
            {st.session_state.analysis_guide}
            """
            
            # 기존 메시지 중 시스템 메시지 대체
            context_messages = [{"role": "system", "content": system_context}]
            # 사용자 메시지 추가 (ID 필드 제외)
            for msg in st.session_state.messages:
                if msg["role"] != "system":
                    context_messages.append({"role": msg["role"], "content": msg["content"]})
            
            # 응답 생성
            with st.spinner("응답 작성 중..."):
                # 스트리밍 응답을 위한 플레이스홀더
                temp_placeholder = st.empty()
                
                # Stream API 호출 (기존 메시지도 컨텍스트로 포함)
                response = analyze_saju_with_llm(user_input, context_messages)
                
                # 스트리밍 응답 처리
                full_response = stream_response(response, temp_placeholder)
                
                # 대화 기록에 추가 (고유 ID 부여)
                st.session_state.message_id_counter += 1
                assistant_msg_id = f"msg_{st.session_state.message_id_counter}"
                st.session_state.messages.append({"role": "assistant", "content": full_response, "id": assistant_msg_id})
                
                # Supabase에 대화 로깅
                log_conversation(user_input, full_response)
            
            # 재실행하여 UI 업데이트
            st.rerun()
        except Exception as e:
            st.error(f"메시지 처리 중 오류가 발생했습니다: {str(e)}")

    # 챗봇 UI 개선
    st.markdown("""
    <style>
    .chat-container {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
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

    # 대화 초기화 버튼 (상단으로 이동)
    col1, col2 = st.columns([4, 1])
    with col2:
        # 초기화 콜백 함수 설정
        if 'reset_chat_clicked' not in st.session_state:
            st.session_state.reset_chat_clicked = False
        if 'reset_in_progress' not in st.session_state:
            st.session_state.reset_in_progress = False
            
        # 초기화 콜백 함수
        def handle_reset_chat():
            if not st.session_state.reset_in_progress:
                st.session_state.reset_chat_clicked = True
                st.session_state.reset_in_progress = True
            
        st.button("🔄 대화 초기화", on_click=handle_reset_chat, key="reset_chat_button")
        
        # 버튼 클릭 처리
        if st.session_state.reset_chat_clicked and st.session_state.reset_in_progress:
            # 모든 메시지와 관련 상태 초기화
            st.session_state.messages = []
            st.session_state.message_id_counter = 0
            st.session_state.last_input = ""
            st.session_state.input_text = ""
            st.session_state.reset_chat_clicked = False
            st.session_state.reset_in_progress = False
            st.rerun()

    # 채팅 메시지 표시 (고정된 높이의 컨테이너에)
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 사주에 대해 궁금한 점을 물어보세요. 사주 분석 시작하기 버튼을 클릭하여 기본 분석을 받아보세요.")
        
        # 메시지 표시
        for msg in st.session_state.messages:
            try:
                if not isinstance(msg, dict):
                    continue
                    
                msg_role = msg.get("role", "")
                msg_content = msg.get("content", "")
                msg_id = msg.get("id", str(uuid.uuid4()))
                
                if not msg_content:  # 내용이 없으면 표시하지 않음
                    continue
                    
                # 메시지 내용을 안전하게 이스케이프하고 줄바꿈 처리
                safe_content = html.escape(msg_content).replace('\n', '<br/>')
                    
                if msg_role == "user":
                    # 사용자 메시지 표시
                    st.markdown(f"""
                    <div class="chat-container user-message" id="msg_{msg_id}">
                        <strong>👤 나:</strong>
                        <div class="chat-msg-content">{safe_content}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif msg_role == "assistant":
                    # 어시스턴트 메시지 표시
                    st.markdown(f"""
                    <div class="chat-container assistant-message" id="msg_{msg_id}">
                        <strong>🔮 사주 분석가:</strong>
                        <div class="chat-msg-content">{safe_content}</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                # 오류 발생 시 간단히 표시하고 계속 진행
                st.error(f"메시지 표시 오류: {str(e)[:100]}")
                continue
    
    # 입력 영역 (하단에 고정)
    st.markdown("### 질문하기")
    
    # 입력 필드와 버튼 분리
    col1, col2 = st.columns([5, 1])
    
    # 콜백 함수 - 입력 처리를 위한 상태 변수 초기화
    if 'submit_clicked' not in st.session_state:
        st.session_state.submit_clicked = False
    if 'last_input' not in st.session_state:
        st.session_state.last_input = ""
    
    # 입력값 변경 감지 콜백 함수
    def process_input():
        # 입력값이 변경되면 세션 상태에 저장
        if "temp_input" in st.session_state:
            st.session_state.input_text = st.session_state.temp_input
    
    # 버튼 콜백 함수 
    def handle_submit():
        # 입력값이 있고 이전 입력과 다른 경우에만 처리
        current_input = st.session_state.input_text.strip()
        if current_input and current_input != st.session_state.last_input:
            st.session_state.submit_clicked = True
            st.session_state.last_input = current_input
            # 입력값 초기화를 위한 값 설정
            st.session_state.input_text = ""
    
    # 입력 필드 (세션 상태를 통해 관리)
    with col1:
        st.text_area(
            "사주에 대해 궁금한 점을 입력하세요:",
            key="temp_input",
            value=st.session_state.input_text,
            on_change=process_input,
            height=100,
            placeholder="예: '제 성격은 어떤가요?', '건강운은 어떤가요?', '적합한 직업은 무엇인가요?'",
            label_visibility="collapsed"
        )
    
    # 제출 버튼
    with col2:
        st.button("💬 대화하기", on_click=handle_submit, key="submit_chat_button")
    
    # 팁
    st.caption("💡 **팁**: 메시지를 입력한 후 대화하기 버튼을 클릭하세요.")
    
    # 버튼이 클릭되었고 입력값이 있는 경우 처리
    if st.session_state.submit_clicked:
        # 마지막 저장된 입력값 사용
        current_input = st.session_state.last_input.strip()
        if current_input:
            # 메시지 제출
            submit_message(current_input)
        # 제출 플래그 초기화
        st.session_state.submit_clicked = False

# 초기 분석 시작 버튼
if not st.session_state.messages:
    # 분석 시작 콜백 함수 설정 변수
    if 'start_analysis_clicked' not in st.session_state:
        st.session_state.start_analysis_clicked = False
    if 'analysis_in_progress' not in st.session_state:
        st.session_state.analysis_in_progress = False
        
    # 분석 시작 콜백 함수
    def handle_start_analysis():
        # 이미 진행 중이면 무시
        if not st.session_state.analysis_in_progress:
            st.session_state.start_analysis_clicked = True
            st.session_state.analysis_in_progress = True
        
    if st.button("🔮 사주 분석 시작하기", on_click=handle_start_analysis, key="start_analysis_button_tab2"):
        pass  # 콜백으로 처리하므로 여기서는 아무것도 하지 않음
    
    # 버튼 클릭 시 실제 처리
    if st.session_state.start_analysis_clicked and st.session_state.analysis_in_progress:
        try:
            with st.spinner("사주를 분석 중입니다..."):
                # 분석 가이드와 사주 데이터를 포함한 초기 프롬프트 구성
                saju_data = st.session_state.saju_data
                
                # 현재 날짜와 시간 정보 가져오기
                current_time = datetime.now()
                current_time_str = current_time.strftime("%Y년 %m월 %d일 %H시 %M분")
                
                # 생년월일 정보 가져오기
                birth_info = ""
                if "원본정보" in saju_data:
                    info = saju_data["원본정보"]
                    date_type = "음력" if info["is_lunar"] else "양력"
                    birth_info = f"{info['year']}년 {info['month']}월 {info['day']}일 {info['hour']}시 ({date_type}), 성별: {info['gender']}"
                else:
                    # 이전 버전 호환성
                    양력정보 = saju_data["양력정보"]
                    birth_info = f"{양력정보['year']}년 {양력정보['month']}월 {양력정보['day']}일 {양력정보['hour']}시 (양력), 성별: {양력정보['gender']}"
                
                # 지역 및 시간 보정 정보 추가
                region_info = ""
                time_adjustment_info = ""
                if "지역" in saju_data:
                    region_info = f"출생지역: {saju_data['지역']}"
                    
                    # 보정 시간 정보가 있는 경우
                    if "원본시간" in saju_data and "보정시간" in saju_data:
                        orig = saju_data["원본시간"]
                        adj = saju_data["보정시간"]
                        
                        # 원본 시간과 보정된 시간이 다른 경우에만 표시
                        if orig != adj:
                            orig_str = f"{orig['year']}년 {orig['month']}월 {orig['day']}일 {orig['hour']}시 {orig['minute']}분"
                            adj_str = f"{adj['year']}년 {adj['month']}월 {adj['day']}일 {adj['hour']}시 {adj['minute']}분"
                            time_adjustment_info = f"원본 시간: {orig_str}\n보정된 시간: {adj_str} (동경 127.5도 기준)"
                
                initial_prompt = f"""
                현재 시간: {current_time_str}
                
                다음은 사주 데이터입니다:
                - 생년월일시: {birth_info}
                - {region_info}
                {time_adjustment_info}
                - 연주: {saju_data['연주']}
                - 월주: {saju_data['월주']}
                - 일주: {saju_data['일주']}
                - 시주: {saju_data['시주']}
                - 일간: {saju_data['일간']}
                - 오행 분포: {saju_data['오행개수']}
                - 십이운성: {saju_data['십이운성']}
                - 대운: {saju_data['대운']}
                
                다음은 사주 분석 가이드라인입니다:
                {st.session_state.analysis_guide}
                
                위 가이드라인에 따라 이 사주에 대한 간략한 첫 인상과 이 사주의 가장 특징적인 부분을 알려주세요. 
                그리고 어떤 항목들에 대해 더 자세히 알고 싶은지 물어봐주세요.
                """
                
                # 스트리밍 응답을 위한 플레이스홀더
                with st.empty():
                    with st.spinner("사주를 분석 중입니다..."):
                        # Stream API 호출
                        response = analyze_saju_with_llm(initial_prompt)
                        
                        # 스트리밍 응답 처리를 위한 임시 컨테이너
                        temp_placeholder = st.empty()
                        full_response = stream_response(response, temp_placeholder)
                        
                        # 대화 기록에 추가
                        st.session_state.message_id_counter += 1
                        user_msg_id = f"msg_{st.session_state.message_id_counter}"
                        st.session_state.messages.append({"role": "user", "content": "사주 분석을 시작해주세요.", "id": user_msg_id})
                        
                        st.session_state.message_id_counter += 1
                        assistant_msg_id = f"msg_{st.session_state.message_id_counter}"
                        st.session_state.messages.append({"role": "assistant", "content": full_response, "id": assistant_msg_id})
                        
                        # Supabase에 대화 로깅
                        log_conversation("사주 분석을 시작해주세요.", full_response)
                
                # 플래그 초기화
                st.session_state.start_analysis_clicked = False
                st.session_state.analysis_in_progress = False
                
                # 재실행하여 UI 업데이트
                st.rerun()
        except Exception as e:
            st.error(f"사주 분석 시작 중 오류가 발생했습니다: {str(e)}")
            # 오류 발생 시에도 플래그 초기화
            st.session_state.start_analysis_clicked = False
            st.session_state.analysis_in_progress = False 