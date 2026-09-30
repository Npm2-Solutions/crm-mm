// The patient area, built apart from the CRM: its own entry, its own output
// (`/assets/crm/area`), none of the staff's code. The page that serves it is
// `crm/www/area.html`, copied from the build with its Jinja placeholders.
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import path from 'path'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

export default defineConfig({
  // frappe-ui's own plugin for its icons and for importing only the components
  // the area uses; none of its CRM-page features (proxy, boot data, build paths)
  plugins: [
    frappeui({
      frappeProxy: false,
      jinjaBootData: false,
      buildConfig: false,
      lucideIcons: true,
    }),
    vue(),
  ],
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, 'src') },
    dedupe: ['vue', 'vue-router', 'frappe-ui'],
  },
  css: {
    postcss: {
      plugins: [
        tailwindcss({ config: './tailwind.area.config.js' }),
        autoprefixer(),
      ],
    },
  },
  build: {
    outDir: '../crm/public/area',
    emptyOutDir: true,
    rollupOptions: { input: path.resolve(import.meta.dirname, 'area.html') },
  },
})
