/**
 * 登录页面 - Page Object Model
 */

const { expect } = require('@playwright/test');
const { safeFill, safeClick, sleep } = require('../utils/test-helpers');

class LoginPage {
  constructor(page) {
    this.page = page;

    // 选择器定义 - 基于 UniApp 页面实际结构
    this.selectors = {
      // 登录表单
      loginIdentifier: '.input-field',
      password: '.input-field[type="password"]',
      loginButton: '.login-btn',

      // 注册链接
      registerLink: '.register-link',

      // 微信登录
      wechatLoginButton: '.wechat-btn',

      // 错误提示
      errorMessage: '.error-msg',

      // 页面标题
      pageTitle: '.app-name',
    };
  }

  /**
   * 导航到登录页面
   */
  async goto() {
    // H5模式下先访问首页，然后点击"立即使用"按钮
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');

    // 等待首页加载并点击"立即使用"按钮
    await this.page.waitForSelector('.header-btn', { state: 'visible', timeout: 10000 });
    await this.page.click('.header-btn');

    // 等待跳转到登录页
    await this.page.waitForURL(/\/pages\/login\/login/, { timeout: 10000 });
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 填写登录表单
   * @param {string} identifier - 手机号或邮箱
   * @param {string} password - 密码
   */
  async fillLoginForm(identifier, password) {
    // UniApp H5 使用 Web Components，直接选择底层 input 元素
    // 账号输入框（第一个原生 input）
    await this.page.locator('input[type="text"]').fill(identifier);

    // 密码输入框
    await this.page.locator('input[type="password"]').fill(password);

    // 等待按钮变为可点击
    await sleep(500);
  }

  /**
   * 点击登录按钮
   */
  async clickLoginButton() {
    await safeClick(this.page, this.selectors.loginButton);
    // 等待登录请求完成和页面跳转
    await sleep(2000);
  }

  /**
   * 执行登录操作
   * @param {string} identifier - 手机号或邮箱
   * @param {string} password - 密码
   */
  async login(identifier, password) {
    await this.fillLoginForm(identifier, password);
    await this.clickLoginButton();
  }

  /**
   * 点击注册链接
   */
  async clickRegisterLink() {
    await safeClick(this.page, this.selectors.registerLink);
  }

  /**
   * 点击微信登录按钮
   */
  async clickWechatLogin() {
    await safeClick(this.page, this.selectors.wechatLoginButton);
  }

  /**
   * 获取错误消息
   * @returns {Promise<string>} 错误消息文本
   */
  async getErrorMessage() {
    const errorElement = this.page.locator(this.selectors.errorMessage);
    return await errorElement.textContent();
  }

  /**
   * 验证页面标题
   * @param {string} expectedTitle - 期望的标题
   */
  async expectTitle(expectedTitle) {
    const title = this.page.locator(this.selectors.pageTitle);
    await expect(title).toContainText(expectedTitle);
  }

  /**
   * 验证错误消息显示
   * @param {string} expectedMessage - 期望的错误消息
   */
  async expectErrorMessage(expectedMessage) {
    const errorElement = this.page.locator(this.selectors.errorMessage);
    await expect(errorElement).toContainText(expectedMessage);
  }

  /**
   * 验证当前 URL
   * @param {string} expectedPath - 期望的 URL 路径
   */
  async expectUrl(expectedPath) {
    await expect(this.page).toHaveURL(new RegExp(expectedPath));
  }

  /**
   * 等待页面加载完成
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    // 等待登录表单元素可见（第一个输入框）
    await this.page.waitForSelector('.input-field', { state: 'visible' });
  }
}

module.exports = { LoginPage };
