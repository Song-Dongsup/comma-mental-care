import streamlit as st

def apply_pro_css():
    st.markdown("""
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

        html, body, [class*="css"] {
            font-family: 'Pretendard', sans-serif;
            color: #333333;
        }
        
        /* 메인 컨테이너 여백 조정 (모바일 최적화) */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 5rem !important;
            max-width: 600px;
        }
        
        /* 헤더 숨김 */
        header {visibility: hidden;}

        /* --- [UI 컴포넌트] 페르소나 카드 --- */
        .persona-card {
            background-color: white;
            border-radius: 15px;
            padding: 10px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 10px;
            cursor: pointer;
        }
        .persona-img {
            width: 80px; 
            height: 80px; 
            border-radius: 50%; 
            object-fit: cover;
            margin-bottom: 5px;
        }
        
        /* --- [UI 컴포넌트] 채팅방 리스트 카드 (카톡 스타일) --- */
        .chat-list-item {
            background-color: white;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid #F0F0F0;
            display: flex;
            align-items: center;
            transition: 0.2s;
        }
        .chat-list-item:hover {
            background-color: #FAFAFA;
        }

        /* --- [UI 컴포넌트] 하단 내비게이션 바 --- */
        /* 스트림릿 기본 버튼 스타일을 아이콘처럼 변경 */
        div[data-testid="column"] > button {
            width: 100%;
            border: none;
            background: transparent;
            font-size: 24px; 
            padding: 5px 0;
        }
        div[data-testid="column"] > button:hover {
            background-color: #F5F5F5;
            color: #FF4B4B;
        }
        div[data-testid="column"] > button:active, div[data-testid="column"] > button:focus {
            background-color: transparent;
            color: #FF4B4B;
            border: none;
            outline: none;
            box-shadow: none;
        }

        /* 말풍선 스타일 (이전과 동일 유지) */
        [data-testid="stChatMessageContent"] {
            padding: 12px 16px !important;
            border-radius: 20px !important;
            font-size: 14px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        [data-testid="stChatMessage"][data-testid*="assistant"] [data-testid="stChatMessageContent"] {
            background-color: #E8EAF6 !important;
        }
        [data-testid="stChatMessage"][data-testid*="user"] {
            flex-direction: row-reverse;
        }
        [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageAvatar"] {
            display: none;
        }
        [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
            background-color: #FCE4EC !important;
        }
        </style>
    """, unsafe_allow_html=True)
