import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import viteCompression from 'vite-plugin-compression'
import path from 'path'
// 1. 引入 Tailwind CSS 插件
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'

  return {
    plugins: [
      vue(),
      isProduction && viteCompression({
        verbose: true,
        disable: false,
        threshold: 10240,
        algorithm: 'gzip',
        ext: '.gz',
        deleteOriginFile: false
      })
    ].filter(Boolean),
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      },
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      open: false,
      cors: true
    },
    // 2. 添加 CSS 预处理器配置，集成 Tailwind + Autoprefixer
    css: {
      postcss: {
        plugins: [
          // 配置 Tailwind（自动读取项目根目录的 tailwind.config.js）
          tailwindcss(),
          // 自动添加浏览器前缀（如 -webkit-、-moz-）
          autoprefixer()
        ]
      }
    },
    esbuild: {
      drop: isProduction ? ['console', 'debugger'] : []
    },
    build: {
      sourcemap: false,
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.warn'],
          reduce_vars: false,
          computed_props: false
        },
        mangle: {
          toplevel: false
        },
        format: {
          comments: false,
          beautify: false
        }
      },
      rollupOptions: {
        output: {
          manualChunks: {
            vue: ['vue'],
            vendor: ['axios', 'md5'],
            // 可选：拆分 Tailwind 相关样式（优化缓存）
            tailwind: ['tailwindcss']
          },
          compact: true,
          generatedCode: {
            constBindings: true,
            objectShorthand: true
          }
        }
      },
      chunkSizeWarningLimit: 1500
    }
  }
})