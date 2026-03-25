import { createSSRApp } from "vue";
import App from "./App.vue";
import * as Pinia from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

export function createApp() {
  const app = createSSRApp(App);
  // 先创建 Pinia 实例
  const pinia = Pinia.createPinia()
  
  // 仅在浏览器环境下为 Pinia 添加持久化插件
  if (typeof window !== 'undefined') {
    pinia.use(piniaPluginPersistedstate)
  }
  
  // 再将 Pinia 实例挂载到 Vue 应用
  app.use(pinia);
  
  return {
    app,
    Pinia
  };
}