<template>
  <Dialog v-model:open="show" :size="'xl'">
    <template #body>
      <div class="bg-surface-elevation-2 px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-3xl-semibold leading-6 text-ink-gray-9">
              {{ __('New Contact') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit Fields Layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              icon="lucide-x"
              @click="show = false"
            />
          </div>
        </div>
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="_contact.doc"
          doctype="Contact"
        />
        <ErrorMessage v-if="error" class="mt-6" :message="__(error)" />
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="insertContact.loading"
            @click="createContact"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useDocument } from '@/data/document'
import { evaluateDependsOnValue } from '@/utils'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource } from 'frappe-ui'
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  contact: { type: Object, default: () => {} },
  options: {
    type: Object,
    default: () => ({ redirect: true, afterInsert: () => {} }),
  },
})

const { isManager } = usersStore()
const { capture } = useTelemetry()

const router = useRouter()
const show = defineModel({ type: Boolean })

const error = ref(null)

const { document: _contact, triggerOnBeforeCreate } = useDocument('Contact')

function validateRequiredFields() {
  if (!tabs.data) return null

  const missingFields = []

  tabs.data.forEach((tab) => {
    tab.sections.forEach((section) => {
      section.columns.forEach((column) => {
        column.fields.forEach((field) => {
          const isMandatory =
            field.reqd ||
            (field.mandatory_depends_on &&
              evaluateDependsOnValue(field.mandatory_depends_on, _contact.doc))

          if (isMandatory && !_contact.doc[field.fieldname]) {
            missingFields.push(__(field.label))
          }
        })
      })
    })
  })

  if (missingFields.length) {
    return __('{0} is required', [missingFields.join(', ')])
  }

  if (_contact.doc.email_id && !_contact.doc.email_id.includes('@')) {
    return __('Invalid Email Address')
  }

  if (
    _contact.doc.mobile_no &&
    isNaN(_contact.doc.mobile_no.replace(/[-+() ]/g, ''))
  ) {
    return __('Mobile number should be a number')
  }

  return null
}

// Adding someone to the address book means adding a person: the endpoint
// creates the lead, the lead brings its contact, and neither is left orphaned.
const insertContact = createResource({
  url: 'crm.api.contact.create_person',
  onSuccess: (person) => {
    capture('contact_created')
    handleContactUpdate(person)
    _contact.doc = {}
  },
  onError: (err) => {
    error.value = err.error?.messages?.[0]
  },
})

async function createContact() {
  error.value = null

  const validationError = validateRequiredFields()
  if (validationError) {
    error.value = validationError
    return
  }

  await triggerOnBeforeCreate?.()

  // email and number stay flat: the backend puts them where they belong
  insertContact.submit({ person: { ..._contact.doc } })
}

function handleContactUpdate(person) {
  props.contact?.reload?.()
  // open the person, not their address book entry: that page has the
  // conversation and the activity on it
  if (person.lead && props.options.redirect) {
    router.push({ name: 'Lead', params: { leadId: person.lead } })
  } else if (person.contact && props.options.redirect) {
    router.push({ name: 'Contact', params: { contactId: person.contact } })
  }
  show.value = false
  // callers that add someone to a deal want the contact's name, as before —
  // the lead comes along for whoever cares which person it is
  props.options.afterInsert?.({ name: person.contact, ...person })
}

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Contact'],
  params: { doctype: 'Contact', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'email_id') {
              field.read_only = false
            } else if (field.fieldname == 'mobile_no') {
              field.read_only = false
            } else if (field.fieldname == 'address') {
              field.create = (value, close) => {
                _contact.doc.address = value
                showAddressModal()
                close()
              }
              field.edit = (address) => showAddressModal(address)
            } else if (field.fieldtype === 'Table') {
              _contact.doc[field.fieldname] = []
            }
            if (field.fieldname === 'first_name') {
              field.reqd = 1
            }
          })
        })
      })
    })
  },
})

onMounted(() => {
  _contact.doc = {}
  Object.assign(_contact.doc, props.contact.data || props.contact)
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'Contact' }
  nextTick(() => (show.value = false))
}

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        _contact.doc.address = d.name
      },
    },
  })
}
</script>

<style scoped>
:deep(:has(> .dropdown-button)) {
  width: 100%;
}
</style>
