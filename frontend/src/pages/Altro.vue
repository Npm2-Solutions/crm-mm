<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  "More" on a phone (docs/progetto-ghl/29): what the bar at the bottom has no
  room for, as a page of an app rather than the desk's sidebar in a drawer.
  Who one is, the notifications, the rest of the menu (utils/menu.js), the saved
  views, the first steps, the account's entries (composables/vociAccount.js) and
  the way out, in cards of rows a thumb hits: 52px each, the whole row the target.
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <h1 class="truncate text-lg font-semibold text-ink-gray-9">
        {{ __('More') }}
      </h1>
    </template>
  </LayoutHeader>
  <div class="flex flex-col gap-6 px-4 pb-10 pt-2">
    <!-- who one is: the profile, in the settings -->
    <button
      type="button"
      class="flex w-full items-center gap-3 rounded-2xl bg-surface-elevation-1 px-4 py-3.5 text-left shadow-sm ring-1 ring-outline-gray-1 active:bg-surface-gray-2"
      :aria-label="__('Profile')"
      @click="apriImpostazioni({ page: 'Profile' })"
    >
      <Avatar
        :image="utente.user_image"
        :label="utente.full_name"
        size="3xl"
        class="shrink-0"
      />
      <span class="flex min-w-0 flex-1 flex-col gap-0.5">
        <span class="truncate text-lg font-semibold text-ink-gray-9">
          {{ utente.full_name }}
        </span>
        <span class="truncate text-p-sm text-ink-gray-5">
          {{ utente.email }}
        </span>
      </span>
      <span
        class="lucide-chevron-right size-5 shrink-0 text-ink-gray-4"
        aria-hidden="true"
      />
    </button>

    <FirstStepsCard />

    <!-- on the home screen it opens like an app -->
    <InstallaApp />

    <section
      v-for="gruppo in gruppi"
      :key="gruppo.key"
      :aria-label="gruppo.titolo || undefined"
    >
      <h2
        v-if="gruppo.titolo"
        class="mb-2 px-4 text-sm font-medium uppercase tracking-wide text-ink-gray-5"
      >
        {{ gruppo.titolo }}
      </h2>
      <ul
        class="divide-y divide-outline-gray-1 overflow-hidden rounded-2xl bg-surface-elevation-1 shadow-sm ring-1 ring-outline-gray-1"
      >
        <li v-for="riga in gruppo.righe" :key="riga.key">
          <component
            :is="riga.to ? RouterLink : ElementoNativo"
            v-bind="
              riga.to ? { to: riga.to } : { tag: 'button', type: 'button' }
            "
            class="flex min-h-[3.25rem] w-full items-center gap-3 px-4 py-2 text-left active:bg-surface-gray-2"
            @click="riga.azione?.()"
          >
            <span
              class="grid size-8 shrink-0 place-items-center rounded-lg"
              :class="
                riga.rossa
                  ? 'bg-surface-red-2 text-ink-red-6'
                  : 'bg-surface-gray-2 text-ink-gray-7'
              "
              aria-hidden="true"
            >
              <img
                v-if="riga.logo"
                :src="riga.logo"
                alt=""
                class="size-5 rounded"
              />
              <Icon v-else :icon="riga.icona" class="size-[18px]" />
            </span>
            <span
              class="min-w-0 flex-1 truncate text-base"
              :class="riga.rossa ? 'text-ink-red-6' : 'text-ink-gray-9'"
            >
              {{ riga.etichetta }}
            </span>
            <!-- what is new, in the brand's subtle as the sidebar has it -->
            <span
              v-if="riga.numero"
              class="shrink-0 rounded-full bg-[var(--brand-subtle)] px-2 text-sm font-medium leading-6 text-[var(--on-brand-subtle)]"
            >
              {{ riga.numero }}
            </span>
            <span
              v-if="riga.to"
              class="lucide-chevron-right size-5 shrink-0 text-ink-gray-4"
              aria-hidden="true"
            />
          </component>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import LucideBell from '~icons/lucide/bell'
