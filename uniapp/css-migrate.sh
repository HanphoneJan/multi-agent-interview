#!/bin/bash
# CSS 变量迁移脚本 - 批量替换常见硬编码颜色

# 定义颜色映射
# 注意：此脚本仅作参考，实际替换需要根据上下文判断

echo "CSS 变量迁移助手"
echo "=================="
echo ""
echo "请手动在 Vue 文件中替换以下颜色值："
echo ""
echo "## 主要替换映射："
echo ""
echo "| 原颜色值 | 替换为 |"
echo "|----------|--------|"
echo "| #3964fe, #2a7bf6, #1565C0, #1976D2, #2196F3 | var(--color-primary) |"
echo "| #ffffff, #fff, #FFFFFF, #FFF | var(--bg-card) 或 var(--text-inverse) |"
echo "| #333, #333333, #2c3e50 | var(--text-primary) |"
echo "| #666, #666666, #81858c | var(--text-secondary) |"
echo "| #999, #999999 | var(--text-tertiary) |"
echo "| #f5f5f5, #f8f8f8, #f9fafb, #F0F4F8, #f5f7fa | var(--bg-page) |"
echo "| #e0e0e0, #e0e3e7, #E0E0E0, #f0f0f0 | var(--border-default) |"
echo "| #ff4d4f, #F44336, #ff5722 | var(--color-error) |"
echo "| #22c55e, #4caf50 | var(--color-success) |"
echo "| #f59e0b, #ff9800 | var(--color-warning) |"
echo ""
echo "## 注意事项："
echo "1. 渐变色需要特殊处理：linear-gradient 中的颜色也需要替换 |"
echo "2. rgba() 颜色需要转换为 CSS 变量或使用 rgb 配合 opacity |"
echo "3. 阴影中的颜色建议使用 var(--color-primary) 并配合低透明度 |"
echo ""
