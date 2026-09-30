<template>
  <Dialog
    v-model:open="show"
    :title="__('Add Existing User')"
    @close="show = false"
  >
    <template #default>
      <div class="flex gap-1 border rounded mb-4 p-2 text-ink-gray-5">
        <span class="lucide-info size-3.5 mt-0.5" aria-hidden="true" />
        <p class="text-p-sm">
          {{
            __(
              'Add existing system users to {brand}, with the levels they will have. They sign in with their current credentials.',
            )
          }}
        </p>
      </div>

      <label class="block text-xs text-ink-gray-5 mb-1.5">
        {{ __('Users') }}
      </label>

      <div class="p-2 group bg-surface-gray-2 hover:bg-surface-gray-3 rounded">
        <EmailMultiSelect
          v-if="users?.data?.crmUsers?.length"
          v-model="newUsers"
          class="flex-1"
          inputClass="!bg-surface-gray-2 hover:!bg-surface-gray-3 group-hover:!bg-surface-gray-3"
          :placeholder="__('john@doe.com')"
          :validate="validateEmail"
          :fetchUsers="true"
          :existingEmails="[
            ...users.data.crmUsers.map((user) => user.name),
            'admin@example.com',
          ]"
          :error-message="
            (value) => __('{0} is an invalid email address', [value])
          "
          :emptyPlaceholder="__('No Users Found')"
        />
      </div>
      <div class="mt-4 flex flex-col gap-2">
        <div class="text-xs text-ink-gray-5">{{ __('Levels') }}</div>
        <LevelPicker v-model="chosenLevels" :levels="levels.data || []" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="__('Add')"
          :disabled="!newUsers.length || !chosenLevels.length"
          :loading="addNewUser.loading"
          @click="addNewUser.submit()"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EmailMultiSelect from '@/components/Controls/EmailMultiSelect.vue'
import LevelPicker from '@/components/Settings/LevelPicker.vue'
import { useLevels } from '@/composables/levels'
import { validateEmail } from '@/utils'
import { usersStore } from '@/stores/users'
import { createResource, toast } from 'frappe-ui'
import { ref, watch } from 'vue'

const { users } = usersStore()
const levels = useLevels()

const show = defineModel({ type: Boolean })

const newUsers = ref([])
const chosenLevels = ref([])

watch(
  () => levels.data,
  (data) => {
    if (!chosenLevels.value.length && data?.some((l) => l.key === 'segreteria'))
      chosenLevels.value = ['segreteria']
  },
  { immediate: true },
)

const addNewUser = createResource({
  url: 'crm.api.user.add_existing_users',
  makeParams: () => ({
    users: JSON.stringify(newUsers.value),
    levels: JSON.stringify(chosenLevels.value),
  }),
  onSuccess: () => {
    toast.success(__('Users Added Successfully'))
    newUsers.value = []
    show.value = false
    users.reload()
  },
  onError: (error) => {
    toast.error(error.messages[0] || __('Failed to Add Users'))
  },
})
</script>
