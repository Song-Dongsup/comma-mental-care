import streamlit as st
import time
import os
import google.generativeai as genai
from datetime import datetime
import uuid
import json

# 파트너님의 로컬 파일들
import config
import database
import personas
import styles

# 1. 페이지 설정 및 스타일 적용
st.set_page_config(page_title="Comma", layout="centered", initial_sidebar_state="collapsed")
styles.apply_pro_css()

# 2. 세션 상태 및 보안 초기화
if "user" not in st.session_state:
    st.session_state.user = f"User_{str(uuid.uuid4())[:8]}"

if "app_state" not in st.session_state:
    st.session_state.app_state = "SPLASH"

if "page_mode" not in st.session_state:
    st.session_state.page_mode = "CHAT"

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "transfer_situation" not in st.session_state:
    st.session_state.transfer_situation = ""

# 3. AI 모델 설정
try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
except Exception:
    pass

# 4. 데이터 로드 (Guest 에러 방지)
all_data = database.load_all_data()
if st.session_state.user not in all_data:
    all_data[st.session_state.user] = {
        "sessions": {}, "total_exp": 0, "mood_calendar": {}
    }
    database.save_all_data(all_data)

# --- 헬퍼 함수들 ---
def get_tree_level(exp):
    if exp < 50: return "🌱 씨앗", "시작이 반이에요."
    elif exp < 150: return "🌿 새싹", "마음의 싹이 트고 있어요."
    elif exp < 300: return "🌳 묘목", "줄기가 단단해지고 있어요."
    else: return "🌲 나무", "당신의 마음은 숲이 되었습니다."

def analyze_chat_for_garden(messages, persona_name):
    if not messages: return None
    chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-10:]])
    prompt = f"상담 내용을 바탕으로 요약, 감정 단어, 색상코드(HEX), 행동 미션을 JSON으로 출력하세요: {chat_history}"
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {"summary": "수고하셨습니다.", "emotion": "평온", "color": "#E3F2FD", "mission": "심호흡하기"}

def analyze_other_person(target, situation):
    prompt = f"[{target}]님이 [{situation}]과 같은 행동을 한 이유와 속마음, 대처법을 JSON으로 분석하세요."
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {"hidden_mind": "분석 중입니다.", "reason": "상황 파악 중...", "advice": "잠시 기다려주세요."}

def generate_short_title(user_msg):
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        prompt = f"다음 문장을 10자 이내의 명사형 키워드 제목으로 요약하세요: {user_msg}"
        response = model.generate_content(prompt)
        return response.text.strip()[:10]
    except:
        return user_msg[:8] + ".."

def check_relation_keywords(text):
    keywords = ["그 사람", "걔", "엄마", "아빠", "동생", "친구", "상사", "남친", "여친", "남편", "아내", "싸웠", "화나", "짜증", "이해", "서운"]
    return any(k in text for k in keywords)

# --- 화면 제어 로직 ---

