import LucideType from '~icons/lucide/type'
import LucideHash from '~icons/lucide/hash'
import LucideList from '~icons/lucide/list'
import LucideToggleLeft from '~icons/lucide/toggle-left'
import LucideCalendar from '~icons/lucide/calendar'
import LucideGauge from '~icons/lucide/gauge'
import LucideTable from '~icons/lucide/table'
import LucideColumns2 from '~icons/lucide/columns-2'
import LucidePaperclip from '~icons/lucide/paperclip'
import LucideAlignLeft from '~icons/lucide/align-left'
import LucideCalculator from '~icons/lucide/calculator'
import LucideSigma from '~icons/lucide/sigma'
import LucideShieldCheck from '~icons/lucide/shield-check'
import LucideSignature from '~icons/lucide/signature'
import LucideSquareDashed from '~icons/lucide/square-dashed'
import LucidePersonStanding from '~icons/lucide/person-standing'

// one icon per component, shared by the palette, the field cards and the list
const ICONS = {
  text: LucideType,
  number: LucideHash,
  choice: LucideList,
  yesno: LucideToggleLeft,
  date: LucideCalendar,
  scale: LucideGauge,
  table: LucideTable,
  sides: LucideColumns2,
  attachment: LucidePaperclip,
  paragraph: LucideAlignLeft,
  calc: LucideCalculator,
  score: LucideSigma,
  consent: LucideShieldCheck,
  signature: LucideSignature,
  body_chart: LucidePersonStanding,
}

export function componentIcon(type) {
  return ICONS[type] || LucideSquareDashed
}

// the same icons as class names, for menus that take a `lucide-*` string
const NAMES = {
  text: 'lucide-type',
  number: 'lucide-hash',
  choice: 'lucide-list',
  yesno: 'lucide-toggle-left',
  date: 'lucide-calendar',
  scale: 'lucide-gauge',
  table: 'lucide-table',
  sides: 'lucide-columns-2',
  attachment: 'lucide-paperclip',
  paragraph: 'lucide-align-left',
  calc: 'lucide-calculator',
  score: 'lucide-sigma',
  consent: 'lucide-shield-check',
  signature: 'lucide-signature',
  body_chart: 'lucide-person-standing',
}

export function componentIconName(type) {
  return NAMES[type] || 'lucide-square-dashed'
}
