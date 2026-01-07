import streamlit as st

def apply_pro_css():
    st.markdown("""
        <style>
        /* 1. 폰트 설정 */
        @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
        
        html, body, [class*="css"] {
            font-family: 'Pretendard', sans-serif !important;
        }

        /* 2. 전체 레이아웃 */
        .stApp {
            background-color: #F0F2F5;
        }
        
        .block-container {
            max-width: 420px !important;
            margin: 0 auto !important;
            background-color: #FFFFFF;
            min-height: 100vh;
            
            /* [핵심] 상단 여백을 없애서 헤더가 맨 위로 붙게 하되, 잘리지는 않게 함 */
            padding-top: 0 !important; 
            padding-bottom: 120px !important; 
            
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
        }

        /* 3. [핵심] Streamlit 기본 헤더 처리 (투명화 + 버튼 살리기) */
        header[data-testid="stHeader"] {
            background: transparent !important; /* 배경 투명 */
            height: 60px !important;
            z-index: 1000 !important; /* 제일 위에 둬서 버튼 클릭 가능하게 */
        }
        
        /* 헤더 안의 아이콘 색상 (잘 보이게) */
        header[data-testid="stHeader"] button {
            color: #555 !important;
        }
        
        /* 4. [핵심] 커스텀 헤더 (Sticky + 안전 여백) */
        .custom-header {
            position: sticky; /* 본문 흐름에 고정 (사이드바 밀림 대응) */
            top: 0;
            z-index: 999; /* 기본 헤더 바로 아래 */
            
            width: 100%;
            height: 60px;
            
            background-color: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(5px);
            border-bottom: 1px solid #F0F0F0;
            
            display: flex;
            align-items: center;
            justify-content: center; /* 로고 중앙 정렬 */
            
            /* [수정] 마이너스 마진 삭제 -> 로고 잘림 방지 */
            margin-top: -60px; /* 기본 헤더 자리만큼만 위로 당김 (겹치기용) */
            padding: 0;
        }
        
        /* 로고: 중앙 배치 */
        .header-logo-container {
            display: flex; 
            align-items: center; 
            justify-content: center;
            width: 100%;
        }
        
        .header-logo-img { 
            height: 24px !important; 
            width: auto !important; 
            object-fit: contain;
            /* 위쪽 여백을 살짝 줘서 화살표랑 라인 맞춤 */
            margin-top: 2px; 
        }
        
        /* 프로필: 오른쪽 절대 위치 */
        .header-profile-img { 
            position: absolute;
            right: 20px;
            width: 32px !important; 
            height: 32px !important; 
            border-radius: 50%; 
            border: 1px solid #eee;
            object-fit: cover;
        }

        /* 5. 입력창 (너비 맞춤) */
        [data-testid="stChatInput"] {
            background: white;
            /* 본문 너비에 맞춤 */
            max-width: 420px !important;
            margin: 0 auto !important;
            
            padding-bottom: 20px !important;
            border-top: 1px solid #F5F5F5;
            z-index: 1000;
        }
        
        .stChatInputContainer textarea {
            border-radius: 25px !important;
            border: 1px solid #E0E0E0 !important;
            background-color: #FAFAFA !important;
            min-height: 50px !important;
            font-size: 16px !important;
            padding: 12px 15px !important;
        }

        /* 6. 콤마 로딩 (유지) */
        @keyframes comma-bounce {
            0% { content: ","; }
            33% { content: ",,"; }
            66% { content: ",,,"; }
        }
        .comma-loading::after {
            content: ",";
            animation: comma-bounce 1.5s infinite steps(1);
            font-weight: 800;
            color: #FF6B6B;
            letter-spacing: 2px;
        }
        .loading-text {
            font-size: 14px; color: #666;
            background-color: #F8F9FA;
            padding: 12px 20px;
            border-radius: 20px;
            border-bottom-left-radius: 4px;
            display: inline-block;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }

        /* 7. 말풍선 스타일 */
        [data-testid="stChatMessage"] { padding: 0.5rem 0.5rem !important; }
        
        div[data-testid="stChatMessage"]:has(div[aria-label="user"]) {
            flex-direction: row-reverse;
        }
        div[data-testid="stChatMessage"]:has(div[aria-label="user"]) .st-emotion-cache-1c7y2kd {
            background-color: #4A90E2; color: white; 
            border-radius: 18px; border-top-right-radius: 2px;
            padding: 10px 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        div[data-testid="stChatMessage"]:has(div[aria-label="assistant"]) .st-emotion-cache-1c7y2kd {
            background-color: #F3F4F6; color: #333;
            border-radius: 18px; border-top-left-radius: 2px;
            padding: 10px 16px;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 스플래시 */
        .fixed-splash {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: white; z-index: 99999;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
        }
        .splash-gif { width: 60px !important; height: auto; }
        </style>
    """, unsafe_allow_html=True)