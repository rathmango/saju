"""
Supabase 데이터베이스 연결 및 로깅 관련 함수
"""
import os
import json
from datetime import datetime
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

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