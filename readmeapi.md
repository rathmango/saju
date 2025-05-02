# 한국천문연구원 음양력 정보 API

## 개요
한국천문연구원 음양력 정보 API. 양/음력 변환, 율리우스 적일 등 천문 정보 제공.

## API 인증 정보
- 서비스 유형: REST
- 활용 기간: 2025-05-02 ~ 2027-05-02
- 일일 트래픽: 각 기능별 10,000회
- 서비스 EndPoint: https://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService

### 인증키
- Encoding: lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X%2FgHbvyM%2B2W1DlEv3ViocMaq8%2B0YB1H2jkYPhnYlNl4hZQj23JnA%3D%3D
- Decoding: lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X/gHbvyM+2W1DlEv3ViocMaq8+0YB1H2jkYPhnYlNl4hZQj23JnA==

## API 기능

### 1. 음력일정보 조회 (getLunCalInfo)
양력일을 기준으로 음력날짜, 요일, 윤년, 평달/윤달 여부, 음력 간지, 율리우스 적일 등의 정보 제공.

#### 요청 URL
```
http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo
```

#### 요청 파라미터
| 파라미터명 | 설명 | 필수여부 | 타입 | 예시 |
|------------|------|----------|------|------|
| serviceKey | 인증키 | 필수 | String | 인증키 |
| solYear | 연(양력) | 필수 | String | 2015 |
| solMonth | 월(양력) | 필수 | String | 09 |
| solDay | 일(양력) | 옵션 | String | 22 |

#### 응답 결과
| 항목명(국문) | 항목명(영문) | 설명 | 예시 |
|--------------|--------------|------|------|
| 연(음력) | lunYear | 연(음력) | 2015 |
| 월(음력) | lunMonth | 월(음력) | 09 |
| 일(음력) | lunDay | 일(음력) | 22 |
| 연 | solYear | 연(양력) | 2015 |
| 월 | solMonth | 월(양력) | 01 |
| 일 | solDay | 일(양력) | 01 |
| 윤년구분 | solLeapyear | 윤년구분(평 : 평년, 윤 : 윤년) | 평 |
| 윤달구분 | lunLeapmonth | 윤달구분(평 : 평달, 윤 : 윤달) | 평 |
| 요일 | solWeek | 요일 | 화 |
| 간지(세차) | lunSecha | 간지(세차) | 을미(乙未) |
| 간지(월) | lunWolgeon | 간지(월) | 을유(乙酉) |
| 간지(일) | lunIljin | 간지(일) | 신축(辛丑) |
| 월일수(음력) | lunNday | 월일수(음력) | 29 |
| 율리우스적일 | solJd | 율리우스적일 | 2457288 |

### 2. 특정 음력일 정보조회 (getSpcifyLunCalInfo)
양력연월일(내역), 요일 등의 정보 제공.

#### 요청 URL
```
http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getSpcifyLunCalInfo
```

#### 요청 파라미터
| 파라미터명 | 설명 | 필수여부 | 타입 | 예시 |
|------------|------|----------|------|------|
| serviceKey | 인증키 | 필수 | String | 인증키 |
| lunYear | 연(음력) | 필수 | String | 2015 |
| lunMonth | 월(음력) | 필수 | String | 09 |
| lunDay | 일(음력) | 필수 | String | 22 |

### 3. 율리우스적일 정보조회 (getJulianCalInfo)
양력날짜, 음력날짜, 요일, 윤년, 평달/윤달 여부, 음력 간지 등의 정보 제공.

#### 요청 URL
```
http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getJulianCalInfo
```

#### 요청 파라미터
| 파라미터명 | 설명 | 필수여부 | 타입 | 예시 |
|------------|------|----------|------|------|
| serviceKey | 인증키 | 필수 | String | 인증키 |
| solJd | 율리우스적일 | 필수 | String | 2457288 |

### 4. 양력일정보 조회 (getSolCalInfo)
음력일을 기준으로 양력날짜, 요일, 윤년, 평달/윤달 여부, 음력 간지, 율리우스 적일 등의 정보 제공.

#### 요청 URL
```
http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getSolCalInfo
```

#### 요청 파라미터
| 파라미터명 | 설명 | 필수여부 | 타입 | 예시 |
|------------|------|----------|------|------|
| serviceKey | 인증키 | 필수 | String | 인증키 |
| lunYear | 연(음력) | 필수 | String | 2015 |
| lunMonth | 월(음력) | 필수 | String | 09 |
| lunDay | 일(음력) | 필수 | String | 22 |

## 사용 예제

### 1. 음력일정보 조회 (양력 -> 음력 변환)

#### cURL
```bash
curl --include --request GET 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo?serviceKey=lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X%2FgHbvyM%2B2W1DlEv3ViocMaq8%2B0YB1H2jkYPhnYlNl4hZQj23JnA%3D%3D&solYear=2015&solMonth=09&solDay=22'
```

#### Python
```python
import requests
import xml.etree.ElementTree as ET

url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo'
params = {
    'serviceKey': 'lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X/gHbvyM+2W1DlEv3ViocMaq8+0YB1H2jkYPhnYlNl4hZQj23JnA==',  # Decoded key
    'solYear': '2015',
    'solMonth': '09',
    'solDay': '22'
}

response = requests.get(url, params=params)
root = ET.fromstring(response.content)

items = root.findall('.//item')
for item in items:
    lunYear = item.find('lunYear').text
    lunMonth = item.find('lunMonth').text
    lunDay = item.find('lunDay').text
    print(f"음력: {lunYear}년 {lunMonth}월 {lunDay}일")
    
    solWeek = item.find('solWeek').text
    lunLeapmonth = item.find('lunLeapmonth').text
    print(f"요일: {solWeek}, 윤달여부: {lunLeapmonth}")
```

