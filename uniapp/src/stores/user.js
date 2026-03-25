import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
  state: () => ({
    username: '',     // 用户名
    userId: null,     // 用户ID
    name: '',         // 真实姓名
    avatarUrl: 'https://hanphone.top/images/zhuxun.jpg', // 头像URL
    email: '',        // 邮箱
    phone: '',        // 电话
    age:'',          // 年龄
    gender: '',       // 性别
    major: '',        // 专业
    university: '',   // 学校
    province: '',     // 省份
    city: '',         // 城市
    district: '',     // 区县
    address: '',      // 地址
    ethnicity: '',    // 民族
    learningStage: '', // 学习阶段
    access: '',       // JWT访问令牌
    refresh: '',      // JWT刷新令牌
    isLoggedIn: false, // 是否登录
    tokenExpire: null, // 令牌过期时间
    isH5: false, // 是否为H5端
    platform:'', // 平台信息
    sessionId: null, // 面试会话ID
  }),
  actions: {
    setUser(userData) {
      // 提取并存储用户信息
      this.username = userData.username || '';
      this.userId = userData.userId || null;
      this.avatarUrl = userData.avatarUrl || userData.avatar_url || 'https://hanphone.top/images/zhuxun.jpg';
      this.name = userData.name || '';
      this.email = userData.email || '';
      this.phone = userData.phone || '';
      this.gender = userData.gender || '';
      this.major = userData.major || '';
      this.university = userData.university || '';
      this.province = userData.province || '';
      this.city = userData.city || '';
      this.district = userData.district || '';
      this.address = userData.address || '';
      this.ethnicity = userData.ethnicity || '';
      this.age = userData.age || null; // 存储年龄信息
      this.learningStage = userData.learningStage || userData.learning_stage || ''; // 存储学习阶段信息
      // 存储认证信息
      this.access = userData.access || '';
      this.refresh = userData.refresh || '';
      this.isLoggedIn = userData.isLoggedIn || false;
      this.tokenExpire = userData.tokenExpire || null;
      this.isH5 = userData.isH5 || false;
      this.platform = userData.platform || '';
      this.sessionId = userData.sessionId || userData.session_id || null;
    },
    clearUser() {
      // 清空所有用户信息
      this.username = '';
      this.userId = null;
      this.avatarUrl = 'https://hanphone.top/images/zhuxun.jpg';
      this.name = '';
      this.email = '';
      this.phone = '';
      this.age = null;
      this.learningStage = '';
      this.gender = '';
      this.major = '';
      this.university = '';
      this.province = '';
      this.city = '';
      this.district = '';
      this.address = '';
      this.ethnicity = '';
      this.access = '';
      this.refresh = '';
      this.isLoggedIn = false;
      this.tokenExpire = null;
      this.sessionId = null;
    }
  },
  persist: {
		storage: {
			getItem: uni.getStorageSync,
			setItem: uni.setStorageSync
		}
	}
});