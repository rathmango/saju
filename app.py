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
from manseryeok_utils import adjust_time_for_manseryeok, format_time_adjustment  # 만세력 시간 보정 유틸리티

# 지역별 경도/위도 데이터 (도.분 형식)
REGION_COORDINATES = {
    # 서울/경기
    "서울특별시": {"경도": 126.58, "위도": 37.33},  # 서울
    "인천광역시": {"경도": 126.42, "위도": 37.45},  # 인천
    "경기도 수원시": {"경도": 127.00, "위도": 37.16},  # 수원
    "경기도 성남시": {"경도": 127.08, "위도": 37.26},  # 성남
    "경기도 고양시": {"경도": 126.50, "위도": 37.39},  # 고양
    "경기도 용인시": {"경도": 127.12, "위도": 37.16},  # 용인
    "경기도 부천시": {"경도": 126.46, "위도": 37.29},  # 부천
    "경기도 안산시": {"경도": 126.50, "위도": 37.19},  # 안산
    "경기도 남양주시": {"경도": 127.12, "위도": 37.38},  # 남양주
    "경기도 안양시": {"경도": 126.57, "위도": 37.23},  # 안양
    "경기도 화성시": {"경도": 126.55, "위도": 37.12},  # 화성
    "경기도 평택시": {"경도": 127.06, "위도": 36.59},  # 평택
    "경기도 의정부시": {"경도": 127.02, "위도": 37.44},  # 의정부
    "경기도 시흥시": {"경도": 126.48, "위도": 37.22},  # 시흥
    "경기도 파주시": {"경도": 126.46, "위도": 37.45},  # 파주
    "경기도 김포시": {"경도": 126.43, "위도": 37.36},  # 김포
    "경기도 광명시": {"경도": 126.51, "위도": 37.28},  # 광명
    "경기도 광주시": {"경도": 127.15, "위도": 37.25},  # 광주
    "경기도 군포시": {"경도": 126.56, "위도": 37.21},  # 군포
    "경기도 이천시": {"경도": 127.26, "위도": 37.16},  # 이천
    "경기도 오산시": {"경도": 127.02, "위도": 37.09},  # 오산
    "경기도 하남시": {"경도": 127.12, "위도": 37.32},  # 하남
    "경기도 양주시": {"경도": 127.03, "위도": 37.47},  # 양주
    "경기도 구리시": {"경도": 127.08, "위도": 37.35},  # 구리
    "경기도 안성시": {"경도": 127.16, "위도": 37.00},  # 안성
    "경기도 포천시": {"경도": 127.12, "위도": 37.53},  # 포천
    "경기도 의왕시": {"경도": 126.58, "위도": 37.20},  # 의왕
    "경기도 여주시": {"경도": 127.38, "위도": 37.17},  # 여주
    "경기도 양평군": {"경도": 127.29, "위도": 37.29},  # 양평
    "경기도 동두천시": {"경도": 127.03, "위도": 37.54},  # 동두천
    "경기도 과천시": {"경도": 126.59, "위도": 37.25},  # 과천
    "경기도 가평군": {"경도": 127.30, "위도": 37.49},  # 가평
    "경기도 연천군": {"경도": 127.04, "위도": 38.05},  # 연천
    
    # 광역시
    "부산광역시": {"경도": 129.04, "위도": 35.10},  # 부산
    "대구광역시": {"경도": 128.36, "위도": 35.52},  # 대구
    "광주광역시": {"경도": 126.51, "위도": 35.09},  # 광주
    "대전광역시": {"경도": 127.23, "위도": 36.20},  # 대전
    "울산광역시": {"경도": 129.18, "위도": 35.32},  # 울산
    "세종특별자치시": {"경도": 127.17, "위도": 36.32},  # 세종
    
    # 제주도
    "제주특별자치도 제주시": {"경도": 126.32, "위도": 33.30},  # 제주
    "제주특별자치도 서귀포시": {"경도": 126.33, "위도": 33.15},  # 서귀포
    
    # 기본값 (서울 기준)
    "기본값": {"경도": 126.58, "위도": 37.33}  # 서울
}

# 지역별 시차 데이터 (동경 127.5도 기준, 분:초 형식)
REGION_TIME_OFFSET = {
    # 서울/경기
    "서울특별시": 2.05,    # 2분 5초
    "인천광역시": 5.22,
    # ... 기존 코드 유지 ...
}

