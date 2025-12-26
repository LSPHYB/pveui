import { resolve } from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteMockServe } from 'vite-plugin-mock'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  return {
    base: '/',
    resolve: {
      extensions: ['.vue', '.js'],
      alias: {
        '@': resolve(__dirname, 'src'),
        '@novnc/novnc/core/rfb': resolve(__dirname, 'node_modules/@novnc/novnc/lib/rfb.js')
      }
    },
    plugins: [
      vue(),
    ]
  }
})
