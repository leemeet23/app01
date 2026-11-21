import streamlit as st
from openai import OpenAI

# ==========================================
# [설정 영역] 여기에 OpenAI API 키를 직접 입력하세요
# ==========================================
OPENAI_API_KEY = "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"
# ==========================================

# 페이지 기본 설정
st.set_page_config(page_title="AI 음성 상담소", page_icon="🎙️", layout="centered")

st.title("🎙️ AI 음성 기초 상담소")
st.caption("마이크로 고민을 말씀하시면 AI가 음성을 인식하고 따뜻한 기초 상담을 진행해 드립니다.")

# API 키 유효성 체크
if not OPENAI_API_KEY or "여기에_OPENAI" in OPENAI_API_KEY:
    st.warning("⚠️ 코드 상단의 `OPENAI_API_KEY` 변수에 실제 OpenAI API 키를 입력해 주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# 세션 상태 초기화 (대화 기록 및 중복 처리 방지용)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "당신은 따뜻하고 공감 능력이 뛰어난 전문 심리·고민 상담사입니다. "
                "내담자의 음성에서 변환된 텍스트를 바탕으로 감정에 깊이 공감해 주고, "
                "마음을 다독이는 위로와 함께 현실적이고 긍정적인 기초 상담 내용을 한국어로 3~5문장 내외로 작성해 주세요."
            ),
        }
    ]

if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

# 사이드바: 상담 초기화 버튼
with st.sidebar:
    st.header("⚙️ 상담 관리")
    if st.button("🗑️ 상담 기록 초기화", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.last_audio_bytes = None
        st.rerun()
    st.info("마이크 아이콘을 눌러 녹음을 시작하고, 정지 버튼을 누르면 자동으로 음성을 분석해 상담을 시작합니다.")

# 기존 상담 대화 내역 출력 (system 메시지 제외)
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# 마이크 음성 입력 위젯
audio_value = st.audio_input("🎤 마이크 버튼을 눌러 고민을 말씀해 주세요")

if audio_value is not None:
    audio_bytes = audio_value.getvalue()

    # 동일한 녹음 파일이 리런(rerun) 시 중복 처리되지 않도록 방지
    if audio_bytes != st.session_state.last_audio_bytes:
        st.session_state.last_audio_bytes = audio_bytes

        # 1. OpenAI 음성 인식 (STT)
        with st.spinner("음성을 텍스트로 변환하고 있습니다..."):
            try:
                transcription = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",  # 필요시 "whisper-1" 또는 "gpt-4o-transcribe"로 변경 가능
                    file=audio_value,
                    language="ko"
                )
                user_text = transcription.text.strip()
            except Exception as e:
                st.error(f"음성 인식 중 오류가 발생했습니다: {e}")
                st.stop()

        if not user_text:
            st.warning("인식된 음성이 없습니다. 마이크 상태를 확인하고 다시 말씀해 주세요.")
        else:
            # 인식된 사용자 음성 화면에 표시 및 기록 저장
            st.session_state.messages.append({"role": "user", "content": user_text})
            with st.chat_message("user"):
                st.write(user_text)

            # 2. OpenAI 기초 상담 답변 생성
            with st.chat_message("assistant"):
                with st.spinner("AI 상담사가 답변을 작성하고 있습니다..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=st.session_state.messages,
                            temperature=0.7
                        )
                        ai_reply = response.choices[0].message.content.strip()
                        st.write(ai_reply)

                        # AI 답변 기록 저장
                        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    except Exception as e:
                        st.error(f"상담 답변 생성 중 오류가 발생했습니다: {e}")