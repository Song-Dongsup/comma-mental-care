import streamlit as st
import time
import os
import google.generativeai as genai
from datetime import datetime
import uuid
import json

# 로컬 파일 import
import config
import database
import personas
import styles

# --- [초기 설정] ---
st.set_page_config(page_title="Comma", layout="centered", initial_sidebar_state="collapsed")
styles.apply_pro_css()

# 세션 초기화 (보안 + 네비게이션 상태)
if "user" not in st.session_state:
    st.session_state.user = f"User_{str(uuid.uuid4())[:8]}"
if "nav_menu" not in st.session_state:
    st.session_state.nav_menu = "HOME" # 현재 보고 있는 화면 (HOME, LIST, CHAT, GARDEN, RELATION)
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "transfer_situation" not in st.session_state:
    st.session_state.transfer_situation = ""

# API 및 데이터 로드
try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
except: pass

all_data = database.load_all_data()
if st.session_state.user not in all_data:
    all_data[st.session_state.user] = {"sessions": {}, "total_exp": 0, "mood_calendar": {}}
    database.save_all_data(all_data)

# --- [헬퍼 함수: AI 로직] (기존 기능 유지) ---
def get_tree_level(exp):
    if exp < 50: return "🌱 씨앗", "시작이 반이에요."
    elif exp < 150: return "🌿 새싹", "마음의 싹이 트고 있어요."
    elif exp < 300: return "🌳 묘목", "줄기가 단단해지고 있어요."
    else: return "🌲 나무", "당신의 마음은 숲이 되었습니다."

def analyze_chat_for_garden(messages):
    chat_str = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-10:]])
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        res = model.generate_content(f"요약/감정단어/색상(HEX)/미션 JSON으로: {chat_str}", generation_config={"response_mime_type": "application/json"})
        return json.loads(res.text)
    except: return {"summary": "수고했어요", "emotion": "평온", "color": "#E3F2FD", "mission": "심호흡"}

def analyze_other_person(target, sit):
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        res = model.generate_content(f"[{target}]의 행동 [{sit}]에 대한 속마음/원인/대처법 JSON 분석", generation_config={"response_mime_type": "application/json"})
        return json.loads(res.text)
    except: return {"hidden_mind": "분석 실패", "reason": "네트워크 오류", "advice": "다시 시도"}

def generate_title(msg):
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        return model.generate_content(f"'{msg}'를 10자 이내 명사형 제목으로 요약").text.strip()[:10]
    except: return msg[:8]

