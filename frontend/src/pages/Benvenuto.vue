<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The centre's first opening (crm/benvenuto.py), for whoever sets it up: the
  language the centre works in, Italian or English, each said in its own words;
  then the centre's name and clock, and the demo data if they want to look
  around first. A language other than the page's is saved and the page comes
  back in it, on the second screen (`?passo=centro`). The sign-in's look: the
  product's icon, a title, a short line, the fields in one column; on a phone the
  screen's width, the action at the thumb.
-->
<template>
  <div
    class="flex min-h-dvh flex-col items-center bg-surface-base px-4 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-[max(3.5rem,env(safe-area-inset-top))] max-md:pt-[max(2.5rem,env(safe-area-inset-top))]"
  >
    <main class="flex w-full max-w-sm flex-1 flex-col gap-6">
      <div class="flex flex-col gap-4">
        <CRMLogo class="size-10 rounded-[10px]" />
        <!-- where one is: two marks, the first full -->
        <div
          class="flex gap-1.5"
          role="img"
          :aria-label="__('Step {0} of {1}', [passo === 'lingua' ? 1 : 2, 2])"
        >
          <span class="h-1 w-8 rounded-full bg-[var(--brand-segno)]" />
          <span
            class="h-1 w-8 rounded-full"
            :class="
              passo === 'centro'
                ? 'bg-[var(--brand-segno)]'
                : 'bg-surface-gray-3'
            "
          />
        </div>
      </div>

      <div
        v-if="!dati.data && !dati.error"
        class="flex flex-1 items-start justify-center py-10 text-ink-gray-5"
      >
        <LoadingIndicator class="size-5" />
      </div>
      <ErrorMessage
        v-else-if="dati.error"
        :message="__('The page could not be loaded: try again in a moment.')"
      />

      <!-- 1. the centre's language -->
      <section v-else-if="passo === 'lingua'" class="flex flex-col gap-5">
        <header class="flex flex-col gap-1.5">
          <h1 class="text-2xl-semibold text-ink-gray-9">
            {{ __('Welcome to {brand}') }}
          </h1>
          <p class="text-p-base text-ink-gray-7">
            {{
              __(
                'Which language does the centre work in? Its emails, documents and screens will speak it; each person can choose their own later.',
              )
            }}
          </p>
        </header>
        <div class="flex flex-col gap-2.5" role="list">
          <!-- each language said in its own words: whoever reads the other
               one finds theirs -->
          <button
            v-for="lingua in LINGUE"
            :key="lingua.value"
            type="button"
            role="listitem"
            class="flex min-h-16 w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition-colors hover:bg-surface-gray-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--focus)] disabled:opacity-60"
            :class="
              dati.data.language === lingua.value
                ? 'border-outline-gray-4'
                : 'border-outline-gray-2'
            "
            :lang="lingua.value"
            :disabled="scegli.loading"
            @click="sceltaLaLingua(lingua.value)"
          >
            <span class="flex min-w-0 flex-1 flex-col gap-0.5">
              <span class="text-lg-semibold text-ink-gray-9">
                {{ lingua.label }}
              </span>
              <span class="text-p-sm text-ink-gray-6">{{ lingua.riga }}</span>
            </span>
            <LoadingIndicator
              v-if="scegli.loading && scegli.params?.language === lingua.value"
              class="size-4 shrink-0 text-ink-gray-5"
            />
            <span
              v-else-if="dati.data.language === lingua.value"
              class="dc-scelto lucide-check size-4 shrink-0 text-ink-gray-7"
              aria-hidden="true"
            />
            <span
              v-else
              class="lucide-chevron-right size-4 shrink-0 text-ink-gray-5"
              aria-hidden="true"
            />
          </button>
        </div>
      </section>

      <!-- 2. the centre's name and clock -->
      <form
        v-else
        class="flex flex-col gap-5"
        novalidate
        @submit.prevent="finisci"
      >
        <header class="flex flex-col gap-1.5">
          <h1 class="text-2xl-semibold text-ink-gray-9">
            {{ __('Your centre') }}
          </h1>
          <p class="text-p-base text-ink-gray-7">
            {{
              __(
                'Its name heads the booking page, the forms and the emails your clients receive.',
              )
            }}
          </p>
        </header>
        <div class="flex flex-col gap-1.5">
          <label for="benvenuto-nome" class="text-sm text-ink-gray-5">
            {{ __('The centre’s name') }}
            <span class="segno-obbligatorio text-ink-red-6" aria-hidden="true"
              >*</span
            >
          </label>
          <TextInput
            id="benvenuto-nome"
            ref="campoNome"
            v-model="nome"
            size="md"
            required
            autocomplete="organization"
            :placeholder="__('e.g. Studio Medico Aurora')"
            v-bind="tastiera('nome')"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormControl
            v-model="fuso"
            type="select"
            :label="__('The centre’s time zone')"
            :options="fusi"
          />
          <p class="text-p-sm text-ink-gray-6">
            {{
              __('The hours of the agenda, the reminders and the booking page.')
            }}
          </p>
        </div>
        <label
          v-if="dati.data.demo"
          class="flex cursor-pointer items-start gap-3 rounded-xl border border-outline-gray-2 px-4 py-3"
        >
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="text-base-medium text-ink-gray-8">
              {{ __('Look around with demo data first') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'People, appointments and invoices to try {brand} on, taken away in one tap from Settings › The centre › Demo data.',
                )
              }}
            </span>
          </span>
          <Switch
            v-model="demo"
            class="mt-0.5 shrink-0"
            :aria-label="__('Look around with demo data first')"
          />
        </label>
        <ErrorMessage v-if="errore" :message="errore" />
        <div class="flex flex-col gap-3">
          <Button
            type="submit"
            variant="solid"
            size="lg"
            class="w-full"
            :label="__('Start using {brand}')"
            :loading="fine.loading"
          />
          <Button
            variant="ghost"
            class="self-start"
            icon-left="chevron-left"
            :label="__('Language')"
            :disabled="fine.loading"
            @click="passo = 'lingua'"
          />
        </div>
      </form>
    </main>
    <footer class="mt-8 flex w-full max-w-sm justify-center">
      <!-- the centre is set up later from Settings; the welcome comes back with
           the next tab -->
      <button
        type="button"
        class="touch-target text-p-sm text-ink-gray-6 underline-offset-2 hover:underline"
        @click="dopo"
      >
        {{ __('Do it later') }}
      </button>
    </footer>
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { BENVENUTO_DOPO } from '@/router'
import { fusiOrari } from '@/utils/fusiOrari'
import { appLocale } from '@/utils/locale'
import { tastiera } from '@/utils/tastiera'
import {
  Button,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  TextInput,
  createResource,
  usePageMeta,
} from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// the two languages, each in its own words (crm/lingue.py: LINGUE, NOMI)
const LINGUE = [
  { value: 'it', label: 'Italiano', riga: 'Il centro lavora in italiano' },
  { value: 'en', label: 'English', riga: 'The centre works in English' },
]

