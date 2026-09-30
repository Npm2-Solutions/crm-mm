import frappeUIPreset from 'frappe-ui/tailwind'

// the patient area's own classes: its files and the frappe-ui components it uses
export default {
  presets: [frappeUIPreset],
  content: [
    './area.html',
    './src/area/**/*.{vue,js}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts}',
  ],
}
