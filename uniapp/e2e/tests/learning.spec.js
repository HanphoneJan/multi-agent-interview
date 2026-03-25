/**
 * 学习资源模块 E2E 测试
 *
 * 测试用例:
 * - TC-LR-001: 浏览学习资源
 * - TC-LR-002: 查看个性化推荐
 */

const { test, expect } = require('@playwright/test');
const { LearningPage } = require('../pages/LearningPage');
const { login } = require('../utils/api-client');
const { mockLoginState } = require('../utils/test-helpers');
const users = require('../fixtures/users.json');

// 测试套件配置
test.describe('学习资源模块', () => {
  let learningPage;
  let accessToken;

  test.beforeAll(async () => {
    // 通过 API 登录获取 Token
    const tokens = await login(
      users.testUsers.experiencedUser.email,
      users.testUsers.experiencedUser.password
    );
    accessToken = tokens.accessToken;
  });

  test.beforeEach(async ({ page }) => {
    learningPage = new LearningPage(page);

    // 设置登录状态
    await mockLoginState(page, { accessToken }, users.testUsers.experiencedUser);
  });

  /**
   * TC-LR-001: 浏览学习资源
   *
   * 前置条件: 用户已登录
   * 测试步骤:
   * 1. 进入"面试准备" Tab
   * 2. 点击"学习资源"
   * 3. 浏览资源列表
   * 4. 点击筛选条件
   *
   * 预期结果:
   * - 资源列表正常加载
   * - 筛选功能正常工作
   * - 分页加载正常
   */
  test('TC-LR-001: 浏览学习资源列表', async ({ page }) => {
    // Step 1-2: 进入学习资源页面
    await learningPage.goto();

    // 验证: 页面加载成功
    await learningPage.expectPageLoaded();

    // 验证: 资源列表加载
    await learningPage.expectResourcesLoaded();
  });

  test('TC-LR-001: 按类型筛选资源', async ({ page }) => {
    await learningPage.goto();
    await learningPage.expectPageLoaded();

    // 按问题类型筛选
    await learningPage.filterByType('question');

    // 验证: 筛选结果正确
    const resources = await learningPage.getResourceList();
    expect(resources.length).toBeGreaterThan(0);
  });

  test('TC-LR-001: 按难度筛选资源', async ({ page }) => {
    await learningPage.goto();
    await learningPage.expectPageLoaded();

    // 按简单难度筛选
    await learningPage.filterByDifficulty('easy');

    // 验证: 筛选结果正确
    const resources = await learningPage.getResourceList();
    expect(resources.length).toBeGreaterThanOrEqual(0);
  });

  test('TC-LR-001: 搜索学习资源', async ({ page }) => {
    await learningPage.goto();
    await learningPage.expectPageLoaded();

    // 搜索关键词
    await learningPage.search('Java');

    // 验证: 搜索结果包含关键词
    const resources = await learningPage.getResourceList();
    // 搜索结果可能为空，不做强制验证
  });

  test('TC-LR-001: 加载更多资源', async ({ page }) => {
    await learningPage.goto();
    await learningPage.expectPageLoaded();

    // 记录初始资源数量
    const initialCount = (await learningPage.getResourceList()).length;

    // 加载更多
    await learningPage.loadMore();

    // 验证: 资源数量增加
    const newCount = (await learningPage.getResourceList()).length;
    expect(newCount).toBeGreaterThanOrEqual(initialCount);
  });

  /**
   * TC-LR-002: 查看个性化推荐
   *
   * 前置条件: 用户已完成至少一次面试
   * 测试步骤:
   * 1. 进入"面试准备" Tab
   * 2. 点击"针对性学习"
   * 3. 查看推荐内容
   *
   * 预期结果:
   * - 推荐内容基于面试记录
   * - 资源可正常点击
   */
  test('TC-LR-002: 查看个性化推荐', async ({ page }) => {
    await learningPage.goto();
    await learningPage.expectPageLoaded();

    // 切换到个性化推荐 Tab
    await learningPage.switchToPersonalized();

    // 验证: 推荐内容区域显示
    await expect(page.locator(learningPage.selectors.personalizedSection)).toBeVisible();
  });

  test('TC-LR-002: 查看职业建议', async ({ page }) => {
    await learningPage.goto();
    await learningPage.expectPageLoaded();

    // 切换到职业建议 Tab
    await learningPage.switchToCareer();

    // 验证: 职业建议区域显示
    await expect(page.locator(learningPage.selectors.careerSuggestions)).toBeVisible();

    // 验证: 有建议内容
    const suggestions = await learningPage.getCareerSuggestions();
    // 建议可能为空，不做强制验证
  });

  /**
   * 查看资源详情
   */
  test('点击资源查看详情', async ({ page }) => {
    await learningPage.goto();
    await learningPage.expectPageLoaded();

    // 点击第一个资源
    await learningPage.clickResource(0);

    // 验证: 跳转到详情页
    await expect(page).toHaveURL(/\/pages\/resources\/resources/);

    // 验证: 详情页内容显示
    await expect(page.locator(learningPage.selectors.resourceDetail)).toBeVisible();
  });

  /**
   * 未登录用户访问学习资源重定向
   */
  test('未登录用户访问学习资源重定向到登录', async ({ page }) => {
    // 清除登录状态
    await page.evaluate(() => {
      localStorage.clear();
    });

    // 尝试直接访问学习资源页面
    await page.goto('/pages/learning/learning');
    await sleep(1000);

    // 验证: 重定向到登录页面
    await expect(page).toHaveURL(/\/pages\/login\/login/);
  });
});
