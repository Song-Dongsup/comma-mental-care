import streamlit as st

def apply_pro_css():
    st.markdown("""
        <style>
        /* --- 전체 앱 스타일 --- */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

        html, body, [class*="css"] {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
            color: #333333;
        }

        /* 메인 영역 배경 및 여백 */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
            max-width: 700px;
        }

        /* 헤더 숨김 및 상단 여백 제거 */
        header {visibility: hidden;}
        [data-testid="stViewContainer"] > section:first-child {
             padding-top: 0 !important;
        }

        /* --- 커스텀 헤더 --- */
        .custom-header {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 15px 0;
            background-color: #FFFFFF;
            border-bottom: 1px solid #EEE;
            margin-bottom: 20px;
            position: sticky;
            top: 0;
            z-index: 999;
        }
        .header-logo-img {
            height: 40px;
            object-fit: contain;
        }

        /* --- 스플래시 화면 (로딩) --- */
        .fixed-splash {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: #FFFFFF;
            display: flex;
            flex-direction: column; /* 위아래 배치 */
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .splash-gif {
            width: 150px; /* 로고 크기 조절 */
            margin-bottom: 20px;
            /* 두근거리는 애니메이션 효과 */
            animation: heartbeat 1.5s ease-in-out infinite both;
        }
        .splash-text {
            font-size: 18px;
            color: #888888; /* 회색 텍스트 */
            font-weight: 500;
        }
        @keyframes heartbeat {
            from { transform: scale(1); transform-origin: center center; animation-timing-function: ease-out; }
            10% { transform: scale(1.05); animation-timing-function: ease-in; }
            17% { transform: scale(1); animation-timing-function: ease-out; }
            33% { transform: scale(1.05); animation-timing-function: ease-in; }
            45% { transform: scale(1); animation-timing-function: ease-out; }
        }

        /* --- 채팅 메시지 스타일 --- */
        /* 1. 기본 컨테이너 스타일 제거 */
        [data-testid="stChatMessage"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin-bottom: 10px !important;
        }

        /* 2. 아바타 스타일 */
        [data-testid="stChatMessageAvatar"] {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
        }

        /* 3. 메시지 내용 컨테이너 (말풍선) 공통 스타일 */
        [data-testid="stChatMessageContent"] {
            padding: 12px 16px !important;
            border-radius: 20px !important; /* 모서리 20px */
            font-size: 14px !important; /* 글자 크기 14pt */
            line-height: 1.5 !important;
            max-width: 80%;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        /* 4. AI (Assistant) 메시지 스타일 - 왼쪽 */
        [data-testid="stChatMessage"][data-testid*="assistant"] {
            flex-direction: row;
        }
        [data-testid="stChatMessage"][data-testid*="assistant"] [data-testid="stChatMessageContent"] {
            background-color: #E8EAF6 !important; /* 네이비 블루 음영 20% */
            color: #333333 !important;
            border-top-left-radius: 5px !important; /* 왼쪽 상단 꼬리 느낌 시도 */
            margin-right: auto; /* 왼쪽 정렬 */
        }

        /* 5. 사용자 (User) 메시지 스타일 - 오른쪽 */
        [data-testid="stChatMessage"][data-testid*="user"] {
            flex-direction: row-reverse; /* 아이콘 오른쪽에 배치 */
        }
        [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageAvatar"] {
            margin-right: 0;
            margin-left: 10px;
            display: none; /* 사용자 아이콘 숨김 (깔끔하게) */
        }
        [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
            background-color: #FCE4EC !important; /* 버건디 레드 음영 20% */
            color: #333333 !important;
            border-top-right-radius: 5px !important; /* 오른쪽 상단 꼬리 느낌 시도 */
            margin-left: auto; /* 오른쪽 정렬 */
        }

        /* --- 사이드바 스타일 --- */
        [data-testid="stSidebar"] {
            background-color: #F9FAFB;
            padding-top: 2rem;
        }
        [data-testid="stSidebar"] hr {
            margin: 1.5rem 0;
        }
        /* 버튼 스타일 */
        .stButton > button {
            border-radius: 10px;
            border: none;
            background-color: #FFFFFF;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            color: #555;
            padding: 0.5rem 1rem;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background-color: #F0F2F6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
            color: #FF4B4B;
        }
        /* 입력창 스타일 */
        .stTextInput > div > div > input, .stSelectbox > div > div > div, .stTextArea > div > div > textarea {
            border-radius: 10px;
            border: 1px solid #EEE;
        }
        /* 하단 채팅 입력창 */
        [data-testid="stChatInput"] {
            bottom: 20px;
        }
        [data-testid="stChatInput"] > div > div {
            border-radius: 25px;
            border: 1px solid #DDD;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)
