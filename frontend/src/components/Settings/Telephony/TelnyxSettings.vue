<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > Phone > Telephony > Telnyx (doc 64).

  The centre connects its own Telnyx account with two codes of the portal, once:
  an API key and the account's public key. Telnyx has no space inside an account,
  as Twilio has: DottorCloud keeps the key and works only on what it makes there -
  an application, a connection, two profiles, named after the site - and on the
  numbers the centre gives it. Calls and messages are paid to Telnyx by the
  centre, from the account's balance; the rest is done here. The agency may
  connect its own account instead. One carrier at a time: with Twilio connected,
  this page waits for it to go.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Telnyx')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="stato"
          :label="
            stato.connected
              ? __('Connected', null, 'Twilio')
              : __('Not connected', null, 'Twilio')
          "
          variant="subtle"
          :theme="stato.connected ? 'green' : 'gray'"
        />
        <Badge
          v-if="stato?.connected && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="stato?.connected && isDirty" class="flex gap-2">
        <Button
          :label="__('Discard Changes')"
          variant="subtle"
          @click="telnyx.reload()"
        />
        <AzioneImpostazioni :loading="telnyx.save.loading" @click="update" />
      </div>
    </template>
    <template #content>
      <div
        v-if="connessione.loading && !stato"
        class="mt-[35%] flex items-center justify-center"
      >
        <LoadingIndicator class="size-6" />
      </div>

      <!-- the other carrier is on: one at a time -->
      <div
        v-else-if="stato && !stato.connected && stato.other"
        class="flex flex-col gap-3"
      >
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'The phone goes through {0} now: disconnect it to use {1} instead.',
              [stato.other, 'Telnyx'],
            )
          }}
        </p>
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'The centre’s calls, numbers and SMS go through one carrier at a time, so that a call and its answer never go two ways.',
            )
          }}
        </p>
      </div>

      <!-- not connected: three steps, two codes -->
      <div v-else-if="stato && !stato.connected" class="flex flex-col gap-5">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "Calls and messages go through your own Telnyx account: you pay Telnyx, at Telnyx's prices, from the account's balance. Everything else you do here in {brand}.",
            )
          }}
        </p>

        <ol class="flex flex-col gap-3">
          <li class="flex items-start gap-3">
            <span
              class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-p-sm font-medium text-ink-gray-7"
              >1</span
            >
            <div class="flex min-w-0 flex-1 flex-col gap-1.5">
              <span class="text-p-base text-ink-gray-8">
                {{
                  __(
                    'Create your account on Telnyx, if you have none, verify it and top up its balance: Italian numbers are sold only to a verified account.',
                  )
                }}
              </span>
              <a
                :href="TELNYX.registrazione"
                target="_blank"
                rel="noopener"
                class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
              >
                {{ __('Open Telnyx') }}
                <span class="lucide-external-link size-3.5" />
              </a>
            </div>
          </li>
          <li class="flex items-start gap-3">
            <span
              class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-p-sm font-medium text-ink-gray-7"
              >2</span
            >
            <div class="flex min-w-0 flex-1 flex-col gap-1.5">
              <span class="text-p-base text-ink-gray-8">
                {{
                  __(
                    'In the Telnyx portal, create an API key and copy it; then copy the account’s public key, which tells {brand} that a message comes from Telnyx.',
                  )
                }}
              </span>
              <div class="flex flex-wrap gap-x-4 gap-y-1">
                <a
                  :href="TELNYX.chiavi"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
                >
                  {{ __('API keys') }}
                  <span class="lucide-external-link size-3.5" />
                </a>
                <a
                  :href="TELNYX.pubblica"
                  target="_blank"
                  rel="noopener"
                  class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
                >
                  {{ __('Public key') }}
                  <span class="lucide-external-link size-3.5" />
                </a>
              </div>
            </div>
          </li>
          <li class="flex items-start gap-3">
            <span
              class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-gray-2 text-p-sm font-medium text-ink-gray-7"
              >3</span
            >
            <div class="flex min-w-0 flex-1 flex-col gap-3">
              <span class="text-p-base text-ink-gray-8">
                {{ __('Paste them here and connect.') }}
              </span>
              <div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
                <Password
                  v-model="codici.api_key"
                  :label="__('API key', null, 'Telnyx portal')"
                  placeholder="KEY…"
                />
                <FormControl
                  autocapitalize="none"
                  spellcheck="false"
                  v-model="codici.public_key"
                  :label="__('Public key', null, 'Telnyx portal')"
                  type="text"
                  placeholder="…="
                  autocomplete="off"
                />
              </div>
              <ErrorMessage :message="errore" />
              <div class="flex flex-wrap items-center gap-2">
                <Button
                  variant="solid"
                  :label="__('Connect')"
                  :loading="collega.loading"
                  @click="connetti"
                />
              </div>
            </div>
          </li>
        </ol>

        <div
          class="rounded-lg border border-outline-gray-2 px-4 py-3 text-p-sm text-ink-gray-6"
        >
          {{
            __(
              '{brand} keeps the key on its server, never shows it again, and works only on what it makes in your account - an application, a connection and two profiles named after this site - and on the numbers you give it. Disconnecting forgets the key.',
            )
          }}
        </div>

        <div
          v-if="stato.agency_account"
          class="flex items-center justify-between gap-4 border-t border-outline-elevation-2 pt-4 max-md:flex-col max-md:items-start"
        >
          <div class="flex min-w-0 flex-col gap-1">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __("The agency's account") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  "For a centre with the agency's front desk: the numbers live in the agency's Telnyx account, and the agency pays.",
                )
              }}
            </span>
          </div>
          <Button
            class="shrink-0"
            :label="__('Use the agency\'s account')"
            :loading="collegaAgenzia.loading"
            @click="connettiAgenzia"
          />
        </div>
      </div>

      <!-- connected: whose account, what DottorCloud made in it, what Check found -->
      <div v-else-if="stato" class="flex flex-col gap-4">
        <div
          class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="riga in righe"
            :key="riga.label"
            class="flex items-start justify-between gap-4 px-4 py-2.5 max-md:flex-col max-md:gap-0.5"
          >
            <span class="shrink-0 text-p-sm text-ink-gray-6">
              {{ riga.label }}
            </span>
            <span
              class="min-w-0 break-words text-right text-p-sm text-ink-gray-8 max-md:text-left"
            >
              {{ riga.value }}
            </span>
          </div>
        </div>

        <div v-if="controllo" class="flex flex-col gap-1">
          <p v-if="!controllo.ok" class="text-p-sm text-ink-red-8">
            {{ controllo.error }}
          </p>
          <template v-else>
            <p
              v-if="controllo.balance !== undefined"
              class="text-p-sm text-ink-gray-8"
            >
              {{
                __('Telnyx balance: {0}', [
                  soldi(controllo.balance, controllo.currency),
                ])
              }}
            </p>
            <p v-if="controllo.note" class="text-p-sm text-ink-amber-8">
              {{ controllo.note }}
            </p>
            <p
              v-for="riga in righeDelControllo(controllo)"
              :key="riga[0]"
              class="text-p-sm text-ink-gray-6"
            >
              {{ __(riga[0], [riga[1]]) }}
            </p>
          </template>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            :label="__('Check')"
            icon-left="lucide-refresh-cw"
            :loading="controlla.loading"
            @click="controlla.submit()"
          />
          <Button
            :label="__('Open Telnyx')"
            icon-left="lucide-external-link"
            @click="apri(TELNYX.portale)"
          />
          <Button
            v-if="stato.may_change"
            :label="__('Disconnect')"
            theme="red"
            variant="subtle"
            :loading="scollega.loading"
            @click="chiediDiScollegare"
          />
        </div>

        <!--
          What the account spends, its balance and what went wrong (doc 64), for
          whoever pays for it: this month by kind, the two alerts, the last
          days' problems in words.
        -->
        <template v-if="consumi.data?.visible">
          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex flex-col gap-3">
            <div class="flex items-start justify-between gap-3">
              <div class="flex min-w-0 flex-col">
                <div class="text-p-base-medium text-ink-gray-7">
                  {{ __('This month') }}
                </div>
                <div class="text-p-sm text-ink-gray-5">
                  {{
                    __(
                      'What the account spent since {0}, as Telnyx counts it.',
                      [formatDate(consumi.data.since, 'D MMMM')],
                    )
                  }}
                </div>
              </div>
              <div
                v-if="consumi.data.month"
                class="shrink-0 text-lg font-semibold tabular-nums text-ink-gray-9"
              >
                {{ soldi(consumi.data.month.total) }}
              </div>
            </div>
            <p v-if="consumi.data.error" class="text-p-sm text-ink-red-8">
              {{ consumi.data.error }}
            </p>
            <template v-else>
              <div
                class="flex flex-col divide-y divide-outline-gray-1 rounded border border-outline-gray-1"
              >
                <div
                  v-for="voce in consumi.data.month.items"
                  :key="voce.key"
                  class="flex items-center justify-between gap-3 px-3 py-2"
                >
                  <div class="flex min-w-0 flex-col">
                    <span class="text-p-sm text-ink-gray-8">{{
                      voce.label
                    }}</span>
                    <span
                      v-if="quantiNellaVoce(voce)"
                      class="text-p-xs text-ink-gray-5"
                    >
                      {{ __(...quantiNellaVoce(voce)) }}
                    </span>
                  </div>
                  <span class="shrink-0 text-p-sm tabular-nums text-ink-gray-8">
                    {{ soldi(voce.price) }}
                  </span>
                </div>
              </div>

              <!-- the balance: Telnyx is paid in advance -->
              <div
                v-if="consumi.data.balance"
                class="flex items-start justify-between gap-3 rounded bg-surface-gray-1 px-3 py-2"
              >
                <div class="flex min-w-0 flex-col">
                  <span class="text-p-sm text-ink-gray-8">
                    {{ __('Balance') }}
                  </span>
                  <span
                    class="text-p-xs"
                    :class="
                      consumi.data.balance.note
                        ? 'text-ink-amber-8'
                        : 'text-ink-gray-5'
                    "
                  >
                    {{
                      consumi.data.balance.note ||
                      __(
                        'Telnyx is paid in advance: calls and SMS stop when the balance runs out.',
                      )
                    }}
                  </span>
                </div>
                <div class="flex shrink-0 flex-col items-end gap-0.5">
                  <span class="text-p-sm tabular-nums text-ink-gray-8">
                    {{ soldi(consumi.data.balance.balance) }}
                  </span>
                  <a
                    :href="TELNYX.bilancio"
                    target="_blank"
                    rel="noopener"
                    class="inline-flex items-center gap-1 text-p-xs text-ink-gray-6 underline"
                  >
                    {{ __('Top up') }}
                    <span class="lucide-external-link size-3" />
                  </a>
                </div>
              </div>
            </template>

            <div v-if="telnyx.doc" class="flex flex-col gap-3">
              <div class="flex flex-col gap-1.5">
                <div class="flex flex-wrap items-center gap-2">
                  <label
                    for="avviso-spesa-telnyx"
                    class="text-p-sm text-ink-gray-7"
                  >
                    {{ __('Tell me when the month reaches') }}
                  </label>
                  <div class="flex shrink-0 items-center gap-1.5">
                    <FormControl
                      id="avviso-spesa-telnyx"
                      v-model="avvisoDiSpesa"
                      class="w-36"
                      type="number"
                      min="0"
                      step="1"
                      :placeholder="__('No alert')"
                    />
                    <span class="text-p-sm text-ink-gray-5">{{ simbolo }}</span>
                  </div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <label
                    for="avviso-bilancio-telnyx"
                    class="text-p-sm text-ink-gray-7"
                  >
                    {{ __('Tell me when the balance goes down to') }}
                  </label>
                  <div class="flex shrink-0 items-center gap-1.5">
                    <FormControl
                      id="avviso-bilancio-telnyx"
                      v-model="avvisoDiBilancio"
                      class="w-36"
                      type="number"
                      min="0"
                      step="1"
                      :placeholder="__('No alert')"
                    />
                    <span class="text-p-sm text-ink-gray-5">{{ simbolo }}</span>
                  </div>
                </div>
              </div>
              <p class="text-p-xs text-ink-gray-5">
                {{
                  __(
                    '{brand} looks every hour: the spend once a month, the balance once until it is topped up. Whoever pays for the account reads it among the notifications. Empty: no alert.',
                  )
                }}
              </p>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0 text-p-base-medium text-ink-gray-7">
                {{ __('Problems in the last {0} days', [consumi.data.days]) }}
              </div>
              <Button
                class="shrink-0"
                variant="ghost"
                size="sm"
                icon-left="lucide-external-link"
                :label="__('Telnyx’s log')"
                @click="apri(TELNYX.registro)"
              />
            </div>
            <p
              v-if="!consumi.data.error && !consumi.data.problems?.length"
              class="text-p-sm text-ink-gray-5"
            >
              {{ __('None: the SMS went through.') }}
            </p>
            <div
              v-for="problema in consumi.data.problems"
              :key="problema.code || problema.telnyx"
              class="flex flex-col gap-0.5 rounded bg-surface-gray-1 px-3 py-2"
            >
              <span class="text-p-sm text-ink-gray-8">{{
                problema.sentence
              }}</span>
              <span class="text-p-xs text-ink-gray-5">
                {{ __(...quanteVolte(problema.count)) }} ·
                {{
                  __('last on {0}', [
                    formatDate(problema.last, 'ddd D MMM, HH:mm'),
                  ])
                }}<template v-if="problema.code">
                  · {{ __('error {0}', [problema.code]) }}</template
                >
              </span>
            </div>
          </div>
        </template>

        <div class="h-px border-t border-outline-elevation-2" />

        <div class="flex flex-col gap-3">
          <div
            class="flex items-center justify-between gap-4 max-md:flex-col max-md:items-start"
          >
            <div class="flex min-w-0 flex-col">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('Numbers') }}
              </div>
              <div
                class="text-p-sm"
                :class="
                  stato.not_reaching ? 'text-ink-red-8' : 'text-ink-gray-5'
                "
              >
                {{ numeriInParole }}
              </div>
            </div>
            <div class="flex shrink-0 flex-wrap gap-2">
              <Button
                :label="__('New number')"
                icon-left="lucide-plus"
                :disabled="!offerta.data"
                :loading="offerta.loading"
                @click="apriNuovo()"
              />
              <Button
                :label="__('I already have a number')"
                @click="trasloco = true"
              />
              <Button
                :label="__('Manage')"
                @click="emit('updateStep', 'caller-id-settings')"
              />
            </div>
          </div>

          <!-- the numbers asked of Telnyx: where each request is -->
          <div
            v-if="richieste.length"
            class="flex flex-col divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div
              v-for="riga in richieste"
              :key="riga.name"
              class="flex items-start justify-between gap-3 px-4 py-3 max-md:flex-col"
            >
              <div class="flex min-w-0 flex-col gap-1">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-p-base-medium text-ink-gray-8">
                    {{ nomeDellaRichiesta(riga) }}
                  </span>
                  <Badge
                    :label="
                      __(
                        statoDellaRichiesta(riga, 'Telnyx').label,
                        null,
                        'Number request',
                      )
                    "
                    :theme="statoDellaRichiesta(riga, 'Telnyx').theme"
                    variant="subtle"
                  />
                </div>
                <span class="text-p-sm text-ink-gray-6">
                  {{ __(...statoDellaRichiesta(riga, 'Telnyx').riga) }}
                </span>
                <span
                  v-if="riga.ordered?.length"
                  class="text-p-sm text-ink-gray-7"
                >
                  {{
                    __('Ordered: {0}', [
                      riga.ordered.map((n) => n.label).join(', '),
                    ])
                  }}
                </span>
                <span
                  v-if="riga.numbers.length"
                  class="text-p-sm text-ink-gray-7"
                >
                  {{
                    __('Bought: {0}', [
                      riga.numbers.map((n) => n.label).join(', '),
                    ])
                  }}
                </span>
                <span
                  v-for="motivo in riga.failures"
                  :key="motivo"
                  class="text-p-sm text-ink-red-8"
                  >{{ motivo }}</span
                >
              </div>
              <div class="flex shrink-0 flex-wrap gap-2">
                <Button
                  v-if="riga.may_buy"
                  :label="
                    riga.numbers.length
                      ? __('Another number')
                      : __('Choose the number')
                  "
                  @click="apriNuovo(riga)"
                />
                <template v-if="riga.may_resend">
                  <Button :label="__('Send again')" @click="apriNuovo(riga)" />
                  <Button
                    :label="__('Remove')"
                    theme="red"
                    variant="subtle"
                    @click="chiediDiTogliere(riga)"
                  />
                </template>
              </div>
            </div>
          </div>
          <Button
            v-if="richieste.some((r) => r.status === 'In review')"
            class="w-fit"
            :label="__('Ask Telnyx now')"
            icon-left="lucide-refresh-cw"
            :loading="chiediATelnyx.loading"
            @click="chiediATelnyx.submit()"
          />
        </div>

        <template v-if="telnyx.doc">
          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex items-center justify-between gap-4">
            <div class="flex min-w-0 flex-col">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('Record Calls') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  __('Enable call recording for incoming and outgoing calls')
                }}
              </div>
            </div>
            <Switch
              :aria-label="__('Record Calls')"
              v-model="telnyx.doc.record_calls"
              size="sm"
            />
          </div>

          <div v-if="telnyx.doc.record_calls" class="pt-1">
            <div class="text-p-base-medium text-ink-gray-7">
              {{ __('Recording Notice') }}
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Spoken to the other party before they are connected. Empty means no announcement — check what your jurisdiction requires.',
                )
              }}
            </div>
            <FormControl
              v-model="telnyx.doc.recording_notice"
              type="textarea"
              rows="2"
              class="mt-2"
              :placeholder="
                __('This call may be recorded for quality purposes.')
              "
            />
          </div>

          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex flex-col gap-2">
            <div class="flex min-w-0 flex-col">
              <div
                id="paesi-che-si-chiamano-telnyx"
                class="text-p-base-medium text-ink-gray-7"
              >
                {{ __('Countries That Can Be Called') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Calls from {brand} go only to these countries, never to premium-rate numbers. Telnyx is told the same, so a stolen key could not call anywhere else either.',
                  )
                }}
              </div>
            </div>
            <div
              class="flex flex-wrap items-center gap-1.5"
              role="list"
              aria-labelledby="paesi-che-si-chiamano-telnyx"
            >
              <Badge
                v-for="codice in paesiScelti"
                :key="codice"
                role="listitem"
                size="lg"
                variant="subtle"
                theme="gray"
              >
                {{ nomeDelPaese(codice, lingua) }}
                <template v-if="paesiScelti.length > 1" #suffix>
                  <button
                    type="button"
                    class="touch-target -mr-1 flex size-4 items-center justify-center rounded hover:bg-surface-gray-4"
                    :aria-label="
                      __('Remove {0}', [nomeDelPaese(codice, lingua)])
                    "
                    @click="togliIlPaese(codice)"
                  >
                    <span class="lucide-x size-3" aria-hidden="true" />
                  </button>
                </template>
              </Badge>
              <Combobox
                :model-value="null"
                :options="paesiDaAggiungere(paesiScelti, lingua)"
                :placeholder="__('Search a country')"
                @update:selected-option="(o) => o && aggiungiIlPaese(o.value)"
              >
                <template #trigger="{ open, setOpen }">
                  <Button
                    variant="ghost"
                    icon-left="lucide-plus"
                    :label="__('Add a country')"
                    @click="setOpen(!open)"
                  />
                </template>
              </Combobox>
            </div>
          </div>

          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex flex-col gap-2">
            <div class="flex min-w-0 flex-col">
              <div
                id="mittente-sms-telnyx"
                class="text-p-base-medium text-ink-gray-7"
              >
                {{ __('SMS Sender') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Every SMS the centre sends leaves from here: the waiting list’s offers, the client area’s news, the automations, the ones written by hand.',
                  )
                }}
              </div>
            </div>
            <div
              class="flex flex-col gap-2"
              role="radiogroup"
              aria-labelledby="mittente-sms-telnyx"
            >
              <SceltaRadio
                v-model="mittente"
                nome="mittente-sms-telnyx"
                :scelta="{
                  value: 'Name',
                  label: __('The centre’s name'),
                  description: __(
                    'Up to 11 letters without accents, digits and spaces. Nobody can reply to a name.',
                  ),
                }"
              />
              <div v-if="mittente === 'Name'" class="md:pl-7">
                <FormControl
                  v-model="nomeSms"
                  :maxlength="11"
                  :placeholder="opzioniSms.data?.name"
                />
              </div>
              <SceltaRadio
                v-if="numeriSms.length"
                v-model="mittente"
                nome="mittente-sms-telnyx"
                :scelta="{
                  value: 'Number',
                  label: __('One of the centre’s numbers'),
                  description: __(
                    'People can reply: the answers reach the person’s conversation, and a STOP is heard.',
                  ),
                }"
              />
              <div
                v-if="mittente === 'Number' && numeriSms.length"
                class="md:pl-7"
              >
                <FormControl
                  v-model="numeroSms"
                  type="select"
                  :options="numeriSms"
                />
              </div>
              <p v-if="!numeriSms.length" class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Telnyx sells no Italian mobile number: an Italian landline sends no SMS. The centre’s name is the sender, and nobody can reply to it.',
                  )
                }}
              </p>
            </div>
          </div>
        </template>
      </div>
    </template>
  </SettingsLayoutBase>
  <NewNumberDialog
    v-if="nuovo.aperto && offerta.data"
    v-model="nuovo.aperto"
    :offerta="offerta.data"
    :richiesta="nuovo.richiesta"
    modulo="crm.telephony.telnyx.numeri"
    operatore="Telnyx"
    @changed="aggiornaLeRichieste"
  />
  <TelnyxMoveDialog
    v-if="trasloco"
    v-model="trasloco"
    :del-centro="stato.owner === 'Centre'"
    @moved="connessione.reload()"
    @verifica="verificaUnNumero"
  />
  <VerifyNumberDialog
    v-if="verifica"
    v-model="verifica"
    carrier="telnyx"
    @changed="connessione.reload()"
  />
