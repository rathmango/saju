"""
사주 계산 관련 함수 (사주 기본 요소 계산, 천간, 지지, 오행, 십이운성 등)
"""
from datetime import datetime, date, timedelta
from modules.date_utils import get_lunar_date, get_solar_date

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