const passo = ref(route.query.passo === 'centro' ? 'centro' : 'lingua')
const nome = ref('')
const fuso = ref('')
const demo = ref(false)
const errore = ref('')
const campoNome = ref(null)

const dati = createResource({
  url: 'crm.benvenuto.get_welcome',
  auto: true,
  onSuccess: (risposta) => {
    nome.value = risposta.centre_name || ''
    fuso.value = risposta.time_zone || ''
  },
})

const fusi = computed(() =>
  fusiOrari({
    zone: dati.data?.time_zones || [],
    scelto: fuso.value,
    dispositivo: Intl.DateTimeFormat().resolvedOptions().timeZone,
    lingua: appLocale() || 'it',
  }),
)

const scegli = createResource({
  url: 'crm.benvenuto.choose_language',
  onSuccess: () => {
    // every word of the page comes in the new language from the server's start
    const indirizzo = router.resolve({
      name: 'Onboarding',
      query: { passo: 'centro' },
    })
    window.location.replace(indirizzo.href)
  },
})

function sceltaLaLingua(lingua) {
  if (lingua === dati.data?.language) {
    passo.value = 'centro'
    return
  }
  scegli.submit({ language: lingua })
}

const fine = createResource({
  url: 'crm.benvenuto.finish',
  onSuccess: () => {
    // the boot says the centre's name, and that there is no welcome any more
    window.location.replace(router.resolve({ name: 'Home' }).href)
  },
  onError: (e) => {
    errore.value =
      e.messages?.join(' ') || __('The centre could not be saved: try again.')
  },
})

function finisci() {
  errore.value = ''
  if (!nome.value.trim()) {
    errore.value = __("Write the centre's name")
    campoNome.value?.el?.focus?.()
    return
  }
  fine.submit({
    centre_name: nome.value.trim(),
    time_zone: fuso.value,
    demo: demo.value ? 1 : 0,
  })
}

function dopo() {
  try {
    window.sessionStorage.setItem(BENVENUTO_DOPO, '1')
  } catch {
    // a private window: the welcome comes back at the next page, harmless
  }
  router.replace({ name: 'Home' })
}

// the name is what is asked on the second screen: the keyboard comes up on it
watch(
  () => [passo.value, Boolean(dati.data)],
  async ([ora, pronti]) => {
    if (ora !== 'centro' || !pronti) return
    await nextTick()
    campoNome.value?.el?.focus?.()
  },
  { immediate: true },
)

usePageMeta(() => ({ title: __('Welcome to {brand}') }))
</script>
