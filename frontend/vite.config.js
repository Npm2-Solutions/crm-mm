// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'
import frappeUiNellaLingua from './vite/frappeUi.js'
import precaricaSoloIlNuovo from './vite/precarica.js'

// https://vitejs.dev/config/
export default defineConfig(async ({ mode }) => {
  const isDev = mode === 'development'
  // a dynamic import preloads only what its caller has not loaded (vite/precarica.js)
  const precarica = precaricaSoloIlNuovo()
  const config = {
    plugins: [
      // frappe-ui's own words in the user's language, not English (vite/frappeUi.js)
      frappeUiNellaLingua(),
      precarica.plugin,
      vue(),
      vueJsx(),
      VitePWA({
        // The service worker this made was registered on /assets/crm/frontend/,
        // a scope with no page of DottorCloud in it (they are under /crm), so
        // it answered nothing - and on a phone's first visit, and at every new
        // version, it downloaded the whole app in the background to keep it
        // (392 files, 7.6 MB). It now removes itself and what it kept, from the
        // phones that have it too.
        selfDestroying: true,
        registerType: 'autoUpdate',
        workbox: {
          maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
        },
        devOptions: {
          enabled: true,
        },
        // The phone's manifest is the brand's - the vertical's the plan has on -
        // so the server writes it (crm.marchio.manifest) and index.html links it:
        // a manifest built here would carry one name and one icon for every site.
        manifest: false,
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, 'src'),
        // vuedraggable is published as a UMD bundle that does `require("vue")`:
        // that brought Vue's CommonJS build, template compiler and all, into the
        // first download of every page. Its own ES sources (in the package) take
        // the runtime the rest of the app uses, and nothing compiles templates.
        vuedraggable: path.resolve(
          import.meta.dirname,
          'node_modules/vuedraggable/src/vuedraggable.js',
        ),
        // point at the package src dir (not index.ts) so subpath imports like
        // `@framework/ui/components/Notifications` resolve. Importing subpaths avoids the
        // barrel, which `export *`s components (Grid/Phone/FormLayout) that need a newer
        // frappe-ui (`frappe-ui/internals`) than this app pins.
        '@framework/ui': path.resolve(
          import.meta.dirname,
          '../../frappe/ui/src',
        ),
      },
      // ensure the linked framework package reuses the host app's single copy of each peer.
      // `dompurify` is an implicit dep of @framework/ui's sanitize util (not declared in its
      // package.json); dedupe resolves it to the host's copy since the symlinked source has
      // no node_modules of its own.
      // the editor packages must resolve to one copy each: tiptap imports
      // `@tiptap/pm/model` while prosemirror-state/transform/tables import bare
      // `prosemirror-model`, so a nested install of either throws "multiple
      // versions of prosemirror-model were loaded" on mention insert. Unlike
      // optimizeDeps (dev-only) this also applies to the production build.
      dedupe: [
        'vue',
        'vue-router',
        'frappe-ui',
        'dompurify',
        '@tiptap/core',
        '@tiptap/pm',
        '@tiptap/vue-3',
        'prosemirror-model',
        'prosemirror-state',
        'prosemirror-view',
        'prosemirror-transform',
        // one Sortable for vuedraggable and @vueuse's useSortable (a list's sort
        // order): vuedraggable pins 1.14.0 in its own node_modules, so a list page
        // downloaded two
        'sortablejs',
      ],
    },
    build: {
      modulePreload: { resolveDependencies: precarica.resolveDependencies },
    },
    optimizeDeps: {
      include: [
        'feather-icons',
        'tailwind.config.js',
        'prosemirror-state',
        'prosemirror-view',
        'lowlight',
        'interactjs',
      ],
    },
    server: {
      fs: {
        // allow the bench `apps/` dir so Vite can serve linked local packages
        // (frappe-ui, @framework/ui) that live in sibling app repos
        allow: [path.resolve(import.meta.dirname, '../..')],
      },
    },
  }

  const frappeui = await importFrappeUIPlugin(isDev, config)
  config.plugins.unshift(
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      buildConfig: {
        indexHtmlPath: '../crm/www/crm.html',
        emptyOutDir: true,
        sourcemap: true,
      },
    }),
  )

  return config
})

async function importFrappeUIPlugin(isDev, config) {
  if (isDev) {
    try {
      // Check if local frappe-ui has the vite plugin file
      const fs = await import('node:fs')
      const localVitePluginPath = path.resolve(
        import.meta.dirname,
        '../frappe-ui/vite/index.js',
      )

      if (fs.existsSync(localVitePluginPath)) {
        const module = await import('../frappe-ui/vite/index.js')
        console.info('Local frappe-ui vite plugin found, using local plugin')
        config.resolve.alias = getAliases(config)
        return module.default
      } else {
        console.warn('Local frappe-ui vite plugin not found, using npm package')
      }
    } catch (error) {
      console.warn(
        'Local frappe-ui not found, falling back to npm package:',
        error.message,
      )
    }
  }
  // Fall back to npm package if local import fails
  const module = await import('frappe-ui/vite')
  return module.default
}

function getAliases(config) {
  return {
    ...config.resolve.alias,
    'frappe-ui/tailwind': path.resolve(
      import.meta.dirname,
      '../frappe-ui/tailwind/preset.js',
    ),
    'frappe-ui/style.css': path.resolve(
      import.meta.dirname,
      '../frappe-ui/src/style.css',
    ),
    'frappe-ui/frappe': path.resolve(
      import.meta.dirname,
      '../frappe-ui/frappe/index.js',
    ),
    // subpath entries must precede the bare `frappe-ui` key: a plain string alias
    // matches by prefix, so without these subpaths would rewrite under
    // `.../src/index.ts`. `internals` is pulled in by @framework/ui.
    'frappe-ui/icons': path.resolve(
      import.meta.dirname,
      '../frappe-ui/icons/index.ts',
    ),
    'frappe-ui/editor': path.resolve(
      import.meta.dirname,
      '../frappe-ui/src/molecules/editor/index.ts',
    ),
    'frappe-ui/editor-style.css': path.resolve(
      import.meta.dirname,
      '../frappe-ui/src/molecules/editor/style.css',
    ),
    'frappe-ui/internals': path.resolve(
      import.meta.dirname,
      '../frappe-ui/internals.ts',
    ),
    'frappe-ui': path.resolve(import.meta.dirname, '../frappe-ui/src/index.ts'),
  }
}
