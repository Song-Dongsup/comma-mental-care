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

# 세션 초기화
if "user" not in st.session_state:
    st.session_state.user = f"User_{str(uuid.uuid4())[:8]}"
if "nav_menu" not in st.session_state:
    st.session_state.nav_menu = "HOME"
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

# --- [헬퍼 함수] ---
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

# --- [이미지 매핑 함수: 이름표 고치기] ---
def get_persona_image_path(name):
    # 파트너님 화면에 나오는 이름(Key)과 파일명(Value)을 정확히 매칭
    mapping = {
        "정신과 의사": "doctor.jpg",     # [수정됨] 화면에 '정신과 의사'로 나옴
        "부처님": "buddha.jpg",
        "예수님": "jesus.jpg",
        "거스 히딩크": "hiddink.jpg",
        "손웅정": "logo.png",           # 아직 파일이 없어서 로고로 대체
        "소크라테스": "철학자.jpg",      # [수정됨] 철학자 사진 연결
        "니체": "철학자.jpg",           # 니체도 일단 철학자 사진으로 (임시)
        "워렌 버핏": "워렌버핏.jpg",
        "엄마/아빠": "logo.png"
    }
    filename = mapping.get(name, "logo.png")
    return f"assets/images/{filename}"

# --- [화면 1: HOME] ---
def view_home():
    # 로고
    logo_b64 = database.get_image_base64("assets/images/logo.png")
    if logo_b64:
        st.markdown(f'<div style="text-align:center; margin-bottom:20px;"><img src="data:image/png;base64,{logo_b64}" width="120"></div>', unsafe_allow_html=True)
    
    st.subheader("상담사 선택 >")
    
    categories = list(personas.PERSONA_LIBRARY.keys())
    for cat in categories:
        st.markdown(f"**{cat}**")
        p_names = list(personas.PERSONA_LIBRARY[cat].keys())
        cols = st.columns(3)
        for i, name in enumerate(p_names):
            char = personas.PERSONA_LIBRARY[cat][name]
            img_path = get_persona_image_path(name)
            img_b64 = database.get_image_base64(img_path) if os.path.exists(img_path) else database.get_image_base64("assets/images/logo.png")
            
            with cols[i % 3]:
                # 이미지 표시
                st.markdown(f"""
                <div style="text-align:center;">
                    <img src="data:image/jpeg;base64,{img_b64}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; border:2px solid #EEE;">
                    <div style="font-size:13px; font-weight:bold; margin-top:5px;">{name}</div>
                </div>
                """, unsafe_allow_html=True)
                # 투명 버튼 대신 일반 버튼 사용 (모바일 터치 오류 방지)
                if st.button("대화하기", key=f"btn_{cat}_{name}"):
                    st.session_state.selected_persona = name
                    st.session_state.selected_cat = cat
                    st.session_state.nav_menu = "LIST"
                    st.rerun()
        st.write("---")

