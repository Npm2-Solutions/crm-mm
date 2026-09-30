<template>
  <div
    class="flex h-full flex-col gap-6 p-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <!-- Header -->
    <div
      class="flex justify-between px-2 pt-2 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1 w-9/12 max-md:w-full">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Users') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Add or invite the people who work in DottorCloud, and give each one their levels: what they see and what they can do',
            )
          }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end max-md:w-auto max-md:justify-start"
      >
        <Dropdown
          :options="[
            {
              label: __('Add Existing User'),
              onClick: () => (showAddExistingModal = true),
            },
            {
              label: __('Invite New User'),
              onClick: () => (activeSettingsPage = 'Invite User'),
            },
          ]"
          :button="{
            label: __('New'),
            iconLeft: 'plus',
            variant: 'solid',
          }"
          placement="right"
        />
      </div>
    </div>

    <!-- loading state -->
    <div v-if="users.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="users.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <!-- Empty State -->
    <EmptyState
      v-if="!users.loading && users.data?.crmUsers?.length == 1"
      name="Users"
      :description="__('Add one to get started.')"
      icon="user"
    />

    <!-- Users List -->
    <div
      v-if="!users.loading && users.data?.crmUsers?.length > 1"
      class="flex flex-col overflow-hidden"
    >
      <div
        v-if="users.data?.crmUsers?.length > 10"
        class="flex items-center gap-2 mb-4 px-2 pt-0.5"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search User')"
          class="w-full"
          :debounce="300"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-6"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <Select
          v-model="currentLevel"
          class="shrink-0"
          :options="levelOptions"
        />
      </div>
      <ul class="divide-y divide-outline-elevation-2 overflow-y-auto px-2">
        <template v-for="user in usersList" :key="user.name">
          <!-- the name gives way, not the role: an address as long as the
               row pushed the role and the menu past the edge of a phone -->
          <li class="flex items-center justify-between gap-3 py-2">
            <div class="flex min-w-0 items-center">
              <Avatar
                :image="user.user_image"
                :label="user.full_name"
                size="xl"
              />
              <div class="ml-3 flex min-w-0 flex-col">
                <div class="truncate text-p-base text-ink-gray-8">
                  {{ user.full_name }}
                </div>
                <div class="truncate text-p-sm text-ink-gray-5">
                  {{ user.name }}
                </div>
              </div>
            </div>
            <div class="flex shrink-0 flex-row-reverse items-center gap-2">
              <Dropdown
                :options="getMoreOptions(user)"
                :button="{
                  icon: 'more-horizontal',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmRemove = false
                  },
                }"
                placement="right"
              />
              <Tooltip
                v-if="user.agency"
                :text="
                  __(
                    'Manages the site: the agency sets their access, from the Desk',
                  )
                "
              >
                <Button :label="__('Agency')" icon-left="lucide-shield" />
              </Tooltip>
              <Button
                v-else
                class="max-w-56 max-md:max-w-36"
                :icon-left="levelIcon(user)"
                @click="editing = user"
              >
                <span class="truncate" :class="{ italic: user.levels_implied }">
                  {{ levelText(user) }}
                </span>
              </Button>
            </div>
          </li>
        </template>
      </ul>
    </div>
  </div>
  <AddExistingUserModal
    v-if="showAddExistingModal"
    v-model="showAddExistingModal"
  />
  <UserAccessModal
    v-if="editing"
    :key="editing.name"
    :user="editing"
    :model-value="Boolean(editing)"
    @update:model-value="(open) => !open && (editing = null)"
  />
</template>

<script setup>
import AddExistingUserModal from '@/components/Modals/AddExistingUserModal.vue'
import UserAccessModal from '@/components/Modals/UserAccessModal.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { activeSettingsPage } from '@/composables/settings'
import { useLevels, levelLabels } from '@/composables/levels'
import { usersStore } from '@/stores/users'
import {
  Dropdown,
  Avatar,
  TextInput,
  toast,
  call,
  Tooltip,
  Select,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { ConfirmDelete } from '../../utils'

const { users } = usersStore()
const levels = useLevels()

const showAddExistingModal = ref(false)
const searchRef = ref(null)
const search = ref('')
const currentLevel = ref('All')
// the person whose access is being changed
const editing = ref(null)

const labels = computed(() => levelLabels(levels.data))

const levelOptions = computed(() => [
  { label: __('All'), value: 'All' },
  ...(levels.data || []).map((l) => ({ label: __(l.label), value: l.key })),
  { label: __('Agency'), value: 'agency' },
])

// A person's levels, as the button shows them. Levels a user holds only
// because of their roles from before levels are shown in italics.
function levelText(user) {
  const names = (user.levels || []).map((key) => __(labels.value[key] || key))
  return names.length ? names.join(', ') : __('No level')
}

function levelIcon(user) {
  if (user.levels?.includes('manager')) return 'lucide-briefcase'
  if (user.levels?.includes('operatore')) return 'lucide-stethoscope'
  return 'lucide-user-check'
}

const usersList = computed(() => {
  let filteredUsers =
    users.data?.crmUsers?.filter((user) => user.name !== 'Administrator') || []

  const query = search.value.toLowerCase()
  return filteredUsers
    .filter(
      (user) =>
        user.name?.toLowerCase().includes(query) ||
        user.full_name?.toLowerCase().includes(query),
    )
    .filter((user) => {
      if (currentLevel.value === 'All') return true
      if (currentLevel.value === 'agency') return user.agency
      return user.levels?.includes(currentLevel.value)
    })
})

const confirmRemove = ref(false)

function getMoreOptions(user) {
  return [
    ...ConfirmDelete({
      onConfirmDelete: () => removeUser(user),
      isConfirmingDelete: confirmRemove,
      label: __('Remove'),
    }),
  ]
}

function removeUser(user) {
  call('crm.api.user.remove_crm_roles_from_user', {
    user: user.name,
  })
    .then(() => {
      toast.success(__('User {0} has been removed', [user.full_name]))
      users.reload()
    })
    .catch((e) => {
      toast.error(e?.messages?.[0] || __('Something went wrong'))
    })
}

onMounted(() => {
  if (searchRef.value) {
    searchRef.value.el.focus()
  }
})
</script>
