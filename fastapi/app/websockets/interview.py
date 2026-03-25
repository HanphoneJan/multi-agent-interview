"""Interview WebSocket handler"""
import json
import asyncio
from typing import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import selectinload

from app.core.constants import PROGRESS_AUDIO_START, PROGRESS_COMPLETE, ATTENTION_SCORE_THRESHOLD
from app.dependencies import SessionDep, get_current_user
from app.websockets.manager import manager
from app.websockets.protocol import MessageType, parse_message
from app.services.audio_service import audio_service
from app.services.video_service import video_service, video_analytics_service
from app.services.webrtc_service import webrtc_service
from app.services.qwen3_omni_http_service import get_qwen3_omni_http_service, ChatChunk
from app.core.llm_context import append_message, get_messages

router = APIRouter()


@router.websocket("/ws/interview/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str,
    db: SessionDep,
):
    """
    WebSocket endpoint for real-time interview communication.

    The token should be provided as a query parameter: ?token=your_jwt_token
    """
    # Verify token and get user
    from app.core.security import verify_token
    from app.config import get_settings
    from app.models.interview import interview_sessions, interview_scenarios

    settings = get_settings()

    # 添加调试日志
    print(f"WebSocket连接请求: session_id={session_id}, token={'已提供' if token else '未提供'}")

    if not token:
        print("WebSocket连接被拒绝: 缺少token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    payload = verify_token(token, settings.JWT_SECRET_KEY)

    if not payload:
        print(f"WebSocket连接被拒绝: token验证失败, session_id={session_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    print(f"WebSocket token验证成功: payload={payload}")

    user_id = payload.get("user_id")

    # Verify session exists and belongs to user
    # Also verify this is a NON-REALTIME interview (传统面试模式)
    result = await db.execute(
        select(
            interview_sessions,
            interview_scenarios.c.is_realtime.label("scenario_is_realtime")
        )
        .select_from(interview_sessions)
        .join(
            interview_scenarios,
            interview_sessions.c.scenario_id == interview_scenarios.c.id
        )
        .where(
            interview_sessions.c.id == int(session_id),
            interview_sessions.c.user_id == user_id
        )
    )
    row = result.first()

    if not row:
        print(f"WebSocket连接被拒绝: 会话不存在或用户不匹配, session_id={session_id}, user_id={user_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        return

    # Check if this is a realtime interview - if so, reject connection to this endpoint
    session_dict = dict(row._asdict())
    if session_dict.get("scenario_is_realtime"):
        print(f"WebSocket连接被拒绝: 实时面试请使用 /ws/interview/realtime/{session_id} 端点")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Realtime interviews must use /ws/interview/realtime endpoint"
        )
        return

    print(f"WebSocket连接成功: session_id={session_id}, user_id={user_id}, mode=non-realtime")

    # Connect WebSocket
    await manager.connect(websocket, session_id, user_id)
    await manager.send_message(
        {
            "type": MessageType.CONNECTED.value,
            "message": "Connected to interview session",
            "session_id": session_id,
        },
        session_id,
        user_id
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_dict = json.loads(data)

            # Handle message based on type
            msg_type = message_dict.get("type")

            if msg_type == MessageType.START_INTERVIEW.value:
                await handle_start_interview(session_id, user_id, db)

            elif msg_type == MessageType.PAUSE_INTERVIEW.value:
                await handle_pause_interview(session_id, user_id, db)

            elif msg_type == MessageType.RESUME_INTERVIEW.value:
                await handle_resume_interview(session_id, user_id, db)

            elif msg_type == MessageType.END_INTERVIEW.value:
                await handle_end_interview(session_id, user_id, db)
                break

            elif message_dict.get("type") == "end":
                # Handle frontend's 'end' message (compatibility)
                await handle_end_interview(session_id, user_id, db)
                break

            elif msg_type == MessageType.AUDIO.value:
                await handle_audio(message_dict, session_id, user_id)

            elif msg_type == MessageType.VIDEO_FRAME.value:
                await handle_video_frame(message_dict, session_id, user_id)

            elif msg_type == MessageType.TEXT.value:
                await handle_text(message_dict, session_id, user_id, db)

            elif message_dict.get("type") == "webrtc_offer":
                await handle_webrtc_offer(message_dict, session_id, user_id)

            elif message_dict.get("type") == "webrtc_answer":
                await handle_webrtc_answer(message_dict, session_id, user_id)

            elif message_dict.get("type") == "webrtc_ice_candidate":
                await handle_webrtc_ice(message_dict, session_id, user_id)

            elif message_dict.get("type") == "webrtc_cleanup":
                await handle_webrtc_cleanup(session_id, user_id)

            elif message_dict.get("type") == "ping":
                # Handle heartbeat ping
                manager.update_heartbeat(session_id, user_id)
                await manager.send_pong(session_id, user_id)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: session {session_id}, user {user_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.send_error(
            session_id,
            user_id,
            error="Internal error",
            error_code="INTERNAL_ERROR"
        )
    finally:
        await manager.disconnect(session_id, user_id)


# Voice mapping from frontend values to Qwen3-Omni voices
VOICE_MAPPING = {
    "standard": "Cherry",    # 标准清晰
    "deep": "Ethan",         # 低沉稳重 (male)
    "clear": "Serena",       # 清脆明亮 (female)
    "soft": "Chelsie",       # 柔和亲切 (female)
    "passionate": "Ethan",   # 激情澎湃 (male)
    "magnetic": "Ethan",     # 富有磁性 (male)
}

# Gender-based fallback voices
GENDER_VOICE_FALLBACK = {
    "male": "Ethan",
    "female": "Serena",
}


def get_voice_for_settings(settings: dict) -> str:
    """Get Qwen3-Omni voice based on user interviewer settings"""
    voice = settings.get("voice", "standard")
    gender = settings.get("gender", "male")

    # Try to get voice from mapping
    if voice in VOICE_MAPPING:
        return VOICE_MAPPING[voice]

    # Fallback to gender-based voice
    return GENDER_VOICE_FALLBACK.get(gender, "Cherry")


# Interview style modifiers for system prompt
STYLE_MODIFIERS = {
    "serious": "你是一位严肃专业的技术面试官，注重考察候选人的技术深度和专业素养。语气正式、严谨。",
    "friendly": "你是一位友善亲切的技术面试官，擅长营造轻松的面试氛围。语气温和、鼓励性强。",
    "challenging": "你是一位挑战型的技术面试官，善于提出有深度的问题来测试候选人的极限。会直接追问不足之处。",
    "guiding": "你是一位引导型的技术面试官，擅长通过提示和引导帮助候选人展现最佳水平。会给予适当的提示。",
    "technical": "你是一位技术专家型面试官，专注于考察候选人的技术细节和原理理解。问题深入且专业。",
    "boss": "你是一位高管型面试官，从管理者角度评估候选人的综合素质和潜力。关注大局观和解决问题的能力。",
}


def apply_style_to_system_prompt(base_prompt: str, style: str) -> str:
    """Apply interview style modifier to system prompt"""
    if style in STYLE_MODIFIERS:
        modifier = STYLE_MODIFIERS[style]
        return f"{modifier}\n\n{base_prompt}"
    return base_prompt


async def handle_start_interview(
    session_id: str,
    user_id: int,
    db: AsyncSession,
):
    """Handle interview start using Qwen3-Omni HTTP API"""
    from datetime import datetime, timezone
    from app.models.interview import interview_sessions, interview_questions, interview_scenarios
    from app.config import get_settings
    from app.services.auth_service import get_user_interviewer_settings

    # Get Qwen3-Omni HTTP service
    qwen3_service = get_qwen3_omni_http_service()

    # Get user's interviewer settings
    interviewer_settings = await get_user_interviewer_settings(db, user_id)
    voice = get_voice_for_settings(interviewer_settings)
    print(f"Using interviewer voice: {voice} for user {user_id}, settings: {interviewer_settings}")

    # Update session status
    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == int(session_id))
        .values(
            status="in_progress",
            start_time=datetime.now(timezone.utc)
        )
    )
    await db.commit()

    # Get scenario info for personalized first question
    scenario_name = "通用技术面试"
    scenario_description = ""
    try:
        row = (await db.execute(
            select(interview_sessions).where(interview_sessions.c.id == int(session_id))
        )).first()
        if row and getattr(row, "scenario_id", None):
            sc = (await db.execute(
                select(interview_scenarios).where(interview_scenarios.c.id == row.scenario_id)
            )).first()
            if sc:
                scenario_name = getattr(sc, "name", None) or getattr(sc, "technology_field", None) or scenario_name
                scenario_description = getattr(sc, "description", None) or ""
    except Exception as e:
        print(f"Get scenario info: {e}")

    # First question: use Qwen3-Omni if API key is set
    first_question = "请自我介绍一下"
    audio_data = None

    try:
        if get_settings().DASHSCOPE_API_KEY:
            # Build system prompt for first question
            system_prompt = qwen3_service.build_interview_system_prompt(
                scenario_name=scenario_name,
                scenario_description=scenario_description,
                is_technical=True
            )

            # Apply interview style modifier
            style = interviewer_settings.get("style", "serious")
            system_prompt = apply_style_to_system_prompt(system_prompt, style)

            # Ask Qwen3-Omni to generate first question
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请为{scenario_name}生成一个开场问题，让候选人进行自我介绍。只输出问题本身，不要有多余内容。"}
            ]

            # Collect response
            response_text = []
            audio_chunks = []

            async for chunk in qwen3_service.chat(messages, voice=voice, stream=False):
                if chunk.type == "text" and chunk.content:
                    response_text.append(chunk.content)
                elif chunk.type == "audio" and chunk.audio_data:
                    audio_chunks.append(chunk.audio_data)

            if response_text:
                first_question = "".join(response_text).strip()[:500]

            # Combine audio chunks if any
            if audio_chunks:
                audio_data = "".join(audio_chunks)

            print(f"Generated first question using Qwen3-Omni: {first_question[:100]}...")
    except Exception as e:
        print(f"Qwen3-Omni first question error: {e}, using default")
        import traceback
        traceback.print_exc()

    # Send first question (with audio if available)
    await manager.send_question(
        session_id,
        user_id,
        question=first_question,
        question_id=1,
        order=1
    )

    # Send audio separately if available
    if audio_data:
        await manager.send_message(
            {
                "type": "audio",
                "audio": audio_data,
                "text": first_question,
                "question_id": 1
            },
            session_id,
            user_id
        )

    # Create question record
    await db.execute(
        insert(interview_questions).values(
            session_id=int(session_id),
            question_text=first_question,
            question_number=1,
        )
    )
    await db.commit()

    # Persist first question in LLM context for multi-turn memory
    try:
        await append_message(session_id, "assistant", first_question)
    except Exception as e:
        print(f"LLM context append (start): {e}")


async def handle_pause_interview(
    session_id: str,
    user_id: int,
    db: AsyncSession,
):
    """Handle interview pause"""
    from datetime import datetime, timezone
    from app.models.interview import interview_sessions

    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == int(session_id))
        .values(
            status="paused",
            paused_at=datetime.now(timezone.utc)
        )
    )
    await db.commit()

    await manager.send_message(
        {"type": "info", "message": "Interview paused"},
        session_id,
        user_id
    )


