import frappeUIPreset from 'frappe-ui/tailwind'

// the patient area's own classes: its files, the CRM's components it borrows (the
// centre's tile, the design system's, a food's mark with the icons piani.js names)
// and the frappe-ui components it uses
export default {
  presets: [frappeUIPreset],
  content: [
    './area.html',
    './src/area/**/*.{vue,js}',
    './src/components/CentreTile.vue',
    './src/components/Espresso/**/*.vue',
    './src/components/Plans/FoodMark.vue',
    './src/utils/piani.js',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts}',
  ],
}
