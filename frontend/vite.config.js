import fs from 'fs'
import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { getProxyOptions } from 'frappe-ui/src/utils/vite-dev-server'

const sitesDir = path.resolve(__dirname, '../../../sites')
const common = JSON.parse(fs.readFileSync(path.join(sitesDir, 'common_site_config.json'), 'utf8'))

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [vue()],
  // Production assets are served from sites/assets via symlink; keep browser URLs at /accounting-workbench/* (see router base).
  base: command === 'serve' ? '/' : '/assets/accounting_workbench/workbench/',
  server: {
    port: 8080,
    proxy: getProxyOptions({ port: common.webserver_port }),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    // Must live under accounting_workbench/accounting_workbench/public so bench
    // symlinks it to sites/assets/accounting_workbench (see hooks app linking).
    outDir: path.resolve(__dirname, '../accounting_workbench/public/workbench'),
    emptyOutDir: true,
    target: 'es2015',
  },
  optimizeDeps: {
    include: ['frappe-ui > feather-icons', 'showdown', 'engine.io-client'],
  },
}))