async def handle_resume_interview(
    session_id: str,
    user_id: int,
    db: AsyncSession,
):
    """Handle interview resume"""
    from datetime import datetime, timezone
    from app.models.interview import interview_sessions

    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == int(session_id))
        .values(
            status="in_progress",
            resumed_at=datetime.now(timezone.utc)
        )
    )
    await db.commit()

    await manager.send_message(
        {"type": "info", "message": "Interview resumed"},
        session_id,
        user_id
    )


async def handle_end_interview(
    session_id: str,
    user_id: int,
    db: AsyncSession,
):
    """Handle interview end"""
    from datetime import datetime, timezone
    from app.models.interview import interview_sessions

    await db.execute(
        update(interview_sessions)
        .where(interview_sessions.c.id == int(session_id))
        .values(
            status="completed",
            is_finished=True,
            end_time=datetime.now(timezone.utc)
        )
    )
    await db.commit()

    # Send end message to frontend
    await manager.send_message(
        {
            "type": "end",
            "message": "Interview ended",
            "summary": {
                "overall_evaluation": "面试已完成，请查看详细报告",
                "recommendation": "面试正常结束"
            }
        },
        session_id,
        user_id
    )

    # Keep LLM context temporarily so non-realtime video analysis can still
    # combine the recorded video with the interview transcript. The context
    # will be cleared after downstream analysis or by TTL expiration.