# --- [화면 2: LIST] ---
def view_list():
    st.subheader("📂 대화 목록")
    if not st.session_state.selected_persona:
        st.info("먼저 상담사를 선택해주세요.")
        if st.button("홈으로 가기"): st.session_state.nav_menu = "HOME"; st.rerun()
        return

    curr = st.session_state.selected_persona
    
    # 상단 프로필
    img_path = get_persona_image_path(curr)
    img_b64 = database.get_image_base64(img_path) if os.path.exists(img_path) else ""
    st.markdown(f"""
    <div style="display:flex; align-items:center; margin-bottom:20px; background:white; padding:15px; border-radius:15px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <img src="data:image/jpeg;base64,{img_b64}" style="width:50px; height:50px; border-radius:50%; margin-right:15px; object-fit:cover;">
        <span style="font-size:18px; font-weight:bold;">{curr}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(f"➕ 새 대화 시작", use_container_width=True):
        if "sessions" not in all_data[st.session_state.user]: all_data[st.session_state.user]["sessions"] = {}
        if curr not in all_data[st.session_state.user]["sessions"]: all_data[st.session_state.user]["sessions"][curr] = []
        new_id = str(uuid.uuid4())
        new_sess = {"id": new_id, "created_at": datetime.now().strftime("%m/%d"), "title": "새로운 상담", "is_completed": False, "messages": []}
        all_data[st.session_state.user]["sessions"][curr].insert(0, new_sess)
        database.save_all_data(all_data)
        st.session_state.current_session_id = new_id
        st.session_state.nav_menu = "CHAT"
        st.rerun()

    if "sessions" in all_data[st.session_state.user] and curr in all_data[st.session_state.user]["sessions"]:
        sessions = all_data[st.session_state.user]["sessions"][curr]
        for s in sessions:
            c1, c2, c3 = st.columns([5, 1.5, 1])
            c1.write(f"**{s['title']}** ({s['created_at']})")
            if c2.button("입장", key=f"ent_{s['id']}"):
                st.session_state.current_session_id = s['id']; st.session_state.nav_menu = "CHAT"; st.rerun()
            if c3.button("🗑", key=f"del_{s['id']}"):
                sessions.remove(s); database.save_all_data(all_data); st.rerun()
            st.divider()

# --- [화면 3: CHAT] ---
def view_chat():
    if not st.session_state.current_session_id: st.session_state.nav_menu = "LIST"; st.rerun()
    
    # 상단 헤더 (뒤로가기)
    c1, c2 = st.columns([1, 6])
    if c1.button("⬅"): st.session_state.nav_menu = "LIST"; st.rerun()
    c2.markdown(f"**{st.session_state.selected_persona}**와의 대화")
    
    p_name = st.session_state.selected_persona
    cat = st.session_state.get('selected_cat', list(personas.PERSONA_LIBRARY.keys())[0])
    char = personas.PERSONA_LIBRARY[cat][p_name]
    img_path = get_persona_image_path(p_name)
    
    sessions = all_data[st.session_state.user]["sessions"][p_name]
    active = next((s for s in sessions if s['id'] == st.session_state.current_session_id), None)
    
    for m in active['messages']:
        avatar = img_path if m['role']=='assistant' and os.path.exists(img_path) else None
        with st.chat_message(m['role'], avatar=avatar): st.markdown(m['content'])
        
    if not active.get('is_completed', False):
        if prompt := st.chat_input("메시지 입력..."):
            active['messages'].append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if len(active['messages']) == 2: active['title'] = generate_title(prompt); database.save_all_data(all_data)
            
            with st.chat_message("assistant", avatar=img_path if os.path.exists(img_path) else None):
                msg_box = st.empty(); full_res = ""
                try:
                    model = genai.GenerativeModel(config.SELECTED_MODEL, system_instruction=char['base_msg'])
                    hist = [{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in active['messages'][:-1]]
                    chat = model.start_chat(history=hist)
                    res = chat.send_message(prompt, stream=True)
                    for chunk in res: full_res+=chunk.text; msg_box.markdown(full_res+"▌")
                    msg_box.markdown(full_res)
                    active['messages'].append({"role": "assistant", "content": full_res})
                    database.save_all_data(all_data)
                except Exception as e: st.error(str(e))
            st.rerun()
            
        if len(active['messages']) > 2:
             if st.button("✨ 대화 종료 (정원 가꾸기)", use_container_width=True):
                 earned = len(active['messages'])*3; database.update_user_exp(st.session_state.user, earned)
                 anl = analyze_chat_for_garden(active['messages'])
                 active['is_completed']=True; database.save_all_data(all_data)
                 st.session_state.temp_result = {"earned":earned, "analysis":anl}
                 st.session_state.nav_menu = "GARDEN"; st.rerun()

# --- [화면 4, 5: GARDEN, RELATION] ---
def view_garden():
    st.subheader("🌿 마음 정원")
    exp = database.get_user_exp(st.session_state.user)
    lvl, msg = get_tree_level(exp)
    st.info(f"{lvl} ({exp} Point)\n{msg}")
    if "temp_result" in st.session_state:
        res = st.session_state.temp_result['analysis']
        st.success(f"결과: {res.get('summary')}")
        if st.button("확인"): st.session_state.nav_menu = "HOME"; st.rerun()

def view_relation():
    st.subheader("🔍 타인 심리 분석")
    with st.form("rel"):
        t = st.text_input("대상"); s = st.text_area("상황")
        if st.form_submit_button("분석"):
            res = analyze_other_person(t, s)
            st.write(res)

# === [메인 컨트롤러] ===
menu = st.session_state.nav_menu
if menu == "HOME": view_home()
elif menu == "LIST": view_list()
elif menu == "CHAT": view_chat()
elif menu == "GARDEN": view_garden()
elif menu == "RELATION": view_relation()

# === [하단 내비게이션 바 (안전한 버전)] ===
# HTML/JS 버튼 대신 Streamlit Native 버튼 사용 (모바일 작동 100% 보장)
st.markdown("---")
st.markdown("""
<style>
/* 하단 버튼 스타일을 아이콘처럼 보이게 조정 */
div[data-testid="stHorizontalBlock"] > div > button {
    width: 100%;
    border: none;
    background-color: transparent;
    font-size: 20px;
}
</style>
""", unsafe_allow_html=True)

# 4개의 컬럼으로 하단바 구성 (이모지로 대체)
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🏠\n홈", key="nav_home", use_container_width=True): 
        st.session_state.nav_menu = "HOME"; st.rerun()
with c2:
    if st.button("💬\n대화", key="nav_list", use_container_width=True): 
        if st.session_state.selected_persona: st.session_state.nav_menu = "LIST"
        else: st.session_state.nav_menu = "HOME"
        st.rerun()
with c3:
    if st.button("🌿\n정원", key="nav_garden", use_container_width=True): 
        st.session_state.nav_menu = "GARDEN"; st.rerun()
with c4:
    if st.button("🔍\n분석", key="nav_rel", use_container_width=True): 
        st.session_state.nav_menu = "RELATION"; st.rerun()