# [STATE 1] 스플래시 화면
if st.session_state.app_state == "SPLASH":
    gif_b64 = database.get_image_base64("assets/images/loading.gif") if os.path.exists("assets/images/loading.gif") else ""
    # [수정] 로고 이미지 아래에 텍스트(<p class="splash-text">) 추가
    st.markdown(f"""
        <div class="fixed-splash">
            <img src="data:image/gif;base64,{gif_b64}" class="splash-gif">
            <p class="splash-text">나를 위한 작은 쉼표</p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.0)
    st.session_state.app_state = "MAIN"
    st.rerun()

# [STATE 2] 메인 화면
elif st.session_state.app_state == "MAIN":
    
    with st.sidebar:
        if os.path.exists("assets/images/logo.png"):
            st.image("assets/images/logo.png", width=100)
        
        st.caption(f"ID: {st.session_state.user}") # 유저 아이디 표시
        
        st.divider()
        if st.button("💬 1:1 상담 (Chat)", use_container_width=True): st.session_state.page_mode = "CHAT"; st.rerun()
        if st.button("🌿 마음 정원 (Garden)", use_container_width=True): st.session_state.page_mode = "GARDEN"; st.rerun()
        if st.button("🔍 타인 심리 분석 (Why?)", use_container_width=True): st.session_state.page_mode = "RELATION"; st.rerun()
            
        st.subheader("상담 파트너 설정")
        # [복구] 기본값을 '전문 상담' 카테고리의 첫 번째(정신과 전문의)로 자동 설정
        category_keys = list(personas.PERSONA_LIBRARY.keys())
        category = st.selectbox("카테고리", category_keys, index=0)
        
        persona_keys = list(personas.PERSONA_LIBRARY[category].keys())
        selected_persona_name = st.selectbox("이름", persona_keys, index=0) # 첫 번째 인물이 기본 선택됨
        char_data = personas.PERSONA_LIBRARY[category][selected_persona_name]
        
        custom_context = ""
        my_gender = ""
        if "가족" in category:
            my_gender = st.radio("성별", ["아들", "딸"], horizontal=True)
            custom_context = st.text_area("특이사항", height=60)

        st.divider()
        # 유저 세션 관리
        if selected_persona_name not in all_data[st.session_state.user]["sessions"]:
             all_data[st.session_state.user]["sessions"][selected_persona_name] = []
        user_sessions = all_data[st.session_state.user]["sessions"][selected_persona_name]

        if st.session_state.page_mode == "CHAT":
            if st.button("➕ 새 대화 시작하기", use_container_width=True):
                new_id = str(uuid.uuid4())
                new_session = {"id": new_id, "created_at": datetime.now().strftime("%m/%d %H:%M"), "title": "새 대화", "is_completed": False, "messages": []}
                user_sessions.insert(0, new_session)
                all_data[st.session_state.user]["sessions"][selected_persona_name] = user_sessions
                database.save_all_data(all_data)
                st.session_state.current_session_id = new_id
                st.rerun()

            # 세션 목록 표시
            for idx, session in enumerate(user_sessions):
                sess_title = session.get('title', session['created_at'])
                if session.get('is_completed', False): sess_title = f"✔️ {sess_title}"
                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button(f"📂 {sess_title}", key=f"sel_{session['id']}", use_container_width=True):
                        st.session_state.current_session_id = session['id']; st.rerun()
                with c2:
                    if st.button("x", key=f"del_{session['id']}"):
                        user_sessions.pop(idx)
                        if st.session_state.current_session_id == session['id']: st.session_state.current_session_id = None
                        database.save_all_data(all_data); st.rerun()

    # 헤더
    logo_b64 = database.get_image_base64("assets/images/logo.png")
    st.markdown(f'<div class="custom-header"><div class="header-logo-container"><img src="data:image/png;base64,{logo_b64}" class="header-logo-img"></div></div>', unsafe_allow_html=True)

    if st.session_state.page_mode == "CHAT":
        # 세션이 없거나 선택되지 않았을 때 자동 생성
        if not st.session_state.current_session_id:
            if user_sessions: st.session_state.current_session_id = user_sessions[0]['id']
            else:
                new_id = str(uuid.uuid4())
                new_session = {"id": new_id, "created_at": datetime.now().strftime("%m/%d %H:%M"), "title": "새 대화", "is_completed": False, "messages": []}
                user_sessions.insert(0, new_session)
                all_data[st.session_state.user]["sessions"][selected_persona_name] = user_sessions
                database.save_all_data(all_data)
                st.session_state.current_session_id = new_id
                st.rerun()

        active_session = next((s for s in user_sessions if s['id'] == st.session_state.current_session_id), None)
        
        if active_session:
            # [복구] 대화방에 처음 들어오면 자동으로 인사말 건네기
            if not active_session['messages']:
                greeting = f"안녕하세요, 오늘 기분은 어때요?"
                if "가족" in category and my_gender: greeting = f"우리 {my_gender}, 오늘 기분은 좀 어때?"
                active_session['messages'].append({"role": "assistant", "content": greeting})
                database.save_all_data(all_data)
                st.rerun() # 인사를 바로 보여주기 위해 새로고침

            for m in active_session['messages']:
                avatar = char_data.get("img") if m["role"] == "assistant" and os.path.exists(char_data.get("img", "")) else None
                with st.chat_message(m["role"], avatar=avatar): st.markdown(m["content"])
            
            # 대화 종료 및 정원 이동 버튼
            if len(active_session['messages']) > 2 and not active_session.get('is_completed', False):
                if st.button("✨ 멘탈 성장 (대화 종료)", use_container_width=True):
                    with st.spinner("분석 중..."):
                        earned = len(active_session['messages']) * 3
                        database.update_user_exp(st.session_state.user, earned)
                        analysis_result = analyze_chat_for_garden(active_session['messages'], selected_persona_name)
                        active_session['is_completed'] = True
                        database.save_all_data(all_data)
                        st.session_state.temp_result = {"earned": earned, "analysis": analysis_result}
                        st.session_state.page_mode = "GARDEN"
                        st.rerun()

            # 입력창 및 응답 로직
            if not active_session.get('is_completed', False):
                if prompt := st.chat_input("메시지 입력..."):
                    # 사용자 메시지 추가
                    active_session['messages'].append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)
                    
                    # 제목 자동 생성
                    if len(active_session['messages']) == 2:
                        active_session['title'] = generate_short_title(prompt)
                        database.save_all_data(all_data)

                    # AI 응답 생성
                    ai_avatar = char_data.get("img") if os.path.exists(char_data.get("img", "")) else None
                    with st.chat_message("assistant", avatar=ai_avatar):
                        msg_placeholder = st.empty()
                        full_res = ""
                        try:
                            sys_prompt = char_data['base_msg']
                            if custom_context: sys_prompt += f"\n[설정]: {custom_context}"
                            if my_gender: sys_prompt += f"\n[User Info]: 나는 {my_gender}입니다."
                            
                            # ChatHistory 구성
                            history = [{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in active_session['messages'][:-1]]
                            
                            model = genai.GenerativeModel(config.SELECTED_MODEL, system_instruction=sys_prompt)
                            chat = model.start_chat(history=history)
                            response = chat.send_message(prompt, stream=True)
                            
                            for chunk in response:
                                full_res += chunk.text
                                msg_placeholder.markdown(full_res + "▌")
                            msg_placeholder.markdown(full_res)
                            
                            active_session['messages'].append({"role": "assistant", "content": full_res})
                            database.save_all_data(all_data)
                        except Exception as e:
                            st.error(f"Error: {e}")
                    
                    # [복구] 타인 심리 분석 추천 (Info 메시지가 아닌 버튼으로 복구)
                    if check_relation_keywords(prompt):
                        with st.chat_message("assistant", avatar="🔍"):
                            st.markdown(f"**상대방 때문에 고민이 많으시군요.**\n\n방금 말씀하신 내용을 바탕으로 심리를 분석해드릴까요?")
                            if st.button("🔍 이 내용으로 바로 분석하기", key=f"rec_{len(active_session['messages'])}"):
                                st.session_state.transfer_situation = prompt
                                st.session_state.page_mode = "RELATION"
                                st.rerun()

    elif st.session_state.page_mode == "GARDEN":
        st.subheader("🌿 마음 정원")
        curr_exp = database.get_user_exp(st.session_state.user)
        lvl_name, lvl_msg = get_tree_level(curr_exp)
        
        earned = st.session_state.temp_result.get("earned", 0) if "temp_result" in st.session_state else 0
        analysis = st.session_state.temp_result.get("analysis", {}) if "temp_result" in st.session_state else {}
        
        st.markdown(f"""<div style="background-color:#F1F8E9; padding:30px; border-radius:20px; text-align:center;"><div style="font-size:80px;">🌳</div><h2 style="color:#2E7D32; margin:0;">{lvl_name}</h2><p>"{lvl_msg}"</p><h1 style="color:#33691E;">+{earned} Point</h1></div>""", unsafe_allow_html=True)
        st.info(f"💌 메시지: {analysis.get('summary', '수고하셨습니다.')}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎨 감정 색깔 남기기"):
                database.save_mood_entry(st.session_state.user, datetime.now().strftime("%Y-%m-%d"), {"color": analysis.get('color', '#EEE'), "emotion": analysis.get('emotion', '평온')})
                st.success("저장되었습니다!")
        with col2:
             if st.button("🏃 기분 전환 미션"):
                st.success(f"미션: {analysis.get('mission', '물 한 잔 마시기')}"); st.balloons()
        
        if st.button("💬 대화 목록으로 돌아가기", use_container_width=True):
            st.session_state.page_mode = "CHAT"; st.rerun()

    elif st.session_state.page_mode == "RELATION":
        st.subheader("🔍 타인 심리 분석 (Why?)")
        with st.form("rel_form"):
            target = st.text_input("누구인가요?")
            sit = st.text_area("어떤 행동을 했나요?", value=st.session_state.transfer_situation, height=150)
            if st.form_submit_button("분석하기", use_container_width=True):
                with st.spinner("분석 중..."):
                    res = analyze_other_person(target, sit)
                    st.markdown(f"### 💭 속마음\n{res.get('hidden_mind')}")
                    st.markdown(f"### 💧 원인\n{res.get('reason')}")
                    st.markdown(f"### 💡 대처법\n{res.get('advice')}")
                    st.session_state.transfer_situation = ""
