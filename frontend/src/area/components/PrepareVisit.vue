<!--
  Preparing the visit: the forms the centre asks before the next appointment,
  filled here on the forms page - already open, since the person came in with a
  code - and back to the area when they are done.
-->
<template>
  <section v-if="forms.data?.forms?.length" class="flex flex-col gap-2">
    <h2 class="text-base font-medium text-ink-gray-7">
      {{ __('Prepare your visit') }}
    </h2>
    <div
      class="flex flex-col gap-2 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
    >
      <p v-if="forms.data.appointment" class="text-p-sm text-ink-gray-6">
        {{
          __('Before your appointment of {0}', [
            day(forms.data.appointment.starts_on),
          ])
        }}
      </p>
      <div
        v-for="form in forms.data.forms"
        :key="form.template"
        class="flex items-center justify-between gap-3 border-b border-outline-gray-1 py-2 last:border-0"
      >
        <div class="flex min-w-0 flex-col">
          <span class="text-base text-ink-gray-9">{{ form.title }}</span>
          <span class="text-p-sm text-ink-gray-5">
            {{ state(form) }}
          </span>
        </div>
        <Button
          v-if="form.fill"
          class="shrink-0"
          variant="solid"
          :label="form.pending ? __('Continue') : __('Fill')"
          :loading="opening === form.template"
          @click="fill([form.template])"
        />
      </div>
      <p v-if="!forms.data.can_fill" class="text-p-sm text-ink-gray-6">
        {{ whyNot[forms.data.why_not] }}
      </p>
      <ErrorMessage :message="error" />
    </div>
  </section>
</template>

<script setup>
import { Button, ErrorMessage, call, createResource } from 'frappe-ui'
import { ref } from 'vue'
import { day } from '../dates'
import { area, messageOf } from '../store'

const forms = createResource({
  url: 'crm.clinica.area.api.get_forms',
  params: { person: area.person },
  auto: true,
})

// who is in and does not sign: a child sees, the parent signs
const whyNot = {
  parent: __(
    'Your forms are answered by a parent or guardian, from their area',
  ),
  not_linked: __(
    'To sign for them, ask the centre to add you to their related people',
  ),
  follows: __('The person signs their own forms'),
}

function state(form) {
  if (form.pending === 'to_sign_at_desk') return __('To sign at the centre')
  return form.pending ? __('Started') : __('To fill')
}

const opening = ref(null)
const error = ref('')

async function fill(templates) {
  opening.value = templates[0]
  error.value = ''
  try {
    const open = await call('crm.clinica.area.api.fill_forms', {
      person: area.person,
      templates: JSON.stringify(templates),
    })
    // the forms page finds its session here, and asks for no code
    try {
      sessionStorage.setItem('modulo:' + open.token, open.session)
    } catch {
      /* without storage the page asks for a code, as from an email */
    }
    window.location.href = `${open.url}?from=area`
  } catch (e) {
    error.value = __(messageOf(e))
    opening.value = null
  }
}
</script>
