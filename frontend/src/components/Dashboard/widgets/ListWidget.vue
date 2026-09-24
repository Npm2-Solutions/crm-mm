<template>
  <div class="flex h-full flex-col">
    <div
      v-if="!items.length"
      class="flex flex-1 items-center justify-center px-6 pb-6 text-center text-sm text-ink-gray-5"
    >
      {{ answer.empty || __('Nothing here') }}
    </div>
    <ul v-else class="min-h-0 flex-1 overflow-y-auto px-2 pb-1">
      <li v-for="(item, index) in items" :key="index">
        <!-- not <component :is="'button'">: Vue resolves that name to the
             registered frappe-ui Button before the native element -->
        <div
          class="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left"
          :class="
            linked(item)
              ? 'cursor-pointer hover:bg-surface-gray-1 focus-visible:bg-surface-gray-1 focus-visible:outline-none'
              : ''
          "
          :role="linked(item) ? 'button' : undefined"
          :tabindex="linked(item) ? 0 : undefined"
          @click="$emit('navigate', item)"
          @keydown.enter="$emit('navigate', item)"
        >
          <UserAvatar
            v-if="item.user"
            :user="item.user"
            size="sm"
            class="shrink-0"
          />
          <span
            v-else-if="item.icon"
            class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2"
          >
            <Icon
              :icon="iconName(item.icon)"
              class="size-3.5 text-ink-gray-6"
            />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-medium text-ink-gray-8">
              {{ item.title }}
            </span>
            <span
              v-if="item.subtitle"
              class="block truncate text-xs text-ink-gray-5"
            >
              {{ item.subtitle }}
            </span>
          </span>
          <span class="flex max-w-[50%] shrink-0 flex-col items-end gap-1">
            <span
              v-if="item.value != null"
              class="text-sm font-medium tabular-nums text-ink-gray-8"
            >
              {{
                formatValue(item.value, item.format, {
                  locale,
                  currency: answer.currency,
                })
              }}
            </span>
            <Badge
              v-if="item.badge"
              class="max-w-full overflow-hidden"
              :title="item.badge.label"
              :label="item.badge.label"
              :theme="badgeTheme(item.badge.color)"
              variant="subtle"
              size="sm"
            />
            <span
              v-if="item.time"
              class="whitespace-nowrap text-xs text-ink-gray-5"
              :title="exactTime(item.time)"
            >
              {{ item.clock ? clockTime(item.time) : timeAgo(item.time) }}
            </span>
          </span>
        </div>
      </li>
    </ul>
    <div
      v-if="footer || answer.more"
      class="flex items-center justify-between gap-2 border-t border-outline-gray-1 px-4 py-2 text-xs"
    >
      <span class="text-ink-gray-5">{{ footer }}</span>
      <button
        v-if="answer.more"
        class="inline-flex items-center gap-0.5 font-medium text-ink-gray-7 hover:text-ink-gray-9"
        @click="$emit('navigate', answer.more)"
      >
        {{ answer.more.label }}
        <span class="lucide-arrow-right size-3" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { badgeTheme } from '@/components/Dashboard/meta'
import { formatValue } from '@/utils/dashboard'
import { timeAgo } from '@/utils'
import { Badge, dayjsLocal } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  answer: { type: Object, required: true },
  locale: { type: String, default: undefined },
})

defineEmits(['navigate'])

const items = computed(() => props.answer.items || [])

// "6 of 23": the list is the top of something bigger
const footer = computed(() => {
  const total = props.answer.total
  if (total && total > items.value.length) {
    return __('{0} of {1}', [items.value.length, total])
  }
  return ''
})

function linked(item) {
  return Boolean(item.route || item.settings)
}

function iconName(icon) {
  return (
    {
      whatsapp: 'message-circle',
      sms: 'message-square-text',
      email: 'mail',
      message: 'message-square',
      phone: 'phone',
    }[icon] || icon
  )
}

// an appointment is read on a clock: "10:30", "tomorrow 09:00", "Thu 26 Sep 17:00"
function clockTime(value) {
  const date = dayjsLocal(value)
  const time = date.format('HH:mm')
  const today = dayjsLocal().startOf('day')
  const day = date.startOf('day').diff(today, 'day')
  if (day === 0) return time
  if (day === 1) return `${__('tomorrow')} ${time}`
  const label = new Intl.DateTimeFormat(props.locale, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(date.toDate())
  return `${label} ${time}`
}

function exactTime(value) {
  return new Intl.DateTimeFormat(props.locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(dayjsLocal(value).toDate())
}
</script>
