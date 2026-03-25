import js from '@eslint/js';
import pluginVue from 'eslint-plugin-vue';
import globals from 'globals';

export default [
  // 忽略的文件和目录
  {
    ignores: [
      'dist/**/*',
      'node_modules/**/*',
      'unpackage/**/*',
      'src/uni_modules/**/*',
      'src/static/**/*',
    ],
  },

  // JavaScript 文件配置
  {
    files: ['**/*.js', '**/*.mjs'],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.node,
        uni: 'readonly',
        wx: 'readonly',
        getApp: 'readonly',
        getCurrentPages: 'readonly',
      },
    },
    rules: {
      ...js.configs.recommended.rules,
      // 自定义规则
      'no-console': 'off', // 允许 console（开发环境需要）
      'no-debugger': 'warn',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'prefer-const': 'warn',
      'no-var': 'warn',
    },
  },

  // Vue 文件配置
  ...pluginVue.configs['flat/recommended'].map(config => ({
    ...config,
    files: ['**/*.vue'],
  })),

  // Vue 文件特定配置
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        ecmaVersion: 2024,
        sourceType: 'module',
      },
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.node,
        uni: 'readonly',
        wx: 'readonly',
        getApp: 'readonly',
        getCurrentPages: 'readonly',
      },
    },
    rules: {
      // Vue 特定规则
      'vue/multi-word-component-names': 'off', // 允许单单词组件名（如 index.vue）
      'vue/no-unused-vars': 'warn',
      'vue/require-default-prop': 'off',
      'vue/require-prop-types': 'off',
      'vue/no-reserved-keys': 'off', // UniApp 中使用 _ 前缀的变量很常见
      'vue/html-self-closing': 'off', // UniApp 中不强制自闭合
      'vue/singleline-html-element-content-newline': 'off', // 不强制单行元素换行
      'vue/multiline-html-element-content-newline': 'off', // 不强制多行元素换行
      'vue/html-indent': 'off', // 不强制缩进
      'vue/max-attributes-per-line': ['warn', {
        singleline: 4,
        multiline: 1,
      }],
      'vue/attributes-order': 'off', // 不强制属性顺序
    },
  },
];
