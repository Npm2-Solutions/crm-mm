// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

// The icon of each entry of the main menu, by the name utils/menu.js gives it:
// the sidebar and the phone's bar draw the same ones.
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideClipboardCheck from '~icons/lucide/clipboard-check'
import LucideGlobe from '~icons/lucide/globe'
import LucideReceipt from '~icons/lucide/receipt-text'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import AutomationIcon from '@/components/Icons/AutomationIcon.vue'
import SocialIcon from '@/components/Icons/SocialIcon.vue'
import { markRaw } from 'vue'

export const ICONE_DEL_MENU = Object.fromEntries(
  Object.entries({
    dashboard: LucideLayoutDashboard,
    today: LucideClipboardCheck,
    calendar: CalendarIcon,
    conversations: SMSIcon,
    tasks: TaskIcon,
    invoices: LucideReceipt,
    people: LeadsIcon,
    deals: DealsIcon,
    automations: AutomationIcon,
    social: SocialIcon,
    site: LucideGlobe,
  }).map(([nome, icona]) => [nome, markRaw(icona)]),
)
