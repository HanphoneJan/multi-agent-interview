/**
 * HTTP Request utility for UniApp
 * Handles token management, automatic refresh, and error handling
 */

import { API_BASE_URL, API_VERSION, ENDPOINTS } from './api.js';
import { useUserStore } from './user.js';

// Request timeout (10 seconds)
const TIMEOUT = 10000;

// Token 过期时间配置（与后端 config.py 保持一致）
const ACCESS_TOKEN_EXPIRE_MINUTES = 30;
const ACCESS_TOKEN_EXPIRE_MS = ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000;

// 并发请求处理 - 刷新锁和等待队列
let isRefreshing = false;
let refreshSubscribers = [];

/**
 * 订阅token刷新
 * @param {Function} callback - token刷新后的回调
 */
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback);
}

/**
 * 通知所有订阅者新token
 * @param {string} token - 新的access token
 */
function onTokenRefreshed(token) {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
}

/**
 * Normalize UniApp request result for cross-platform compatibility
 * H5 returns response directly, while mini-programs return [error, response]
 * @param {any} result - UniApp request result
 * @returns {[Error|null, Object|null]} Normalized [error, response] tuple
 */
function normalizeResult(result) {
  // Mini-program environment: already [error, response]
  if (Array.isArray(result)) {
    return result;
  }

  // H5 environment: returns response object directly
  if (result && typeof result === 'object') {
    // Check if this is a standard UniApp response with statusCode
    if (result.statusCode !== undefined) {
      if (result.statusCode >= 200 && result.statusCode < 300) {
        return [null, result];
      }
      return [result, null];
    }

    // H5 may return the response data directly (without statusCode wrapper)
    // If result has data property that looks like our API response, wrap it
    if (result.data !== undefined && typeof result.data === 'object') {
      return [null, result];
    }

    // If result looks like our API response (has typical fields), wrap it
    if (result.access_token || result.refresh_token || result.detail || result.message) {
      // Create a mock response object
      return [null, { statusCode: 200, data: result }];
    }
  }

  // Unknown format
  return [new Error('Unknown response format'), null];
}

/**
 * Get stored access token
 * Note: Use localStorage directly to avoid Pinia state synchronization issues
 * @returns {string|null} Access token
 */
function getAccessToken() {
  // Always read from localStorage to ensure we get the latest token
  // Pinia state may not be synchronized in some edge cases
  return uni.getStorageSync('access_token');
}

/**
 * Get stored refresh token
 * @returns {string|null} Refresh token
 */
function getRefreshToken() {
  return uni.getStorageSync('refresh_token');
}

/**
 * Save tokens to storage
 * @param {string} access - Access token
 * @param {string} refresh - Refresh token
 */
function saveTokens(access, refresh) {
  const userStore = useUserStore();
  userStore.access = access;
  userStore.refresh = refresh;
  // 修复：使用与后端一致的过期时间（30分钟）
  const tokenExpire = Date.now() + ACCESS_TOKEN_EXPIRE_MS;
  userStore.tokenExpire = tokenExpire;
  uni.setStorageSync('access_token', access);
  uni.setStorageSync('refresh_token', refresh);
  uni.setStorageSync('token_expire', tokenExpire);
}

/**
 * Clear tokens from storage
 */
function clearTokens() {
  const userStore = useUserStore();
  userStore.access = null;
  userStore.refresh = null;
  userStore.isLoggedIn = false;
  userStore.tokenExpire = null;
  uni.removeStorageSync('access_token');
  uni.removeStorageSync('refresh_token');
  uni.removeStorageSync('token_expire');
}

/**
 * Refresh access token - 带并发控制
 * @returns {Promise<string|null>} New access token
 */
async function refreshAccessToken() {
  // 如果正在刷新，则等待刷新完成
  if (isRefreshing) {
    return new Promise((resolve) => {
      subscribeTokenRefresh((token) => {
        resolve(token);
      });
    });
  }

  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    return null;
  }

  // 设置刷新锁
  isRefreshing = true;

  try {
    const result = await uni.request({
      url: ENDPOINTS.user.refresh,
      method: 'POST',
      data: { refresh: refreshToken },
      header: {
        'Content-Type': 'application/json',
      },
      timeout: TIMEOUT,
    });

    const [error, res] = normalizeResult(result);

    if (error || !res || res.statusCode !== 200) {
      console.error('Token refresh failed:', error || (res && res.data));
      clearTokens();
      onTokenRefreshed(null);
      return null;
    }

    const { access_token, refresh_token } = res.data;
    saveTokens(access_token, refresh_token);

    // 通知所有等待的订阅者
    onTokenRefreshed(access_token);

    return access_token;
  } catch (err) {
    console.error('Token refresh error:', err);
    clearTokens();
    onTokenRefreshed(null);
    return null;
  } finally {
    isRefreshing = false;
  }
}

