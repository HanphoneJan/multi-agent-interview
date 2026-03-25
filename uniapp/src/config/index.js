/**
 * 全局配置文件
 * 统一管理后端服务地址，方便开发和生产环境切换
 */

// 开发环境标识
const isDev = process.env.NODE_ENV === 'development';

// 后端服务配置
export const config = {
  // FastAPI 后端地址
  baseURL: isDev
    ? 'http://localhost:8000'           // 开发环境
    : 'https://www.hanphone.top',       // 生产环境

  // API 版本前缀
  apiVersion: '/api/v1',

  // WebSocket 配置
  ws: {
    protocol: isDev ? 'ws://' : 'wss://',
    host: isDev ? 'localhost:8000' : 'www.hanphone.top',
    path: '/api/v1/ws/interview',
  },

  // 静态资源地址（图片等）
  assets: {
    // 默认头像
    defaultAvatar: 'https://hanphone.top/images/zhuxun.jpg',
    // Logo
    logo: 'https://hanphone.top/ai-interview/logo.png',
    // Font Awesome CDN
    fontAwesome: 'https://hanphone.top/ai-interview/html/font-awesome-4.7.0/css/font-awesome.min.css',
  },
};

// 计算属性
export const API_BASE_URL = config.baseURL;
export const API_VERSION = config.apiVersion;
export const API_URL = config.baseURL + config.apiVersion;
export const WS_URL = config.ws.protocol + config.ws.host + config.ws.path;

export default config;
