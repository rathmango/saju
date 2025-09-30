"""
24절기(節氣) 계산 모듈
태양의 황경을 기준으로 정확한 절입일을 계산합니다.
"""
from datetime import datetime, timedelta
import math

def get_solar_longitude(year, month, day, hour=12):
    """
    태양의 황경(黃經) 계산
    간단한 근사 공식 사용 (정확도: ±1일)
    """
    # 율리우스일(Julian Day) 계산
    if month <= 2:
        year -= 1
        month += 12
    
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    
    JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour/24.0 + B - 1524.5
    
    # 율리우스 세기
    T = (JD - 2451545.0) / 36525.0
    
    # 태양의 평균 황경
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    L0 = L0 % 360
    
    # 태양의 평균 근점 이각
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    M = math.radians(M)
    
    # 이심률
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T
    
    # 중심차
    C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M)
    C += (0.019993 - 0.000101 * T) * math.sin(2 * M)
    C += 0.000289 * math.sin(3 * M)
    
    # 진황경
    true_longitude = L0 + C
    true_longitude = true_longitude % 360
    
    return true_longitude

def find_solar_term_date(year, target_longitude):
    """
    특정 황경에 해당하는 절기일 찾기
    
    Args:
        year: 연도
        target_longitude: 목표 황경 (0-360도)
    
    Returns:
        datetime: 절기일시
    """
    # 대략적인 시작 월 추정
    month = int(target_longitude / 30) + 1
    if month > 12:
        month -= 12
    
    # 해당 월의 1일부터 검색
    current_date = datetime(year if month >= 3 else year - 1, 
                           month if month >= 3 else month + 12 - 12, 1)
    
    # 황경이 목표값에 가장 가까운 날 찾기
    min_diff = 360
    best_date = current_date
    
    for day_offset in range(-5, 35):  # 전후 한 달 범위에서 검색
        test_date = current_date + timedelta(days=day_offset)
        longitude = get_solar_longitude(test_date.year, test_date.month, test_date.day)
        
        # 황경 차이 계산 (360도 경계 고려)
        diff = abs(longitude - target_longitude)
        if diff > 180:
            diff = 360 - diff
        
        if diff < min_diff:
            min_diff = diff
            best_date = test_date
    
    return best_date

def get_solar_term_for_date(year, month, day):
    """
    특정 날짜가 속한 음력 월 계산 (24절기 기준)
    
    Args:
        year, month, day: 양력 날짜
    
    Returns:
        int: 음력 월 (1-12)
    """
    # 12절기의 황경 (입춘부터 시작)
    solar_terms_longitude = [
        315,  # 1월 - 입춘 (立春)
        345,  # 2월 - 경칩 (驚蟄)
        15,   # 3월 - 청명 (淸明)
        45,   # 4월 - 입하 (立夏)
        75,   # 5월 - 망종 (芒種)
        105,  # 6월 - 소서 (小暑)
        135,  # 7월 - 입추 (立秋)
        165,  # 8월 - 백로 (白露)
        195,  # 9월 - 한로 (寒露)
        225,  # 10월 - 입동 (立冬)
        255,  # 11월 - 대설 (大雪)
        285,  # 12월 - 소한 (小寒)
    ]
    
    # 현재 날짜의 황경
    current_longitude = get_solar_longitude(year, month, day)
    
    # 어느 절기와 다음 절기 사이인지 찾기
    for i in range(12):
        current_term = solar_terms_longitude[i]
        next_term = solar_terms_longitude[(i + 1) % 12]
        
        # 황경이 현재 절기와 다음 절기 사이에 있는지 확인
        if current_term < next_term:
            # 일반적인 경우
            if current_term <= current_longitude < next_term:
                return i + 1
        else:
            # 연말-연초 경계 (315-345-15)
            if current_longitude >= current_term or current_longitude < next_term:
                return i + 1
    
    return 1  # 기본값

def get_month_stem_branch(year_stem, year, month, day):
    """
    연간과 절기 기준 월로부터 월주 천간지지 계산
    
    Args:
        year_stem: 연간 (천간)
        year, month, day: 양력 날짜
    
    Returns:
        tuple: (월간, 월지)
    """
    stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    branches = ["인", "묘", "진", "사", "오", "미", "신", "유", "술", "해", "자", "축"]
    
    # 절기 기준 음력 월 계산
    lunar_month = get_solar_term_for_date(year, month, day)
    
    # 월의 지지: 음력 1월(인) ~ 12월(축)
    branch = branches[lunar_month - 1]
    
    # 연간에 따른 월간 결정 (오호지법)
    stem_start_map = {
        "갑": 2, "을": 4, "병": 6, "정": 8, "무": 0,
        "기": 2, "경": 4, "신": 6, "임": 8, "계": 0
    }
    
    start_stem_idx = stem_start_map[year_stem]
    stem_idx = (start_stem_idx + lunar_month - 1) % 10
    stem = stems[stem_idx]
    
    return stem, branch
