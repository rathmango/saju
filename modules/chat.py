"""
채팅 인터페이스 및 사주 분석 채팅 기능
"""
import streamlit as st
import uuid
from datetime import datetime
from modules.api import analyze_saju_with_llm
from modules.ui_helpers import stream_response
from modules.db import log_conversation
import json

def init_chat_state():
    """채팅 세션 상태를 초기화합니다."""
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
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'submit_clicked' not in st.session_state:
        st.session_state.submit_clicked = False
    if 'last_input' not in st.session_state:
        st.session_state.last_input = ""
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""
    if 'start_analysis_clicked' not in st.session_state:
        st.session_state.start_analysis_clicked = False
    if 'analysis_in_progress' not in st.session_state:
        st.session_state.analysis_in_progress = False
    if 'reset_chat_clicked' not in st.session_state:
        st.session_state.reset_chat_clicked = False
    if 'reset_in_progress' not in st.session_state:
        st.session_state.reset_in_progress = False

def submit_message(user_input):
    """사용자 메시지를 처리하고 응답을 생성합니다."""
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

def start_analysis():
    """사주 초기 분석을 시작합니다."""
    try:
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
        
        # 사용자 메시지 먼저 추가
        st.session_state.message_id_counter += 1
        user_msg_id = f"msg_{st.session_state.message_id_counter}"
        st.session_state.messages.append({"role": "user", "content": "사주 분석을 시작해주세요.", "id": user_msg_id})
        
        # 챗봇 메시지도 미리 추가 (빈 내용으로)
        st.session_state.message_id_counter += 1
        assistant_msg_id = f"msg_{st.session_state.message_id_counter}"
        st.session_state.messages.append({"role": "assistant", "content": "분석 중...", "id": assistant_msg_id})
        
        # UI 갱신을 위해 재실행
        st.rerun()
        
        # 이 부분은 재실행 후에 실행됨
        with st.spinner("사주를 분석 중입니다..."):
            # API 호출
            response = analyze_saju_with_llm(initial_prompt)
            
            # 응답 처리 - 채팅 메시지로 직접 업데이트
            from modules.ui_helpers import stream_response
            
            # 응답 내용을 직접 스트리밍 (채팅 컨테이너 내의 해당 메시지로)
            # 실제 텍스트는 chat_container에 의해 표시된 메시지에 반영됨
            full_response = ""
            for msg in st.session_state.messages:
                if msg.get("id") == assistant_msg_id:
                    try:
                        # 응답이 문자열인 경우 (오류 메시지 등)
                        if isinstance(response, str):
                            full_response = response
                        else:
                            # 스트리밍 응답인 경우
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
                                                            # 메시지 내용 업데이트
                                                            msg["content"] = full_response
                                                            # UI 갱신
                                                            st.rerun()
                                            except json.JSONDecodeError:
                                                continue
                            except Exception as e:
                                error_msg = f"응답 처리 중 오류가 발생했습니다: {str(e)}"
                                msg["content"] = error_msg
                                st.rerun()
                    except Exception as e:
                        st.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
                    break
            
            # Supabase에 대화 로깅
            log_conversation("사주 분석을 시작해주세요.", full_response)
            
        # 플래그 초기화
        st.session_state.start_analysis_clicked = False
        st.session_state.analysis_in_progress = False
            
    except Exception as e:
        st.error(f"사주 분석 시작 중 오류가 발생했습니다: {str(e)}")
        # 오류 발생 시에도 플래그 초기화
        st.session_state.start_analysis_clicked = False
        st.session_state.analysis_in_progress = False

def reset_chat():
    """채팅 내역을 초기화합니다."""
    st.session_state.messages = []
    st.session_state.message_id_counter = 0
    st.session_state.last_input = ""
    st.session_state.input_text = ""
    st.session_state.reset_chat_clicked = False
    st.session_state.reset_in_progress = False
    st.rerun()

def display_chat_messages():
    """채팅 메시지를 표시합니다."""
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