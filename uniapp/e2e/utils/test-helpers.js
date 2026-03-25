/**
 * E2E 测试辅助函数
 */

const { expect } = require('@playwright/test');

/**
 * 等待页面加载完成
 * @param {Page} page - Playwright page 对象
 * @param {number} timeout - 超时时间(毫秒)
 */
async function waitForPageLoad(page, timeout = 10000) {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * 等待元素可见并可点击
 * @param {Page} page - Playwright page 对象
 * @param {string} selector - 元素选择器
 * @param {number} timeout - 超时时间(毫秒)
 */
async function waitForElement(page, selector, timeout = 5000) {
  const element = page.locator(selector);
  await element.waitFor({ state: 'visible', timeout });
  return element;
}

/**
 * 安全点击元素(等待元素可见后点击)
 * @param {Page} page - Playwright page 对象
 * @param {string} selector - 元素选择器
 * @param {number} timeout - 超时时间(毫秒)
 */
async function safeClick(page, selector, timeout = 5000) {
  const element = await waitForElement(page, selector, timeout);
  await element.click();
}

/**
 * 安全填充输入框
 * @param {Page} page - Playwright page 对象
 * @param {string} selector - 输入框选择器
 * @param {string} value - 要输入的值
 * @param {number} timeout - 超时时间(毫秒)
 */
async function safeFill(page, selector, value, timeout = 5000) {
  const element = await waitForElement(page, selector, timeout);
  await element.clear();
  await element.fill(value);
}

/**
 * 等待指定时间(毫秒)
 * @param {number} ms - 等待时间
 */
async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 检查元素是否包含指定文本
 * @param {Page} page - Playwright page 对象
 * @param {string} selector - 元素选择器
 * @param {string} text - 期望文本
 * @param {number} timeout - 超时时间(毫秒)
 */
async function expectTextToContain(page, selector, text, timeout = 5000) {
  const element = page.locator(selector);
  await expect(element).toContainText(text, { timeout });
}

/**
 * 检查 Toast 消息
 * @param {Page} page - Playwright page 对象
 * @param {string} text - 期望的 Toast 文本
 * @param {number} timeout - 超时时间(毫秒)
 */
async function expectToast(page, text, timeout = 5000) {
  // UniApp Toast 通常使用 uni-popup 或 uni-toast 组件
  const toastSelectors = [
    '.uni-toast-text',
    '.uni-popup-message-text',
    '.toast-message',
    '[class*="toast"]'
  ];

  for (const selector of toastSelectors) {
    const toast = page.locator(selector);
    try {
      await expect(toast).toContainText(text, { timeout: 2000 });
      return;
    } catch {
      continue;
    }
  }

  // 如果找不到特定选择器，尝试通过文本内容查找
  const body = page.locator('body');
  await expect(body).toContainText(text, { timeout });
}

/**
 * 模拟登录状态
 * @param {Page} page - Playwright page 对象
 * @param {Object} tokens - Token 信息
 * @param {Object} userInfo - 用户信息
 */
async function mockLoginState(page, tokens, userInfo) {
  try {
    // 尝试在主frame中设置localStorage
    await page.evaluate(({ tokens, userInfo }) => {
      // 支持UniApp的存储键名（snake_case和camelCase）
      localStorage.setItem('accessToken', tokens.accessToken || tokens.access_token || '');
      localStorage.setItem('access_token', tokens.accessToken || tokens.access_token || '');
      localStorage.setItem('refreshToken', tokens.refreshToken || tokens.refresh_token || '');
      localStorage.setItem('refresh_token', tokens.refreshToken || tokens.refresh_token || '');
      localStorage.setItem('userInfo', JSON.stringify(userInfo));
      localStorage.setItem('user_info', JSON.stringify(userInfo));
      localStorage.setItem('tokenExpireTime', String(Date.now() + 30 * 60 * 1000));
      localStorage.setItem('token_expire', String(Date.now() + 30 * 60 * 1000));
    }, { tokens, userInfo });
  } catch (error) {
    console.warn('Failed to set localStorage in main frame:', error.message);

    // 如果失败，尝试在所有frames中设置
    const frames = page.frames();
    for (const frame of frames) {
      try {
        await frame.evaluate(({ tokens, userInfo }) => {
          localStorage.setItem('accessToken', tokens.accessToken || tokens.access_token || '');
          localStorage.setItem('access_token', tokens.accessToken || tokens.access_token || '');
          localStorage.setItem('refreshToken', tokens.refreshToken || tokens.refresh_token || '');
          localStorage.setItem('refresh_token', tokens.refreshToken || tokens.refresh_token || '');
          localStorage.setItem('userInfo', JSON.stringify(userInfo));
          localStorage.setItem('user_info', JSON.stringify(userInfo));
          localStorage.setItem('tokenExpireTime', String(Date.now() + 30 * 60 * 1000));
          localStorage.setItem('token_expire', String(Date.now() + 30 * 60 * 1000));
        }, { tokens, userInfo });
      } catch (frameError) {
        // 忽略单个frame的错误
      }
    }
  }
}

/**
 * 清除登录状态
 * @param {Page} page - Playwright page 对象
 */
async function clearLoginState(page) {
  const clearStorage = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('user_info');
    localStorage.removeItem('tokenExpireTime');
    localStorage.removeItem('token_expire');
  };

  try {
    await page.evaluate(clearStorage);
  } catch (error) {
    // 尝试在所有frames中清除
    const frames = page.frames();
    for (const frame of frames) {
      try {
        await frame.evaluate(clearStorage);
      } catch (e) {
        // 忽略错误
      }
    }
  }
}

/**
 * 获取当前登录状态
 * @param {Page} page - Playwright page 对象
 * @returns {Object} 登录状态
 */
async function getLoginState(page) {
  const getStorage = () => ({
    accessToken: localStorage.getItem('access_token') || localStorage.getItem('accessToken'),
    refreshToken: localStorage.getItem('refresh_token') || localStorage.getItem('refreshToken'),
    userInfo: JSON.parse(localStorage.getItem('userInfo') || localStorage.getItem('user_info') || 'null'),
    tokenExpireTime: localStorage.getItem('tokenExpire') || localStorage.getItem('token_expire'),
  });

  try {
    return await page.evaluate(getStorage);
  } catch (error) {
    // 尝试从任何可用的frame获取
    const frames = page.frames();
    for (const frame of frames) {
      try {
        const state = await frame.evaluate(getStorage);
        if (state.accessToken) {
          return state;
        }
      } catch (e) {
        // 继续尝试下一个frame
      }
    }
    return { accessToken: null, refreshToken: null, userInfo: null, tokenExpireTime: null };
  }
}

/**
 * 截图保存
 * @param {Page} page - Playwright page 对象
 * @param {string} name - 截图名称
 */
async function takeScreenshot(page, name) {
  await page.screenshot({
    path: `test-results/screenshots/${name}_${Date.now()}.png`,
    fullPage: true,
  });
}

module.exports = {
  waitForPageLoad,
  waitForElement,
  safeClick,
  safeFill,
  sleep,
  expectTextToContain,
  expectToast,
  mockLoginState,
  clearLoginState,
  getLoginState,
  takeScreenshot,
};
