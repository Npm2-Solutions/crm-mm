<template>
  <Dialog v-model:open="show" :title="__('WhatsApp Templates')" :size="'4xl'">
    <template #default>
      <div class="w-full flex items-center gap-2">
        <TextInput
          ref="searchInput"
          v-model="search"
          class="w-full"
          type="text"
          :placeholder="__('Welcome Message')"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-4"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <!-- templates are made in Settings, which only managers can open -->
        <Button
          v-if="isManager()"
          :label="__('Create New Template')"
          variant="solid"
          @click="newWhatsappTemplate"
        >
          <template #prefix>
            <span class="lucide-plus h-4 w-4" aria-hidden="true" />
          </template>
        </Button>
      </div>
      <div
        v-if="filteredTemplates.length"
        class="mt-2 grid max-h-[560px] grid-cols-1 gap-2 overflow-y-auto sm:grid-cols-3"
      >
        <div
          v-for="template in filteredTemplates"
          :key="template.name"
          class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border p-3 hover:bg-surface-gray-2"
          @click="pick(template)"
        >
          <div
            class="border-b pb-2 text-base-semibold truncate"
            :title="template.name"
          >
            {{ template.name }}
          </div>
          <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
          <!-- eslint-disable vue/no-v-html -->
          <div
            v-if="template.template"
            class="prose-f prose-sm max-w-none !text-sm text-ink-gray-5 flex-1 overflow-hidden"
            v-html="sanitizeHTML(template.template)"
          />
          <!-- eslint-enable vue/no-v-html -->
        </div>
      </div>
      <div v-else class="mt-2">
        <div class="flex h-56 flex-col items-center justify-center gap-2 px-8">
          <div class="text-lg text-ink-gray-4">
            {{ __('No Templates Found') }}
          </div>
          <!--
            An empty list where templates plainly exist needs a reason. They
            belong to a number that is no longer the one sending, and Meta will
            not send a template from an account it was not approved on — so they
            are not hidden by mistake, they are unusable.
          -->
          <p
            v-if="hiddenForOtherAccount"
            class="text-center text-p-sm text-ink-gray-5"
          >
            {{
              isManager()
                ? __(
                    '{0} approved templates belong to another number and cannot be sent from {1}. A template lives on the WhatsApp account it was approved on, so they have to be created again here.',
                    [hiddenForOtherAccount, sending.data?.account],
                  )
                : __(
                    '{0} approved templates belong to another number and cannot be sent from the one in use. A manager can create them again for this number.',
                    [hiddenForOtherAccount],
                  )
            }}
          </p>
          <Button
            v-if="isManager()"
            :label="__('Create New')"
            class="mt-2"
            @click="newWhatsappTemplate"
          />
        </div>
      </div>
    </template>
  </Dialog>

  <!-- a template with {{n}} placeholders cannot be sent blind: ask for the
       values, and show the message exactly as it will leave -->
  <Dialog
    v-model="showVariables"
    :options="{ title: __('Fill in the template'), size: 'lg' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <div
          class="rounded-md bg-surface-gray-1 p-3 text-p-base text-ink-gray-7 whitespace-pre-line"
        >
          {{ preview }}
        </div>
        <FormControl
          v-for="(value, index) in variables"
          :key="index"
          v-model="variables[index]"
          type="text"
          :label="placeholderLabel(index)"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Send')"
        :disabled="variables.some((v) => !v)"
        @click="sendWithVariables"
      />
    </template>
  </Dialog>
</template>

<script setup>
import {
  createListResource,
  createResource,
  Dialog,
  FormControl,
  toast,
} from 'frappe-ui'
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { sanitizeHTML } from '@/utils'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'

const props = defineProps({
  doctype: { type: String, default: '' },
})

const { isManager } = usersStore()

const show = defineModel({ type: Boolean })
const searchInput = ref('')

const emit = defineEmits(['send'])

const search = ref('')

// A template is approved **on one WhatsApp Business account** and belongs to it.
// Sent from another number Meta refuses it. This list used to show every
// approved template on the site — including the ones left behind by a number no
// longer in use — and offered Send on all of them, so half the choices were
// choices that could only fail.
const sending = createResource({
  url: 'crm.api.whatsapp.get_sending_account',
  auto: true,
  onSuccess: () => templates.fetch(),
})

const templates = createListResource({
  type: 'list',
  doctype: 'WhatsApp Templates',
  fields: ['name', 'template', 'footer', 'whatsapp_account'],
  filters: { status: 'APPROVED', for_doctype: ['in', [props.doctype, '']] },
  orderBy: 'modified desc',
  pageLength: 99999,
})

onMounted(() => {
  if (templates.data == null && sending.data) templates.fetch()
})

const filteredTemplates = computed(() => {
  const account = sending.data?.account
  return (
    templates.data?.filter((template) => {
      // an empty account is a template whose owner nobody recorded: it will be
      // sent from whichever number is sending, so it stays
      if (
        account &&
        template.whatsapp_account &&
        template.whatsapp_account !== account
      )
        return false
      return template.name.toLowerCase().includes(search.value.toLowerCase())
    }) ?? []
  )
})

// How many were left out because they belong elsewhere — the difference between
// "you have no templates" and "you have templates that this number cannot send".
const hiddenForOtherAccount = computed(() => {
  const account = sending.data?.account
  if (!account) return 0
  return (templates.data || []).filter(
    (t) => t.whatsapp_account && t.whatsapp_account !== account,
  ).length
})

const showVariables = ref(false)
const variables = ref([])
const preview = ref('')
const pending = ref(null)

function placeholderLabel(index) {
  return __('Value for {0}', ['{{' + (index + 1) + '}}'])
}

function pick(template) {
  createResource({
    url: 'crm.api.whatsapp.get_template_placeholders',
    params: { template: template.name },
    auto: true,
    onSuccess: (data) => {
      const count = data.body_count || 0
      if (!count) {
        emit('send', template.name)
        return
      }
      pending.value = template.name
      variables.value = Array.from({ length: count }, () => '')
      preview.value = data.template
      show.value = false
      showVariables.value = true
    },
    // if the lookup fails, fall back to sending as before rather than blocking
    onError: () => emit('send', template.name),
  })
}

function sendWithVariables() {
  showVariables.value = false
  emit('send', pending.value, [...variables.value])
  pending.value = null
}

function newWhatsappTemplate() {
  show.value = false
  // templates are created in the CRM now, not in the Desk form
  showSettings.value = true
  activeSettingsPage.value = 'WhatsApp Templates'
}

watch(show, (value) => value && nextTick(() => searchInput.value?.el?.focus()))
</script>
