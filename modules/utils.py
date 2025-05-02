"""
만세력 기준 시간 보정 및 날짜 변환 관련 유틸리티 함수
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
import streamlit as st

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

def adjust_time_for_manseryeok(year, month, day, hour, minute, region):
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