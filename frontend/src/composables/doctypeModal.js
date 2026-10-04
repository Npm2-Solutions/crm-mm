// Modifications copyright (c) 2026, NPM2 Solutions Srl
import { computed, ref } from 'vue'

const show = ref(false)
const doctype = ref('')
const name = ref('')
const title = ref('')
const defaults = ref({})
const callbacks = ref({})

function showModal({
  name: _name = null,
  doctype: _doctype,
  title: _title = '',
  defaults: _defaults = {},
  callbacks: _callbacks = {},
}) {
  name.value = _name
  doctype.value = _doctype
  title.value = _title
  defaults.value = _defaults
  callbacks.value = _callbacks
  show.value = true
}

function triggerCallback(event, ...args) {
  callbacks.value[event]?.(...args)
}

// the sheet offers to take the record away when whoever opened it handles
// that too (`callbacks.afterDelete`): on a phone the list has no menu of its own
const eliminabile = computed(() => Boolean(callbacks.value.afterDelete))

export function useDoctypeModal() {
  return {
    show,
    doctype,
    name,
    title,
    defaults,
    showModal,
    triggerCallback,
    eliminabile,
  }
}
