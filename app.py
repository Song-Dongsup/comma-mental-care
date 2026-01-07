import streamlit as st
import time
import os
import google.generativeai as genai
from datetime import datetime
import uuid
import json

import config
import database
import personas
import styles

# 1. 설정 및 초기화
st.set_page_config(page_title="Comma", layout="centered", initial_sidebar_state="collapsed")
styles.apply_pro_css()

# 세션 상태 초기화
if "user" not in st.session_state:
    st.session_state.user = "Guest"
if "app_state" not in st.session_state:
    st.session_state.app_state = "SPLASH"
if "page_mode" not in st.session_state:
    st.session_state.page_mode = "CHAT"
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "transfer_situation" not in st.session_state:
    st.session_state.transfer_situation = ""

# API 설정
try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
except Exception:
    pass

# 2. 데이터 로드 및 유저 데이터 안전 생성
all_data = database.load_all_data()

# [수정] 유저 정보가 없으면 에러 없이 즉시 생성
if st.session_state.user not in all_data:
    all_data[st.session_state.user] = {
        "sessions": {}, 
        "total_exp": 0, 
        "mood_calendar": {}
    }
    database.save_all_data(all_data)

# --- 헬퍼 함수 ---
def get_tree_level(exp):
    if exp < 50: return "🌱 씨앗", "시작이 반이에요."
    elif exp < 150: return "🌿 새싹", "마음의 싹이 트고 있어요."
    elif exp < 300: return "🌳 묘목", "줄기가 단단해지고 있어요."
    else: return "🌲 나무", "당신의 마음은 숲이 되었습니다."

def get_warm_summary(messages, persona_name):
    if not messages: return "오늘도 수고했어요."
    chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-5:]])
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        response = model.generate_content(f"상담 내용 요약 및 격려 한 문장 (해요체): {chat_history}")
        return response.text.strip()
    except:
        return "당신의 이야기를 들어줄 수 있어 기뻤습니다."

def analyze_chat_for_garden(messages, persona_name):
    if not messages: return None
    chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-10:]])
    
    prompt = f"""
    당신은 심리 상담 분석가입니다. 아래 상담 내용을 바탕으로 다음 3가지를 JSON 형식으로 출력하세요.
    1. summary: 위로와 격려의 한 문장 (해요체)
    2. emotion: 핵심 감정 단어 (예: 편안함, 불안)
    3. color: 감정 컬러 코드 (HEX)
    4. mission: 쉬운 행동 미션 1개

    [대화 내용] {chat_history}
    """
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        response = model.generate_content(
            prompt, 
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except:
        return {
            "summary": "수고하셨습니다.", "emotion": "평온", "color": "#E3F2FD", "mission": "심호흡하기"
        }

def analyze_other_person(target, situation):
    prompt = f"""
    당신은 인간관계 심리 전문가입니다. '대상'과 '상황'을 분석하세요.
    
    [대상]: {target}
    [상황]: {situation}
    
    다음 3가지 항목을 JSON으로 출력하세요. (각 항목 2~3문장)
    1. hidden_mind: 상대방의 무의식적 속마음/의도
    2. reason: 그런 행동을 한 배경/결핍
    3. advice: 사용자의 현명한 대처법
    
    Output JSON Format:
    {{
        "hidden_mind": "...",
        "reason": "...",
        "advice": "..."
    }}
    """
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "hidden_mind": f"분석 중 오류가 발생했습니다. ({e})",
            "reason": "입력 내용이 너무 짧거나 네트워크 문제일 수 있습니다.",
            "advice": "다시 시도해주세요."
        }

def generate_short_title(user_msg):
    try:
        model = genai.GenerativeModel(config.SELECTED_MODEL)
        prompt = f"입력된 문장에서 핵심 키워드 1~2개를 뽑아 제목을 만드세요. 오직 단어만 출력하세요: {user_msg}"
        response = model.generate_content(prompt)
        cleaned_title = response.text.strip().split('\n')[0].replace('"', '').replace("'", "")
        return cleaned_title[:10]
    except:
        return user_msg[:8] + ".."