# 주요 도시 경도 정보
CITY_LONGITUDE = {
    "서울특별시": 126.58,
    "부산광역시": 129.04,
    "대구광역시": 128.36,
    "인천광역시": 126.42,
    "광주광역시": 126.51,
    "대전광역시": 127.23,
    "울산광역시": 129.18,
    "세종특별자치시": 127.17,
    "제주특별자치도 제주시": 126.32
}

# 만세력 기준 경도 (동경 135도)
MANSERYEOK_STANDARD_LONGITUDE = 135.0

# 지역 시간 보정 함수 (만세력 기준)
def adjust_birth_time_for_manseryeok(year, month, day, hour, minute, region):
    """
    출생 시간을 만세력 기준(동경 135도)으로 보정합니다.
    
    Args:
        year, month, day, hour, minute: 출생 시간 정보
        region: 출생 지역
        
    Returns:
        tuple: 보정된 (시간, 분, 일, 월, 연도)
    """
    # 특수 기간 확인 (1908-04-01 ~ 1911-12-31, 1954-03-21 ~ 1961-08-09)
    special_period = False
    if (1908 <= year <= 1911) or (year == 1954 and month >= 3 and day >= 21) or \
       (1954 < year < 1961) or (year == 1961 and month <= 8 and day <= 9):
        special_period = True
        standard_longitude = 127.5  # 특수 기간에는 동경 127.5도 기준
    else:
        standard_longitude = MANSERYEOK_STANDARD_LONGITUDE  # 그 외에는 만세력 기준(동경 135도)

    # 출생 지역의 경도 정보 가져오기
    region_info = REGION_COORDINATES.get(region, REGION_COORDINATES["기본값"])
    region_longitude = region_info["경도"]
    
    # 시차 계산 (1도당 4분)
    longitude_diff = standard_longitude - region_longitude
    time_diff_minutes = longitude_diff * 4  # 1도당 약 4분의 시차
    
    # 분 단위로 시간 계산
    total_minutes = hour * 60 + minute
    adjusted_minutes = total_minutes + time_diff_minutes
    
    # 날짜 변경 처리
    adjusted_days = day
    adjusted_month = month
    adjusted_year = year
    
    # 음수 시간 처리 (전날로 변경)
    while adjusted_minutes < 0:
        adjusted_minutes += 24 * 60  # 하루 추가
        adjusted_days -= 1
        
        # 월 변경 처리
        if adjusted_days < 1:
            adjusted_month -= 1
            if adjusted_month < 1:
                adjusted_month = 12
                adjusted_year -= 1
            
            # 각 월의 마지막 날 계산
            if adjusted_month in [4, 6, 9, 11]:
                adjusted_days = 30
            elif adjusted_month == 2:
                # 윤년 계산
                if (adjusted_year % 4 == 0 and adjusted_year % 100 != 0) or (adjusted_year % 400 == 0):
                    adjusted_days = 29
                else:
                    adjusted_days = 28
            else:
                adjusted_days = 31
    
    # 24시간 초과 처리 (다음날로 변경)
    while adjusted_minutes >= 24 * 60:
        adjusted_minutes -= 24 * 60  # 하루 뺌
        adjusted_days += 1
        
        # 월 변경 처리
        days_in_month = 31
        if adjusted_month in [4, 6, 9, 11]:
            days_in_month = 30
        elif adjusted_month == 2:
            # 윤년 계산
            if (adjusted_year % 4 == 0 and adjusted_year % 100 != 0) or (adjusted_year % 400 == 0):
                days_in_month = 29
            else:
                days_in_month = 28
                
        if adjusted_days > days_in_month:
            adjusted_days = 1
            adjusted_month += 1
            if adjusted_month > 12:
                adjusted_month = 1
                adjusted_year += 1
    
    # 시와 분으로 변환
    adjusted_hour = int(adjusted_minutes // 60)
    adjusted_minute = int(adjusted_minutes % 60)
    
    return adjusted_hour, adjusted_minute, adjusted_days, adjusted_month, adjusted_year

# 보정 결과 표시용 함수 업데이트
def format_time_adjustment(original_time, adjusted_time, region):
    """시간 보정 결과를 사용자 친화적으로 표시합니다"""
    orig_year, orig_month, orig_day, orig_hour, orig_minute = original_time
    adj_year, adj_month, adj_day, adj_hour, adj_minute = adjusted_time
    
    # 지역 정보와 경도 가져오기
    region_info = REGION_COORDINATES.get(region, REGION_COORDINATES["기본값"])
    region_longitude = region_info["경도"]
    
    # 특수 기간 확인
    special_period = False
    if (1908 <= orig_year <= 1911) or (orig_year == 1954 and orig_month >= 3 and orig_day >= 21) or \
       (1954 < orig_year < 1961) or (orig_year == 1961 and orig_month <= 8 and orig_day <= 9):
        special_period = True
        standard_longitude = 127.5  # 특수 기간에는 동경 127.5도 기준
        standard_name = "구 한국표준시(동경 127도 30분)"
    else:
        standard_longitude = MANSERYEOK_STANDARD_LONGITUDE
        standard_name = "만세력 기준(동경 135도)"
    
    # 시차 계산 (분 단위)
    time_diff = (standard_longitude - region_longitude) * 4  # 1도당 약 4분의 시차
    time_diff_abs = abs(time_diff)
    time_diff_hours = int(time_diff_abs // 60)
    time_diff_minutes = int(time_diff_abs % 60)
    
    # 시차 문자열
    if time_diff >= 0:
        diff_str = f"느림 (약 {time_diff_hours}시간 {time_diff_minutes:02d}분)"
    else:
        diff_str = f"빠름 (약 {time_diff_hours}시간 {time_diff_minutes:02d}분)"
    
    # 원본 시간과 보정된 시간이 다른지 확인
    is_different = (orig_year != adj_year or orig_month != adj_month or 
                   orig_day != adj_day or orig_hour != adj_hour or 
                   orig_minute != adj_minute)
    
    # 결과 텍스트 생성
    orig_str = f"{orig_year}년 {orig_month}월 {orig_day}일 {orig_hour:02d}시 {orig_minute:02d}분"
    adj_str = f"{adj_year}년 {adj_month}월 {adj_day}일 {adj_hour:02d}시 {adj_minute:02d}분"
    
    result = f"입력하신 출생 시간: {orig_str} ({region}, 동경 약 {region_longitude}도)\n"
    result += f"사용된 기준시: {standard_name}\n"
    result += f"지역 시차: {diff_str}\n"
    
    if is_different:
        result += f"만세력 기준 시간: {adj_str}\n"
        result += "※ 사주 계산에는 보정된 시간이 사용됩니다."
    else:
        result += "시간 보정이 필요하지 않습니다."
    
    return result

# .env 파일 로드
load_dotenv()

# OpenAI API 키 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Supabase 설정
def setup_supabase():
    """Supabase 클라이언트를 설정합니다."""
    try:
        # 디버깅 위해 상태 출력
        print("Supabase 설정 확인 중...")
        
        # 1. Streamlit Cloud에서는 st.secrets 사용
        supabase_url = st.secrets.get("SUPABASE_URL", None)
        supabase_key = st.secrets.get("SUPABASE_KEY", None)
        
        # 디버깅 출력
        if supabase_url and supabase_key:
            print("Streamlit secrets에서 Supabase 설정을 찾았습니다.")
        
        # 2. 로컬 개발 환경에서는 환경 변수 사용 가능
        if not supabase_url or not supabase_key:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY")
            if supabase_url and supabase_key:
                print("환경 변수에서 Supabase 설정을 찾았습니다.")
        
        # 3. .env 파일에서 직접 로드
        if not supabase_url or not supabase_key:
            from dotenv import load_dotenv
            load_dotenv()  # .env 파일 다시 로드
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if supabase_url and supabase_key:
                print(".env 파일에서 Supabase 설정을 찾았습니다.")
        
        if not supabase_url or not supabase_key:
            print("Supabase 설정을 찾을 수 없습니다. 로깅이 비활성화됩니다.")
            return None
        
        # URL 형식 확인
        if not supabase_url.startswith('https://'):
            print(f"경고: Supabase URL이 올바른 형식이 아닙니다: {supabase_url}")
            
        client = create_client(supabase_url, supabase_key)
        print("Supabase 클라이언트가 성공적으로 생성되었습니다.")
        return client
    except Exception as e:
        print(f"Supabase 설정 오류: {str(e)}")
        import traceback
        print(traceback.format_exc())
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
            print("Supabase 연결 실패: 설정 값 없음")
            return  # Supabase 연결 실패 시 조용히 반환
        
        # 사용자 정보 추출 (사주 데이터가 있는 경우)
        user_info = {}
        if 'saju_data' in st.session_state and st.session_state.saju_data:
            saju_data = st.session_state.saju_data
            
            # 기본 정보
            original_info = saju_data.get("원본정보", {})
            if isinstance(original_info, dict):
                user_info = {
                    "year": original_info.get("year", ""),
                    "month": original_info.get("month", ""),
                    "day": original_info.get("day", ""),
                    "hour": original_info.get("hour", ""),
                    "gender": original_info.get("gender", ""),
                    "is_lunar": original_info.get("is_lunar", False)
                }
            
            # 분 정보 추가
            if "원본시간" in saju_data:
                user_info["minute"] = saju_data["원본시간"].get("minute", "")
            
            # 지역 정보 추가
            if "지역" in saju_data:
                region = saju_data["지역"]
                user_info["region"] = region
                
                # 광역 지역 추출 
                if region.startswith("서울") or region.startswith("부산") or region.startswith("대구") or \
                   region.startswith("인천") or region.startswith("광주") or region.startswith("대전") or \
                   region.startswith("울산") or region.startswith("세종"):
                    user_info["region_metro"] = region.split()[0]  # 첫 번째 단어 (예: "서울특별시")
                elif " " in region:
                    user_info["region_metro"] = region.split()[0]  # 첫 번째 단어 (예: "경기도")
                    user_info["region_city"] = region  # 전체 지역
                else:
                    user_info["region_metro"] = region
            
            # 만세력 보정 시간 추가
            if "보정시간" in saju_data:
                adjusted = saju_data["보정시간"]
                user_info["adjusted_year"] = adjusted.get("year", "")
                user_info["adjusted_month"] = adjusted.get("month", "")
                user_info["adjusted_day"] = adjusted.get("day", "")
                user_info["adjusted_hour"] = adjusted.get("hour", "")
                user_info["adjusted_minute"] = adjusted.get("minute", "")
        
        # 메타데이터 추가
        metadata = {
            "app_version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # 디버깅: 로깅 시도 출력
        print(f"로깅 시도: session_id={st.session_state.session_id}, 메시지 길이={len(user_input)}/{len(assistant_response)}")
        print(f"로깅 사용자 정보: {user_info}")
        
        # Supabase에 데이터 삽입
        result = supabase.table("saju_conversations").insert({
            "session_id": st.session_state.session_id,
            "user_input": user_input,
            "assistant_response": assistant_response,
            "user_info": user_info,
            "metadata": metadata
        }).execute()
        
        # 디버깅: 성공 출력
        print(f"로깅 성공: {result}")
        return result
    except Exception as e:
        print(f"로깅 오류 상세: {str(e)}")
        import traceback
        print(traceback.format_exc())
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
st.set_page_config(
    page_title="로컬 만세력 사주풀이", 
    page_icon="🔮", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# 로컬 만세력 사주풀이\n### 만세력 기반의 정확한 사주 계산 및 풀이\n전통 만세력을 기반으로 정확한 시간 보정을 통해 사주를 계산하고, AI가 사주를 실시간으로 분석해드립니다."
    }
)

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
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False

# 스트림릿 UI에 스타일 추가
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
</style>
""", unsafe_allow_html=True)

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
    st.header("⚙️ 로컬 만세력 사주풀이")
    
    # API 키 상태 확인
    is_api_key_set = check_api_key()
    
    if is_api_key_set:
        st.success("✅ 사주 상세 분석이 가능한 상태입니다")
    
    st.markdown("---")
    st.markdown("### 📝 앱 정보")
    st.markdown("""
    **로컬 만세력 사주풀이**는 한국 전통 만세력을 기반으로 정확한 사주를 계산하고 분석합니다.
    
    - ✅ 동경 135도 만세력 기준 시간 보정
    - ✅ 정밀한 지역별 경도 차이 계산
    - ✅ 실시간 AI 사주 풀이 채팅
    - ✅ 전문적인 사주명리학 분석 방법론 적용
    
    이 앱은 수천 년간 전해져 내려온 동양 전통 사주명리학의 지혜를 현대 AI 기술과 결합하여 보다 정확하고 심층적인 사주 풀이를 제공합니다.
    """)

# 스트림릿 UI에 스타일 추가
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
</style>
""", unsafe_allow_html=True)

# 탭 구조 제거 - 하나의 흐름으로 구성
st.title("🔮 로컬 만세력 사주풀이")
st.markdown("""
**로컬 만세력 사주풀이**는 한국 전통 만세력을 기반으로 정확한 시간 보정을 통해 사주를 계산하고, 
AI가 사주를 실시간으로 분석해드립니다. 수백 가지 사주 패턴과 법칙을 바탕으로 
깊이 있는 사주 해석을 제공합니다.
""")

# 사주 계산 영역
st.markdown("### 📅 생년월일 입력")
st.markdown("생년월일시와 성별을 입력하면 만세력 기준으로 정확히 보정된 사주의 모든 요소를 계산해드립니다.")

with st.form("birth_info_form"):
    col1, col2 = st.columns([3, 2])
    
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
            filtered_regions = [region for region in REGION_COORDINATES.keys() 
                              if region.startswith("서울") or region.startswith("경기도") or region.startswith("인천")]
        elif region_category == "강원도":
            filtered_regions = [region for region in REGION_COORDINATES.keys() if region.startswith("강원")]
        elif region_category == "충청북도":
            filtered_regions = [region for region in REGION_COORDINATES.keys() if region.startswith("충청북도")]
        elif region_category == "충청남도/세종":
            filtered_regions = [region for region in REGION_COORDINATES.keys() 
                              if region.startswith("충청남도") or region.startswith("세종")]
        elif region_category == "전라북도":
            filtered_regions = [region for region in REGION_COORDINATES.keys() if region.startswith("전라북도")]
        elif region_category == "전라남도":
            filtered_regions = [region for region in REGION_COORDINATES.keys() if region.startswith("전라남도")]
        elif region_category == "경상북도":
            filtered_regions = [region for region in REGION_COORDINATES.keys() if region.startswith("경상북도")]
        elif region_category == "경상남도/부산/울산":
            filtered_regions = [region for region in REGION_COORDINATES.keys() 
                              if region.startswith("경상남도") or region.startswith("부산") or region.startswith("울산")]
        elif region_category == "제주도":
            filtered_regions = [region for region in REGION_COORDINATES.keys() if region.startswith("제주")]
        elif region_category == "광역시":
            filtered_regions = [region for region in REGION_COORDINATES.keys() 
                              if region.endswith("광역시") and not (region.startswith("부산") or region.startswith("울산"))]
            filtered_regions.append("세종특별자치시")
        
        birth_region = st.selectbox("태어난 지역(시/군)", filtered_regions)
        
        # 성별 입력
        gender = st.radio("성별", ["남", "여"])
        
        # 제출 버튼을 여기로 이동 (강조 클래스 추가)
        st.markdown('<div class="highlight-button">', unsafe_allow_html=True)
        submit_button = st.form_submit_button("💫 사주 계산하기")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        # 만세력 보정 방법으로 변경하고 태어난 시간대 섹션을 통합
        with st.expander("ℹ️ 만세력 보정 방법", expanded=False):
            st.info("""
            각 지역별 시차는 만세력 기준인 동경 135도를 기준으로 보정됩니다.
            이는 전통 역법에서 사용하는 표준 경도로, 현대 표준시와는 다릅니다.
            
            지역에 따라 실제 출생 시간이 사주 계산에 사용되는 
            시간과 차이가 있을 수 있습니다. 예를 들어 서울에서
            15시에 출생한 경우, 만세력 기준으로는 약 15시 32분으로
            보정되어 사주가 계산됩니다.
            
            이 시간 보정은 지역의 경도 차이에 따라 결정됩니다(경도 1도당 4분 차이).
            
            <전통 십이지지 시간>
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

# 사주 계산 처리 (submit_button 위치가 변경되었으므로 나머지 코드는 그대로 유지)
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
        
        # 지역에 따른 시간 보정 적용 (만세력 기준 - 동경 135도)
        adjusted_hour, adjusted_minute, adjusted_day, adjusted_month, adjusted_year = adjust_time_for_manseryeok(
            year, month, day, birth_hour, minute, region
        )
        
        # 보정된 시간 정보
        adjusted_time = (adjusted_year, adjusted_month, adjusted_day, adjusted_hour, adjusted_minute)
        
        # 보정 결과 안내 메시지
        adjustment_message = format_time_adjustment(original_time, adjusted_time, region)
        
        st.success("사주 계산을 시작합니다. 입력값: " + str(adjusted_year) + "년 " + str(adjusted_month) + "월 " + str(adjusted_day) + "일 " + str(adjusted_hour) + "시 " + str(gender))
        
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
        
        # 기본 정보 테이블 추가
        st.markdown("## 📋 기본 정보")
        
        # 원본 정보
        if is_lunar:
            date_type = "음력"
        else:
            date_type = "양력"
            
        # 시간에 해당하는 십이지지 표시
        hours_to_zodiac = {
            0: "자(子)시", 
            1: "축(丑)시", 2: "축(丑)시", 
            3: "인(寅)시", 4: "인(寅)시", 
            5: "묘(卯)시", 6: "묘(卯)시", 
            7: "진(辰)시", 8: "진(辰)시", 
            9: "사(巳)시", 10: "사(巳)시", 
            11: "오(午)시", 12: "오(午)시", 
            13: "미(未)시", 14: "미(未)시", 
            15: "신(申)시", 16: "신(申)시", 
            17: "유(酉)시", 18: "유(酉)시", 
            19: "술(戌)시", 20: "술(戌)시", 
            21: "해(亥)시", 22: "해(亥)시",
            23: "자(子)시"
        }
        hour_zodiac = hours_to_zodiac.get(adjusted_hour, "")
        
        # 오행 정보
        five_elements_map = {
            "갑": "목", "을": "목", 
            "병": "화", "정": "화", 
            "무": "토", "기": "토", 
            "경": "금", "신": "금", 
            "임": "수", "계": "수"
        }
        day_master_element = five_elements_map.get(saju_data['일간'], "")
        
        # 기본 정보 표
        basic_info = [
            {"항목": "생년월일", "값": f"{year}년 {month}월 {day}일 ({date_type})"},
            {"항목": "시간", "값": f"{birth_hour}시 {minute}분 (입력 시간)"},
            {"항목": "보정된 시간", "값": f"{adjusted_hour}시 {adjusted_minute}분 ({hour_zodiac}) - 만세력 기준"},
            {"항목": "성별", "값": gender},
            {"항목": "일간(日干)", "값": f"{saju_data['일간']} ({day_master_element})"}
        ]
        basic_info_df = pd.DataFrame(basic_info)
        st.table(basic_info_df)
        
        # 사주 정보 테이블 표시
        st.markdown("### 사주팔자")
        st.markdown(f"**일간(일주 천간)**: {saju_data['일간']}")
        st.markdown("※ 아래 사주는 만세력 기준으로 보정된 시간을 바탕으로 계산되었습니다.")
        
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
        import traceback
        st.error(f"사주 계산 중 오류가 발생했습니다: {str(e)}")
        st.error(f"오류 상세 정보: {traceback.format_exc()}")
    
    st.markdown("""
    **참고 사항**:
    - 이 계산기는 한국 사주명리학의 기본 원리를 바탕으로 계산합니다.
    - 지역별 시차는 동경 127.5도를 기준으로 보정됩니다.
    - 실제 전문적인 사주 분석을 위해서는 더 많은 요소들이 고려되어야 합니다.
    """)

# 사주 분석 챗봇 영역
st.markdown("---")
st.markdown("## 💬 사주 분석 AI 채팅")
st.markdown("""
AI 사주 분석가가 만세력 기반으로 정확히 계산된 사주를 바탕으로 다양한 질문에 답변해드립니다.
수백 가지 사주 패턴과 법칙을 학습한 AI가 사주의 특성과 운세를 상세히 풀이해드립니다.
""")

if not OPENAI_API_KEY:
    st.warning("사주 분석을 위해 OpenAI API 키가 필요합니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
elif st.session_state.saju_data is None:
    st.info("먼저 위에서 사주를 계산해주세요.")
else:
    # 대화 초기화 버튼과 사주 분석 시작 버튼을 일렬로 배치
    col1, col2 = st.columns([1, 1])
    with col1:
        # 초기화 콜백 함수 설정
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
        
        st.markdown('<div class="highlight-button">', unsafe_allow_html=True)
        st.button("🔮 사주 분석 시작하기", on_click=handle_start_analysis, key="start_analysis_button_tab2")
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        st.markdown('<div class="highlight-button">', unsafe_allow_html=True)
        st.button("💬 대화하기", on_click=handle_submit, key="submit_chat_button")
        st.markdown('</div>', unsafe_allow_html=True)
    
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