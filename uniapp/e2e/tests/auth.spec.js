/**
 * 用户认证模块 E2E 测试
 *
 * 测试用例:
 * - TC-AUTH-001: 用户登录成功
 * - TC-AUTH-002: 用户登录失败
 * - TC-AUTH-003: 表单验证
 * - TC-AUTH-004: Token 自动刷新
 */

const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');
const { HomePage } = require('../pages/HomePage');
const { mockLoginState, getLoginState, sleep } = require('../utils/test-helpers');
const users = require('../fixtures/users.json');

// 测试套件配置
test.describe('用户认证模块', () => {
  let loginPage;
  let homePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    homePage = new HomePage(page);
  });

  test.afterEach(async ({ page }) => {
    // 清理登录状态
    await page.evaluate(() => {
      localStorage.clear();
    });
  });

  /**
   * TC-AUTH-001: 用户登录成功
   *
   * 前置条件: 用户已注册，后端服务正常运行
   * 测试步骤:
   * 1. 打开登录页面
   * 2. 输入有效的邮箱/手机号
   * 3. 输入正确的密码
   * 4. 点击登录按钮
   *
   * 预期结果:
   * - 登录成功提示
   * - 跳转到首页
   * - Token 正确存储
   */
  test('TC-AUTH-001: 用户使用邮箱登录成功', async ({ page }) => {
    // 监听控制台日志和网络请求
    page.on('console', msg => console.log('Browser console:', msg.type(), msg.text()));
    page.on('pageerror', err => console.log('Page error:', err.message));
    page.on('request', req => {
      if (req.url().includes('/login')) {
        console.log('Request:', req.method(), req.url());
        console.log('Request headers:', JSON.stringify(req.headers()));
        req.postData() && console.log('Request body:', req.postData());
      }
    });
    page.on('response', async res => {
      if (res.url().includes('/login')) {
        console.log('Response:', res.status(), res.url());
        try {
          const body = await res.json();
          console.log('Response body:', JSON.stringify(body));
        } catch (e) {
          console.log('Response body: [not JSON]');
        }
      }
    });

    // Step 1: 打开登录页面
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    // Step 2-4: 输入正确的登录信息并登录
    const { email, password, name } = users.testUsers.newUser;
    console.log('Attempting login with:', email, password);
    await loginPage.login(email, password);

    // 验证: 跳转到首页
    await expect(page).toHaveURL(/\/pages\/home\/home/);

    // 验证: 登录成功（导航到个人中心页面验证用户信息）
    await page.click('.nav-item:has-text("个人中心"), .tab-item:has-text("我的")');
    await sleep(1000);

    // 验证: 个人中心页面显示正确的用户名
    await expect(page.locator('.username')).toContainText(name);

    // 验证: Token 已存储
    const loginState = await getLoginState(page);
    expect(loginState.accessToken).toBeTruthy();
    expect(loginState.refreshToken).toBeTruthy();
    expect(loginState.tokenExpireTime).toBeTruthy();
  });

  test('TC-AUTH-001: 用户使用手机号登录成功', async ({ page }) => {
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    const { phone, password, name } = users.testUsers.newUser;
    await loginPage.login(phone, password);

    await expect(page).toHaveURL(/\/pages\/home\/home/);

    // 导航到个人中心验证用户信息
    await page.click('.nav-item:has-text("个人中心"), .tab-item:has-text("我的")');
    await sleep(1000);
    await expect(page.locator('.username')).toContainText(name);
  });

  /**
   * TC-AUTH-002: 用户登录失败
   *
   * 前置条件: 用户已注册
   * 测试步骤:
   * 1. 打开登录页面
   * 2. 输入错误的密码
   * 3. 点击登录按钮
   *
   * 预期结果:
   * - 显示错误提示
   * - 停留在登录页
   */
  test('TC-AUTH-002: 使用错误的密码登录失败', async ({ page }) => {
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    const { email } = users.testUsers.newUser;
    const { password: wrongPassword } = users.invalidUsers.wrongPassword;

    await loginPage.login(email, wrongPassword);

    // 验证: 显示错误提示
    await loginPage.expectErrorMessage(/密码错误|登录失败|invalid/i);

    // 验证: 停留在登录页
    await expect(page).toHaveURL(/\/pages\/login\/login/);

    // 验证: 未存储 Token
    const loginState = await getLoginState(page);
    expect(loginState.accessToken).toBeFalsy();
  });

  test('TC-AUTH-002: 使用不存在的账号登录失败', async ({ page }) => {
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    const { email: nonExistentEmail, password } = users.invalidUsers.nonExistent;

    await loginPage.login(nonExistentEmail, password);

    // 验证: 显示错误提示
    await loginPage.expectErrorMessage(/用户不存在|账号不存在|not found/i);

    // 验证: 停留在登录页
    await expect(page).toHaveURL(/\/pages\/login\/login/);
  });

  /**
   * TC-AUTH-003: 表单验证
   *
   * 测试各种表单验证场景
   */
  test('TC-AUTH-003: 空邮箱/手机号验证', async ({ page }) => {
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    // 只输入密码，不输入邮箱
    await loginPage.fillLoginForm('', 'SomePassword123');
    await loginPage.clickLoginButton();

    // 验证: 显示验证错误
    await loginPage.expectErrorMessage(/请输入|不能为空|required/i);
  });

  test('TC-AUTH-003: 空密码验证', async ({ page }) => {
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    const { email } = users.testUsers.newUser;
    await loginPage.fillLoginForm(email, '');
    await loginPage.clickLoginButton();

    // 验证: 显示验证错误
    await loginPage.expectErrorMessage(/请输入密码|不能为空|required/i);
  });

  test('TC-AUTH-003: 邮箱格式验证', async ({ page }) => {
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    // 输入无效的邮箱格式
    await loginPage.fillLoginForm('invalid-email', 'SomePassword123');
    await loginPage.clickLoginButton();

    // 验证: 显示格式错误
    await loginPage.expectErrorMessage(/格式错误|无效|invalid format/i);
  });

  test('TC-AUTH-003: 手机号格式验证', async ({ page }) => {
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    // 输入无效的手机号格式
    await loginPage.fillLoginForm('12345', 'SomePassword123');
    await loginPage.clickLoginButton();

    // 验证: 显示格式错误
    await loginPage.expectErrorMessage(/格式错误|无效|invalid format/i);
  });

  /**
   * TC-AUTH-004: Token 自动刷新
   *
   * 前置条件: 用户已登录，Token 即将过期
   * 测试步骤:
   * 1. 模拟即将过期的 Token
   * 2. 执行需要认证的操作
   *
   * 预期结果:
   * - Token 自动刷新成功
   * - 操作正常执行
   */
  test('TC-AUTH-004: Token 过期时自动刷新', async ({ page }) => {
    // 先正常登录
    await loginPage.goto();
    await loginPage.waitForPageLoad();

    const { email, password } = users.testUsers.newUser;
    await loginPage.login(email, password);
    await expect(page).toHaveURL(/\/pages\/home\/home/);

    // 模拟 Token 即将过期(设置为过去的时间)
    const expiredTime = Date.now() - 1000;
    await page.evaluate((time) => {
      localStorage.setItem('tokenExpireTime', String(time));
    }, expiredTime);

    // 刷新页面，触发 Token 刷新
    await page.reload();
    await sleep(2000);

    // 验证: 页面仍然可以正常访问
    await expect(page).toHaveURL(/\/pages\/home\/home/);

    // 验证: Token 已被刷新
    const loginState = await getLoginState(page);
    const newExpireTime = parseInt(loginState.tokenExpireTime);
    expect(newExpireTime).toBeGreaterThan(Date.now());
  });

  /**
   * 登录状态持久化测试
   */
  test('登录状态在页面刷新后保持', async ({ page }) => {
    // 先登录
    await loginPage.goto();
    await loginPage.login(users.testUsers.newUser.email, users.testUsers.newUser.password);
    await expect(page).toHaveURL(/\/pages\/home\/home/);

    // 记录登录状态
    const beforeRefresh = await getLoginState(page);

    // 刷新页面
    await page.reload();
    await sleep(2000);

    // 验证: 登录状态保持
    const afterRefresh = await getLoginState(page);
    expect(afterRefresh.accessToken).toBe(beforeRefresh.accessToken);
    expect(afterRefresh.userInfo).toEqual(beforeRefresh.userInfo);
  });

  /**
   * 登出功能测试
   */
  test('用户登出功能正常', async ({ page }) => {
    // 先登录
    await loginPage.goto();
    await loginPage.login(users.testUsers.newUser.email, users.testUsers.newUser.password);
    await expect(page).toHaveURL(/\/pages\/home\/home/);

    // 导航到个人中心
    const homePage = new HomePage(page);
    await homePage.switchTab('profile');

    // 点击登出按钮(需要根据实际情况调整选择器)
    await page.click('.logout-button, button:has-text("退出")');
    await sleep(500);

    // 确认登出
    await page.click('.confirm-button, button:has-text("确认")');
    await sleep(1000);

    // 验证: 跳转到登录页
    await expect(page).toHaveURL(/\/pages\/login\/login/);

    // 验证: Token 已被清除
    const loginState = await getLoginState(page);
    expect(loginState.accessToken).toBeFalsy();
    expect(loginState.refreshToken).toBeFalsy();
  });
});
