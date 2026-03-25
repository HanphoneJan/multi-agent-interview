/**
 * 现代职场科技蓝 - 主题色彩配置
 * Modern Professional Tech Blue Theme
 */

// 主色板
export const colors = {
  // 主色 - 深海蓝 (Primary)
  primary: {
    50: '#E3F2FD',
    100: '#BBDEFB',
    200: '#90CAF9',
    300: '#64B5F6',
    400: '#42A5F5',
    500: '#2196F3',
    600: '#1976D2',
    700: '#1565C0',
    800: '#0D47A1',
    900: '#0A3670',
  },

  // 辅色 - 青绿色 (Secondary)
  secondary: {
    50: '#E0F2F1',
    100: '#B2DFDB',
    200: '#80CBC4',
    300: '#4DB6AC',
    400: '#26A69A',
    500: '#009688',
    600: '#00897B',
    700: '#00796B',
  },

  // 强调色 - 琥珀橙 (Accent)
  accent: {
    50: '#FFF8E1',
    100: '#FFECB3',
    200: '#FFE082',
    300: '#FFD54F',
    400: '#FFCA28',
    500: '#FFC107',
    600: '#FFB300',
    700: '#FFA000',
    800: '#FF8F00',
    900: '#FF6F00',
  },

  // 语义色
  semantic: {
    success: '#43A047',
    warning: '#FB8C00',
    error: '#E53935',
    info: '#1976D2',
  },

  // 中性色
  neutral: {
    white: '#FFFFFF',
    background: '#F0F4F8',
    surface: '#FFFFFF',
    border: '#E2E8F0',
    divider: '#CBD5E1',
  },

  // 文字色
  text: {
    primary: '#263238',
    secondary: '#546E7A',
    tertiary: '#78909C',
    disabled: '#B0BEC5',
    inverse: '#FFFFFF',
  },
};

// 渐变配置
export const gradients = {
  primary: 'linear-gradient(135deg, #1565C0, #1976D2)',
  primaryHover: 'linear-gradient(135deg, #1976D2, #2196F3)',
  secondary: 'linear-gradient(135deg, #00897B, #26A69A)',
  accent: 'linear-gradient(135deg, #FF6F00, #FF8F00)',
  background: 'linear-gradient(180deg, #F0F4F8 0%, #FFFFFF 100%)',
  surface: 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)',
};

// 阴影配置
export const shadows = {
  sm: '0 2rpx 8rpx rgba(21, 101, 192, 0.08)',
  md: '0 4rpx 16rpx rgba(21, 101, 192, 0.12)',
  lg: '0 8rpx 32rpx rgba(21, 101, 192, 0.15)',
  xl: '0 16rpx 48rpx rgba(21, 101, 192, 0.2)',
  card: '0 4rpx 12rpx rgba(0, 0, 0, 0.05)',
  cardHover: '0 8rpx 24rpx rgba(21, 101, 192, 0.15)',
};

// 常用组合
export const theme = {
  // 按钮主色
  btnPrimary: {
    background: gradients.primary,
    color: colors.neutral.white,
    shadow: shadows.md,
  },

  // 按钮辅色
  btnSecondary: {
    background: gradients.secondary,
    color: colors.neutral.white,
  },

  // 卡片样式
  card: {
    background: colors.neutral.surface,
    borderRadius: '16rpx',
    shadow: shadows.card,
    shadowHover: shadows.cardHover,
  },

  // 输入框样式
  input: {
    border: `2rpx solid ${colors.neutral.border}`,
    borderFocus: `2rpx solid ${colors.primary[500]}`,
    background: colors.neutral.white,
  },

  // 标签样式
  tag: {
    primary: {
      background: colors.primary[50],
      color: colors.primary[700],
      border: `1rpx solid ${colors.primary[200]}`,
    },
    secondary: {
      background: colors.secondary[50],
      color: colors.secondary[700],
    },
    accent: {
      background: colors.accent[50],
      color: colors.accent[900],
    },
  },
};

export default {
  colors,
  gradients,
  shadows,
  theme,
};
