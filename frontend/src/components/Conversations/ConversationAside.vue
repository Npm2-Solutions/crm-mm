<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The right column: who you are talking to.

  Deliberately short. The record page is one click away and holds everything;
  what belongs here is only what you need *while replying* — who this is, how
  else to reach them, and whose conversation it is. What you decide about the
  conversation itself — read, later, done — moved up to the header, next to the
  thread it is about.

  And the person's summary, the same as on their page: one person, two doors
  (docs/crm/54). «When is my appointment?», «what do I owe?» are
  answered here, without leaving the chat.
-->
<template>
  <div
    class="flex w-full shrink-0 flex-col gap-5 overflow-y-auto bg-surface-base p-4 sm:w-72 sm:border-l"
  >
    <div class="flex flex-col items-center gap-2 pt-2 text-center">
      <PersonAvatar :name="title" :image="person.image" size="xl" />
      <div class="min-w-0 max-w-full">
        <div class="truncate text-lg font-semibold text-ink-gray-9">
          {{ title }}
        </div>
        <div
          v-if="person.lead_name && person.organization"
          class="truncate text-p-sm text-ink-gray-5"
        >
          {{ person.organization }}
        </div>
      </div>
      <!-- on the chat, where one was: the conversations are its door -->
      <Button
        :label="__('Open the record')"
        iconRight="lucide-arrow-up-right"
        size="sm"
        @click="apri('activity')"
      />
    </div>

    <div v-if="person.mobile_no || person.email" class="flex flex-col gap-1">
      <span class="px-2 text-p-xs font-medium text-ink-gray-5">
        {{ __('Contact') }}
      </span>
      <a
        v-if="person.mobile_no"
        class="flex min-w-0 items-center gap-2 rounded-md px-2 py-1.5 text-p-sm text-ink-gray-8 hover:bg-surface-gray-2"
        :href="`tel:${person.mobile_no}`"
      >
        <span
          class="lucide-phone size-4 shrink-0 text-ink-gray-5"
          aria-hidden="true"
        />
        <span class="truncate tabular-nums">{{
          leggibile(person.mobile_no)
        }}</span>
      </a>
      <a
        v-if="person.email"
        class="flex min-w-0 items-center gap-2 rounded-md px-2 py-1.5 text-p-sm text-ink-gray-8 hover:bg-surface-gray-2"
        :href="`mailto:${person.email}`"
      >
        <span
          class="lucide-mail size-4 shrink-0 text-ink-gray-5"
          aria-hidden="true"
        />
        <span class="truncate">{{ person.email }}</span>
      </a>
    </div>

    <div class="flex flex-col gap-1.5">
      <span class="px-2 text-p-xs font-medium text-ink-gray-5">
        {{ __('Assigned to') }}
      </span>
      <!--
        Whose it is, without touching what was decided about it: giving a
        conversation to a colleague used to unpark it, because it went through
        the same door as «open».
      -->
      <Link
        class="w-full"
        doctype="User"
        :value="person.conversation_assigned_to"
        :placeholder="__('Nobody')"
        @change="(user) => assign(user)"
      />
    </div>

    <SummaryArea
      v-if="person.name"
      :key="person.name"
      :lead="person.name"
      :persona="person"
      compatto
      @apri="apri"
    />
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import SummaryArea from '@/components/Activities/SummaryArea.vue'
import PersonAvatar from '@/components/Conversations/PersonAvatar.vue'
import { useConversationState } from '@/composables/conversationState'
import { leggibile } from '@/utils/telefono'
import { computed, toRef } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  person: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['changed'])

const router = useRouter()

const { assign } = useConversationState(toRef(props, 'person'), () =>
  emit('changed'),
)

// the person's page, on the tab a line of the summary names
function apri(scheda) {
  router.push({
    name: 'Lead',
    params: { leadId: props.person.name },
    hash: '#' + scheda,
  })
}

const title = computed(
  () =>
    props.person.lead_name ||
    props.person.organization ||
    props.person.name ||
    '',
)
</script>
