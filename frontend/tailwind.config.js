/** @type {import('tailwindcss').Config} */
module.exports = {
  // 1. 确保扫描到所有 Vue/HTML 文件（覆盖完整）
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./src/App.vue",
    "./src/views/**/*.vue",
    "./src/components/**/*.vue"
  ],
  // 2. 禁用preflight避免和Element Plus样式冲突（保留）
  corePlugins: {
    preflight: false,
  },
  // 3. 集成DaisyUI（核心新增）
  daisyui: {
    themes: ["light", "dark", "cupcake"], // 启用常用主题（可按需增减）
    // darkTheme: "dark", // 指定默认暗色主题
    base: true, // 启用DaisyUI基础样式（依赖preflight: false时建议开启）
    styled: true, // 启用DaisyUI组件样式
    utils: true, // 启用DaisyUI工具类
    prefix: "", // 无前缀（直接用btn、card等类）
    logs: true, // 开发时显示DaisyUI日志（方便调试）
  },
  theme: {
    extend: {
      // 保留原有动画配置
      animation: {
        'aurora-pulse': 'aurora-pulse 6s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'aurora-pulse': {
          '0%, 100%': { opacity: '0.3', transform: 'scale(1)' },
          '50%': { opacity: '0.6', transform: 'scale(1.1)' },
        },
      },
      // 可选：扩展自定义颜色（适配DaisyUI主题）
      colors: {
        primary: '#0078D4', // 匹配你的项目主色
        secondary: '#60a5fa',
      },
    },
  },
  // 4. 注册DaisyUI插件（核心新增）
  plugins: [
    require('daisyui') // 引入DaisyUI插件
  ],
}