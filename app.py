import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date
import pandas as pd
import os
from openai import OpenAI
import time
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI API 키 가져오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

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
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'analysis_guide' not in st.session_state:
    # analysisguide.md 파일 읽기
    try:
        with open('analysisguide.md', 'r', encoding='utf-8') as file:
            st.session_state.analysis_guide = file.read()
    except Exception as e:
        st.session_state.analysis_guide = "분석 가이드를 불러오지 못했습니다: " + str(e)

# 스트림 응답 개선 함수 - 상단에 함수 정의!
def stream_response(response, message_placeholder):
    """스트림 응답을 더 부드럽게 표시하는 함수"""
    full_response = ""
    
    # 단일 텍스트 영역 생성
    response_area = message_placeholder.empty()
    
    # 응답이 문자열인 경우 (오류 메시지 등)
    if isinstance(response, str):
        # 마크다운 대신 일반 텍스트로 표시 (HTML 해석 방지)
        response_area.text(response)
        return response
    
    # 스트리밍 응답인 경우
    for chunk in response:
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
            content_chunk = chunk.choices[0].delta.content
            full_response += content_chunk
            # 마크다운 대신 일반 텍스트로 표시 (HTML 해석 방지)
            response_area.text(full_response)
    
    return full_response

# ================ 사주 분석 함수 ================
def analyze_saju_with_llm(prompt, messages=None, stream=True):
    """OpenAI API를 사용하여 사주를 분석합니다."""
    try:
        if not OPENAI_API_KEY:
            return "API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        
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
        
        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=conversation,
            temperature=0.7,
            max_tokens=32768,  # 높은 값 설정
            stream=stream
        )
        
        if stream:
            return response
        else:
            return response.choices[0].message.content
    
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
        st.success("✅ API 키가 .env 파일에서 로드되었습니다.")
    
    st.markdown("---")
    st.markdown("### 📝 앱 정보")
    st.markdown("이 앱은 한국 전통 사주명리학을 기반으로 사주를 계산하고 분석합니다.")
    st.markdown("OpenAI API를 사용하여 전문적인 사주 해석을 제공합니다.")

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
        birth_hour = st.selectbox(
            "태어난 시(時)",
            list(range(24)),
            format_func=lambda x: f"{x:02d}:00 ~ {x:02d}:59"
        )
        
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
    
    submit_button = st.form_submit_button("사주 계산하기")

