// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The icon of each entry of the main menu, by the name utils/menu.js gives it:
// the sidebar and the phone's bar draw the same ones.
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideGlobe from '~icons/lucide/globe'
import LucideReceipt from '~icons/lucide/receipt-text'
import LucideShare from '~icons/lucide/share-2'
import LucideWorkflow from '~icons/lucide/workflow'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import { markRaw } from 'vue'

export const ICONE_DEL_MENU = Object.fromEntries(
  Object.entries({
    dashboard: LucideLayoutDashboard,
    calendar: CalendarIcon,
    conversations: SMSIcon,
    tasks: TaskIcon,
    invoices: LucideReceipt,
    people: LeadsIcon,
    deals: DealsIcon,
    // a flow of steps, and posts shared: not the deals' bolt nor a link out
    automations: LucideWorkflow,
    social: LucideShare,
    site: LucideGlobe,
  }).map(([nome, icona]) => [nome, markRaw(icona)]),
)
