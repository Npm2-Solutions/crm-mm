<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  One notification: who it comes from - their face with the kind's mark on its
  corner, or the mark alone when it is DottorCloud itself - what it says, the
  first words of the message it is about, when, and the dot while it is unread.
  The whole row opens it; reading or unreading it is its own button, there on a
  touch screen too.
-->
<template>
  <div
    class="group relative flex items-start gap-1 rounded px-2 py-2.5 hover:bg-surface-gray-2"
  >
    <!-- a row without a page of its own opens what it is about by itself -->
    <component
      :is="riga.route ? RouterLink : ElementoNativo"
      v-bind="
        riga.route ? { to: riga.route } : { tag: 'button', type: 'button' }
      "
      class="flex min-w-0 flex-1 items-start gap-3 rounded text-left focus-visible:[outline:var(--focus-outline-default)] focus-visible:outline-offset-2"
      @click="emit('opened', riga)"
    >
      <span class="relative mt-0.5 shrink-0">
        <UserAvatar v-if="riga.from" :user="riga.from.name" size="lg" />
        <NotificationMark v-else :kind="riga.kind" />
        <NotificationMark
          v-if="riga.from"
          :kind="riga.kind"
          taglia="sm"
          class="absolute -bottom-1 -right-1.5"
        />
      </span>
      <span class="flex min-w-0 flex-1 flex-col gap-1">
        <!-- eslint-disable vue/no-v-html -- the server's sentence, its words and names escaped -->
        <span
          class="text-p-base [&_b]:font-medium [&_b]:text-ink-gray-9"
          :class="riga.read ? 'text-ink-gray-6' : 'text-ink-gray-8'"
          v-html="sanitizeHTML(riga.text)"
        />
        <!-- eslint-enable vue/no-v-html -->
        <span
          v-if="riga.excerpt"
          class="line-clamp-2 border-l-2 border-outline-gray-2 pl-2 text-p-sm text-ink-gray-6"
        >
          {{ riga.excerpt }}
        </span>
        <span class="text-sm text-ink-gray-5">
          {{ quando }} · {{ __(segno.parola, null, 'Kind of notification') }}
        </span>
      </span>
    </component>

    <span class="flex shrink-0 flex-col items-center gap-1 pt-1">
      <span
        class="size-2 rounded-full"
        :class="riga.read ? 'bg-transparent' : 'bg-[var(--brand-segno)]'"
        :role="riga.read ? undefined : 'img'"
        :aria-label="riga.read ? undefined : __('Unread')"
      />
      <Button
        variant="ghost"
        size="sm"
        class="touch-target opacity-0 focus-visible:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
        :tooltip="riga.read ? __('Mark as unread') : __('Mark as read')"
        :aria-label="riga.read ? __('Mark as unread') : __('Mark as read')"
        @click.stop="emit(riga.read ? 'unread' : 'read', riga)"
      >
        <template #icon>
          <LucideMail v-if="riga.read" class="size-4 text-ink-gray-5" />
          <LucideCheck v-else class="size-4 text-ink-gray-5" />
        </template>
      </Button>
    </span>
  </div>
</template>

<script setup>
import ElementoNativo from '@/components/ElementoNativo'
import NotificationMark from '@/components/Notifications/NotificationMark.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { sanitizeHTML } from '@/utils'
import { appLocale } from '@/utils/locale'
import { aspetto, orario } from '@/utils/notifiche'
import { dayjsLocal } from 'frappe-ui'
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import LucideCheck from '~icons/lucide/check'
import LucideMail from '~icons/lucide/mail'

const props = defineProps({
  riga: { type: Object, required: true },
  // the reader's now, as the list's days were cut with it
  adesso: { type: String, required: true },
})

const emit = defineEmits(['opened', 'read', 'unread'])

const segno = computed(() => aspetto(props.riga.kind))
const quando = computed(() =>
  orario(
    dayjsLocal(props.riga.creation).format('YYYY-MM-DD HH:mm:ss'),
    props.adesso,
    appLocale(),
  ),
)
</script>
