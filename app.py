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

# --- [이미지 매핑 함수: 파트너님 파일명 반영] ---
def get_persona_image_path(name):
    # 파트너님이 올리신 파일명과 페르소나 이름 매칭
    mapping = {
        "부처님": "buddha.jpg",
        "히딩크 감독": "hiddink.jpg",
        "워렌 버핏": "워렌버핏.jpg", # 또는 '어두운 서재 워렌버핏.jpg'
        "철학자": "철학자.jpg", # 소크라테스 등
        "예수님": "jesus.jpg",
        "법륜스님": "법륜스님.jpeg",
        "정신과 전문의": "doctor.jpg", # 기본 페르소나
        "상담사": "doctor.jpg"
    }
    filename = mapping.get(name, "logo.png") # 없으면 로고
    return f"assets/images/{filename}"

# --- [화면 1: HOME - 페르소나 선택 (디자인 반영)] ---
def view_home():
    # 검색창 스타일 (장식용)
    st.markdown("""
        <div style="background-color:#F0F2F6; padding:10px 15px; border-radius:10px; color:#888; margin-bottom:20px; font-size:14px;">
            🔍 검색
        </div>
    """, unsafe_allow_html=True)

    # 메인 배너 (부처님 이미지 활용 예시)
    banner_img = database.get_image_base64("assets/images/buddha.jpg")
    if banner_img:
        st.markdown(f"""
        <div style="position:relative; width:100%; height:150px; border-radius:15px; overflow:hidden; margin-bottom:25px;">
            <img src="data:image/jpeg;base64,{banner_img}" style="width:100%; height:100%; object-fit:cover; opacity:0.9;">
            <div style="position:absolute; top:40%; left:20px; color:white; font-weight:bold; font-size:24px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">
                당신의 상담사
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("상담사 선택 >")
    
    # 카테고리별 페르소나 그리드 표시
    categories = list(personas.PERSONA_LIBRARY.keys())
    
    # 탭 대신 전체 나열 (스크롤 방식)
    for cat in categories:
        st.markdown(f"**{cat}**")
        p_names = list(personas.PERSONA_LIBRARY[cat].keys())
        
        # 3열 그리드로 배치 (보내주신 UI와 유사하게)
        cols = st.columns(3)
        for i, name in enumerate(p_names):
            char = personas.PERSONA_LIBRARY[cat][name]
            img_path = get_persona_image_path(name)
            
            # 이미지 로드
            if os.path.exists(img_path):
                img_b64 = database.get_image_base64(img_path)
            else:
                img_b64 = database.get_image_base64("assets/images/logo.png")

            with cols[i % 3]:
                # 원형 이미지 + 이름 UI
                st.markdown(f"""
                <div style="display:flex; flex-direction:column; align-items:center; margin-bottom:15px;">
                    <div style="width:70px; height:70px; border-radius:50%; overflow:hidden; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
                        <img src="data:image/jpeg;base64,{img_b64}" style="width:100%; height:100%; object-fit:cover;">
                    </div>
                    <div style="margin-top:8px; font-weight:600; font-size:14px; text-align:center;">{name}</div>
                    <div style="font-size:10px; color:#888; text-align:center;">{char.get('description', '')[:10]}..</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 투명 버튼으로 클릭 기능 구현
                if st.button(f"대화하기_{name}", key=f"btn_{cat}_{name}", help=f"{name}님과 대화하기"):
                    st.session_state.selected_persona = name
                    st.session_state.selected_cat = cat
                    st.session_state.nav_menu = "LIST"
                    st.rerun()
        st.write("") # 간격

# --- [화면 2: LIST - 채팅 목록] ---
def view_list():
    st.subheader("대화 목록")
    if not st.session_state.selected_persona:
        st.info("먼저 상담사를 선택해주세요.")
        if st.button("상담사 선택하러 가기"): st.session_state.nav_menu = "HOME"; st.rerun()
        return

    curr = st.session_state.selected_persona
    
    # 상단 선택된 페르소나 프로필 카드
    img_path = get_persona_image_path(curr)
    img_b64 = database.get_image_base64(img_path) if os.path.exists(img_path) else ""
    
    st.markdown(f"""
    <div style="background-color:white; padding:15px; border-radius:15px; display:flex; align-items:center; box-shadow:0 2px 5px rgba(0,0,0,0.05); margin-bottom:20px;">
        <img src="data:image/jpeg;base64,{img_b64}" style="width:60px; height:60px; border-radius:50%; object-fit:cover; margin-right:15px;">
        <div>
            <div style="font-weight:bold; font-size:18px;">{curr}</div>
            <div style="color:#666; font-size:12px;">지금 대화를 시작해보세요.</div>
        </div>
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
    
    # 목록 표시
    if "sessions" in all_data[st.session_state.user] and curr in all_data[st.session_state.user]["sessions"]:
        sessions = all_data[st.session_state.user]["sessions"][curr]
        for s in sessions:
            with st.container():
                c1, c2, c3 = st.columns([5, 1.5, 1])
                c1.markdown(f"**{s['title']}**\n<span style='color:#888; font-size:12px'>{s['created_at']}</span>", unsafe_allow_html=True)
                if c2.button("입장", key=f"ent_{s['id']}"):
                    st.session_state.current_session_id = s['id']; st.session_state.nav_menu = "CHAT"; st.rerun()
                if c3.button("🗑", key=f"del_{s['id']}"):
                    sessions.remove(s); database.save_all_data(all_data); st.rerun()
                st.markdown("---")

# --- [화면 3: CHAT] ---
def view_chat():
    if not st.session_state.current_session_id: st.session_state.nav_menu = "LIST"; st.rerun()
    
    # 상단 헤더
    p_name = st.session_state.selected_persona
    st.markdown(f"""
    <div style="padding:10px 0; border-bottom:1px solid #EEE; margin-bottom:15px; display:flex; align-items:center;">
        <span style="font-size:18px; font-weight:bold;">{p_name}</span>
    </div>
    """, unsafe_allow_html=True)
    
    cat = st.session_state.get('selected_cat', list(personas.PERSONA_LIBRARY.keys())[0])
    char = personas.PERSONA_LIBRARY[cat][p_name]
    img_path = get_persona_image_path(p_name)
    
    sessions = all_data[st.session_state.user]["sessions"][p_name]
    active = next((s for s in sessions if s['id'] == st.session_state.current_session_id), None)
    
    # 메시지 표시
    for m in active['messages']:
        avatar = img_path if m['role']=='assistant' and os.path.exists(img_path) else None
        with st.chat_message(m['role'], avatar=avatar): st.markdown(m['content'])
        
    # 입력 및 응답
    if not active.get('is_completed', False):
        if prompt := st.chat_input("메시지 입력..."):
            active['messages'].append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            if len(active['messages']) == 2:
                active['title'] = generate_title(prompt); database.save_all_data(all_data)
            
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

# --- [화면 4, 5: GARDEN, RELATION] (간략 유지) ---
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

# --- [하단 내비게이션 바 (HTML/CSS + Hidden Buttons)] ---
st.markdown('<div style="height: 80px;"></div>', unsafe_allow_html=True) # 여백

# 아이콘 이미지 로드 (없으면 텍스트 대체)
def load_icon(name):
    path = f"assets/images/{name}"
    if os.path.exists(path):
        return f"data:image/png;base64,{database.get_image_base64(path)}"
    return ""

icon_home = load_icon("icon_home.png")
icon_chat = load_icon("icon_chat.png")
icon_garden = load_icon("icon_garden.png")
icon_analysis = load_icon("icon_analysis.png")

# CSS 스타일 (고퀄리티 하단바)
st.markdown("""
<style>
.bottom-nav {
    position: fixed; bottom: 0; left: 0; width: 100%;
    background: white; border-top: 1px solid #EEE;
    display: flex; justify-content: space-around;
    padding: 12px 0; z-index: 999;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.03);
}
.nav-btn {
    background: none; border: none; cursor: pointer;
    display: flex; flex-direction: column; align-items: center;
}
.nav-img { width: 24px; height: 24px; margin-bottom: 4px; }
.nav-txt { font-size: 10px; color: #999; }
.nav-btn.active .nav-txt { color: #333; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 하단바 HTML 출력
st.markdown(f"""
<div class="bottom-nav">
    <button class="nav-btn {'active' if menu=='HOME' else ''}" onclick="document.getElementById('btn_home').click()">
        <img src="{icon_home}" class="nav-img"><span class="nav-txt">홈</span>
    </button>
    <button class="nav-btn {'active' if menu=='LIST' else ''}" onclick="document.getElementById('btn_list').click()">
        <img src="{icon_chat}" class="nav-img"><span class="nav-txt">대화</span>
    </button>
    <button class="nav-btn {'active' if menu=='GARDEN' else ''}" onclick="document.getElementById('btn_garden').click()">
        <img src="{icon_garden}" class="nav-img"><span class="nav-txt">정원</span>
    </button>
    <button class="nav-btn {'active' if menu=='RELATION' else ''}" onclick="document.getElementById('btn_rel').click()">
        <img src="{icon_analysis}" class="nav-img"><span class="nav-txt">분석</span>
    </button>
</div>
""", unsafe_allow_html=True)

# 숨겨진 Streamlit 버튼 (로직 처리용)
with st.container():
    st.markdown('<div style="display:none;">', unsafe_allow_html=True)
    if st.button("H", key="btn_home"): st.session_state.nav_menu = "HOME"; st.rerun()
    if st.button("L", key="btn_list"): 
        if st.session_state.selected_persona: st.session_state.nav_menu = "LIST"
        else: st.session_state.nav_menu = "HOME"
        st.rerun()
    if st.button("G", key="btn_garden"): st.session_state.nav_menu = "GARDEN"; st.rerun()
    if st.button("R", key="btn_rel"): st.session_state.nav_menu = "RELATION"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
