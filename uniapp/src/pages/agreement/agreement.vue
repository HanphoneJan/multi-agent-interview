<template>
  <div class="terms-container">
    <div class="terms-header">
      <h1>用户协议</h1>
      <p class="effective-date">生效日期: {{ effectiveDate }}</p>
    </div>

    <div class="terms-content">
      <div class="tabs">
        <button 
          v-for="(tab, index) in tabs" 
          :key="index" 
          :class="['tab-button', { 'active': activeTab === index }]"
          @click="activeTab = index"
        >
          {{ tab.title }}
        </button>
      </div>

      <div class="tab-content">
        <section v-for="(section, index) in tabs[activeTab].sections" :key="index" class="terms-section">
          <h2 class="section-title">{{ section.title }}</h2>
          <div class="section-content">
            <p v-for="(paragraph, pIndex) in section.content" :key="pIndex">{{ paragraph }}</p>
            <ul v-if="section.listItems" class="terms-list">
              <li v-for="(item, lIndex) in section.listItems" :key="lIndex">{{ item }}</li>
            </ul>
          </div>
        </section>
      </div>
    </div>

    <div class="terms-footer">
      <p class="contact-info">
        如有任何疑问，请联系我们: <a href="mailto:support@example.com">support@example.com</a>
      </p>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  setup() {
    const effectiveDate = ref('2025年7月16日');
    const activeTab = ref(0);
    const isAgreed = ref(false);

    const tabs = ref([
      {
        title: '基本条款',
        sections: [
          {
            title: '1. 协议接受',
            content: [
              '通过访问或使用本服务，您确认已阅读、理解并同意受本用户协议的约束。',
              '如果您不同意本协议的任何条款，请立即停止使用本服务。'
            ]
          },
          {
            title: '2. 服务描述',
            content: [
              '本服务提供......（此处填写您的服务描述）',
              '我们保留随时修改或中断服务的权利，恕不另行通知。'
            ]
          },
          {
            title: '3. 用户义务',
            content: [
              '您同意在使用本服务时遵守所有适用法律和法规。',
              '您不得：'
            ],
            listItems: [
              '以任何非法目的使用本服务',
              '干扰或破坏服务的安全性',
              '尝试未经授权访问任何账户或网络',
              '上传或传播任何恶意软件或有害代码'
            ]
          }
        ]
      },
      {
        title: '账户条款',
        sections: [
          {
            title: '1. 账户注册',
            content: [
              '要使用某些功能，您可能需要注册一个账户。',
              '您同意提供准确、完整和最新的注册信息。'
            ]
          },
          {
            title: '2. 账户安全',
            content: [
              '您有责任维护账户凭证的机密性。',
              '您应对账户下发生的所有活动负责。'
            ]
          },
          {
            title: '3. 账户终止',
            content: [
              '我们保留自行决定终止或暂停您账户的权利，恕不另行通知。',
              '您可以在任何时候通过账户设置停用您的账户。'
            ]
          }
        ]
      },
      {
        title: '知识产权',
        sections: [
          {
            title: '1. 所有权',
            content: [
              '本服务及其原始内容、功能和特性归我们所有并受版权保护。',
              '未经明确书面许可，不得复制、修改或创建衍生作品。'
            ]
          },
          {
            title: '2. 用户内容',
            content: [
              '您保留您提交到本服务的任何内容的权利。',
              '通过提交内容，您授予我们全球性、非独占的许可，以使用、复制和展示该内容。'
            ]
          },
          {
            title: '3. 反馈',
            content: [
              '您提供的任何反馈、评论或建议将被视为非机密信息。',
              '我们有权不受限制地使用和披露此类信息。'
            ]
          }
        ]
      },
      {
        title: '免责声明',
        sections: [
          {
            title: '1. 服务"按原样"提供',
            content: [
              '本服务按"现状"和"可用"的基础提供，不附带任何明示或暗示的保证。',
              '我们不保证服务将不间断、及时、安全或无错误。'
            ]
          },
          {
            title: '2. 责任限制',
            content: [
              '在法律允许的最大范围内，我们对任何间接、附带、特殊或后果性损害不承担责任。',
              '我们的总责任限于您为使用本服务支付的金额（如有）。'
            ]
          }
        ]
      }
    ]);


    return {
      effectiveDate,
      tabs,
      activeTab,
      isAgreed
    };
  }
};
</script>

<style scoped>
.terms-container {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background-color: var(--bg-card);
  box-shadow: 0 0 15px rgba(52, 152, 219, 0.1);
  border-radius: 8px;
  color: var(--text-primary);
}

.terms-header {
  text-align: center;
  padding-bottom: 20px;
  border-bottom: 2px solid #3498db;
  margin-bottom: 25px;
}

.terms-header h1 {
  color: var(--text-primary);
  font-size: 2.2rem;
  margin-bottom: 10px;
}

.effective-date {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.tabs {
  display: flex;
  border-bottom: 1px solid var(--border-default);
  margin-bottom: 20px;
  overflow-x: auto;
}

.tab-button {
  padding: 12px 20px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  color: var(--text-tertiary);
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-button:hover {
  color: var(--color-primary);
}

.tab-button.active {
  color: var(--color-primary);
  border-bottom: 3px solid var(--color-primary);
  font-weight: bold;
}

.terms-section {
  margin-bottom: 30px;
}

.section-title {
  color: var(--text-primary);
  font-size: 1.3rem;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-default);
}

.section-content {
  line-height: 1.6;
}

.section-content p {
  margin-bottom: 12px;
}

.terms-list {
  margin: 15px 0 15px 20px;
  padding-left: 20px;
}

.terms-list li {
  margin-bottom: 8px;
}

.terms-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 2px solid #3498db;
}


@media (max-width: 480px) {
  .terms-header h1 {
    font-size: 1.5rem;
  }
  
  .effective-date {
    font-size: 0.8rem;
  }
  
  .tab-button {
    padding: 10px 15px;
    font-size: 0.9rem;
  }
  
  .section-content p, .terms-list li {
    font-size: 0.9rem;
  }
}
</style>