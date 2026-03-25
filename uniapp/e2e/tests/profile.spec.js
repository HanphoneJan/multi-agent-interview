/**
 * 个人中心模块 E2E 测试
 *
 * 测试用例:
 * - TC-PC-001: 查看个人资料
 * - TC-PC-002: 编辑个人资料
 */

const { test, expect } = require('@playwright/test');
const { login } = require('../utils/api-client');
const { mockLoginState, safeFill, safeClick, sleep } = require('../utils/test-helpers');
const users = require('../fixtures/users.json');

// 测试套件配置
test.describe('个人中心模块', () => {
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
    // 设置登录状态
    await mockLoginState(page, { accessToken }, users.testUsers.experiencedUser);
  });

  /**
   * TC-PC-001: 查看个人资料
   *
   * 前置条件: 用户已登录
   * 测试步骤:
   * 1. 进入"我的" Tab
   * 2. 查看个人资料
   *
   * 预期结果:
   * - 用户信息正确显示
   * - 头像、昵称等加载正常
   */
  test('TC-PC-001: 查看个人资料', async ({ page }) => {
    // Step 1: 进入"我的" Tab
    await page.goto('/pages/mine/mine');
    await page.waitForLoadState('networkidle');

    // Step 2: 验证个人资料显示
    // 验证: 用户名显示
    await expect(page.locator('.user-name, .username, .nickname')).toContainText(
      users.testUsers.experiencedUser.name
    );

    // 验证: 头像显示
    await expect(page.locator('.user-avatar, .avatar')).toBeVisible();

    // 验证: 面试统计显示
    await expect(page.locator('.interview-stats, .stats-container')).toBeVisible();
  });

  /**
   * TC-PC-002: 编辑个人资料
   *
   * 前置条件: 用户已登录
   * 测试步骤:
   * 1. 进入个人资料页
   * 2. 点击编辑
   * 3. 修改信息
   * 4. 保存
   *
   * 预期结果:
   * - 信息更新成功
   * - 页面显示更新后的信息
   */
  test('TC-PC-002: 编辑个人昵称', async ({ page }) => {
    // Step 1: 进入个人中心
    await page.goto('/pages/mine/mine');
    await page.waitForLoadState('networkidle');

    // Step 2: 点击编辑按钮
    await safeClick(page, '.edit-profile, .edit-btn, button:has-text("编辑")');

    // 验证: 进入编辑页面
    await expect(page).toHaveURL(/\/pages\/profile\/profile/);

    // Step 3: 修改昵称
    const newName = '修改后的昵称' + Date.now();
    await safeFill(page, 'input[name="name"], .nickname-input', newName);

    // Step 4: 保存
    await safeClick(page, '.save-btn, button:has-text("保存")');
    await sleep(1000);

    // 验证: 保存成功提示
    await expect(page.locator('.toast-message, .success-message')).toContainText(/保存成功|更新成功/i);

    // 验证: 返回个人中心，昵称已更新
    await expect(page).toHaveURL(/\/pages\/mine\/mine/);
    await expect(page.locator('.user-name, .username')).toContainText(newName);
  });

  /**
   * 查看面试记录
   */
  test('查看面试记录列表', async ({ page }) => {
    await page.goto('/pages/mine/mine');
    await page.waitForLoadState('networkidle');

    // 点击面试记录入口
    await safeClick(page, '.interview-history, [data-nav="history"]');

    // 验证: 跳转到面试记录页面
    await expect(page).toHaveURL(/\/pages\/report\/report/);

    // 验证: 面试记录列表显示
    await expect(page.locator('.report-list, .interview-list')).toBeVisible();
  });

  /**
   * 查看面试报告详情
   */
  test('查看面试报告详情', async ({ page }) => {
    // 先进入报告列表
    await page.goto('/pages/report/report');
    await page.waitForLoadState('networkidle');

    // 如果有面试记录，点击查看详情
    const reportItems = page.locator('.report-item, .interview-item');
    const count = await reportItems.count();

    if (count > 0) {
      await reportItems.first().click();
      await sleep(1000);

      // 验证: 报告详情显示
      await expect(page.locator('.report-detail, .detail-container')).toBeVisible();
    }
  });

  /**
   * 简历评估入口
   */
  test('访问简历评估页面', async ({ page }) => {
    await page.goto('/pages/mine/mine');
    await page.waitForLoadState('networkidle');

    // 点击简历评估入口
    await safeClick(page, '.resume-eval, [data-nav="resume"]');

    // 验证: 跳转到简历评估页面
    await expect(page).toHaveURL(/\/pages\/resume\/resume/);

    // 验证: 上传区域显示
    await expect(page.locator('.upload-area, .resume-upload')).toBeVisible();
  });

  /**
   * 设置页面
   */
  test('访问设置页面', async ({ page }) => {
    await page.goto('/pages/mine/mine');
    await page.waitForLoadState('networkidle');

    // 点击设置按钮
    await safeClick(page, '.settings-btn, button:has-text("设置")');

    // 验证: 跳转到设置页面
    await expect(page).toHaveURL(/\/pages\/settings\/settings/);
  });

  /**
   * 退出登录
   */
  test('退出登录功能', async ({ page }) => {
    await page.goto('/pages/mine/mine');
    await page.waitForLoadState('networkidle');

    // 点击退出登录
    await safeClick(page, '.logout-btn, button:has-text("退出登录")');

    // 确认退出
    await safeClick(page, '.confirm-btn, button:has-text("确认")');
    await sleep(1000);

    // 验证: 跳转到登录页面
    await expect(page).toHaveURL(/\/pages\/login\/login/);

    // 验证: Token 已清除
    const loginState = await page.evaluate(() => {
      return {
        accessToken: localStorage.getItem('accessToken'),
        refreshToken: localStorage.getItem('refreshToken'),
      };
    });
    expect(loginState.accessToken).toBeFalsy();
    expect(loginState.refreshToken).toBeFalsy();
  });
});
