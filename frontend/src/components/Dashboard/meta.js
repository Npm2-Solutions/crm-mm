// What the dashboard shows about the catalogue: category names and icons, the
// icon of each kind of widget, the layout-only widgets. Functions, not constants:
// `__()` must run when the page renders, after the translations are loaded.

import { isDark } from '@/utils/dashboardCharts'
import { useTheme } from 'frappe-ui'
import { computed } from 'vue'

export function categoryMeta(key) {
  const categories = {
    sales: { label: __('Sales'), icon: 'handshake' },
    invoicing: { label: __('Invoicing'), icon: 'receipt-text' },
    people: { label: __('People'), icon: 'users' },
    conversations: { label: __('Conversations'), icon: 'messages-square' },
    whatsapp: { label: __('WhatsApp'), icon: 'message-circle' },
    sms: { label: __('SMS'), icon: 'message-square-text' },
    email: { label: __('Email'), icon: 'mail' },
    calls: { label: __('Calls'), icon: 'phone' },
    agenda: { label: __('Agenda'), icon: 'calendar' },
    booking: { label: __('Online booking'), icon: 'calendar-check' },
    marketing: { label: __('Marketing'), icon: 'megaphone' },
    meta: { label: __('Meta ads'), icon: 'badge-euro' },
    automations: { label: __('Automations'), icon: 'workflow' },
    social: { label: __('Social'), icon: 'share-2' },
    tasks: { label: __('Tasks and notes'), icon: 'list-checks' },
    team: { label: __('Team'), icon: 'users-round' },
    layout: { label: __('Layout'), icon: 'layout-template' },
  }
  return categories[key] || { label: key, icon: 'layout-grid' }
}

export function kindMeta(kind) {
  const kinds = {
    number: { label: __('Number'), icon: 'hash' },
    axis: { label: __('Chart'), icon: 'chart-column' },
    donut: { label: __('Share'), icon: 'chart-pie' },
    funnel: { label: __('Funnel'), icon: 'funnel' },
    list: { label: __('List'), icon: 'list' },
    table: { label: __('Table'), icon: 'table' },
    heatmap: { label: __('Heatmap'), icon: 'grid-3x3' },
    heading: { label: __('Section title'), icon: 'heading' },
    spacer: { label: __('Empty space'), icon: 'separator-horizontal' },
  }
  return kinds[kind] || kinds.number
}

// Widgets that are layout, not data: the server never answers for them.
export const STRUCTURAL = ['heading', 'spacer']

export function isStructural(name) {
  return STRUCTURAL.includes(name)
}

export function layoutWidgets() {
  return [
    {
      id: 'heading',
      kind: 'heading',
      category: 'layout',
      title: __('Section title'),
      description: __('A title that splits the dashboard into sections'),
      size: [20, 1],
      options: [],
    },
    {
      id: 'spacer',
      kind: 'spacer',
      category: 'layout',
      title: __('Empty space'),
      description: __('Blank room to line the widgets up'),
      size: [4, 3],
      options: [],
    },
  ]
}

// Colours a badge can take in list widgets, from the server's names.
export function badgeTheme(color) {
  const themes = {
    green: 'green',
    red: 'red',
    orange: 'orange',
    blue: 'blue',
    gray: 'gray',
    yellow: 'orange',
    amber: 'orange',
    pink: 'red',
    violet: 'blue',
    purple: 'blue',
    cyan: 'blue',
    teal: 'green',
    black: 'gray',
  }
  return themes[color] || 'gray'
}

// Whether the charts draw with the dark palette; follows the theme switcher
// live (setTheme updates the ref before it re-paints <html data-theme>, and a
// computed reads it only on the next render, after both).
export function useDarkCharts() {
  const { currentTheme } = useTheme()
  return computed(() => Boolean(currentTheme.value) && isDark())
}
