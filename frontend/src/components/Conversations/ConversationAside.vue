<!--
  The right column: who you are talking to.

  Deliberately short. The record page is one click away and holds everything;
  what belongs here is only what you need *while replying* — who this is, how
  else to reach them, and whose conversation it is. What you decide about the
  conversation itself — read, later, done — moved up to the header, next to the
  thread it is about.
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
      <Button
        :label="__('Open the record')"
        iconRight="lucide-arrow-up-right"
        size="sm"
        @click="router.push({ name: 'Lead', params: { leadId: person.name } })"
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
        <span class="truncate tabular-nums">{{ person.mobile_no }}</span>
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
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import PersonAvatar from '@/components/Conversations/PersonAvatar.vue'
import { useConversationState } from '@/composables/conversationState'
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

const title = computed(
  () =>
    props.person.lead_name ||
    props.person.organization ||
    props.person.name ||
    '',
)
</script>
