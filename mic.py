import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(page_title="AI 음성 상담소", page_icon="🎙️", layout="centered")

st.title("🎙️ AI 음성 기초 상담소")
st.caption("마이크로 고민을 말씀하시면 AI가 음성을 인식하고 따뜻한 기초 상담을 진행해 드립니다.")

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

# 왼쪽 사이드바: API 키 입력 및 상담 관리
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input(
        "🔑 OpenAI API Key 입력",
        type="password",
        placeholder="sk-...",
        help="OpenAI 플랫폼에서 발급받은 API 키를 입력하세요. 입력한 키는 저장되지 않습니다."
    )

    st.divider()

    if st.button("🗑️ 상담 기록 초기화", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.last_audio_bytes = None
        st.rerun()

    st.info("1. 위 입력창에 OpenAI API 키를 입력하세요.\n2. 마이크 버튼을 눌러 고민을 말씀하시고 정지 버튼을 누르면 AI 상담이 시작됩니다.")

# API 키 입력 여부 확인
if not api_key:
    st.warning("👈 왼쪽 사이드바에 OpenAI API 키를 입력해 주세요.")
    st.stop()

client = OpenAI(api_key=api_key.strip())

# 기존 상담 대화 내역 출력 (system 메시지 제외)
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# 마이크 음성 입력 위젯
audio_value = st.audio_input("🎤 마이크 버튼을 눌러 고민을 말씀해 주세요")

if audio_value is not None:
    audio_bytes = audio_value.getvalue()

    # 동일한 녹음 파일이 중복 처리되지 않도록 방지
    if audio_bytes != st.session_state.last_audio_bytes:
        st.session_state.last_audio_bytes = audio_bytes

        # 1. OpenAI 음성 인식 (STT)
        with st.spinner("음성을 텍스트로 변환하고 있습니다..."):
            try:
                transcription = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",
                    file=audio_value,
                    language="ko"
                )
                user_text = transcription.text.strip()
            except Exception as e:
                st.error(f"음성 인식 중 오류가 발생했습니다 (API 키를 확인해 주세요): {e}")
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