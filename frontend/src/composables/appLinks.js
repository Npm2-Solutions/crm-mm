import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideGlobe from '~icons/lucide/globe'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import SMSIcon from '@/components/Icons/SMSIcon.vue'
import AutomationIcon from '@/components/Icons/AutomationIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import SocialIcon from '@/components/Icons/SocialIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { callEnabled } from '@/composables/telephony'
import { usersStore } from '@/stores/users'

/**
 * Everywhere in the app you can go, in one list.
 *
 * The desktop sidebar reads it flat, in this order. The phone's menu reads the
 * same entries grouped by `group`, because thirteen undifferentiated rows is a
 * list you scan rather than a menu you use. Two readings, one list — so a new
 * screen cannot appear in one and be missing from the other.
 */
export const LINK_GROUPS = [
  { key: 'daily', label: 'Every day' },
  { key: 'records', label: 'Records' },
  { key: 'reach', label: 'Marketing & site' },
  { key: 'numbers', label: 'Numbers' },
]

function links() {
  const { isManager } = usersStore()
  return [
    {
      label: 'Dashboard',
      icon: LucideLayoutDashboard,
      to: 'Dashboard',
      group: 'numbers',
    },
    {
      // the people. "Lead" is what one of them is at the start, not what they
      // are forever: they stay here after a deal is opened, as in GHL and
      // HubSpot, so the list cannot be named after the first ten minutes
      label: 'People',
      icon: LeadsIcon,
      to: 'Leads',
      group: 'daily',
    },
    { label: 'Deals', icon: DealsIcon, to: 'Deals', group: 'daily' },
    {
      label: 'Organizations',
      icon: OrganizationsIcon,
      to: 'Organizations',
      group: 'records',
    },
    {
      // the same people as above; this is where you answer them
      label: 'Conversations',
      icon: SMSIcon,
      to: 'Conversations',
      group: 'daily',
    },
    {
      label: 'Automations',
      icon: AutomationIcon,
      to: 'Automations',
      group: 'reach',
      condition: () => isManager(),
    },
    { label: 'Notes', icon: NoteIcon, to: 'Notes', group: 'records' },
    { label: 'Tasks', icon: TaskIcon, to: 'Tasks', group: 'daily' },
    { label: 'Calendar', icon: CalendarIcon, to: 'Calendar', group: 'daily' },
    {
      label: 'Call Logs',
      icon: PhoneIcon,
      to: 'Call Logs',
      group: 'records',
    },
    {
      label: 'Dialer',
      icon: DialpadIcon,
      to: 'Dialer',
      group: 'records',
      condition: () => callEnabled.value,
    },
    {
      label: 'Social Planner',
      icon: SocialIcon,
      to: 'Social Planner',
      group: 'reach',
    },
    {
      label: 'Site',
      icon: LucideGlobe,
      to: 'Website',
      group: 'reach',
      // managers only: the page itself handles "Builder missing" and "site off",
      // so it stays reachable — otherwise there would be nowhere to turn the
      // site on from
      condition: () => isManager(),
    },
  ]
}

/** The entries this user may see, in the order the desktop sidebar wants them. */
export function visibleLinks() {
  return links().filter((link) => !link.condition || link.condition())
}

/** The same entries, grouped, for the phone's menu. Empty groups drop out. */
export function groupedLinks() {
  const visible = visibleLinks()
  return LINK_GROUPS.map((group) => ({
    ...group,
    links: visible.filter((link) => link.group === group.key),
  })).filter((group) => group.links.length)
}