def check_relation_keywords(text):
    keywords = ["그 사람", "걔", "엄마", "아빠", "동생", "누나", "형", "언니", "오빠", 
                "친구", "팀장", "대리", "부장", "상사", "동료", "남친", "여친", "남편", 
                "아내", "애인", "싸웠", "다퉜", "화나게", "짜증나게", "이해가 안", 
                "왜 그러는지", "무슨 심리", "관계", "시댁", "처가", "자식", "아들", "딸"]
    return any(k in text for k in keywords)

# [STATE 1] 스플래시 화면
if st.session_state.app_state == "SPLASH":
    gif_b64 = database.get_image_base64("assets/images/loading.gif") if os.path.exists("assets/images/loading.gif") else ""
    st.markdown(f"""
        <div class="fixed-splash">
            <img src="data:image/gif;base64,{gif_b64}" class="splash-gif">
            <p class="splash-text">내 마음의 작은 쉼표</p>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.0)
    st.session_state.app_state = "MAIN"
    st.rerun()

# [STATE 2] 메인 화면
elif st.session_state.app_state == "MAIN":
    
    # === 사이드바 ===
    with st.sidebar:
        if os.path.exists("assets/images/logo.png"):
            st.image("assets/images/logo.png", width=100)
        
        st.subheader("내 정보")
        new_nick = st.text_input("닉네임", value=st.session_state.user)
        if new_nick != st.session_state.user:
            st.session_state.user = new_nick
            st.rerun()

        st.divider()

        # [메뉴] 네비게이션
        if st.button("💬 1:1 상담 (Chat)", use_container_width=True):
            st.session_state.page_mode = "CHAT"
            st.rerun()
            
        if st.button("🌿 마음 정원 (Garden)", use_container_width=True):
            st.session_state.page_mode = "GARDEN"
            st.rerun()

        if st.button("🔍 타인 심리 분석 (Why?)", use_container_width=True):
            st.session_state.page_mode = "RELATION"
            st.rerun()
            
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

        # 대화 목록 관리
        if "sessions" not in all_data[st.session_state.user]:
            all_data[st.session_state.user]["sessions"] = {}
        
        if selected_persona_name not in all_data[st.session_state.user]["sessions"]:
            all_data[st.session_state.user]["sessions"][selected_persona_name] = []
        
        user_sessions = all_data[st.session_state.user]["sessions"][selected_persona_name]

        if st.session_state.page_mode == "CHAT":
            st.subheader(f"{selected_persona_name}와의 기록")
            if st.button("➕ 새 대화 시작하기", use_container_width=True):
                new_session_id = str(uuid.uuid4())
                new_session = {
                    "id": new_session_id,
                    "created_at": datetime.now().strftime("%m/%d %H:%M"),
                    "title": "새로운 대화",
                    "is_completed": False,
                    "messages": []
                }
                user_sessions.insert(0, new_session) 
                database.save_all_data(all_data)
                st.session_state.current_session_id = new_session_id
                st.rerun()

            for idx, session in enumerate(user_sessions):
                sess_title = session.get('title', session['created_at'])
                if session.get('is_completed', False): sess_title = f"✔️ {sess_title}"
                c1, c2 = st.columns([4, 1])
                with c1:
                    is_active = (st.session_state.current_session_id == session['id'])
                    if st.button(f"📂 {sess_title}", key=f"sel_{session['id']}", use_container_width=True):
                        st.session_state.current_session_id = session['id']
                        st.rerun()
                with c2:
                    if st.button("x", key=f"del_{session['id']}"):
                        user_sessions.pop(idx)
                        if st.session_state.current_session_id == session['id']:
                            st.session_state.current_session_id = None
                        database.save_all_data(all_data)
                        st.rerun()

        st.divider()
        my_exp = database.get_user_exp(st.session_state.user)
        lvl, _ = get_tree_level(my_exp)
        st.caption(f"내 나무: {lvl} (EXP: {my_exp})")
        st.progress(min(my_exp % 100, 100) / 100)

    # === 헤더 ===
    logo_b64 = database.get_image_base64("assets/images/logo.png")
    header_profile = "https://via.placeholder.com/32"
    if os.path.exists(char_data["img"]):
        header_profile = f"data:image/png;base64,{database.get_image_base64(char_data['img'])}"
    
    st.markdown(f"""
        <div class="custom-header">
            <div class="header-icon">☰</div>
            <div class="header-logo-container">
                <img src="data:image/png;base64,{logo_b64}" class="header-logo-img">
            </div>
            <img src="{header_profile}" class="header-profile-img">
        </div>
    """, unsafe_allow_html=True)

    # === [PAGE 1] CHAT 모드 ===
    if st.session_state.page_mode == "CHAT":
        if not st.session_state.current_session_id:
            if user_sessions:
                st.session_state.current_session_id = user_sessions[0]['id']
            else:
                new_session_id = str(uuid.uuid4())
                new_session = {"id": new_session_id, "created_at": datetime.now().strftime("%m/%d %H:%M"), "title": "새로운 대화", "is_completed": False, "messages": []}
                user_sessions.insert(0, new_session)
                database.save_all_data(all_data)
                st.session_state.current_session_id = new_session_id
            st.rerun()

        active_session = next((s for s in user_sessions if s['id'] == st.session_state.current_session_id), None)
        
        if active_session:
            current_messages = active_session['messages']
            is_completed = active_session.get('is_completed', False)
            
            if not current_messages:
                greeting = f"안녕하세요 {st.session_state.user}님, 오늘 기분은 어때요?"
                if "가족" in category and my_gender: greeting = f"우리 {my_gender}, 오늘 기분은 좀 어때?"
                current_messages.append({"role": "assistant", "content": greeting})
                database.save_all_data(all_data)

            for m in current_messages:
                avatar = char_data.get("img") if m["role"] == "assistant" and os.path.exists(char_data.get("img", "")) else None
                with st.chat_message(m["role"], avatar=avatar):
                    st.markdown(m["content"])
            
            if len(current_messages) > 2 and not is_completed:
                if st.button("✨ 멘탈 성장 (대화 종료)", use_container_width=True):
                    with st.spinner("마음의 양식을 쌓는 중..."):
                        earned = len(current_messages) * 3
                        database.update_user_exp(st.session_state.user, earned)
                        analysis_result = analyze_chat_for_garden(current_messages, selected_persona_name)
                        active_session['is_completed'] = True
                        database.save_all_data(all_data)
                        st.session_state.temp_result = {"earned": earned, "analysis": analysis_result}
                        st.session_state.page_mode = "GARDEN"
                        st.rerun()

            if is_completed:
                st.info("✅ 종료된 상담입니다. 사이드바에서 새 대화를 시작해보세요.")
            else:
                if prompt := st.chat_input("메시지 입력..."):
                    has_relation_keyword = check_relation_keywords(prompt)
                    current_messages.append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)

                    if len(current_messages) == 2:
                        active_session['title'] = generate_short_title(prompt)
                        database.save_all_data(all_data)

                    ai_avatar = char_data.get("img") if os.path.exists(char_data.get("img", "")) else None
                    with st.chat_message("assistant", avatar=ai_avatar):
                        msg_box = st.empty()
                        full_res = ""
                        try:
                            sys_prompt = char_data['base_msg']
                            if custom_context: sys_prompt += f"\n[설정]: {custom_context}"
                            if my_gender: sys_prompt += f"\n[User Info]: 나는 {my_gender}입니다."
                            model = genai.GenerativeModel(config.SELECTED_MODEL, system_instruction=sys_prompt)
                            chat = model.start_chat(history=[{"role": "user" if m["role"]=="user" else "model", "parts": [m["content"]]} for m in current_messages[:-1]])
                            response = chat.send_message(prompt, stream=True)
                            for chunk in response:
                                full_res += chunk.text
                                msg_box.markdown(full_res + "▌")
                            msg_box.markdown(full_res)
                            current_messages.append({"role": "assistant", "content": full_res})
                            database.save_all_data(all_data)
                        except Exception as e:
                            st.error(f"Error: {e}")
                    
                    if has_relation_keyword:
                        with st.chat_message("assistant", avatar="🔍"):
                            st.markdown(f"**상대방 때문에 고민이 많으신가요?**\n\n방금 하신 이야기를 바탕으로 바로 심리 분석을 받아보실 수 있어요.")
                            if st.button("🔍 이 내용으로 바로 분석하기", key=f"rec_{len(current_messages)}"):
                                st.session_state.transfer_situation = prompt
                                st.session_state.page_mode = "RELATION"
                                st.rerun()

    # === [PAGE 2] GARDEN 모드 ===
    elif st.session_state.page_mode == "GARDEN":
        curr_exp = database.get_user_exp(st.session_state.user)
        lvl_name, lvl_msg = get_tree_level(curr_exp)
        earned = st.session_state.temp_result.get("earned", 0) if "temp_result" in st.session_state else 0
        analysis = st.session_state.temp_result.get("analysis", {}) if "temp_result" in st.session_state else {}
        
        summary = analysis.get("summary", "마음을 가꾸는 시간은 언제나 소중합니다.")
        mood_color = analysis.get("color", "#EEE")
        mood_text = analysis.get("emotion", "평온")
        mission_text = analysis.get("mission", "잠시 하늘 바라보기")
        
        st.subheader("🌿 마음 정원")
        st.markdown(f"""<div style="background-color:#F1F8E9; padding:30px; border-radius:20px; text-align:center;"><div style="font-size:80px;">🌳</div><h2 style="color:#2E7D32; margin:0;">{lvl_name}</h2><p>"{lvl_msg}"</p><h1 style="color:#33691E;">+{earned} Point</h1></div>""", unsafe_allow_html=True)
        st.info(f"💌 {selected_persona_name}의 메시지: {summary}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎨 감정 색깔 남기기"):
                database.save_mood_entry(st.session_state.user, datetime.now().strftime("%Y-%m-%d"), {"color": mood_color, "emotion": mood_text})
                st.success(f"오늘의 색: {mood_text}")
        with col2:
            if st.button("🏃 기분 전환 미션"):
                st.success(f"미션: {mission_text}"); st.balloons()
        
        st.subheader("📅 내 감정의 흐름")
        calendar_data = database.get_mood_calendar(st.session_state.user)
        if calendar_data:
            cols = st.columns(7)
            sorted_dates = sorted(calendar_data.keys())[-7:]
            for i, date_key in enumerate(sorted_dates):
                with cols[i]: st.markdown(f"""<div style="text-align:center;"><div style="width:25px;height:25px;background-color:{calendar_data[date_key]['color']};border-radius:50%;margin:auto;"></div><div style="font-size:9px;">{date_key[5:]}</div></div>""", unsafe_allow_html=True)
        
        if st.button("💬 대화 목록으로 돌아가기", use_container_width=True):
            st.session_state.page_mode = "CHAT"; st.rerun()

    # === [PAGE 3] RELATION 모드 ===
    elif st.session_state.page_mode == "RELATION":
        st.subheader("🔍 타인 심리 분석 (Why?)")
        st.markdown('<div style="background-color:#E8EAF6; padding:15px; border-radius:10px; margin-bottom:20px;"><p style="margin:0; font-size:14px; color:#3F51B5;"><b>"도대체 저 사람은 왜 저럴까?"</b><br>이해가 안 되는 상대방의 말과 행동을 입력해보세요.</p></div>', unsafe_allow_html=True)

        with st.form("relation_form"):
            target_name = st.text_input("누구인가요?", placeholder="예: 김부장님, 내 동생")
            situation = st.text_area("어떤 행동을 했나요?", value=st.session_state.transfer_situation, height=150)
            submitted = st.form_submit_button("🔍 심리 분석하기", use_container_width=True)

            if submitted:
                if not target_name or not situation: st.warning("대상과 상황을 모두 입력해주세요.")
                else:
                    with st.spinner(f"{target_name}님의 심리를 분석하는 중..."):
                        result = analyze_other_person(target_name, situation)
                        st.markdown(f"""<div style="background-color:#FFF3E0; padding:20px; border-radius:15px; border-left: 5px solid #FF9800; margin-bottom:15px;"><h4>💭 속마음</h4><p>{result.get('hidden_mind', '분석 불가')}</p></div>""", unsafe_allow_html=True)
                        st.markdown(f"""<div style="background-color:#E3F2FD; padding:20px; border-radius:15px; border-left: 5px solid #2196F3; margin-bottom:15px;"><h4>💧 원인</h4><p>{result.get('reason', '분석 불가')}</p></div>""", unsafe_allow_html=True)
                        st.markdown(f"""<div style="background-color:#F3E5F5; padding:20px; border-radius:15px; border-left: 5px solid #9C27B0; margin-bottom:15px;"><h4>💡 대처법</h4><p>{result.get('advice', '분석 불가')}</p></div>""", unsafe_allow_html=True)
                        st.session_state.transfer_situation = "" # 분석 완료 후 초기화