#### JavaScript
```javascript
var xhr = new XMLHttpRequest();
var url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getLunCalInfo';
var queryParams = '?' + encodeURIComponent('serviceKey') + '='+'lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X%2FgHbvyM%2B2W1DlEv3ViocMaq8%2B0YB1H2jkYPhnYlNl4hZQj23JnA%3D%3D';  // Encoded key
queryParams += '&' + encodeURIComponent('solYear') + '=' + encodeURIComponent('2015');
queryParams += '&' + encodeURIComponent('solMonth') + '=' + encodeURIComponent('09');
queryParams += '&' + encodeURIComponent('solDay') + '=' + encodeURIComponent('22');
xhr.open('GET', url + queryParams);
xhr.onreadystatechange = function () {
    if (this.readyState == 4) {
        if(this.status === 200) {
            var parser = new DOMParser();
            var xmlDoc = parser.parseFromString(this.responseText, "text/xml");
            
            var items = xmlDoc.getElementsByTagName('item');
            for(var i = 0; i < items.length; i++) {
                var item = items[i];
                var lunYear = item.getElementsByTagName('lunYear')[0].textContent;
                var lunMonth = item.getElementsByTagName('lunMonth')[0].textContent;
                var lunDay = item.getElementsByTagName('lunDay')[0].textContent;
                
                console.log("음력: " + lunYear + "년 " + lunMonth + "월 " + lunDay + "일");
                
                var solWeek = item.getElementsByTagName('solWeek')[0].textContent;
                var lunLeapmonth = item.getElementsByTagName('lunLeapmonth')[0].textContent;
                console.log("요일: " + solWeek + ", 윤달여부: " + lunLeapmonth);
            }
        } else {
            console.error("API 호출 실패: " + this.status);
        }
    }
};

xhr.send('');
```

### 2. 양력일정보 조회 (음력 -> 양력 변환)

#### Python
```python
import requests
import xml.etree.ElementTree as ET

url = 'http://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService/getSolCalInfo'
params = {
    'serviceKey': 'lgzl5ZUn691kCie1LGFWnRg3gMwSFay5T2X/gHbvyM+2W1DlEv3ViocMaq8+0YB1H2jkYPhnYlNl4hZQj23JnA==',  # Decoded key
    'lunYear': '2015',
    'lunMonth': '08',
    'lunDay': '10'
}

response = requests.get(url, params=params)
root = ET.fromstring(response.content)

items = root.findall('.//item')
for item in items:
    solYear = item.find('solYear').text
    solMonth = item.find('solMonth').text
    solDay = item.find('solDay').text
    print(f"양력: {solYear}년 {solMonth}월 {solDay}일")
```

## 응답 예시 (XML)

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<response>
    <header>
        <resultCode>00</resultCode>
        <resultMsg>NORMAL SERVICE.</resultMsg>
    </header>
    <body>
        <items>
            <item>
                <solYear>2015</solYear>
                <solMonth>09</solMonth>
                <solDay>22</solDay>
                <lunYear>2015</lunYear>
                <lunMonth>08</lunMonth>
                <lunDay>10</lunDay>
                <solLeapyear>평</solLeapyear>
                <lunLeapmonth>평</lunLeapmonth>
                <solWeek>화</solWeek>
                <lunSecha>을미(乙未)</lunSecha>
                <lunWolgeon>무신(戊申)</lunWolgeon>
                <lunIljin>정미(丁未)</lunIljin>
                <lunNday>30</lunNday>
                <solJd>2457288</solJd>
            </item>
        </items>
    </body>
</response>
```

## 유틸리티 함수

### 날짜 포맷팅 (한 자리 숫자 앞에 0 추가)
```python
def format_date_component(component):
    component = str(component)
    return component.zfill(2)  # 한 자리 숫자라면 앞에 0을 추가

# 사용 예시
year = "2023"
month = "5"  # 한 자리 숫자
day = "9"    # 한 자리 숫자

formatted_month = format_date_component(month)  # "05"
formatted_day = format_date_component(day)      # "09"
```

## 오류 처리 예시
```python
import requests
import xml.etree.ElementTree as ET

def get_lunar_date(solar_year, solar_month, solar_day):
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
            'solWeek': item.find('solWeek').text,
            'lunLeapmonth': item.find('lunLeapmonth').text,
            'solJd': item.find('solJd').text
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {'error': True, 'message': f"요청 오류: {str(e)}"}
    except ET.ParseError:
        return {'error': True, 'message': "XML 파싱 오류"}
    except Exception as e:
        return {'error': True, 'message': f"오류 발생: {str(e)}"}
```

## 참고사항
- 데이터 포맷: XML
- 응답코드 00은 성공을 의미
- 월, 일 값은 '01', '02'와 같이 두 자리로 보내는 것이 안전
- 개발단계/운영단계 모두 자동승인
- 운영계정 전환 시 활용사례 등록하면 트래픽 증가 가능