</template>
<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SceltaRadio from '@/components/Settings/Invoicing/SceltaRadio.vue'
import NewNumberDialog from '@/components/Settings/Telephony/NewNumberDialog.vue'
import TelnyxMoveDialog from '@/components/Settings/Telephony/TelnyxMoveDialog.vue'
import VerifyNumberDialog from '@/components/Settings/Telephony/VerifyNumberDialog.vue'
import { setEnabled } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  comeSalvati,
  conIlPaese,
  nomeDelPaese,
  paesi,
  paesiDaAggiungere,
  senzaIlPaese,
} from '@/utils/chiamate'
import { appLocale } from '@/utils/locale'
import {
  nomeDellaRichiesta,
  prezzoAlMese,
  statoDellaRichiesta,
} from '@/utils/numeri'
import {
  TELNYX,
  chiPaga,
  cosaManca,
  quantiNellaVoce,
  righeDelControllo,
} from '@/utils/telnyx'
import { quanteVolte } from '@/utils/twilio'
import { simboloDellaValuta } from '@/utils/valute'
import {
  Badge,
  Combobox,
  ErrorMessage,
  FormControl,
  Switch,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const emit = defineEmits(['updateStep'])
const { $dialog } = globalStore()

const codici = reactive({ api_key: '', public_key: '' })
const errore = ref('')
const controllo = ref(null)

const connessione = createResource({
  url: 'crm.telephony.telnyx.collegamento.get_telnyx_connection',
  auto: true,
})
const stato = computed(() => connessione.data)

// what the centre decides on calls and SMS: recording, its notice, the
// countries, the sender, the alerts; the codes are the connection's, never here
const { document: telnyx } = useDocument(
  'CRM Telnyx Settings',
  'CRM Telnyx Settings',
)

function dopo(dati, messaggio) {
  connessione.data = dati
  controllo.value = null
  setEnabled('telnyx', Boolean(dati?.connected))
  telnyx.reload()
  if (messaggio) toast.success(messaggio)
}

const collega = createResource({
  url: 'crm.telephony.telnyx.collegamento.connect_telnyx',
  method: 'POST',
  onSuccess: (dati) => {
    codici.api_key = ''
    codici.public_key = ''
    dopo(dati, __('Telnyx is connected'))
    controllo.value = { ok: true, ...dati }
  },
  onError: (e) => (errore.value = e.messages?.[0] || e.message),
})

const collegaAgenzia = createResource({
  url: 'crm.telephony.telnyx.collegamento.connect_agency_telnyx',
  method: 'POST',
  onSuccess: (dati) => dopo(dati, __('Telnyx is connected')),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const controlla = createResource({
  url: 'crm.telephony.telnyx.collegamento.check_telnyx_connection',
  method: 'POST',
  onSuccess: (dati) => {
    connessione.data = dati
    controllo.value = dati
  },
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const scollega = createResource({
  url: 'crm.telephony.telnyx.collegamento.disconnect_telnyx',
  method: 'POST',
  onSuccess: (dati) => dopo(dati, __('Telnyx is disconnected')),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

function connetti() {
  errore.value = ''
  const manca = cosaManca(codici.api_key, codici.public_key)
  if (manca) {
    errore.value = __(manca)
    return
  }
  collega.submit({ ...codici })
}

function connettiAgenzia() {
  collegaAgenzia.submit()
}

function chiediDiScollegare() {
  $dialog({
    title: __('Disconnect Telnyx?'),
    message: __(
      'Calls and messages from {brand} stop and the key is forgotten. What {brand} made in your Telnyx account and the numbers stay there, and the numbers keep costing until you release them.',
    ),
    actions: [
      {
        label: __('Disconnect'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          scollega.submit()
        },
      },
    ],
  })
}

function apri(indirizzo) {
  window.open(indirizzo, '_blank', 'noopener')
}

const righe = computed(() => {
  const s = stato.value || {}
  const tutte = [
    { label: __('API key', null, 'Telnyx portal'), value: s.key || '—' },
    {
      label: __('What {brand} made in the account'),
      value: s.resources?.name || '—',
    },
    { label: __('Who pays'), value: __(chiPaga(s.owner)) || '—' },
  ]
  if (s.connected_on) {
    tutte.push({
      label: __('Connected', null, 'Twilio'),
      value: s.connected_by
        ? __('{0} by {1}', [formatDate(s.connected_on), s.connected_by])
        : formatDate(s.connected_on),
    })
  }
  return tutte
})

const numeriInParole = computed(() => {
  const s = stato.value || {}
  if (!s.numbers) return __('No number of the centre’s on Telnyx yet.')
  if (s.not_reaching && s.numbers === 1) {
    return __('One number, and it does not reach {brand}.')
  }
  if (s.not_reaching === s.numbers) {
    return __('{0} numbers, and none of them reaches {brand}.', [s.numbers])
  }
  if (s.not_reaching === 1) {
    return __('{0} numbers, one of them does not reach {brand}.', [s.numbers])
  }
  if (s.not_reaching) {
    return __('{0} numbers, {1} of them do not reach {brand}.', [
      s.numbers,
      s.not_reaching,
    ])
  }
  return s.numbers === 1
    ? __('One number, and it reaches {brand}.')
    : __('{0} numbers, and they all reach {brand}.', [s.numbers])
})

// the numbers asked of Telnyx, and what Telnyx sells in Italy now (doc 64)
const offerta = createResource({
  url: 'crm.telephony.telnyx.numeri.get_number_offer',
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})
// what the account spends and what went wrong in it, for whoever pays
const consumi = createResource({
  url: 'crm.telephony.telnyx.consumi.get_telnyx_usage',
})
// who every SMS of the centre comes from: its name, or one of its numbers that
// can send SMS; while nothing is chosen, the one the server uses
const opzioniSms = createResource({
  url: 'crm.telephony.sms.get_sms_sender_options',
})
watch(
  () => stato.value?.connected,
  (collegato) => {
    if (!collegato) return
    offerta.fetch()
    consumi.fetch()
    opzioniSms.fetch()
  },
  { immediate: true },
)

const richieste = computed(() => offerta.data?.requests || [])
const nuovo = reactive({ aperto: false, richiesta: null })
// a number the centre already has: in its account, or with another operator
const trasloco = ref(false)
// or kept with its operator and verified, to be shown on calls
const verifica = ref(false)

function verificaUnNumero() {
  trasloco.value = false
  verifica.value = true
}

function apriNuovo(richiesta = null) {
  nuovo.richiesta = richiesta
  nuovo.aperto = true
}

function aggiornaLeRichieste(elenco) {
  if (offerta.data) offerta.data = { ...offerta.data, requests: elenco }
  connessione.reload()
}

const chiediATelnyx = createResource({
  url: 'crm.telephony.telnyx.numeri.refresh_number_requests',
  method: 'POST',
  onSuccess: (dati) => aggiornaLeRichieste(dati.requests),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const togli = createResource({
  url: 'crm.telephony.telnyx.numeri.delete_number_request',
  method: 'POST',
  onSuccess: (dati) => aggiornaLeRichieste(dati.requests),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

function chiediDiTogliere(riga) {
  $dialog({
    title: __('Remove the request?'),
    message: __(
      'The documents written for it go, here and in Telnyx. Nothing has been bought with them.',
    ),
    actions: [
      {
        label: __('Remove'),
        variant: 'solid',
        theme: 'red',
        onClick: (chiudi) => {
          chiudi()
          togli.submit({ request: riga.name })
        },
      },
    ],
  })
}

// where calls may go: Italy to start with, the manager adds the others
const lingua = appLocale() || 'it'
const paesiScelti = computed(() => paesi(telnyx.doc?.allowed_countries))

function aggiungiIlPaese(codice) {
  telnyx.doc.allowed_countries = comeSalvati(
    conIlPaese(telnyx.doc.allowed_countries, codice),
  )
}

function togliIlPaese(codice) {
  telnyx.doc.allowed_countries = comeSalvati(
    senzaIlPaese(telnyx.doc.allowed_countries, codice),
  )
}

const valuta = computed(
  () =>
    consumi.data?.month?.currency || consumi.data?.balance?.currency || 'USD',
)
const simbolo = computed(() => simboloDellaValuta(valuta.value, appLocale()))
function soldi(valore, inValuta = null) {
  return prezzoAlMese(valore, inValuta || valuta.value, lingua)
}

// no alert is an empty field, not a 0
function avvisoDi(campo) {
  return computed({
    get: () => telnyx.doc?.[campo] || '',
    set: (valore) => {
      telnyx.doc[campo] = valore === '' || valore === null ? 0 : Number(valore)
    },
  })
}
const avvisoDiSpesa = avvisoDi('spend_alert')
const avvisoDiBilancio = avvisoDi('balance_alert')

const numeriSms = computed(() =>
  (opzioniSms.data?.numbers || []).map((n) => ({
    label: n.label ? `${n.label} · ${n.number}` : n.number,
    value: n.number,
  })),
)
const mittente = computed({
  get() {
    if (telnyx.doc?.sms_from) return telnyx.doc.sms_from
    return opzioniSms.data?.sender?.startsWith('+') ? 'Number' : 'Name'
  },
  set(valore) {
    telnyx.doc.sms_from = valore
    if (valore === 'Name' && !telnyx.doc.sms_sender_name) {
      telnyx.doc.sms_sender_name = opzioniSms.data?.name || ''
    }
    if (valore === 'Number' && !telnyx.doc.sms_sender_number) {
      telnyx.doc.sms_sender_number = numeriSms.value[0]?.value || ''
    }
  },
})

// while nothing is chosen the fields show the sender in use, and writing in
// them is choosing it
const inUso = computed(() => opzioniSms.data?.sender || '')
const nomeSms = computed({
  get() {
    if (telnyx.doc?.sms_from || telnyx.doc?.sms_sender_name) {
      return telnyx.doc.sms_sender_name || ''
    }
    return inUso.value.startsWith('+') ? '' : inUso.value
  },
  set(valore) {
    telnyx.doc.sms_from = 'Name'
    telnyx.doc.sms_sender_name = valore
  },
})
const numeroSms = computed({
  get() {
    if (telnyx.doc?.sms_sender_number) return telnyx.doc.sms_sender_number
    return inUso.value.startsWith('+') ? inUso.value : ''
  },
  set(valore) {
    telnyx.doc.sms_from = 'Number'
    telnyx.doc.sms_sender_number = valore
  },
})

function update() {
  telnyx.save.submit(null, {
    onSuccess: () => {
      telnyx.reload()
      opzioniSms.reload()
      consumi.reload()
    },
  })
}

const isDirty = computed(() => {
  const doc = telnyx.doc
  const prima = telnyx.originalDoc
  if (!doc || !prima) return false
  return (
    Boolean(doc.record_calls) !== Boolean(prima.record_calls) ||
    (doc.recording_notice || '') !== (prima.recording_notice || '') ||
    comeSalvati(doc.allowed_countries) !==
      comeSalvati(prima.allowed_countries) ||
    ['sms_from', 'sms_sender_name', 'sms_sender_number'].some(
      (campo) => (doc[campo] || '') !== (prima[campo] || ''),
    ) ||
    ['spend_alert', 'balance_alert'].some(
      (campo) => Number(doc[campo] || 0) !== Number(prima[campo] || 0),
    )
  )
})
</script>