# --- [화면 1: HOME - 페르소나 선택] ---
def view_home():
    # 로고 영역
    logo_b64 = database.get_image_base64("assets/images/logo.png")
    st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{logo_b64}" width="120"></div>', unsafe_allow_html=True)
    
    st.markdown("### 💬 누구와 대화할까요?")
    
    # 카테고리 탭 (단순화)
    categories = list(personas.PERSONA_LIBRARY.keys())
    tabs = st.tabs(categories)
    
    for idx, cat in enumerate(categories):
        with tabs[idx]:
            cols = st.columns(3) # 한 줄에 3명씩 배치
            p_names = list(personas.PERSONA_LIBRARY[cat].keys())
            
            for i, name in enumerate(p_names):
                char = personas.PERSONA_LIBRARY[cat][name]
                # 이미지 원형 크롭 스타일 적용
                img_path = char.get('img', '')
                img_b64 = database.get_image_base64(img_path) if os.path.exists(img_path) else ""
                
                with cols[i % 3]:
                    # 클릭 가능한 카드 UI
                    st.markdown(f"""
                    <div style="text-align:center;">
                        <img src="data:image/png;base64,{img_b64}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; border:2px solid #EEE;">
                        <div style="font-weight:bold; font-size:14px; margin-top:5px;">{name}</div>
                        <div style="font-size:11px; color:#888;">{char.get('description','상담사')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("대화하기", key=f"btn_{name}", use_container_width=True):
                        st.session_state.selected_persona = name
                        st.session_state.selected_cat = cat
                        # 바로 채팅 목록으로 이동하거나 새 대화 생성
                        st.session_state.nav_menu = "LIST"
                        st.rerun()
            st.write("")

# --- [화면 2: LIST - 채팅 목록 (카톡 스타일)] ---
def view_list():
    st.subheader("📂 대화 목록")
    
    if not st.session_state.selected_persona:
        st.info("🏠 홈에서 대화 상대를 먼저 선택해주세요.")
        if st.button("상대 고르러 가기"): st.session_state.nav_menu = "HOME"; st.rerun()
        return

    curr_persona = st.session_state.selected_persona
    
    # 데이터 확보
    if "sessions" not in all_data[st.session_state.user]: all_data[st.session_state.user]["sessions"] = {}
    if curr_persona not in all_data[st.session_state.user]["sessions"]: all_data[st.session_state.user]["sessions"][curr_persona] = []
    
    user_sessions = all_data[st.session_state.user]["sessions"][curr_persona]
    
    # [새 대화 시작 버튼]
    if st.button(f"➕ {curr_persona}님과 새 대화 시작", use_container_width=True):
        new_id = str(uuid.uuid4())
        new_sess = {"id": new_id, "created_at": datetime.now().strftime("%m/%d %H:%M"), "title": "새로운 대화", "is_completed": False, "messages": []}
        user_sessions.insert(0, new_sess)
        all_data[st.session_state.user]["sessions"][curr_persona] = user_sessions
        database.save_all_data(all_data)
        st.session_state.current_session_id = new_id
        st.session_state.nav_menu = "CHAT"
        st.rerun()
    
    st.divider()
    
    # [목록 렌더링]
    if not user_sessions:
        st.caption("아직 대화 기록이 없습니다.")
    else:
        for idx, s in enumerate(user_sessions):
            # 카드 UI 구성
            with st.container():
                c1, c2, c3 = st.columns([5, 1.5, 1])
                with c1:
                    title = s.get('title', '새로운 대화')
                    date = s.get('created_at', '')
                    status = "✅ 완료됨" if s.get('is_completed') else "💬 진행중"
                    st.markdown(f"**{title}**")
                    st.caption(f"{date} | {status}")
                with c2:
                    if st.button("입장", key=f"enter_{s['id']}"):
                        st.session_state.current_session_id = s['id']
                        st.session_state.nav_menu = "CHAT"
                        st.rerun()
                with c3:
                    if st.button("🗑", key=f"del_{s['id']}"):
                        user_sessions.pop(idx)
                        database.save_all_data(all_data)
                        st.rerun()
                st.markdown("---") # 구분선

# --- [화면 3: CHAT - 채팅방] ---
def view_chat():
    if not st.session_state.current_session_id:
        st.session_state.nav_menu = "LIST"; st.rerun()
        
    # 헤더 (뒤로가기 느낌)
    c1, c2 = st.columns([1, 6])
    if c1.button("⬅"): st.session_state.nav_menu = "LIST"; st.rerun()
    c2.markdown(f"**{st.session_state.selected_persona}**")
    
    persona_name = st.session_state.selected_persona
    cat_name = st.session_state.get('selected_cat', '전문 상담')
    char_data = personas.PERSONA_LIBRARY[cat_name][persona_name]
    
    sessions = all_data[st.session_state.user]["sessions"][persona_name]
    active_session = next((s for s in sessions if s['id'] == st.session_state.current_session_id), None)
    
    if not active_session: st.error("세션 오류"); return

    # 메시지 렌더링
    for m in active_session['messages']:
        avatar = char_data.get('img') if m['role']=='assistant' and os.path.exists(char_data.get('img','')) else None
        with st.chat_message(m['role'], avatar=avatar):
            st.markdown(m['content'])
            
    # 입력창 (완료되지 않았을 때만)
    if not active_session.get('is_completed', False):
        if prompt := st.chat_input("메시지 입력..."):
            active_session['messages'].append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            # 제목 생성
            if len(active_session['messages']) == 2:
                active_session['title'] = generate_title(prompt)
                database.save_all_data(all_data)
            
            # AI 답변
            with st.chat_message("assistant", avatar=char_data.get('img')):
                msg_box = st.empty()
                full_res = ""
                try:
                    model = genai.GenerativeModel(config.SELECTED_MODEL, system_instruction=char_data['base_msg'])
                    chat_hist = [{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in active_session['messages'][:-1]]
                    chat = model.start_chat(history=chat_hist)
                    res = chat.send_message(prompt, stream=True)
                    for chunk in res:
                        full_res += chunk.text
                        msg_box.markdown(full_res + "▌")
                    msg_box.markdown(full_res)
                    active_session['messages'].append({"role": "assistant", "content": full_res})
                    database.save_all_data(all_data)
                except Exception as e: st.error(str(e))
                
            st.rerun()
            
        # 기능 버튼들
        if len(active_session['messages']) > 2:
            if st.button("✨ 대화 종료 & 정원 가꾸기", use_container_width=True):
                 earned = len(active_session['messages']) * 3
                 database.update_user_exp(st.session_state.user, earned)
                 res = analyze_chat_for_garden(active_session['messages'])
                 active_session['is_completed'] = True
                 database.save_all_data(all_data)
                 st.session_state.temp_result = {"earned": earned, "analysis": res}
                 st.session_state.nav_menu = "GARDEN"
                 st.rerun()

# --- [화면 4: GARDEN - 마음 정원] ---
def view_garden():
    st.subheader("🌿 마음 정원")
    exp = database.get_user_exp(st.session_state.user)
    lvl, msg = get_tree_level(exp)
    st.info(f"내 나무: {lvl} ({exp} Point)\n\n{msg}")
    
    if "temp_result" in st.session_state:
        res = st.session_state.temp_result['analysis']
        st.success(f"🎁 분석 결과: {res.get('summary')}")
        st.markdown(f"**감정:** {res.get('emotion')} | **추천 미션:** {res.get('mission')}")
        if st.button("확인 (홈으로)"): st.session_state.nav_menu = "HOME"; st.rerun()
    else:
        # 캘린더 등 표시
        cal = database.get_mood_calendar(st.session_state.user)
        st.write("최근 감정 기록이 여기에 표시됩니다.")

# --- [화면 5: RELATION - 심리 분석] ---
def view_relation():
    st.subheader("🔍 타인 심리 분석")
    with st.form("rel"):
        t = st.text_input("대상")
        s = st.text_area("상황")
        if st.form_submit_button("분석"):
            res = analyze_other_person(t, s)
            st.write(res)

# === [메인 컨트롤러: 화면 전환 & 하단 탭바] ===

# 1. 현재 선택된 메뉴에 따라 화면 표시
menu = st.session_state.nav_menu

if menu == "HOME": view_home()
elif menu == "LIST": view_list()
elif menu == "CHAT": view_chat()
elif menu == "GARDEN": view_garden()
elif menu == "RELATION": view_relation()

# 2. 하단 내비게이션 바 (고정된 느낌 주기)
st.write("---") # 구분선
col1, col2, col3, col4 = st.columns(4)

# 버튼을 누르면 nav_menu 상태를 변경하고 rerun
with col1:
    if st.button("🏠", help="홈"): st.session_state.nav_menu = "HOME"; st.rerun()
with col2:
    if st.button("💬", help="채팅목록"): 
        if st.session_state.selected_persona: st.session_state.nav_menu = "LIST"
        else: st.toast("대화 상대를 먼저 선택하세요"); st.session_state.nav_menu = "HOME"
        st.rerun()
with col3:
    if st.button("🌿", help="정원"): st.session_state.nav_menu = "GARDEN"; st.rerun()
with col4:
    if st.button("🔍", help="분석"): st.session_state.nav_menu = "RELATION"; st.rerun()
