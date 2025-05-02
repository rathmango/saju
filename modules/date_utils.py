"""
날짜 변환 관련 유틸리티 함수 (음력/양력 변환)
"""
import requests
import xml.etree.ElementTree as ET

# 공공데이터포털 API 서비스 키
API_KEY = 'lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X/gHbvyM+2W1DlEv3ViocMaq8+0YB1H2jkYPhnYlNl4hZQj23JnA=='

def get_lunar_date(solar_year, solar_month, solar_day):
    """양력을 음력으로 변환"""
    url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo'
    params = {
        'serviceKey': API_KEY,
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
        'serviceKey': API_KEY,
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