import LucideSettings from '~icons/lucide/settings'
import LucideBrushCleaning from '~icons/lucide/brush-cleaning'
import ElementoNativo from '@/components/ElementoNativo'
import FirstStepsCard from '@/components/FirstSteps/FirstStepsCard.vue'
import InstallaApp from '@/components/Mobile/InstallaApp.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { ICONE_DEL_MENU } from '@/components/Icons/menu'
import { useDemoData } from '@/composables/demoData'
import { apriImpostazioni } from '@/composables/settings'
import { callEnabled } from '@/composables/telephony'
import { useVociAccount } from '@/composables/vociAccount'
import { useVisteSalvate } from '@/composables/visteSalvate'
import { unreadNotificationsCount } from '@/stores/notifications'
import { usersStore } from '@/stores/users'
import { barraDelTelefono, menuDi } from '@/utils/menu'
import { Avatar } from 'frappe-ui'
import { computed, markRaw } from 'vue'
import { RouterLink } from 'vue-router'

const { getUser, puo, puoUno, ambito } = usersStore()
const { gruppi: account, apps } = useVociAccount()
const visteSalvate = useVisteSalvate()
const { clearDemoData, isDemoDataCreated } = useDemoData()

const utente = computed(() => getUser() || {})

// the rows of the page, in cards: `{ key, titolo, righe: [{ key, etichetta,
// icona | logo, to | azione, numero, rossa }] }`
const gruppi = computed(() => [
  {
    key: 'notifiche',
    righe: [
      {
        key: 'Notifications',
        etichetta: __('Notifications'),
        icona: markRaw(LucideBell),
        to: { name: 'Notifications' },
        numero: unreadNotificationsCount.value || 0,
      },
    ],
  },
  ...menu.value,
  ...visteSalvate.value.map((gruppo) => ({
    key: gruppo.name,
    titolo: __(gruppo.name),
    righe: gruppo.views.map((vista) => ({
      key: vista.key,
      etichetta: __(vista.label),
      icona: vista.icon,
      to: vista.to,
    })),
  })),
  ...vociDellAccount.value,
])

// the menu's entries the bar has no place for, in the menu's groups
const menu = computed(() => {
  const visibile = menuDi({ puo, puoUno, ambito, telefono: callEnabled.value })
  const nellaBarra = new Set(barraDelTelefono(visibile).map((voce) => voce.key))
  return visibile
    .map((gruppo) => ({
      key: gruppo.key,
      titolo: gruppo.label ? __(gruppo.label) : '',
      righe: gruppo.entries
        .filter((voce) => !nellaBarra.has(voce.key))
        .map((voce) => ({
          key: voce.key,
          etichetta: __(voce.label),
          icona: ICONE_DEL_MENU[voce.icon],
          to: { name: voce.key },
        })),
    }))
    .filter((gruppo) => gruppo.righe.length)
})

// The account's entries as the centre ordered them, each application a row of
// its own; the settings always there, the way out last and in red.
const vociDellAccount = computed(() => {
  const gruppiDiRighe = account.value.map((gruppo, i) => ({
    key: `account-${i}`,
    righe: gruppo.flatMap((voce, j) =>
      voce.tipo === 'app'
        ? (apps.data || []).map((app) => ({
            key: `app-${app.name}`,
            etichetta: app.title,
            icona: app.icon,
            logo: app.icon ? '' : app.logo,
            azione: () => (window.location.href = app.route),
          }))
        : [
            {
              key: `${voce.tipo}-${j}`,
              etichetta: voce.etichetta,
              icona: voce.icona,
              azione: voce.azione,
              rossa: voce.tipo === 'esci',
            },
          ],
    ),
  }))
  if (
    !account.value.some((gruppo) =>
      gruppo.some((v) => v.tipo === 'impostazioni'),
    )
  )
    gruppiDiRighe.unshift({
      key: 'impostazioni',
      righe: [
        {
          key: 'impostazioni',
          etichetta: __('Settings'),
          icona: markRaw(LucideSettings),
          azione: () => apriImpostazioni(),
        },
      ],
    })
  if (puo('dati_prova.gestisci') && isDemoDataCreated.value)
    gruppiDiRighe.push({
      key: 'dati-prova',
      righe: [
        {
          key: 'dati-prova',
          etichetta: __('Clear Demo Data'),
          icona: markRaw(LucideBrushCleaning),
          azione: () => clearDemoData(),
          rossa: true,
        },
      ],
    })
  return gruppiDiRighe.filter((gruppo) => gruppo.righe.length)
})
</script>