async def handle_audio(
    message_dict: dict,
    session_id: str,
    user_id: int,
):
    """Handle audio data

    Note: ASR has been moved to frontend. This function now only stores audio for archive purposes.
    Frontend should use Web Speech API or other client-side ASR and send text via 'text' message type.
    """
    audio_data = message_dict.get("audio_data")
    audio_format = message_dict.get("format", "wav")

    if not audio_data:
        await manager.send_error(
            session_id,
            user_id,
            error="No audio data provided",
            error_code="INVALID_AUDIO"
        )
        return

    # Audio is now processed by frontend ASR
    # This endpoint is deprecated - frontend should send text directly
    await manager.send_message(
        {
            "type": "info",
            "message": "请使用前端语音识别后发送文本",
            "suggestion": "使用 {type: 'text', text: '识别结果'} 发送消息"
        },
        session_id,
        user_id
    )

    # Optionally save audio for archive (without ASR)
    try:
        await audio_service.save_audio_only(
            audio_data=audio_data,
            audio_format=audio_format,
            session_id=session_id,
            user_id=user_id
        )
    except Exception as e:
        print(f"Audio archive failed: {e}")


async def handle_video_frame(
    message_dict: dict,
    session_id: str,
    user_id: int,
):
    """Handle video frame with facial analysis integration"""
    frame_data = message_dict.get("frame_data")
    frame_format = message_dict.get("format", "jpeg")
    timestamp = message_dict.get("timestamp")

    if not frame_data:
        # Silently skip frames without data (client might be streaming rapidly)
        return

    # Process video frame
    result = await video_service.process_video_frame(
        frame_data=frame_data,
        frame_format=frame_format,
        timestamp=timestamp,
        session_id=session_id,
        user_id=user_id
    )

    if result.get("success"):
        # Record for analytics
        video_analytics_service.record_frame_result(session_id, user_id, result)

        # Send analysis result (only if significant changes)
        if result.get("face_detected") or result.get("attention_score", 0) < ATTENTION_SCORE_THRESHOLD:
            await manager.send_message(
                {
                    "type": "video_result",
                    "face_detected": result.get("face_detected"),
                    "emotion": result.get("emotion"),
                    "attention_score": result.get("attention_score"),
                    "timestamp": result.get("timestamp")
                },
                session_id,
                user_id
            )