# 사주 계산 처리
if submit_button:
    year = birth_date.year
    month = birth_date.month
    day = birth_date.day
    
    with st.spinner("계산 중..."):
        if is_lunar:
            # 음력 -> 양력 변환
            solar_info = get_solar_date(year, month, day, lunar_leap_month)
            if solar_info.get('error', True):
                st.error(f"음력 변환 중 오류가 발생했습니다: {solar_info.get('message', '알 수 없는 오류')}")
            else:
                solar_year = int(solar_info['solYear'])
                solar_month = int(solar_info['solMonth'])
                solar_day = int(solar_info['solDay'])
                
                st.success(f"음력 {year}년 {month}월 {day}일은 양력으로 {solar_year}년 {solar_month}월 {solar_day}일입니다.")
                
                # 사주 계산 (변환된 양력 기준)
                saju = calculate_saju(solar_year, solar_month, solar_day, birth_hour, gender, False)
                
                # 세션 상태에 사주 데이터 저장
                st.session_state.saju_data = saju
        else:
            # 양력 -> 음력 변환 (정보 표시용)
            lunar_info = get_lunar_date(year, month, day)
            if not lunar_info.get('error', True):
                st.success(f"양력 {year}년 {month}월 {day}일은 음력으로 {lunar_info['lunYear']}년 {lunar_info['lunMonth']}월 {lunar_info['lunDay']}일 ({lunar_info['lunLeapmonth']}달)입니다.")
            
            # 사주 계산
            saju = calculate_saju(year, month, day, birth_hour, gender, False)
            
            # 세션 상태에 사주 데이터 저장
            st.session_state.saju_data = saju
        
        # 결과 표시
        if st.session_state.saju_data:
            st.markdown("## 📊 사주 결과")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📋 기본 정보")
                
                # 기본 정보 테이블
                basic_info = {
                    "항목": ["생년월일", "시간", "성별", "일간(日干)"],
                    "값": [
                        f"{year}년 {month}월 {day}일 ({calendar_type})",
                        f"{birth_hour}시 ({birth_hour//2}{'짝' if birth_hour%2==0 else '홀'})",
                        gender,
                        f"{saju['일간']} ({get_five_elements(saju['일간'])})"
                    ]
                }
                st.table(pd.DataFrame(basic_info))
                
                # 사주 팔자 표시
                st.markdown("### 🔮 사주 팔자")
                saju_data = {
                    "구분": ["천간(天干)", "지지(地支)"],
                    "연주(年柱)": [saju["연주"][0], saju["연주"][1]],
                    "월주(月柱)": [saju["월주"][0], saju["월주"][1]],
                    "일주(日柱)": [saju["일주"][0], saju["일주"][1]],
                    "시주(時柱)": [saju["시주"][0], saju["시주"][1]]
                }
                st.table(pd.DataFrame(saju_data))
                
                # 십이운성 표시
                st.markdown("### 🌟 십이운성")
                twelve_forces = {
                    "구분": ["십이운성"],
                    "연주(年柱)": [saju["십이운성"]["연주"]],
                    "월주(月柱)": [saju["십이운성"]["월주"]],
                    "일주(日柱)": [saju["십이운성"]["일주"]],
                    "시주(時柱)": [saju["십이운성"]["시주"]]
                }
                st.table(pd.DataFrame(twelve_forces))
                
            with col2:
                # 오행 개수 표시
                st.markdown("### 🔥 오행 분석")
                elements = saju["오행개수"]
                
                elements_data = {
                    "오행": list(elements.keys()),
                    "개수": list(elements.values())
                }
                
                # bar_chart 대신 matplotlib 사용
                fig, ax = plt.figure(figsize=(10, 6)), plt.subplot()
                ohaeng = elements_data["오행"]
                counts = elements_data["개수"]
                colors = ['green', 'red', 'brown', 'gold', 'blue']  # 목(녹), 화(적), 토(갈), 금(황), 수(청)
                
                bars = ax.bar(ohaeng, counts, color=colors)
                ax.set_ylabel('개수')
                ax.set_title('오행 분포')
                
                # 각 막대 위에 값 표시
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                st.pyplot(fig)
                
                # 천간 오행
                stems_elements = {
                    "천간": [saju["연주"][0], saju["월주"][0], saju["일주"][0], saju["시주"][0]],
                    "오행": [
                        get_five_elements(saju["연주"][0]),
                        get_five_elements(saju["월주"][0]),
                        get_five_elements(saju["일주"][0]),
                        get_five_elements(saju["시주"][0])
                    ]
                }
                st.markdown("#### 천간 오행")
                st.table(pd.DataFrame(stems_elements))
                
                # 지지 오행
                branches_elements = {
                    "지지": [saju["연주"][1], saju["월주"][1], saju["일주"][1], saju["시주"][1]],
                    "오행": [
                        get_five_elements(saju["연주"][1]),
                        get_five_elements(saju["월주"][1]),
                        get_five_elements(saju["일주"][1]),
                        get_five_elements(saju["시주"][1])
                    ]
                }
                st.markdown("#### 지지 오행")
                st.table(pd.DataFrame(branches_elements))

            # 대운 표시
            st.markdown("### 🔄 대운 흐름")
            if saju["대운"]:
                fortunes_data = pd.DataFrame(saju["대운"])
                st.table(fortunes_data)
            else:
                st.info("대운 정보가 계산되지 않았습니다.")
            
            # 참고 정보
            st.markdown("### ℹ️ 참고 사항")
            st.info("""
            - 이 계산기는 한국 사주명리학의 기본 원리를 바탕으로 계산합니다.
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
    # 채팅 인터페이스를 위한 플레이스홀더
    chat_container = st.container()
    
    # 입력 폼
    with st.form(key="chat_form"):
        user_input = st.text_area(
            "질문을 입력하세요:",
            height=100,
            placeholder="사주에 대해 궁금한 점을 자유롭게 물어보세요. 예: '제 성격은 어떤가요?', '건강운은 어떤가요?', '적합한 직업은 무엇인가요?'"
        )
        submit_chat = st.form_submit_button("질문하기")
    
    # 초기 분석 시작 버튼
    start_analysis = st.button("🔮 사주 분석 시작하기", disabled=len(st.session_state.messages) > 0, key="start_analysis_button_tab2")
    
    # 대화 초기화 버튼
    if st.button("🔄 대화 초기화", key="reset_chat_button_tab2"):
        st.session_state.messages = []
        st.rerun()
    
    # 채팅 메시지 표시
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])
    
    # 사주 분석 시작하기 버튼 처리
    if start_analysis:
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
            
            initial_prompt = f"""
            현재 시간: {current_time_str}
            
            다음은 사주 데이터입니다:
            - 생년월일시: {birth_info}
            - 연주: {saju_data['연주']}
            - 월주: {saju_data['월주']}
            - 일주: {saju_data['일주']}
            - 시주: {saju_data['시주']}
            - 일간: {saju_data['일간']}
            - 오행 분포: {saju_data['오행개수']}
            - 십이운성: {saju_data['십이운성']}
            - 대운: {saju_data['대운'][:3]}
            
            다음은 사주 분석 가이드라인입니다:
            {st.session_state.analysis_guide}
            
            위 가이드라인에 따라 이 사주에 대한 간략한 첫 인상과 이 사주의 가장 특징적인 부분을 알려주세요. 
            그리고 어떤 항목들에 대해 더 자세히 알고 싶은지 물어봐주세요.
            """
            
            # 스트리밍 응답 표시
            message_placeholder = st.chat_message("assistant")
            
            # Stream API 호출
            response = analyze_saju_with_llm(initial_prompt)
            
            # 스트리밍 응답 처리
            full_response = stream_response(response, message_placeholder)
            
            # 대화 기록에 추가
            st.session_state.messages.append({"role": "user", "content": "사주 분석을 시작해주세요."})
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # 재실행하여 UI 업데이트
            st.rerun()
    
    # 사용자 입력 처리
    if submit_chat and user_input:
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # 사용자 메시지 표시
        st.chat_message("user").write(user_input)
        
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
        
        system_context = f"""
        현재 시간: {current_time_str}
        
        당신은 사주명리학의 최고 전문가입니다. 다음 사주 데이터를 기반으로 질문에 답변하세요:
        - 생년월일시: {birth_info}
        - 연주: {saju_data['연주']}
        - 월주: {saju_data['월주']}
        - 일주: {saju_data['일주']}
        - 시주: {saju_data['시주']}
        - 일간: {saju_data['일간']}
        - 오행 분포: {saju_data['오행개수']}
        - 십이운성: {saju_data['십이운성']}
        - 대운: {saju_data['대운'][:3]}
        
        분석 가이드라인:
        {st.session_state.analysis_guide}
        """
        
        # 기존 메시지 중 시스템 메시지 대체
        context_messages = [{"role": "system", "content": system_context}]
        # 사용자 메시지 추가
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                context_messages.append(msg)
        
        # 응답 생성
        with st.spinner("응답 작성 중..."):
            # 스트리밍 응답 표시
            message_placeholder = st.chat_message("assistant")
            
            # Stream API 호출 (기존 메시지도 컨텍스트로 포함)
            response = analyze_saju_with_llm(user_input, context_messages)
            
            # 스트리밍 응답 처리
            full_response = stream_response(response, message_placeholder)
            
            # 대화 기록에 추가
            st.session_state.messages.append({"role": "assistant", "content": full_response}) 