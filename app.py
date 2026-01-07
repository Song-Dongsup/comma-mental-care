import streamlit as st
import time
import os
import google.generativeai as genai
from datetime import datetime
import uuid  # [체크!] 사용자 고유 아이디 생성을 위해 필수입니다.
import json

# 파트너님의 로컬 파일들
import config
import database
import personas
import styles

# 1. 페이지 설정 및 스타일 적용
st.set_page_config(page_title="Comma", layout="centered", initial_sidebar_state="collapsed")
styles.apply_pro_css()

# 2. 세션 상태 초기화 (보안 및 상태 관리)
if "user" not in st.session_state:
    # 접속할 때마다 고유한 아이디를 부여하여 대화가 섞이지 않게 합니다.
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

# 4. 데이터 로드 및 새 유저 자동 등록 (KeyError 방지 핵심)
all_data = database.load_all_data()

# 만약 처음 방문한 유저라면 데이터 파일(users_data.json)에 즉시 자리를 만듭니다.
if st.session_state.user not in all_data:
    all_data[st.session_state.user] = {
        "sessions": {}, 
        "total_exp": 0, 
        "mood_calendar": {}
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
    keywords = ["그 사람", "걔", "엄마", "아빠", "동생", "친구", "상사", "남친", "여친", "남편", "아내", "싸웠", "화나"]
    return any(k in text for k in keywords)

# --- 화면 제어 로직 ---

# [STATE 1] 스플래시 화면
if st.session_state.app_state == "SPLASH":
    gif_b64 = database.get_image_base64("assets/images/loading.gif") if os.path.exists("assets/images/loading.gif") else ""
    st.markdown(f"""<div class="fixed-splash"><img src="data:image/gif;base64,{gif_b64}" class="splash-gif"><p class="splash-text">내 마음의 작은 쉼표</p></div>""", unsafe_allow_html=True)
    time.sleep(2.0)
    st.session_state.app_state = "MAIN"
    st.rerun()

# [STATE 2] 메인 화면
elif st.session_state.app_state == "MAIN":
    
    with st.sidebar:
        if os.path.exists("assets/images/logo.png"):
            st.image("assets/images/logo.png", width=100)
        
        st.subheader(f"내 정보 ({st.session_state.user})")
        
        st.divider()
        if st.button("💬 1:1 상담 (Chat)", use_container_width=True): st.session_state.page_mode = "CHAT"; st.rerun()
        if st.button("🌿 마음 정원 (Garden)", use_container_width=True): st.session_state.page_mode = "GARDEN"; st.rerun()
        if st.button("🔍 타인 심리 분석 (Why?)", use_container_width=True): st.session_state.page_mode = "RELATION"; st.rerun()
            
        st.subheader("상담 파트너 설정")
        category = st.selectbox("카테고리", list(personas.PERSONA_LIBRARY.keys()))
        selected_persona_name = st.selectbox("이름", list(personas.PERSONA_LIBRARY[category].keys()))
        char_data = personas.PERSONA_LIBRARY[category][selected_persona_name]
        
        custom_context = ""
        my_gender = ""
        if "가족" in category:
            my_gender = st.radio("성별", ["아들", "딸"], horizontal=True)
            custom_context = st.text_area("특이사항", height=60)

        st.divider()
        # 유저 세션 관리
        user_sessions = all_data[st.session_state.user]["sessions"].get(selected_persona_name, [])
        if st.session_state.page_mode == "CHAT":
            if st.button("➕ 새 대화 시작하기", use_container_width=True):
                new_id = str(uuid.uuid4())
                new_session = {"id": new_id, "created_at": datetime.now().strftime("%m/%d %H:%M"), "title": "새 대화", "is_completed": False, "messages": []}
                user_sessions.insert(0, new_session)
                all_data[st.session_state.user]["sessions"][selected_persona_name] = user_sessions
                database.save_all_data(all_data)
                st.session_state.current_session_id = new_id
                st.rerun()

    # 헤더 및 메인 뷰
    logo_b64 = database.get_image_base64("assets/images/logo.png")
    st.markdown(f'<div class="custom-header"><div class="header-logo-container"><img src="data:image/png;base64,{logo_b64}" class="header-logo-img"></div></div>', unsafe_allow_html=True)

    if st.session_state.page_mode == "CHAT":
        if not st.session_state.current_session_id:
            if user_sessions: st.session_state.current_session_id = user_sessions[0]['id']
            else:
                new_id = str(uuid.uuid4())
                user_sessions = [{"id": new_id, "created_at": datetime.now().strftime("%m/%d %H:%M"), "title": "새 대화", "is_completed": False, "messages": []}]
                all_data[st.session_state.user]["sessions"][selected_persona_name] = user_sessions
                database.save_all_data(all_data)
                st.session_state.current_session_id = new_id
            st.rerun()

        active_session = next((s for s in user_sessions if s['id'] == st.session_state.current_session_id), None)
        if active_session:
            for m in active_session['messages']:
                with st.chat_message(m["role"]): st.markdown(m["content"])
            
            if not active_session.get('is_completed', False):
                if prompt := st.chat_input("메시지 입력..."):
                    active_session['messages'].append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)
                    
                    with st.chat_message("assistant"):
                        msg_placeholder = st.empty()
                        full_res = ""
                        model = genai.GenerativeModel(config.SELECTED_MODEL, system_instruction=char_data['base_msg'])
                        response = model.generate_content(prompt)
                        full_res = response.text
                        msg_placeholder.markdown(full_res)
                        active_session['messages'].append({"role": "assistant", "content": full_res})
                        database.save_all_data(all_data)
                        if check_relation_keywords(prompt):
                            st.info("상대방의 심리가 궁금하다면 '타인 심리 분석' 탭을 이용해보세요!")

    elif st.session_state.page_mode == "GARDEN":
        st.subheader("🌿 마음 정원")
        curr_exp = database.get_user_exp(st.session_state.user)
        lvl_name, lvl_msg = get_tree_level(curr_exp)
        st.success(f"현재 당신의 마음은 {lvl_name} 상태입니다. {lvl_msg}")

    elif st.session_state.page_mode == "RELATION":
        st.subheader("🔍 타인 심리 분석 (Why?)")
        with st.form("rel_form"):
            target = st.text_input("누구인가요?")
            sit = st.text_area("어떤 상황인가요?")
            if st.form_submit_button("분석하기"):
                res = analyze_other_person(target, sit)
                st.write(f"**속마음:** {res['hidden_mind']}")
                st.write(f"**원인:** {res['reason']}")
                st.write(f"**조언:** {res['advice']}")
