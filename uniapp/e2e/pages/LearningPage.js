/**
 * 学习资源页面 - Page Object Model
 */

const { expect } = require('@playwright/test');
const { safeClick, sleep } = require('../utils/test-helpers');

class LearningPage {
  constructor(page) {
    this.page = page;

    // 选择器定义
    this.selectors = {
      // 页面标题
      pageTitle: '.learning-title, .page-title',

      // 资源列表
      resourceList: '.resource-list, .resource-grid',
      resourceCard: '.resource-card, .resource-item',
      resourceTitle: '.resource-title, .card-title',
      resourceType: '.resource-type, .type-tag',
      resourceDifficulty: '.resource-difficulty, .difficulty-tag',

      // 筛选器
      filterContainer: '.filter-container, .filter-bar',
      typeFilter: '.type-filter, [data-filter="type"]',
      difficultyFilter: '.difficulty-filter, [data-filter="difficulty"]',
      technologyFilter: '.technology-filter, [data-filter="technology"]',

      // 搜索
      searchInput: '.search-input, input[placeholder*="搜索"]',
      searchButton: '.search-button, button:has-text("搜索")',

      // 分页
      pagination: '.pagination, .load-more',
      loadMoreButton: '.load-more-button, button:has-text("加载更多")',

      // 推荐内容
      personalizedSection: '.personalized-section, .recommendations',
      careerSuggestions: '.career-suggestions, .career-section',

      // 资源详情
      resourceDetail: '.resource-detail, .detail-page',
      backButton: '.back-button, button:has-text("返回")',
    };
  }

  /**
   * 导航到学习资源页面
   */
  async goto() {
    await this.page.goto('/pages/learning/learning');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 获取资源列表
   * @returns {Promise<Array>} 资源标题列表
   */
  async getResourceList() {
    const cards = this.page.locator(this.selectors.resourceCard);
    const count = await cards.count();
    const resources = [];

    for (let i = 0; i < count; i++) {
      const title = await cards.nth(i).locator(this.selectors.resourceTitle).textContent();
      resources.push(title);
    }

    return resources;
  }

  /**
   * 点击资源卡片
   * @param {number} index - 资源索引
   */
  async clickResource(index = 0) {
    const card = this.page.locator(this.selectors.resourceCard).nth(index);
    await card.click();
    await sleep(500);
  }

  /**
   * 按类型筛选
   * @param {string} type - 资源类型 (question/course/video)
   */
  async filterByType(type) {
    await safeClick(this.page, this.selectors.typeFilter);
    await sleep(300);
    // 选择具体类型
    await safeClick(this.page, `.type-option:has-text("${type}")`);
    await sleep(500);
  }

  /**
   * 按难度筛选
   * @param {string} difficulty - 难度级别 (easy/medium/hard)
   */
  async filterByDifficulty(difficulty) {
    await safeClick(this.page, this.selectors.difficultyFilter);
    await sleep(300);
    await safeClick(this.page, `.difficulty-option:has-text("${difficulty}")`);
    await sleep(500);
  }

  /**
   * 搜索资源
   * @param {string} keyword - 搜索关键词
   */
  async search(keyword) {
    const searchInput = this.page.locator(this.selectors.searchInput);
    await searchInput.fill(keyword);
    await safeClick(this.page, this.selectors.searchButton);
    await sleep(1000);
  }

  /**
   * 加载更多资源
   */
  async loadMore() {
    await safeClick(this.page, this.selectors.loadMoreButton);
    await sleep(1000);
  }

  /**
   * 切换到个性化推荐Tab
   */
  async switchToPersonalized() {
    await safeClick(this.page, '.tab-personalized, [data-tab="personalized"]');
    await sleep(500);
  }

  /**
   * 切换到职业建议Tab
   */
  async switchToCareer() {
    await safeClick(this.page, '.tab-career, [data-tab="career"]');
    await sleep(500);
  }

  /**
   * 获取职业建议列表
   * @returns {Promise<Array>} 建议列表
   */
  async getCareerSuggestions() {
    const suggestions = this.page.locator('.career-suggestion, .suggestion-item');
    const count = await suggestions.count();
    const list = [];

    for (let i = 0; i < count; i++) {
      const text = await suggestions.nth(i).textContent();
      list.push(text);
    }

    return list;
  }

  /**
   * 验证页面加载成功
   */
  async expectPageLoaded() {
    await expect(this.page.locator(this.selectors.resourceList)).toBeVisible();
  }

  /**
   * 验证资源列表加载成功
   */
  async expectResourcesLoaded() {
    const resources = await this.getResourceList();
    expect(resources.length).toBeGreaterThan(0);
  }

  /**
   * 验证筛选结果
   * @param {string} expectedType - 期望的资源类型
   */
  async expectFilteredByType(expectedType) {
    const cards = this.page.locator(this.selectors.resourceCard);
    const count = await cards.count();

    // 验证所有卡片都显示该类型
    for (let i = 0; i < Math.min(count, 5); i++) {
      const type = await cards.nth(i).locator(this.selectors.resourceType).textContent();
      expect(type.toLowerCase()).toContain(expectedType.toLowerCase());
    }
  }
}

module.exports = { LearningPage };