async def generate_ai_response_stream(
    session_id: str,
    user_id: int,
    db: AsyncSession,
):
    """Generate AI interviewer response with streaming using Qwen3-Omni HTTP API

    This function uses Qwen3-Omni model to generate both text and audio responses.
    """
    from app.models.interview import interview_sessions, interview_scenarios, interview_questions
    from app.core.prompts import INTERVIEWER_SYSTEM_PROMPT, INTERVIEWER_SCENARIO_PROMPT
    from app.services.auth_service import get_user_interviewer_settings

    # Get Qwen3-Omni HTTP service
    qwen3_service = get_qwen3_omni_http_service()

    # Get user's interviewer settings
    interviewer_settings = await get_user_interviewer_settings(db, user_id)
    voice = get_voice_for_settings(interviewer_settings)
    print(f"Using interviewer voice: {voice} for user {user_id} in generate_ai_response_stream")

    try:
        # Get session info
        result = await db.execute(
            select(interview_sessions).where(interview_sessions.c.id == int(session_id))
        )
        session_row = result.first()

        scenario_name = "通用技术面试"
        technology_field = "通用"
        scenario_description = ""
        if session_row and getattr(session_row, "scenario_id", None):
            sc = (await db.execute(
                select(interview_scenarios).where(interview_scenarios.c.id == session_row.scenario_id)
            )).first()
            if sc:
                scenario_name = getattr(sc, "name", None) or "通用技术面试"
                technology_field = getattr(sc, "technology_field", None) or "通用"
                scenario_description = getattr(sc, "description", None) or ""

        # Get conversation context
        messages = await get_messages(session_id)

        # Build system prompt with scenario info
        scenario_prompt = INTERVIEWER_SCENARIO_PROMPT.format(
            scenario=scenario_name,
            technology_field=technology_field
        )

        # Use Qwen3-Omni built-in system prompt builder for better results
        system_prompt = qwen3_service.build_interview_system_prompt(
            scenario_name=scenario_name,
            scenario_description=scenario_description or scenario_prompt,
            is_technical=True
        )

        # Apply interview style modifier
        style = interviewer_settings.get("style", "serious")
        system_prompt = apply_style_to_system_prompt(system_prompt, style)

        # Prepare messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt},
        ]
        # Add conversation history (last 10 messages for context)
        llm_messages.extend(messages[-10:] if len(messages) > 10 else messages)

        # Send stream start
        await manager.send_stream_start(session_id, user_id)

        # Stream AI response using Qwen3-Omni HTTP API
        full_response = ""
        audio_chunks = []
        chunk_count = 0
        stream_success = False

        try:
            print("Using Qwen3-Omni HTTP service for streaming...")

            # Collect text and audio chunks
            async for chunk in qwen3_service.chat(llm_messages, voice=voice, stream=True):
                chunk_count += 1

                if chunk.type == "text" and chunk.content:
                    full_response += chunk.content
                    # Send text chunk to client
                    await manager.send_stream_chunk(session_id, user_id, chunk.content)

                elif chunk.type == "audio" and chunk.audio_data:
                    # Collect audio data
                    audio_chunks.append(chunk.audio_data)
                    # Send audio chunk to client (for real-time playback)
                    await manager.send_message(
                        {
                            "type": "audio_delta",
                            "audio": chunk.audio_data,
                            "finish": False
                        },
                        session_id,
                        user_id
                    )

                elif chunk.type == "usage":
                    print(f"Qwen3-Omni usage: {chunk.usage}")

            stream_success = True
            print(f"Streaming completed: {chunk_count} chunks, {len(full_response)} chars, {len(audio_chunks)} audio chunks")

        except Exception as e:
            print(f"Qwen3-Omni streaming error: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to regular text-only response
            try:
                from app.core.qwen_client import qwen_chat
                full_response = await qwen_chat(llm_messages)
                stream_success = True
                print(f"Fallback response: {len(full_response)} chars")
            except Exception as fallback_e:
                print(f"Fallback also failed: {fallback_e}")

        # Send final audio marker if we have audio chunks
        if audio_chunks:
            await manager.send_message(
                {
                    "type": "audio_delta",
                    "audio": "",
                    "finish": True
                },
                session_id,
                user_id
            )

        # Only send stream end if we got some response
        if stream_success and full_response.strip():
            await manager.send_stream_end(session_id, user_id, full_response)
            # Persist AI response to context
            await append_message(session_id, "assistant", full_response)

            # Save question to database
            try:
                # Get current question count
                result = await db.execute(
                    select(interview_questions).where(
                        interview_questions.c.session_id == int(session_id)
                    )
                )
                question_count = len(result.all())

                await db.execute(
                    insert(interview_questions).values(
                        session_id=int(session_id),
                        question_text=full_response,
                        question_number=question_count + 1,
                    )
                )
                await db.commit()
                print(f"Question saved: #{question_count + 1}, length={len(full_response)}")
            except Exception as e:
                print(f"Failed to save question: {e}")
        else:
            # Send fallback message if no valid response
            print(f"No valid response received, sending fallback. Response length: {len(full_response)}")
            error_message = "感谢你的回答。请继续介绍你的技术背景和项目经验。"
            await manager.send_stream_chunk(session_id, user_id, error_message)
            await manager.send_stream_end(session_id, user_id, error_message)

            # Save fallback as question
            try:
                result = await db.execute(
                    select(interview_questions).where(
                        interview_questions.c.session_id == int(session_id)
                    )
                )
                question_count = len(result.all())
                await db.execute(
                    insert(interview_questions).values(
                        session_id=int(session_id),
                        question_text=error_message,
                        question_number=question_count + 1,
                    )
                )
                await db.commit()
                await append_message(session_id, "assistant", error_message)
            except Exception as e:
                print(f"Failed to save fallback question: {e}")

    except Exception as e:
        print(f"AI response generation failed: {e}")
        import traceback
        traceback.print_exc()


async def handle_text(
    message_dict: dict,
    session_id: str,
    user_id: int,
    db: AsyncSession,
):
    """Handle text message with AI streaming response"""
    # Support both 'text' and 'data' fields for compatibility
    text = message_dict.get("text") or message_dict.get("data")
    print(f"Received text from user {user_id}: {text}")

    if not text or not text.strip():
        await manager.send_error(
            session_id,
            user_id,
            error="Empty message",
            error_code="EMPTY_MESSAGE"
        )
        return

    # Persist user message to context
    try:
        await append_message(session_id, "user", text)
    except Exception as e:
        print(f"Failed to append user message to context: {e}")

    # Send acknowledgment with user's answer
    await manager.send_message(
        {
            "type": "user_message",
            "content": text,
            "role": "user"
        },
        session_id,
        user_id
    )

    # Generate AI response with streaming
    await generate_ai_response_stream(session_id, user_id, db)


async def handle_webrtc_offer(
    message_dict: dict,
    session_id: str,
    user_id: int,
):
    """Handle WebRTC SDP offer"""
    sdp = message_dict.get("sdp")
    sdp_type = message_dict.get("type")  # "offer" or "answer"
    user_type = message_dict.get("user_type", "host")  # "host" or "guest"

    if not sdp:
        await manager.send_error(
            session_id,
            user_id,
            error="No SDP provided",
            error_code="INVALID_WEBRTC_OFFER"
        )
        return

    # Get or create connection
    conn = webrtc_service.get_connection_by_session(session_id)
    if not conn:
        # Create new connection
        conn_result = webrtc_service.create_connection(
            session_id=session_id,
            host_user_id=user_id if user_type == "host" else 0,
            guest_user_id=user_id if user_type == "guest" else None
        )
        conn = webrtc_service.get_connection(conn_result["connection_id"])

    if user_type == "host":
        webrtc_service.set_host_offer(conn.connection_id, {"sdp": sdp, "type": sdp_type})
    else:
        webrtc_service.set_guest_offer(conn.connection_id, {"sdp": sdp, "type": sdp_type})

    # Notify other party about the offer
    # Note: In a real implementation, you'd broadcast to the other user
    await manager.send_message(
        {
            "type": "webrtc_offer_received",
            "user_type": user_type,
            "connection_id": conn.connection_id
        },
        session_id,
        user_id
    )


async def handle_webrtc_answer(
    message_dict: dict,
    session_id: str,
    user_id: int,
):
    """Handle WebRTC SDP answer"""
    sdp = message_dict.get("sdp")
    sdp_type = message_dict.get("type")
    user_type = message_dict.get("user_type", "host")
    connection_id = message_dict.get("connection_id")

    if not sdp or not connection_id:
        await manager.send_error(
            session_id,
            user_id,
            error="Invalid WebRTC answer",
            error_code="INVALID_WEBRTC_ANSWER"
        )
        return

    if user_type == "host":
        webrtc_service.set_host_answer(connection_id, {"sdp": sdp, "type": sdp_type})
    else:
        webrtc_service.set_guest_answer(connection_id, {"sdp": sdp, "type": sdp_type})

    # Check if connection is established
    conn = webrtc_service.get_connection(connection_id)
    if conn and conn.status == "connected":
        await manager.send_message(
            {
                "type": "webrtc_connected",
                "connection_id": connection_id
            },
            session_id,
            user_id
        )


async def handle_webrtc_ice(
    message_dict: dict,
    session_id: str,
    user_id: int,
):
    """Handle WebRTC ICE candidate"""
    candidate = message_dict.get("candidate")
    sdp_mid = message_dict.get("sdp_mid")
    sdp_mline_index = message_dict.get("sdp_mline_index")
    user_type = message_dict.get("user_type", "host")
    connection_id = message_dict.get("connection_id")

    if not candidate or not connection_id:
        return

    ice_candidate = {
        "candidate": candidate,
        "sdp_mid": sdp_mid,
        "sdp_mline_index": sdp_mline_index
    }

    if user_type == "host":
        webrtc_service.add_host_ice_candidate(connection_id, ice_candidate)
    else:
        webrtc_service.add_guest_ice_candidate(connection_id, ice_candidate)

    # Notify about candidate received
    await manager.send_message(
        {
            "type": "webrtc_ice_received",
            "connection_id": connection_id,
            "user_type": user_type
        },
        session_id,
        user_id
    )


async def handle_webrtc_cleanup(
    session_id: str,
    user_id: int,
):
    """Handle WebRTC cleanup"""
    conn = webrtc_service.get_connection_by_session(session_id)
    if conn:
        webrtc_service.close_connection(conn.connection_id)

        # Clean up audio/video temp files
        await audio_service.cleanup_temp_files(session_id)
        await video_service.cleanup_temp_files(session_id)
        video_analytics_service.clear_session_history(session_id)

        await manager.send_message(
            {
                "type": "webrtc_cleanup_complete",
                "connection_id": conn.connection_id
            },
            session_id,
            user_id
        )
