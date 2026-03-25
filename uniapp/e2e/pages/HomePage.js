/**
 * 首页 - Page Object Model
 */

const { expect } = require('@playwright/test');
const { safeClick, sleep } = require('../utils/test-helpers');

class HomePage {
  constructor(page) {
    this.page = page;

    // 选择器定义
    this.selectors = {
      // 页面标题
      pageTitle: '.home-title, .page-title',

      // 用户信息
      userName: '.user-name, .username',
      userAvatar: '.user-avatar, .avatar',

      // 导航 Tab
      tabHome: '.tab-home, [data-tab="home"]',
      tabInterview: '.tab-interview, [data-tab="interview"]',
      tabLearning: '.tab-learning, [data-tab="learning"]',
      tabProfile: '.tab-profile, [data-tab="profile"]',

      // 智能面试卡片 - 使用.card-title类包含"智能面试"文本
      startInterviewButton: '.card-title',

      // 面试场景卡片
      scenarioCard: '.scenario-card, .interview-card',
      scenarioName: '.scenario-name, .card-title',

      // 统计数据
      statsContainer: '.stats-container, .statistics',
      totalInterviews: '.total-interviews, .stat-value',

      // 学习资源入口
      learningEntry: '.learning-entry, .resources-link',

      // 面试记录
      interviewHistory: '.interview-history, .history-list',
    };
  }

  /**
   * 导航到首页
   */
  async goto() {
    await this.page.goto('/pages/home/home');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 点击智能面试卡片
   */
  async clickStartInterview() {
    // 使用getByText找到包含"智能面试"的元素并点击
    await this.page.getByText('智能面试').first().click();
    await sleep(500);
  }

  /**
   * 选择面试场景
   * @param {string} scenarioName - 场景名称
   */
  async selectScenario(scenarioName) {
    // 查找包含指定名称的场景卡片
    const scenarioCard = this.page.locator(`${this.selectors.scenarioCard}:has-text("${scenarioName}")`);
    await scenarioCard.click();
    await sleep(500);
  }

  /**
   * 获取场景列表
   * @returns {Promise<Array>} 场景名称列表
   */
  async getScenarioList() {
    const cards = this.page.locator(this.selectors.scenarioCard);
    const count = await cards.count();
    const scenarios = [];

    for (let i = 0; i < count; i++) {
      const name = await cards.nth(i).locator(this.selectors.scenarioName).textContent();
      scenarios.push(name);
    }

    return scenarios;
  }

  /**
   * 切换 Tab
   * @param {string} tabName - Tab 名称 (home, interview, learning, profile)
   */
  async switchTab(tabName) {
    const tabSelectors = {
      home: this.selectors.tabHome,
      interview: this.selectors.tabInterview,
      learning: this.selectors.tabLearning,
      profile: this.selectors.tabProfile,
    };

    await safeClick(this.page, tabSelectors[tabName]);
    await sleep(500);
  }

  /**
   * 获取用户名
   * @returns {Promise<string>} 用户名
   */
  async getUserName() {
    const userNameElement = this.page.locator(this.selectors.userName);
    return await userNameElement.textContent();
  }

  /**
   * 点击学习资源入口
   */
  async clickLearningEntry() {
    await safeClick(this.page, this.selectors.learningEntry);
    await sleep(500);
  }

  /**
   * 验证页面加载成功
   */
  async expectPageLoaded() {
    // 验证关键元素存在 - 使用getByText找到"智能面试"
    await expect(this.page.getByText('智能面试').first()).toBeVisible();
  }

  /**
   * 验证用户信息显示正确
   * @param {string} expectedName - 期望的用户名
   */
  async expectUserName(expectedName) {
    const userName = await this.getUserName();
    expect(userName).toContain(expectedName);
  }

  /**
   * 验证场景列表加载成功
   */
  async expectScenariosLoaded() {
    const scenarios = await this.getScenarioList();
    expect(scenarios.length).toBeGreaterThan(0);
  }
}

module.exports = { HomePage };