/**
 * Check if token needs refresh
 * @returns {boolean} True if token needs refresh
 */
function shouldRefreshToken() {
  // Read directly from localStorage to avoid Pinia state sync issues
  const tokenExpire = uni.getStorageSync('token_expire');
  if (!tokenExpire) return false;

  // Refresh if token expires in less than 5 minutes
  const fiveMinutes = 5 * 60 * 1000;
  return tokenExpire - Date.now() < fiveMinutes;
}

/**
 * Make HTTP request
 * @param {Object} options - Request options
 * @param {string} options.url - Request URL
 * @param {string} options.method - HTTP method
 * @param {Object} options.data - Request data
 * @param {Object} options.header - Request headers
 * @param {boolean} options.auth - Whether to include auth token
 * @param {boolean} options.retry - Whether to retry on 401
 * @returns {Promise} Request result
 */
export async function request(options = {}) {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    auth = true,
    retry = true,
  } = options;

  // Check if token needs refresh for authenticated requests
  if (auth && shouldRefreshToken()) {
    const newToken = await refreshAccessToken();
    if (!newToken) {
      // Token refresh failed, redirect to login
      uni.showToast({
        title: '登录已过期，请重新登录',
        icon: 'none',
      });
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/login/login' });
      }, 1500);
      return Promise.reject(new Error('Token expired'));
    }
  }

  // Build request headers
  const requestHeaders = {
    'Content-Type': 'application/json',
    ...header,
  };

  // Add auth token if required
  if (auth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
  }

  try {
    const result = await uni.request({
      url,
      method,
      data,
      header: requestHeaders,
      timeout: TIMEOUT,
    });

    const [error, res] = normalizeResult(result);

    if (error) {
      console.error('Request error:', error);
      uni.showToast({
        title: '网络请求失败',
        icon: 'none',
      });
      return Promise.reject(error);
    }

    // Handle 401 Unauthorized
    if (res.statusCode === 401) {
      console.error('DEBUG request.js - Received 401, attempting token refresh');
      if (retry) {
        // Try to refresh token and retry request
        const newToken = await refreshAccessToken();
        if (newToken) {
          // Retry with new token
          return request({
            ...options,
            retry: false, // Prevent infinite retry
          });
        }
      }

      // Token refresh failed or already retried
      clearTokens();
      uni.showToast({
        title: '登录已过期，请重新登录',
        icon: 'none',
      });
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/login/login' });
      }, 1500);
      return Promise.reject(new Error('Unauthorized'));
    }

    // Handle other errors
    if (res.statusCode >= 400) {
      const errorMsg = res.data?.detail || res.data?.message || '请求失败';
      console.error('API error:', res.statusCode, errorMsg);
      return Promise.reject(new Error(errorMsg));
    }

    return res.data;
  } catch (err) {
    console.error('Request exception:', err);
    return Promise.reject(err);
  }
}

/**
 * Upload file
 * @param {Object} options - Upload options
 * @param {string} options.url - Upload URL
 * @param {string} options.filePath - Local file path
 * @param {string} options.name - Form field name
 * @param {Object} options.formData - Additional form data
 * @returns {Promise} Upload result
 */
export async function uploadFile(options = {}) {
  const {
    url,
    filePath,
    name = 'file',
    formData = {},
  } = options;

  const token = getAccessToken();
  const header = {};
  if (token) {
    header.Authorization = `Bearer ${token}`;
  }

  try {
    const result = await uni.uploadFile({
      url,
      filePath,
      name,
      formData,
      header,
    });

    const [error, res] = normalizeResult(result);

    if (error) {
      console.error('Upload error:', error);
      return Promise.reject(error);
    }

    // Parse response data
    if (res.data) {
      try {
        res.data = JSON.parse(res.data);
      } catch (e) {
        // Keep as string if not valid JSON
      }
    }

    return res.data;
  } catch (err) {
    console.error('Upload exception:', err);
    return Promise.reject(err);
  }
}

/**
 * Request methods shorthand
 */
export const http = {
  get: (url, options = {}) => request({ ...options, url, method: 'GET' }),
  post: (url, data, options = {}) => request({ ...options, url, method: 'POST', data }),
  put: (url, data, options = {}) => request({ ...options, url, method: 'PUT', data }),
  delete: (url, options = {}) => request({ ...options, url, method: 'DELETE' }),
  upload: uploadFile,
};

export default {
  request,
  uploadFile,
  http,
  refreshAccessToken,
  // 导出配置供其他模块使用
  ACCESS_TOKEN_EXPIRE_MINUTES,
};
