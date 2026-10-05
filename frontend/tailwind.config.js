// Modifications copyright (c) 2026, NPM2 Solutions Srl

import frappeUIPreset from 'frappe-ui/tailwind'
import plugin from 'tailwindcss/plugin'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    // linked @framework/ui source (apps/frappe/ui/src) — scan so its utility and
    // arbitrary-variant classes (e.g. Notifications TabButtons overrides) are generated
    '../../frappe/ui/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  // The typography sizes nobody draws: frappe-ui's editor only names them in a
  // regular expression, and each built 55 rules that every element is tested
  // against when its style is worked out (`.prose-xl :where(h4 + *)…` keys on
  // no class): 40 ms more to open a menu on a slow phone
  blocklist: ['prose-xl', 'prose-2xl'],
  safelist: [
    '!text-gray-700',
    '!text-blue-600',
    '!text-green-700',
    '!text-red-600',
    '!text-pink-600',
    '!text-orange-600',
    '!text-amber-600',
    '!text-yellow-600',
    '!text-cyan-600',
    '!text-teal-600',
    '!text-violet-600',
    '!text-purple-600',
    '!text-ink-gray-9',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    // A settings page follows the pane it is drawn in (`Settings.vue`), not
    // the screen: on a tablet held upright the pane beside the menu is as
    // narrow as a phone, on a screen `max-md:` takes for a desk's. On a phone
    // the pane is the screen, so the variant holds there too.
    plugin(({ addVariant }) => {
      addVariant(
        'impostazioni-strette',
        '@container impostazioni (max-width: 40rem)',
      )
    }),
  ],
}
