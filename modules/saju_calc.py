"""
사주 계산 관련 함수 (사주 기본 요소 계산, 천간, 지지, 오행, 십이운성 등)
"""
from datetime import datetime, date, timedelta
from modules.date_utils import get_lunar_date, get_solar_date
from modules.solar_terms import get_month_stem_branch

def get_stem_branch_year(year):
    """연도로부터 천간과 지지 계산"""
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    
    return stems[stem_idx], branches[branch_idx]

# 월주 계산은 solar_terms.py의 get_month_stem_branch 함수를 사용합니다

def get_stem_branch_day(year, month, day):
    """연월일로부터 일주 천간지지 계산"""
    # 1900년 1월 1일 = 갑술일(甲戌)
    # 갑(甲) = 0, 술(戌) = 10
    base_date = date(1900, 1, 1)
    target_date = date(year, month, day)
    days_passed = (target_date - base_date).days
    
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 1900.1.1 = 갑술일 기준으로 계산
    stem_idx = (days_passed + 0) % 10  # 갑(甲)부터 시작
    branch_idx = (days_passed + 10) % 12  # 술(戌)부터 시작
    
    return stems[stem_idx], branches[branch_idx]

def get_stem_branch_hour(day_stem, hour):
    """일간과 시간으로부터 시주 천간지지 계산"""
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    # 시간에 따른 지지 결정
    # 23시는 다음날 자시(子時)이므로 특별 처리
    branch_map = {
        0: 0, 1: 1,     # 00:00-01:59 자(子), 01:00-02:59 축(丑) 시작
        2: 1, 3: 2,     # 02:00-02:59 축(丑), 03:00-04:59 인(寅) 시작
        4: 2, 5: 3,     # 04:00-04:59 인(寅), 05:00-06:59 묘(卯) 시작
        6: 3, 7: 4,     # 06:00-06:59 묘(卯), 07:00-08:59 진(辰) 시작
        8: 4, 9: 5,     # 08:00-08:59 진(辰), 09:00-10:59 사(巳) 시작
        10: 5, 11: 6,   # 10:00-10:59 사(巳), 11:00-12:59 오(午) 시작
        12: 6, 13: 7,   # 12:00-12:59 오(午), 13:00-14:59 미(未) 시작
        14: 7, 15: 8,   # 14:00-14:59 미(未), 15:00-16:59 신(申) 시작
        16: 8, 17: 9,   # 16:00-16:59 신(申), 17:00-18:59 유(酉) 시작
        18: 9, 19: 10,  # 18:00-18:59 유(酉), 19:00-20:59 술(戌) 시작
        20: 10, 21: 11, # 20:00-20:59 술(戌), 21:00-22:59 해(亥) 시작
        22: 11, 23: 0   # 22:00-22:59 해(亥), 23:00-00:59 자(子) 시작
    }
    
    branch_idx = branch_map[hour]
    branch = branches[branch_idx]
    
    # 일간에 따른 시간 천간 결정 (오자둔법 - 五鼠遁法)
    # 갑기일: 갑자시 시작, 을경일: 병자시 시작, 병신일: 무자시 시작
    # 정임일: 경자시 시작, 무계일: 임자시 시작
    stem_map = {
        "갑": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],  # 갑자시부터 시작
        "을": [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],  # 병자시부터 시작
        "병": [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],  # 무자시부터 시작
        "정": [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],  # 경자시부터 시작
        "무": [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],  # 임자시부터 시작
        "기": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1],  # 갑자시부터 시작
        "경": [2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3],  # 병자시부터 시작
        "신": [4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5],  # 무자시부터 시작
        "임": [6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7],  # 경자시부터 시작
        "계": [8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]   # 임자시부터 시작
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
    
    # 월주 계산 (24절기 기준)
    month_stem, month_branch = get_month_stem_branch(year_stem, year, month, day)
    
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