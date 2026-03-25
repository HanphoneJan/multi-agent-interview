<template>
  <div class="privacy-policy">
    <header class="header">
      <h1>隐私政策</h1>
      <p class="last-updated">最后更新日期: {{ lastUpdated }}</p>
    </header>

    <main class="content">
      <section v-for="(section, index) in sections" :key="index" class="policy-section">
        <h2 :class="['section-title', { 'active': activeSection === index }]" 
            @click="toggleSection(index)">
          {{ section.title }}
          <span class="toggle-icon">{{ activeSection === index ? '−' : '+' }}</span>
        </h2>
        <div v-show="activeSection === index" class="section-content">
          <p v-for="(paragraph, pIndex) in section.content" :key="pIndex">{{ paragraph }}</p>
        </div>
      </section>
    </main>

    <footer class="footer">
      <p>如果您对我们的隐私政策有任何疑问，请通过以下方式联系我们：</p>
      <div class="contact-info">
        <p>邮箱: <a href="mailto:privacy@example.com">privacy@example.com</a></p>
        <p>电话: 123-456-7890</p>
      </div>
    </footer>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  setup() {
    const lastUpdated = ref('2025年7月16日');
    const activeSection = ref(0);

    const sections = ref([
      {
        title: '1. 信息收集',
        content: [
          '我们收集您在使用我们的服务时主动提供的信息，包括但不限于姓名、电子邮件地址、电话号码等。',
          '我们还可能自动收集某些信息，如IP地址、浏览器类型、访问时间和日期等。'
        ]
      },
      {
        title: '2. 信息使用',
        content: [
          '我们使用收集的信息来提供、维护和改进我们的服务。',
          '您的信息可能用于与您沟通，例如发送服务通知或营销信息（如果您已同意接收）。',
          '我们可能使用匿名或聚合数据进行统计分析，以改进我们的产品和服务。'
        ]
      },
      {
        title: '3. 信息共享',
        content: [
          '我们不会出售您的个人信息给第三方。',
          '我们可能在以下情况下共享信息：与为我们提供服务的供应商（他们必须遵守保密协议）、法律要求时，或在公司合并或收购的情况下。'
        ]
      },
      {
        title: '4. 数据安全',
        content: [
          '我们采取合理的安全措施来保护您的个人信息免受未经授权的访问、更改或破坏。',
          '尽管我们尽力保护您的信息，但请注意没有任何互联网传输或电子存储方法是100%安全的。'
        ]
      },
      {
        title: '5. 您的权利',
        content: [
          '您可以随时请求访问、更正或删除我们持有的关于您的个人信息。',
          '您可以撤回对数据处理活动的同意，或反对某些处理方式。',
          '要行使这些权利，请通过下方提供的联系方式与我们联系。'
        ]
      },
      {
        title: '6. Cookie和技术',
        content: [
          '我们使用Cookie和类似技术来增强用户体验和分析网站使用情况。',
          '您可以通过浏览器设置拒绝Cookie，但这可能会影响某些功能的正常使用。'
        ]
      },
      {
        title: '7. 政策变更',
        content: [
          '我们可能会不时更新本隐私政策。更新后的政策将在发布后立即生效。',
          '我们会通过网站通知或其他显著方式告知您重大变更。'
        ]
      }
    ]);

    const toggleSection = (index) => {
      activeSection.value = activeSection.value === index ? null : index;
    };

    return {
      lastUpdated,
      sections,
      activeSection,
      toggleSection
    };
  }
};
</script>

<style scoped>
.privacy-policy {
  font-family: 'Arial', sans-serif;
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  color: var(--text-primary);
  background-color: var(--bg-card);
  box-shadow: 0 0 20px rgba(0, 0, 255, 0.1);
  border-radius: 8px;
}

.header {
  text-align: center;
  padding: 20px 0;
  border-bottom: 2px solid #3498db;
  margin-bottom: 30px;
}

.header h1 {
  color: var(--text-primary);
  font-size: 2.2rem;
  margin-bottom: 10px;
}

.last-updated {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.policy-section {
  margin-bottom: 20px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  overflow: hidden;
}

.section-title {
  background-color: var(--color-primary);
  color: var(--text-inverse);
  padding: 15px 20px;
  margin: 0;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.3s;
}

.section-title:hover {
  background-color: var(--color-primary-dark);
}

.section-title.active {
  background-color: var(--text-primary);
}

.toggle-icon {
  font-weight: bold;
  font-size: 1.2rem;
}

.section-content {
  padding: 20px;
  background-color: var(--bg-page);
  line-height: 1.6;
}

.section-content p {
  margin-bottom: 15px;
}

.footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 2px solid #3498db;
  text-align: center;
}

.contact-info {
  margin: 20px 0;
}

.contact-info p {
  margin: 5px 0;
}

.contact-info a {
  color: var(--color-primary);
  text-decoration: none;
}

.contact-info a:hover {
  text-decoration: underline;
}


/* 响应式设计 */
@media (max-width: 768px) {
  .privacy-policy {
    padding: 15px;
  }
  
  .header h1 {
    font-size: 1.8rem;
  }
  
  .section-title {
    padding: 12px 15px;
    font-size: 1rem;
  }
  
  .section-content {
    padding: 15px;
  }
}

@media (max-width: 480px) {
  .header h1 {
    font-size: 1.5rem;
  }
  
  .last-updated {
    font-size: 0.8rem;
  }
  
  .section-content p {
    font-size: 0.9rem;
  }
  
  .accept-btn {
    padding: 10px 20px;
  }
}
</style>