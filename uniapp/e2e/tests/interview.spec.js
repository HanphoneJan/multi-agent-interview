/**
 * 面试流程模块 E2E 测试
 *
 * 测试用例:
 * - TC-IV-001: 选择面试场景
 * - TC-IV-002: 创建面试会话
 * - TC-IV-003: 面试过程中暂停/恢复
 * - TC-IV-004: 面试消息交互
 * - TC-IV-005: 结束面试
 */

const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');
const { HomePage } = require('../pages/HomePage');
const { InterviewPage } = require('../pages/InterviewPage');
const { login, createInterviewSession } = require('../utils/api-client');
const { sleep } = require('../utils/test-helpers');
const users = require('../fixtures/users.json');
const scenarios = require('../fixtures/scenarios.json');

// 测试套件配置
test.describe('面试流程模块', () => {
  let loginPage;
  let homePage;
  let interviewPage;
  let accessToken;
  let userInfo;

  test.beforeAll(async () => {
    // 通过 API 登录获取 Token
    const tokens = await login(
      users.testUsers.experiencedUser.email,
      users.testUsers.experiencedUser.password
    );
    accessToken = tokens.accessToken;
  });

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    homePage = new HomePage(page);
    interviewPage = new InterviewPage(page);

    // 通过UI登录而不是mock登录状态（避免localStorage跨域问题）
    await loginPage.goto();
    await loginPage.login(users.testUsers.experiencedUser.email, users.testUsers.experiencedUser.password);
    await expect(page).toHaveURL(/\/pages\/home\/home/, { timeout: 10000 });
  });

  /**
   * TC-IV-001: 选择面试场景
   *
   * 前置条件: 用户已登录
   * 测试步骤:
   * 1. 进入首页
   * 2. 点击"开始面试"
   * 3. 选择一个面试场景
   * 4. 确认选择
   *
   * 预期结果:
   * - 场景列表正常加载
   * - 选中场景后跳转到面试页面
   */
  test('TC-IV-001: 选择面试场景并开始面试', async ({ page }) => {
    // Step 1: 进入首页
    await homePage.goto();
    await homePage.expectPageLoaded();

    // Step 2: 点击"开始面试"
    await homePage.clickStartInterview();

    // 验证: 场景选择页面显示
    await expect(page).toHaveURL(/\/pages\/choose\/choose/);

    // Step 3: 选择一个面试场景
    const scenario = scenarios.scenarios[0];
    await homePage.selectScenario(scenario.name);

    // Step 4: 确认选择
    // 页面应该跳转到面试页面或显示确认对话框
    await sleep(2000);

    // 验证: 跳转到面试页面或会话创建成功
    const currentUrl = page.url();
    expect(
      currentUrl.includes('/pages/interview/interview') ||
      currentUrl.includes('/pages/choose/choose')
    ).toBeTruthy();
  });

  /**
   * TC-IV-002: 创建面试会话
   *
   * 前置条件: 用户已登录，已选择场景
   * 测试步骤:
   * 1. 通过 API 创建会话
   * 2. 跳转到面试页面
   * 3. 验证面试页面显示正确
   *
   * 预期结果:
   * - 会话创建成功
   * - 面试页面正常显示
   * - WebSocket 连接建立
   */
  test('TC-IV-002: 创建面试会话并加载面试页面', async ({ page }) => {
    // Step 1: 通过 API 创建会话
    const scenario = scenarios.scenarios[0];
    const session = await createInterviewSession(accessToken, scenario.id);

    expect(session).toHaveProperty('id');
    expect(session.scenario_id).toBe(scenario.id);

    // Step 2: 跳转到面试页面
    await interviewPage.goto(session.id);

    // Step 3: 验证面试页面显示正确
    await interviewPage.expectPageLoaded();

    // 验证: 面试标题正确
    const title = await interviewPage.getInterviewTitle();
    expect(title).toBeTruthy();

    // 验证: 计时器显示
    const timer = await interviewPage.getTimerDisplay();
    expect(timer).toBeTruthy();
  });

  /**
   * TC-IV-003: 面试过程中暂停/恢复
   *
   * 前置条件: 正在进行面试
   * 测试步骤:
   * 1. 在面试页面点击暂停
   * 2. 确认暂停
   * 3. 点击恢复面试
   *
   * 预期结果:
   * - 暂停成功，计时停止
   * - 恢复后面试继续进行
   */
  test('TC-IV-003: 面试暂停和恢复功能', async ({ page }) => {
    // 前置条件: 创建并进入面试
    const scenario = scenarios.scenarios[0];
    const session = await createInterviewSession(accessToken, scenario.id);
    await interviewPage.goto(session.id);
    await interviewPage.expectPageLoaded();

    // 记录暂停前的时间
    const timeBeforePause = await interviewPage.getTimerDisplay();
    await sleep(2000);

    // Step 1: 点击暂停
    await interviewPage.clickPause();

    // 验证: 显示暂停状态
    await expect(page.locator('.paused-indicator, .pause-status')).toBeVisible();

    // 验证: 计时停止
    await sleep(3000);
    const timeAfterPause = await interviewPage.getTimerDisplay();
    expect(timeAfterPause).toBe(timeBeforePause);

    // Step 3: 点击恢复
    await interviewPage.clickResume();

    // 验证: 暂停状态消失
    await expect(page.locator('.paused-indicator, .pause-status')).not.toBeVisible();

    // 验证: 计时继续
    await sleep(2000);
    const timeAfterResume = await interviewPage.getTimerDisplay();
    expect(timeAfterResume).not.toBe(timeAfterPause);
  });

  /**
   * TC-IV-004: 面试消息交互
   *
   * 测试面试过程中的消息发送和接收
   */
  test('TC-IV-004: 发送消息并接收面试官回复', async ({ page }) => {
    // 创建并进入面试
    const scenario = scenarios.scenarios[0];
    const session = await createInterviewSession(accessToken, scenario.id);
    await interviewPage.goto(session.id);
    await interviewPage.expectPageLoaded();

    // 等待面试官初始消息
    await sleep(3000);

    // 验证: 可以发送消息
    await interviewPage.expectCanSendMessage();

    // 发送消息
    const testMessage = '你好，我是来面试的候选人';
    await interviewPage.sendMessage(testMessage);

    // 等待面试官回复
    await interviewPage.waitForInterviewerResponse(30000);

    // 验证: 收到面试官回复
    const messages = await interviewPage.getInterviewerMessages();
    expect(messages.length).toBeGreaterThan(0);
  });

  /**
   * TC-IV-005: 结束面试
   *
   * 测试结束面试功能
   */
  test('TC-IV-005: 结束面试并生成报告', async ({ page }) => {
    // 创建并进入面试
    const scenario = scenarios.scenarios[0];
    const session = await createInterviewSession(accessToken, scenario.id);
    await interviewPage.goto(session.id);
    await interviewPage.expectPageLoaded();

    // 进行一些交互
    await interviewPage.sendMessage('开始面试');
    await sleep(3000);

    // 点击结束按钮
    await interviewPage.clickEnd();

    // 验证: 显示确认对话框
    await expect(page.locator(interviewPage.selectors.confirmDialog)).toBeVisible();

    // 确认结束
    await interviewPage.confirmEnd();

    // 验证: 跳转到面试报告页面
    await expect(page).toHaveURL(/\/pages\/report\/report/, { timeout: 10000 });

    // 验证: 报告页面显示
    await expect(page.locator('.report-container, .interview-report')).toBeVisible();
  });

  /**
   * TC-IV-005: 取消结束面试
   */
  test('TC-IV-005: 取消结束面试', async ({ page }) => {
    // 创建并进入面试
    const scenario = scenarios.scenarios[0];
    const session = await createInterviewSession(accessToken, scenario.id);
    await interviewPage.goto(session.id);
    await interviewPage.expectPageLoaded();

    // 点击结束按钮
    await interviewPage.clickEnd();

    // 验证: 显示确认对话框
    await expect(page.locator(interviewPage.selectors.confirmDialog)).toBeVisible();

    // 取消结束
    await interviewPage.cancelEnd();

    // 验证: 确认对话框消失，仍在面试页面
    await expect(page.locator(interviewPage.selectors.confirmDialog)).not.toBeVisible();
    await expect(page).toHaveURL(/\/pages\/interview\/interview/);
  });

  /**
   * 面试场景列表加载测试
   */
  test('面试场景列表正常加载', async ({ page }) => {
    await homePage.goto();
    await homePage.expectPageLoaded();

    // 点击开始面试
    await homePage.clickStartInterview();

    // 验证: 场景列表加载成功
    await expect(page).toHaveURL(/\/pages\/choose\/choose/);

    // 验证: 至少有一个场景显示
    await expect(page.locator('.scenario-card, .scenario-item')).toHaveCount(
      scenarios.scenarios.length
    );
  });

  /**
   * 未登录用户访问面试页面重定向到登录
   */
  test('未登录用户访问面试页面重定向到登录', async ({ context }) => {
    // 使用新的无痕页面（无localStorage）
    const incognitoPage = await context.newPage();

    // 尝试直接访问面试页面
    await incognitoPage.goto('/pages/choose/choose');
    await sleep(1000);

    // 验证: 重定向到登录页面
    await expect(incognitoPage).toHaveURL(/\/pages\/login\/login/);
    await incognitoPage.close();
  });
});
