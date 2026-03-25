/**
 * 面试页面 - Page Object Model
 */

const { expect } = require('@playwright/test');
const { safeClick, sleep, expectToast } = require('../utils/test-helpers');

class InterviewPage {
  constructor(page) {
    this.page = page;

    // 选择器定义
    this.selectors = {
      // 面试标题
      interviewTitle: '.interview-title, .scenario-name',

      // 计时器
      timer: '.timer, .interview-timer, .time-display',

      // 面试官头像/消息
      interviewerAvatar: '.interviewer-avatar, .ai-avatar',
      interviewerMessage: '.interviewer-message, .ai-message, .message-bubble.received',

      // 用户输入
      userInput: '.message-input, input[placeholder*="输入"], textarea',
      sendButton: '.send-button, button:has-text("发送"), [data-testid="send-message"]',

      // 语音输入
      voiceButton: '.voice-button, .mic-button, button:has-text("按住说话")',

      // 控制按钮
      pauseButton: '.pause-button, button:has-text("暂停")',
      resumeButton: '.resume-button, button:has-text("继续")',
      endButton: '.end-button, button:has-text("结束")',

      // 确认对话框
      confirmDialog: '.confirm-dialog, .uni-popup-dialog',
      confirmButton: '.confirm-button, button:has-text("确认")',
      cancelButton: '.cancel-button, button:has-text("取消")',

      // 加载状态
      loadingIndicator: '.loading, .spinner, .uni-loading',

      // WebSocket 连接状态
      connectionStatus: '.connection-status, .ws-status',
    };
  }

  /**
   * 导航到面试页面
   * @param {number} sessionId - 面试会话 ID
   */
  async goto(sessionId) {
    await this.page.goto(`/pages/interview/interview?sessionId=${sessionId}`);
    await this.page.waitForLoadState('networkidle');
    // 等待 WebSocket 连接建立
    await sleep(2000);
  }

  /**
   * 获取面试标题
   * @returns {Promise<string>} 面试标题
   */
  async getInterviewTitle() {
    const titleElement = this.page.locator(this.selectors.interviewTitle);
    return await titleElement.textContent();
  }

  /**
   * 获取计时器显示
   * @returns {Promise<string>} 计时器文本
   */
  async getTimerDisplay() {
    const timerElement = this.page.locator(this.selectors.timer);
    return await timerElement.textContent();
  }

  /**
   * 发送消息
   * @param {string} message - 要发送的消息
   */
  async sendMessage(message) {
    // 填写消息
    const input = this.page.locator(this.selectors.userInput);
    await input.fill(message);

    // 点击发送
    await safeClick(this.page, this.selectors.sendButton);
    await sleep(500);
  }

  /**
   * 获取面试官消息列表
   * @returns {Promise<Array>} 消息文本列表
   */
  async getInterviewerMessages() {
    const messages = this.page.locator(this.selectors.interviewerMessage);
    const count = await messages.count();
    const messageList = [];

    for (let i = 0; i < count; i++) {
      const text = await messages.nth(i).textContent();
      messageList.push(text);
    }

    return messageList;
  }

  /**
   * 点击暂停按钮
   */
  async clickPause() {
    await safeClick(this.page, this.selectors.pauseButton);
    await sleep(500);
  }

  /**
   * 点击恢复按钮
   */
  async clickResume() {
    await safeClick(this.page, this.selectors.resumeButton);
    await sleep(500);
  }

  /**
   * 点击结束按钮
   */
  async clickEnd() {
    await safeClick(this.page, this.selectors.endButton);
    await sleep(500);
  }

  /**
   * 确认结束面试
   */
  async confirmEnd() {
    await safeClick(this.page, this.selectors.confirmButton);
    await sleep(1000);
  }

  /**
   * 取消结束面试
   */
  async cancelEnd() {
    await safeClick(this.page, this.selectors.cancelButton);
    await sleep(500);
  }

  /**
   * 等待面试官回复
   * @param {number} timeout - 超时时间(毫秒)
   */
  async waitForInterviewerResponse(timeout = 30000) {
    const initialCount = await this.page.locator(this.selectors.interviewerMessage).count();

    await this.page.waitForFunction(
      (selector, initialCount) => {
        return document.querySelectorAll(selector).length > initialCount;
      },
      this.selectors.interviewerMessage,
      initialCount,
      { timeout }
    );
  }

  /**
   * 验证面试页面加载成功
   */
  async expectPageLoaded() {
    // 验证关键元素存在
    await expect(this.page.locator(this.selectors.interviewTitle)).toBeVisible();
    await expect(this.page.locator(this.selectors.userInput)).toBeVisible();
  }

  /**
   * 验证计时器正在运行(通过检查时间变化)
   */
  async expectTimerRunning() {
    const time1 = await this.getTimerDisplay();
    await sleep(2000);
    const time2 = await this.getTimerDisplay();
    expect(time1).not.toBe(time2);
  }

  /**
   * 验证可以发送消息
   */
  async expectCanSendMessage() {
    const input = this.page.locator(this.selectors.userInput);
    await expect(input).toBeEnabled();

    const sendButton = this.page.locator(this.selectors.sendButton);
    await expect(sendButton).toBeEnabled();
  }

  /**
   * 验证收到面试官回复
   */
  async expectInterviewerResponse() {
    const messages = await this.getInterviewerMessages();
    expect(messages.length).toBeGreaterThan(0);
  }
}

module.exports = { InterviewPage };
