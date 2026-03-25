/**
 * API 客户端 - 用于测试数据准备和清理
 */

const API_BASE_URL = process.env.TEST_API_URL || 'http://localhost:8000/api/v1';

/**
 * 发送 API 请求
 * @param {string} endpoint - API 端点
 * @param {Object} options - 请求选项
 * @returns {Promise<Object>} 响应数据
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, { ...defaultOptions, ...options });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API request failed: ${response.status} - ${error}`);
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json();
  }

  return await response.text();
}

/**
 * 用户登录获取 Token
 * @param {string} email - 邮箱
 * @param {string} password - 密码
 * @returns {Promise<Object>} Token 信息
 */
async function login(email, password) {
  const response = await apiRequest('/users/login-unified', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  return {
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
    tokenType: response.token_type,
  };
}

/**
 * 获取用户信息
 * @param {string} accessToken - Access Token
 * @returns {Promise<Object>} 用户信息
 */
async function getUserInfo(accessToken) {
  return await apiRequest('/users/me', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
}

/**
 * 创建测试面试会话
 * @param {string} accessToken - Access Token
 * @param {number} scenarioId - 场景 ID
 * @returns {Promise<Object>} 会话信息
 */
async function createInterviewSession(accessToken, scenarioId) {
  const url = `${API_BASE_URL}/interviews/sessions`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ scenario_id: scenarioId }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API request failed: ${response.status} - ${error}`);
  }

  return await response.json();
}

/**
 * 获取面试场景列表
 * @param {string} accessToken - Access Token
 * @returns {Promise<Array>} 场景列表
 */
async function getInterviewScenarios(accessToken) {
  const response = await apiRequest('/interviews/scenarios', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  return response.items || response;
}

/**
 * 获取学习资源列表
 * @param {string} accessToken - Access Token
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 资源列表
 */
async function getLearningResources(accessToken, params = {}) {
  const queryString = new URLSearchParams(params).toString();
  const endpoint = `/learning/resources${queryString ? `?${queryString}` : ''}`;

  return await apiRequest(endpoint, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
}

/**
 * 获取用户面试数据
 * @param {string} accessToken - Access Token
 * @returns {Promise<Object>} 用户面试数据
 */
async function getUserInterviewData(accessToken) {
  return await apiRequest('/interviews/user-data', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
}

module.exports = {
  apiRequest,
  login,
  getUserInfo,
  createInterviewSession,
  getInterviewScenarios,
  getLearningResources,
  getUserInterviewData,
};
