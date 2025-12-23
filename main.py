import streamlit as st
import json
import requests
import time

# API Key 설정 (환경 변수에서 자동으로 주입됨)
const_api_key = ""

# 페이지 설정
st.set_page_config(page_title="감성 MBTI 테스트", page_icon="✨", layout="centered")

# 커스텀 CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
        background-color: #fdfbfb;
    }
    
    .stApp {
        background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
    }
    
    .main-title {
        color: #8e9aaf;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .sub-title {
        color: #6d6875;
        text-align: center;
        font-size: 1.3rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }

    .question-box {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 2.5rem;
        border-radius: 25px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }

    .stButton>button {
        background-color: #efd3d7;
        color: #6d6875;
        border: none;
        border-radius: 12px;
        padding: 0.7rem 2rem;
        font-weight: 500;
        font-size: 1rem;
        transition: all 0.3s;
        border: 1px solid transparent;
    }
    
    .stButton>button:hover {
        background-color: #ffffff;
        color: #b5838d;
        border: 1px solid #efd3d7;
        transform: translateY(-2px);
    }
    
    .result-card {
        background-color: #ffffff;
        padding: 2.5rem;
        border-radius: 30px;
        text-align: center;
        border: 2px solid #feeafa;
        box-shadow: 0 15px 30px rgba(0,0,0,0.05);
    }

    /* 로딩 애니메이션 스타일 */
    .loader {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #efd3d7;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 2s linear infinite;
        margin: 10px auto;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
""", unsafe_allow_html=True)

# MBTI 질문 데이터
questions = [
    {"q": "주말에 당신은?", "a": "밖에서 친구들을 만나는 게 최고!", "b": "집에서 혼자 재충전하는 게 좋아.", "type": "EI"},
    {"q": "새로운 사람을 만났을 때?", "a": "먼저 말을 걸고 분위기를 주도한다.", "b": "상대방이 말을 걸 때까지 기다린다.", "type": "EI"},
    {"q": "모임에서 나는 주로?", "a": "주목받는 중심 인물이 된다.", "b": "구석에서 조용히 대화를 듣는다.", "type": "EI"},
    
    {"q": "미래에 대해 생각할 때?", "a": "현실적인 계획과 현재에 집중한다.", "b": "다양한 상상과 가능성을 꿈꾼다.", "type": "SN"},
    {"q": "이야기를 들을 때 나는?", "a": "정확한 사실 위주로 듣는다.", "b": "비유나 전체적인 맥락을 본다.", "type": "SN"},
    {"q": "설명서를 읽을 때?", "a": "처음부터 끝까지 꼼꼼히 읽는다.", "b": "직관적으로 대충 훑고 시작한다.", "type": "SN"},
    
    {"q": "친구가 고민을 털어놓으면?", "a": "상황을 분석하고 해결책을 제시한다.", "b": "감정적으로 깊게 공감하고 위로한다.", "type": "TF"},
    {"q": "결정을 내릴 때 중요한 건?", "a": "논리적 근거와 효율성.", "b": "사람들의 마음과 관계.", "type": "TF"},
    {"q": "비판을 들었을 때?", "a": "내용의 타당성을 따져본다.", "b": "속상한 마음이 먼저 든다.", "type": "TF"},
    
    {"q": "여행 계획을 세울 때?", "a": "시간별로 꼼꼼하게 일정을 짠다.", "b": "큰 틀만 잡고 상황에 맞게 움직인다.", "type": "JP"},
    {"q": "방 정리 스타일은?", "a": "물건들이 제 자리에 정돈되어 있다.", "b": "필요할 때 찾는 편이고 조금 어지럽다.", "type": "JP"},
    {"q": "과제를 할 때 나는?", "a": "미리미리 계획해서 끝낸다.", "b": "마감 직전 몰입해서 처리한다.", "type": "JP"},
]

# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'scores' not in st.session_state:
    st.session_state.scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None

def generate_theme_image(prompt_text):
    """Imagen-4 모델을 사용하여 테마 이미지를 생성합니다."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={const_api_key}"
    payload = {
        "instances": [{"prompt": f"A soft pastel aesthetic digital art of {prompt_text}, dreamy atmosphere, high quality, minimal style"}],
        "parameters": {"sampleCount": 1}
    }
    
    retries = 5
    for i in range(retries):
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                img_data = result['predictions'][0]['bytesBase64Encoded']
                return f"data:image/png;base64,{img_data}"
        except Exception:
            time.sleep(2**i)
    return None

def select_answer(option, q_type):
    if q_type == "EI":
        st.session_state.scores["E" if option == "a" else "I"] += 1
    elif q_type == "SN":
        st.session_state.scores["S" if option == "a" else "N"] += 1
    elif q_type == "TF":
        st.session_state.scores["T" if option == "a" else "F"] += 1
    elif q_type == "JP":
        st.session_state.scores["J" if option == "a" else "P"] += 1
    st.session_state.step += 1

# 메인 UI 시작
st.markdown('<div class="main-title">✨ Pastel MBTI Test</div>', unsafe_allow_html=True)

if st.session_state.step < len(questions):
    progress = st.session_state.step / len(questions)
    st.progress(progress)
    
    q_data = questions[st.session_state.step]
    st.markdown(f'<div class="sub-title">Q{st.session_state.step + 1}. {q_data["q"]}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="question-box">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button(q_data["a"], use_container_width=True, key=f"q{st.session_state.step}a"):
            select_answer("a", q_data["type"])
            st.rerun()
    with col2:
        if st.button(q_data["b"], use_container_width=True, key=f"q{st.session_state.step}b"):
            select_answer("b", q_data["type"])
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # 결과 계산
    s = st.session_state.scores
    mbti = ""
    mbti += "E" if s["E"] >= s["I"] else "I"
    mbti += "S" if s["S"] >= s["N"] else "N"
    mbti += "T" if s["T"] >= s["F"] else "F"
    mbti += "J" if s["J"] >= s["P"] else "P"
    
    themes = {
        "ISTJ": ("정돈된 아침의 서재", "neat wooden library with morning sun, minimalist"),
        "ISFJ": ("포근한 담요와 차 한 잔", "cozy blanket with a cup of warm tea, soft colors"),
        "INFJ": ("새벽녘 안개 낀 숲", "mystical forest with morning fog, ethereal"),
        "INTJ": ("고요한 밤의 우주", "calm starry night sky, deep navy aesthetic"),
        "ISTP": ("시원한 바람이 부는 공방", "cool airy workshop with tools, modern industrial"),
        "ISFP": ("노을 지는 해변의 산책", "beach at sunset with soft waves, coral colors"),
        "INFP": ("꽃이 가득한 비밀 정원", "secret garden full of wildflowers, dreamy pastel"),
        "INTP": ("아이디어가 쏟아지는 화판", "creative art studio with messy sketches, intellectual"),
        "ESTP": ("활기찬 도시의 야경", "vibrant city night lights, energetic aesthetic"),
        "ESFP": ("화려한 파티의 불꽃", "sparkling party fireworks, celebratory mood"),
        "ENFP": ("무지개가 뜬 푸른 언덕", "rainbow over green hills, bright cheerful"),
        "ENTP": ("빛나는 전구 아래 토론", "glowing light bulbs in a dark room, innovative"),
        "ESTJ": ("체계적인 오피스 데스크", "organized office desk, professional blue"),
        "ESFJ": ("따뜻한 카페의 햇살", "warm cafe interior with sunlight, friendly atmosphere"),
        "ENFJ": ("햇살이 내리쬐는 광장", "sunny public square, hopeful golden colors"),
        "ENTJ": ("도시의 스카이라운지", "modern city skyline view from lounge, sophisticated")
    }
    
    result_title, img_prompt = themes.get(mbti, ("멋진 당신", "beautiful abstract pastel art"))

    st.markdown(f"""
        <div class="result-card">
            <h2 style="color: #b5838d;">당신은 <b>{mbti}</b> 타입입니다!</h2>
            <p style="font-size: 1.1rem; color: #6d6875;">당신을 닮은 테마:</p>
            <h3 style="color: #8e9aaf;">「 {result_title} 」</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # 이미지 생성 및 표시
    if st.session_state.generated_image is None:
        with st.spinner("당신만을 위한 테마 이미지를 그리고 있어요..."):
            st.session_state.generated_image = generate_theme_image(img_prompt)
    
    if st.session_state.generated_image:
        st.image(st.session_state.generated_image, use_container_width=True, caption=f"Recommended for {mbti}")
    else:
        st.info("이미지를 불러오지 못했지만, 당신의 테마는 정말 멋져요!")

    if st.button("테스트 다시 하기", use_container_width=True):
        st.session_state.step = 0
        st.session_state.scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
        st.session_state.generated_image = None
        st.rerun()

st.markdown("""
    <div style="text-align: center; margin-top: 3rem; color: #adb5bd; font-size: 0.8rem;">
        © 2024 Pastel MBTI. AI Generated Themes.
    </div>
""", unsafe_allow_html=True)
