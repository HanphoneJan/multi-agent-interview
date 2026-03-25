"""Qwen3-Omni 实时音视频面试 WebSocket 处理器

端点: /ws/interview/realtime/{session_id}

与原有的 interview.py 共存，提供端到端实时音视频理解能力。
"""

import asyncio
import base64
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select, update, insert

from app.dependencies import SessionDep
from app.websockets.manager import manager
from app.core.qwen3_omni_realtime import (
    get_or_create_client,
    close_client,
    Qwen3OmniRealtimeClient,
    ConversationState,
    RealtimeConfig
)
from app.utils.log_helper import get_logger

logger = get_logger("websockets.interview_realtime")

router = APIRouter()


@router.websocket("/ws/interview/realtime/{session_id}")
async def interview_realtime_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str,
    db: SessionDep,
):
    """Qwen3-Omni 实时音视频面试 WebSocket

    支持:
    - 实时音频流输入 (16kHz PCM)
    - 实时视频帧输入 (可选)
    - 实时语音输出 (24kHz PCM)
    - 自然对话打断

    消息协议:
    - Client -> Server:
      - {type: "start", scenario: "..."}  # 开始面试
      - {type: "audio", data: "base64_pcm", timestamp: 123456}  # 实时音频流
      - {type: "audio_end"}  # 音频流结束标记
      - {type: "video", data: "base64_jpg", timestamp: 123456}  # 视频帧
      - {type: "pause"}  # 暂停面试
      - {type: "resume"}  # 恢复面试
      - {type: "end"}  # 结束面试
      - {type: "ping"}  # 心跳

    - Server -> Client:
      - {type: "connected", session_id: "..."}  # 连接成功
      - {type: "audio", data: "base64_pcm", format: "pcm"}  # AI 语音
      - {type: "text_delta", text: "..."}  # AI 文本片段
      - {type: "question", text: "...", id: "..."}  # 完整问题
      - {type: "speech_started"}  # 检测到用户说话
      - {type: "speech_stopped"}  # 用户说话结束
      - {type: "status", state: "listening|thinking|speaking"}  # 状态更新
      - {type: "info", message: "..."}  # 提示信息
      - {type: "end", summary: {...}}  # 面试结束
      - {type: "error", error: "..."}  # 错误
      - {type: "pong"}  # 心跳响应
    """

    # 身份验证
    from app.core.security import verify_token
    from app.config import get_settings
    from app.models.interview import interview_sessions, interview_questions

    settings = get_settings()

    logger.info(f"Realtime WebSocket 连接请求: session_id={session_id}")

    if not token:
        logger.warning("连接被拒绝: 缺少 token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    payload = verify_token(token, settings.JWT_SECRET_KEY)
    if not payload:
        logger.warning(f"连接被拒绝: token 验证失败")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    user_id = payload.get("user_id")

    # 验证会话存在且属于该用户
    # 同时验证这是实时面试 (realtime interview)
    from app.models.interview import interview_scenarios

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
        logger.warning(f"连接被拒绝: 会话不存在或用户不匹配")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session not found")
        return

    # Check if this is a realtime interview
    session_dict = dict(row._asdict())
    if not session_dict.get("scenario_is_realtime"):
        logger.warning(f"连接被拒绝: 非实时面试请使用 /ws/interview/{session_id} 端点")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Non-realtime interviews must use /ws/interview endpoint"
        )
        return

    # 连接管理
    await manager.connect(websocket, session_id, user_id)

    # 初始化组件
    omni_client: Optional[Qwen3OmniRealtimeClient] = None

    # 任务引用
    forward_task: Optional[asyncio.Task] = None
    heartbeat_task: Optional[asyncio.Task] = None

    # 面试状态
    interview_started = False
    interview_paused = False
    conversation_history = []

    async def forward_omni_events():
        """转发 Qwen3-Omni 事件到前端"""
        nonlocal interview_started

        logger.info(f"开始转发 Qwen3-Omni 事件: session={session_id}")
        event_count = 0

        try:
            async for event in omni_client.receive_events():
                event_type = event.get("type", "")
                event_count += 1
                logger.info(f"[事件#{event_count}] 收到 Qwen3-Omni 事件: {event_type}")

                # 打印完整事件内容用于调试（限制长度）
                event_str = str(event)[:500]
                logger.debug(f"[事件#{event_count}] 完整内容: {event_str}...")

                # 处理音频输出 (AI 说话)
                if event_type == "response.audio.delta":
                    audio_b64 = event.get("audio", "")
                    logger.info(f"[事件#{event_count}] 转发音频数据: {len(audio_b64)} bytes")
                    if audio_b64:
                        await manager.send_message({
                            "type": "audio",
                            "data": audio_b64,
                            "format": "pcm",
                            "sample_rate": 24000,
                        }, session_id, user_id)

                # 处理文本增量 (Qwen3-Omni 使用 response.audio_transcript.delta)
                elif event_type in ("response.text.delta", "response.audio_transcript.delta"):
                    text = event.get("text", "") or event.get("delta", "")
                    logger.info(f"[事件#{event_count}] 转发文本增量: {text[:50]}...")
                    if text:
                        await manager.send_message({
                            "type": "text_delta",
                            "text": text,
                        }, session_id, user_id)

                # 处理完整回复
                elif event_type == "response.done":
                    response = event.get("response", {})
                    output = response.get("output", [{}])[0] if response.get("output") else {}
                    text = output.get("text", "")
                    response_id = response.get("id", "")
                    logger.info(f"[事件#{event_count}] 转发完整回复 (response.done): text={text[:100]}...")
                    logger.debug(f"[事件#{event_count}] response.done 完整结构: {event}")

                    if text:
                        await manager.send_message({
                            "type": "question",
                            "text": text,
                            "id": response_id,
                        }, session_id, user_id)
                        logger.info(f"[事件#{event_count}] question 消息已发送到前端")

                        # 保存到历史记录
                        conversation_history.append({
                            "role": "assistant",
                            "content": text,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                        logger.info(f"AI 回复已保存到历史: 当前 {len(conversation_history)} 条消息")
                    else:
                        logger.warning(f"[事件#{event_count}] response.done 中 text 为空，不保存到历史")
                        logger.debug(f"[事件#{event_count}] response 结构: {response}")

                # 检测到用户说话 (打断)
                elif event_type == "input_audio_buffer.speech_started":
                    logger.debug("检测到用户说话，打断 AI")
                    await manager.send_message({
                        "type": "speech_started",
                    }, session_id, user_id)

                # 用户说话结束
                elif event_type == "input_audio_buffer.speech_stopped":
                    await manager.send_message({
                        "type": "speech_stopped",
                    }, session_id, user_id)

                # 处理用户音频转录完成（这是用户语音的识别结果）
                elif event_type == "response.audio_transcript.done":
                    transcript = event.get("transcript", "")
                    logger.info(f"[事件#{event_count}] 用户音频转录完成: {transcript[:100]}...")
                    # 保存用户消息到历史
                    if transcript:
                        conversation_history.append({
                            "role": "user",
                            "content": transcript,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                        logger.info(f"用户消息已保存到历史 (从 audio_transcript.done): 当前 {len(conversation_history)} 条消息")

                # 状态更新
                elif event_type == "response.created":
                    await manager.send_message({
                        "type": "status",
                        "state": "thinking",
                    }, session_id, user_id)

                # 对话项目创建确认（用户消息已接收）
                elif event_type == "conversation.item.created":
                    item = event.get("item", {})
                    logger.info(f"[事件#{event_count}] 对话项目已创建: role={item.get('role')}, type={item.get('type')}")

                # 输入音频缓冲区提交确认
                elif event_type == "input_audio_buffer.committed":
                    logger.info(f"[事件#{event_count}] 音频缓冲区已提交")

                # 处理错误
                elif event_type == "error":
                    error_msg = event.get("error", {}).get("message", "未知错误")
                    logger.error(f"Qwen3-Omni 错误: {error_msg}")
                    await manager.send_message({
                        "type": "error",
                        "error": error_msg,
                    }, session_id, user_id)

                # 记录未处理的事件类型
                else:
                    logger.debug(f"未处理的事件类型: {event_type}")

        except Exception as e:
            logger.error(f"转发事件时出错: {e}", exc_info=True)
        finally:
            logger.info("forward_omni_events 协程结束")

    async def send_heartbeat():
        """发送心跳"""
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒
                if not interview_started:
                    break
                manager.update_heartbeat(session_id, user_id)
                await manager.send_message({"type": "pong"}, session_id, user_id)
        except asyncio.CancelledError:
            pass

    try:
        # 创建系统提示词
        scenario_name = "通用技术面试"
        scenario_id = session_dict.get("scenario_id")
        if scenario_id:
            from app.models.interview import interview_scenarios
            sc = await db.execute(
                select(interview_scenarios)
                .where(interview_scenarios.c.id == scenario_id)
            )
            scenario = sc.first()
            if scenario:
                scenario_name = getattr(scenario, "name", scenario_name) or scenario_name

        system_prompt = f"""你是一位专业的技术面试官，正在进行实时语音视频面试。

面试会话ID: {session_id}
候选人ID: {user_id}
面试场景: {scenario_name}

【极其重要 - 必须遵守】
1. 这是实时连续对话，你必须记住之前的对话内容并在此基础上继续
2. 你正在与候选人进行多轮对话，不要重复已经问过的问题或说过的话
3. 仔细聆听候选人的回答，基于回答内容深入追问，而不是重新开始
4. 一次只问一个问题，等待完整回答后再继续下一个问题
5. 如果候选人已经自我介绍过，绝不要再要求自我介绍
6. 根据对话自然推进面试流程，不要机械地重复开场白

面试态度:
- 保持专业但友好的态度
- 如果候选人表现出紧张，请给予适当鼓励
- 可以通过视频观察候选人的肢体语言和表情
- 通过语音语调感知其情绪状态

面试流程参考（请根据实际对话灵活调整）:
1. 开场: 简短自我介绍，说明面试流程（只进行一次）
2. 技术基础: 2-3个核心技术问题
3. 项目经验: 深入询问1-2个项目
4. 场景题: 1个设计/算法题
5. 候选人提问: 回答候选人问题
6. 结束: 总结面试，说明后续流程

请用中文进行面试。"""

        # 发送连接成功消息
        await manager.send_message({
            "type": "connected",
            "message": "已连接到 AI 面试官 (Qwen3-Omni 实时音视频)",
            "session_id": session_id,
            "features": ["realtime_audio", "video_understanding", "emotion_detection"],
        }, session_id, user_id)

        # 主消息循环
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            if msg_type == "start":
                # 开始面试
                if interview_started:
                    continue

                try:
                    # 初始化 Qwen3-Omni 客户端
                    config = RealtimeConfig(
                        voice=message.get("voice", "Chelsie"),
                        enable_audio=True,
                    )
                    omni_client = await get_or_create_client(session_id, system_prompt, config)

                    # 启动事件转发
                    logger.info("启动事件转发任务...")
                    forward_task = asyncio.create_task(forward_omni_events())
                    heartbeat_task = asyncio.create_task(send_heartbeat())

                    interview_started = True
                    logger.info("面试启动成功，事件转发任务已启动")

                    # 更新数据库状态
                    await db.execute(
                        update(interview_sessions)
                        .where(interview_sessions.c.id == int(session_id))
                        .values(
                            status="in_progress",
                            start_time=datetime.now(timezone.utc)
                        )
                    )
                    await db.commit()

                    await manager.send_message({
                        "type": "info",
                        "message": "面试开始，AI 面试官正在准备第一个问题..."
                    }, session_id, user_id)

                    # 触发 AI 开始面试
                    await omni_client.create_response()

                except Exception as e:
                    logger.error(f"启动面试失败: {e}")
                    await manager.send_message({
                        "type": "error",
                        "error": f"启动失败: {str(e)}"
                    }, session_id, user_id)

            elif msg_type == "audio":
                # 接收实时音频流数据
                if not interview_started or interview_paused:
                    continue

                audio_b64 = message.get("data", "")
                timestamp = message.get("timestamp", 0)

                if audio_b64 and omni_client and omni_client.is_connected():
                    try:
                        pcm_data = base64.b64decode(audio_b64)
                        # 直接发送到 Qwen3-Omni
                        await omni_client.send_audio(pcm_data)
                    except Exception as e:
                        logger.warning(f"发送音频数据失败: {e}")

            elif msg_type == "audio_end":
                # 音频流结束，提交缓冲区并请求 AI 回复
                if not interview_started or interview_paused:
                    continue

                if omni_client and omni_client.is_connected():
                    try:
                        logger.info("收到音频结束标记，提交音频缓冲区")
                        await omni_client.commit_audio()
                        await asyncio.sleep(0.3)
                        await omni_client.create_response()
                        logger.info("音频已提交，已请求 AI 回复")
                    except Exception as e:
                        logger.error(f"提交音频失败: {e}")

            elif msg_type == "video":
                # 接收视频帧
                if not interview_started or interview_paused:
                    continue

                image_b64 = message.get("data", "")
                timestamp = message.get("timestamp")

                if image_b64 and omni_client and omni_client.is_connected():
                    try:
                        await omni_client.send_video_frame(image_b64, timestamp)
                    except Exception as e:
                        logger.warning(f"发送视频帧失败: {e}")

            elif msg_type == "pause":
                interview_paused = True
                await manager.send_message({
                    "type": "info",
                    "message": "面试已暂停"
                }, session_id, user_id)

            elif msg_type == "resume":
                interview_paused = False
                await manager.send_message({
                    "type": "info",
                    "message": "面试已恢复"
                }, session_id, user_id)

            elif msg_type == "end":
                # 结束面试
                await handle_end_interview(
                    session_id, user_id, db,
                    omni_client,
                    conversation_history
                )
                break

            elif msg_type == "ping":
                manager.update_heartbeat(session_id, user_id)
                await manager.send_message({"type": "pong"}, session_id, user_id)

    except WebSocketDisconnect:
        logger.info(f"Realtime WebSocket 断开: session={session_id}, user={user_id}")

    except Exception as e:
        logger.error(f"Realtime WebSocket 错误: {e}")
        try:
            await manager.send_message({
                "type": "error",
                "error": "内部错误",
                "error_code": "INTERNAL_ERROR"
            }, session_id, user_id)
        except:
            pass

    finally:
        # 清理资源
        if heartbeat_task:
            heartbeat_task.cancel()

        if forward_task:
            forward_task.cancel()

        if omni_client:
            await close_client(session_id)

        await manager.disconnect(session_id, user_id)
        logger.info(f"Realtime WebSocket 资源已清理: session={session_id}")


async def handle_end_interview(
    session_id: str,
    user_id: int,
    db: SessionDep,
    omni_client: Optional[Qwen3OmniRealtimeClient],
    conversation_history: list,
):
    """处理面试结束"""
    from app.models.interview import interview_sessions

    try:
        # 更新数据库状态
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

        # 计算面试时长
        # TODO: 从会话记录中计算实际时长

        # 计算面试时长（秒）
        duration_seconds = 0
        try:
            result = await db.execute(
                select(interview_sessions.c.start_time, interview_sessions.c.end_time)
                .where(interview_sessions.c.id == int(session_id))
            )
            row = result.first()
            if row and row.start_time and row.end_time:
                duration_seconds = int((row.end_time - row.start_time).total_seconds())
        except Exception as e:
            logger.warning(f"计算面试时长失败: {e}")

        # 发送结束消息
        await manager.send_message({
            "type": "end",
            "summary": {
                "overall_evaluation": "面试已完成",
                "duration": duration_seconds,
                "duration_formatted": f"{duration_seconds // 60}分{duration_seconds % 60}秒",
                "questions_count": len([m for m in conversation_history if m.get("role") == "assistant"]),
                "message": "评估报告正在生成中，请稍后查看"
            }
        }, session_id, user_id)

        # 触发异步任务生成评估报告
        try:
            from app.workers.tasks import generate_report_task
            generate_report_task.delay(session_id, user_id)
            logger.info(f"已触发报告生成任务: session={session_id}, user={user_id}")
        except Exception as e:
            logger.error(f"触发报告生成任务失败: {e}")

    except Exception as e:
        logger.error(f"结束面试时出错: {e}")
        await manager.send_message({
            "type": "end",
            "summary": {
                "overall_evaluation": "面试结束",
                "error": str(e)
            }
        }, session_id, user_id)
