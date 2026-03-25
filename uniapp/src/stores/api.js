/**
 * API Configuration for AI Interview Agent
 * FastAPI backend
 */
import { API_URL, API_BASE_URL, API_VERSION } from '@/config/index.js';

export { API_BASE_URL, API_VERSION, API_URL };

/**
 * API Endpoints mapping
 * Maps logical names to actual API endpoints
 */
export const ENDPOINTS = {
  // User authentication
  user: {
    login: `${API_URL}/users/login`,
    loginUnified: `${API_URL}/users/login-unified`,  // Compatible with phone/email
    wechatLogin: `${API_URL}/users/wechat/login`,
    register: `${API_URL}/users/register`,
    refresh: `${API_URL}/users/refresh`,
    profile: `${API_URL}/users/me`,
    updateProfile: `${API_URL}/users/me`,
    sendVerificationCode: `${API_URL}/users/verify-email/send`,
    resetPasswordRequest: `${API_URL}/users/reset-password/request`,
    resetPassword: `${API_URL}/users/reset-password/confirm`,
    address: `${API_URL}/users/address`,
    logout: `${API_URL}/users/logout`,
    interviewerSettings: `${API_URL}/users/me/interviewer-settings`,
  },

  // Interview module
  interview: {
    scenarios: `${API_URL}/interviews/scenarios`,
    sessions: `${API_URL}/interviews/sessions`,
    sessionDetail: (id) => `${API_URL}/interviews/sessions/${id}`,
    sessionPause: (id) => `${API_URL}/interviews/sessions/${id}/pause`,
    sessionResume: (id) => `${API_URL}/interviews/sessions/${id}/resume`,
    sessionEnd: (id) => `${API_URL}/interviews/sessions/${id}/end`,
    sessionCancel: (id) => `${API_URL}/interviews/sessions/${id}/cancel`,
    sessionQuestions: (id) => `${API_URL}/interviews/sessions/${id}/questions`,
    sessionVideoUpload: (id) => `${API_URL}/interviews/sessions/${id}/video`,
    sessionAnalyzeVideo: (id) => `${API_URL}/interviews/sessions/${id}/analyze-video`,
    userData: `${API_URL}/interviews/user-data`,
  },

  // Evaluation module
  evaluation: {
    analyzeResume: `${API_URL}/evaluations/resume/analyze`,
    getResume: `${API_URL}/evaluations/resume`,
    reports: `${API_URL}/evaluations/reports`,
    reportDetail: (id) => `${API_URL}/evaluations/reports/${id}`,
    answerEvaluation: (id) => `${API_URL}/evaluations/answers/${id}`,
  },

  // Learning resources
  learning: {
    resources: `${API_URL}/learning/resources`,
    resourceDetail: (id) => `${API_URL}/learning/resources/${id}`,
    resourceView: (id) => `${API_URL}/learning/resources/${id}/view`,
    resourceInteract: (id) => `${API_URL}/learning/resources/${id}/interact`,
    myInteractions: `${API_URL}/learning/my-interactions`,
  },

  // Recommendations
  recommendation: {
    personalized: `${API_URL}/recommendations/personalized`,
    popular: `${API_URL}/recommendations/popular`,
    report: (sessionId) => `${API_URL}/recommendations/report/${sessionId}`,
    career: `${API_URL}/recommendations/career`,
    jobs: `${API_URL}/recommendations/jobs`,
  },

  // Tasks (Celery)
  tasks: {
    status: (id) => `${API_URL}/tasks/${id}/status`,
    result: (id) => `${API_URL}/tasks/${id}/result`,
    processAudio: `${API_URL}/tasks/audio/process`,
    generateReport: `${API_URL}/tasks/reports/generate`,
    cancel: (id) => `${API_URL}/tasks/${id}`,
  },

  // TTS (新增)
  tts: {
    provider: `${API_URL}/tts/provider`,
    synthesize: `${API_URL}/tts/synthesize`,
    voices: (provider) => `${API_URL}/tts/voices/${provider}`,
    test: `${API_URL}/tts/test`,
  },
};

export default {
  API_BASE_URL,
  API_VERSION,
  API_URL,
  ENDPOINTS,
};
