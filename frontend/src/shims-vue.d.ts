declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // 定义一个泛型组件类型，兼容所有 Vue 组件的 props、emit、setup 等
  const component: DefineComponent<{}, {}, any>
  export default component
}