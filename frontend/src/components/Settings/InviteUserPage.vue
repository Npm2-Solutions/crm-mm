<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex px-2 justify-between impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1 w-9/12 max-md:w-full">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Send Invites To') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Invite people to {brand}, with the levels they will have: what they see and what they can do',
            )
          }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end impostazioni-strette:w-auto impostazioni-strette:justify-start"
      >
        <AzioneImpostazioni
          :label="__('Send Invites')"
          :disabled="
            !invitees.length ||
            !chosenLevels.length ||
            userExistMessage ||
            inviteeExistMessage
          "
          :loading="inviteByEmail.loading"
          @click="inviteByEmail.submit()"
        />
      </div>
    </div>
    <div class="flex-1 flex flex-col px-2 gap-8 overflow-y-auto">
      <div>
        <FormControl
          type="textarea"
          :label="__('Invite By Email')"
          placeholder="user1@example.com, user2@example.com, ..."
          :debounce="100"
          :disabled="inviteByEmail.loading"
          :description="
            __(
              'You can invite multiple users by comma separating their email addresses',
            )
          "
          @input="updateInvitees($event.target.value)"
        />
        <div
          v-if="userExistMessage || inviteeExistMessage"
          class="text-xs text-ink-red-6 mt-1.5"
        >
          {{ userExistMessage || inviteeExistMessage }}
        </div>
        <div class="mt-5 flex flex-col gap-2">
          <div class="text-xs text-ink-gray-5">{{ __('Invite As') }}</div>
          <LevelPicker
            v-model="chosenLevels"
            :levels="levels.data || []"
            :disabled="inviteByEmail.loading"
          />
        </div>
      </div>
      <template v-if="pendingInvitations.data?.length && !invitees.length">
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between text-base-semibold">
            <div>{{ __('Pending Invites') }}</div>
          </div>
          <ul class="flex flex-col gap-1">
            <li
              v-for="user in pendingInvitations.data"
              :key="user.name"
              class="flex items-center justify-between px-2 py-1 rounded-lg bg-surface-gray-2"
            >
              <div class="text-base">
                <span class="text-ink-gray-8">
                  {{ user.email }}
                </span>
                <span class="text-ink-gray-5"> ({{ invitedAs(user) }}) </span>
              </div>
              <div>
                <Button
                  :aria-label="__('Delete Invitation')"
                  :tooltip="__('Delete Invitation')"
                  icon="lucide-x"
                  variant="ghost"
                  :loading="
                    pendingInvitations.delete.loading &&
                    pendingInvitations.delete.params.name === user.name
                  "
                  @click="pendingInvitations.delete.submit(user.name)"
                />
              </div>
            </li>
          </ul>
        </div>
      </template>
    </div>
    <ErrorMessage :message="error" />
  </div>
</template>
<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import LevelPicker from '@/components/Settings/LevelPicker.vue'
import { useLevels, levelLabels } from '@/composables/levels'
import { validateEmail, convertArrayToString } from '@/utils'
import { usersStore } from '@/stores/users'
import { useTelemetry } from 'frappe-ui/frappe'
import {
  toast,
  createListResource,
  createResource,
  FormControl,
} from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const { users } = usersStore()
const { capture } = useTelemetry()
const levels = useLevels()

const invitees = ref([])
const chosenLevels = ref([])
const error = ref(null)

// Front desk until someone chooses otherwise: the level most people get
watch(
  () => levels.data,
  (data) => {
    if (!chosenLevels.value.length && data?.some((l) => l.key === 'segreteria'))
      chosenLevels.value = ['segreteria']
  },
  { immediate: true },
)

const userExistMessage = computed(() => {
  const inviteesSet = new Set(invitees.value)
  if (!inviteesSet.size) return null

  if (!users.data?.crmUsers?.length) return null
  const existingEmails = users.data.crmUsers.map((user) => user.name)
  const existingUsersSet = new Set(existingEmails)

  const existingInvitees = inviteesSet.intersection(existingUsersSet)
  if (existingInvitees.size === 0) return null

  return __('User with email {0} already exists', [
    Array.from(existingInvitees).join(', '),
  ])
})

const inviteeExistMessage = computed(() => {
  const inviteesSet = new Set(invitees.value)
  if (!inviteesSet.size) return null

  if (!pendingInvitations.data?.length) return null
  const existingEmails = pendingInvitations.data.map((user) => user.email)
  const existingUsersSet = new Set(existingEmails)

  const existingInvitees = inviteesSet.intersection(existingUsersSet)
  if (existingInvitees.size === 0) return null

  return __('User with email {0} already invited', [
    Array.from(existingInvitees).join(', '),
  ])
})

// invitations from before levels carry a role
const roleMap = {
  'Sales User': __('Sales User'),
  'Sales Manager': __('Manager'),
  'System Manager': __('Admin'),
}

function invitedAs(invitation) {
  const keys = (invitation.levels || '').split('\n').filter(Boolean)
  if (!keys.length) return roleMap[invitation.role] || invitation.role
  const labels = levelLabels(levels.data)
  return keys.map((key) => __(labels[key] || key)).join(', ')
}

const inviteByEmail = createResource({
  url: 'crm.api.invite_by_email',
  makeParams() {
    return {
      emails: convertArrayToString(invitees.value),
      levels: JSON.stringify(chosenLevels.value),
    }
  },
  onSuccess() {
    error.value = null
    invitees.value = []
    pendingInvitations.reload()
    toast.success(__('Invitations sent successfully'))
    capture('user_invited')
  },
  onError(err) {
    error.value = err?.messages?.[0]
    toast.error(error.value)
  },
})

const pendingInvitations = createListResource({
  type: 'list',
  doctype: 'CRM Invitation',
  filters: { status: 'Pending' },
  fields: ['name', 'email', 'role', 'levels'],
  pageLength: 999,
  auto: true,
})

function updateInvitees(value) {
  const emails = value
    .split(',')
    .map((email) => email.trim())
    .filter((email) => validateEmail(email))
  invitees.value = emails
}
</script>
