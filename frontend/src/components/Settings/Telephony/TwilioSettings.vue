<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  Settings > Phone > Telephony > Twilio (doc 52).

  The centre connects its own Twilio account with the two codes of the console's
  first page, once: DottorCloud makes its own space in the account and keeps only
  that space's keys. Calls and messages are paid to Twilio by the centre; the rest
  is done here. The agency may connect its own account instead, for a centre with
  its front desk. What the centre decides on calls (recording) stays below.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Twilio')"
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
          @click="twilio.reload()"
        />
        <AzioneImpostazioni :loading="twilio.save.loading" @click="update" />
      </div>
    </template>
    <template #content>
      <div
        v-if="connessione.loading && !stato"
        class="mt-[35%] flex items-center justify-center"
      >
        <LoadingIndicator class="size-6" />
      </div>

      <!-- not connected: three steps, two codes -->
      <div v-else-if="stato && !stato.connected" class="flex flex-col gap-5">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "Calls and messages go through your own Twilio account: you pay Twilio, at Twilio's prices. Everything else you do here in {brand}.",
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
                    'Create your account on Twilio, if you have none, and upgrade it with a payment method.',
                  )
                }}
              </span>
              <a
                :href="TWILIO.registrazione"
                target="_blank"
                rel="noopener"
                class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
              >
                {{ __('Open Twilio') }}
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
                    'On the first page of the Twilio console, copy the Account SID and the Auth Token.',
                  )
                }}
              </span>
              <a
                :href="TWILIO.console"
                target="_blank"
                rel="noopener"
                class="inline-flex w-fit items-center gap-1 text-p-sm text-ink-gray-6 underline"
              >
                {{ __('Open the console') }}
                <span class="lucide-external-link size-3.5" />
              </a>
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
                <FormControl
                  autocapitalize="none"
                  spellcheck="false"
                  v-model="codici.account_sid"
                  :label="__('Account SID', null, 'Twilio console')"
                  type="text"
                  placeholder="AC…"
                  autocomplete="off"
                />
                <Password
                  v-model="codici.auth_token"
                  :label="__('Auth Token', null, 'Twilio console')"
                  placeholder="••••••••"
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
              'The token is used only now. {brand} makes its own space in your account, with its own keys, and keeps only those: it neither reads nor touches the rest of your account.',
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
                  "For a centre with the agency's front desk: the space lives in the agency's account, and the agency pays.",
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

      <!-- connected: whose account, which space, and what Check found -->
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
              class="min-w-0 text-right text-p-sm text-ink-gray-8 max-md:text-left"
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
            <p class="text-p-sm text-ink-gray-8">
              {{ statoDelContoInParole }}
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
            :label="__('Open Twilio')"
            icon-left="lucide-external-link"
            @click="apri(TWILIO.console)"
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
          What the space spends and what went wrong in it (doc 52), for whoever
          pays for it: this month by kind, the alert, the last days' problems in
          words. The credit is the account's, and Twilio shows it.
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
                      'What the space spent since {0}, as Twilio counts it. The credit is the account’s: Twilio shows it, and that is where it is topped up.',
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
            <div
              v-else
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

            <!-- an account connected by hand gets no trigger of DottorCloud's -->
            <div
              v-if="twilio.doc && stato.owner !== 'Manual'"
              class="flex flex-col gap-1.5"
            >
              <div class="flex flex-wrap items-center gap-2">
                <label for="avviso-spesa" class="text-p-sm text-ink-gray-7">
                  {{ __('Tell me when the month reaches') }}
                </label>
                <div class="flex shrink-0 items-center gap-1.5">
                  <FormControl
                    id="avviso-spesa"
                    v-model="avvisoDiSpesa"
                    class="w-36"
                    type="number"
                    min="0"
                    step="1"
                    :placeholder="__('No alert')"
                  />
                  <span class="text-p-sm text-ink-gray-5">
                    {{ consumi.data.month?.currency }}
                  </span>
                </div>
              </div>
              <p class="text-p-xs text-ink-gray-5">
                {{
                  __(
                    'Twilio says it once a month, the moment the spend gets there: whoever pays for the space reads it among the notifications. Empty: no alert.',
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
                :label="__('Twilio’s log')"
                @click="apri(TWILIO.registro)"
              />
            </div>
            <p
              v-if="!consumi.data.error && !consumi.data.problems?.length"
              class="text-p-sm text-ink-gray-5"
            >
              {{ __('None: calls and SMS went through.') }}
            </p>
            <div
              v-for="problema in consumi.data.problems"
              :key="problema.code || problema.twilio"
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
            <div class="flex shrink-0 gap-2">
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

          <!-- the numbers asked of Twilio: where each request is -->
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
                        statoDellaRichiesta(riga).label,
                        null,
                        'Number request',
                      )
                    "
                    :theme="statoDellaRichiesta(riga).theme"
                    variant="subtle"
                  />
                </div>
                <span class="text-p-sm text-ink-gray-6">
                  {{ __(...statoDellaRichiesta(riga).riga) }}
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
            :label="__('Ask Twilio now')"
            icon-left="lucide-refresh-cw"
            :loading="chiediATwilio.loading"
            @click="chiediATwilio.submit()"
          />
        </div>

        <template v-if="twilio.doc">
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
              v-model="twilio.doc.record_calls"
              size="sm"
            />
          </div>

          <div v-if="twilio.doc.record_calls" class="pt-1">
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
              v-model="twilio.doc.recording_notice"
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
                id="paesi-che-si-chiamano"
                class="text-p-base-medium text-ink-gray-7"
              >
                {{ __('Countries That Can Be Called') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  stato.owner === 'Manual'
                    ? __(
                        'Calls from {brand} go only to these countries, never to premium-rate numbers.',
                      )
                    : __(
                        'Calls from {brand} go only to these countries, never to premium-rate numbers. Twilio is told the same, so a stolen key could not call anywhere else either.',
                      )
                }}
              </div>
            </div>
            <div
              class="flex flex-wrap items-center gap-1.5"
              role="list"
              aria-labelledby="paesi-che-si-chiamano"
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
              <div id="mittente-sms" class="text-p-base-medium text-ink-gray-7">
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
              aria-labelledby="mittente-sms"
            >
              <SceltaRadio
                v-model="mittente"
                nome="mittente-sms"
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
                nome="mittente-sms"
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
                    'For the answers to come back the centre needs a number that can send SMS, like a mobile one: ask for it in Numbers, above.',
                  )
                }}
              </p>
            </div>
          </div>
        </template>

        <template v-if="stato.agency">
          <div class="h-px border-t border-outline-elevation-2" />

          <div class="flex items-center justify-between gap-4">
            <div class="flex min-w-0 flex-col">
              <div class="text-p-base-medium text-ink-gray-7">
                {{ __('SIP Trunking') }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{
                  trunks.length
                    ? __('{0} elastic SIP trunk(s) on this account', [
                        trunks.length,
                      ])
                    : __(
                        'Read the Elastic SIP trunks configured on this account.',
                      )
                }}
              </div>
            </div>
            <Button
              class="shrink-0"
              :label="__('Refresh')"
              icon-left="lucide-refresh-cw"
              :loading="twilio.fetchSipTrunks?.loading"
              @click="twilio.fetchSipTrunks.fetch"
            />
          </div>

          <div
            v-for="trunk in trunks"
            :key="trunk.sid"
            class="rounded-md border border-outline-gray-2 px-3 py-2"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="truncate text-p-base-medium text-ink-gray-8">
                {{ trunk.friendly_name || trunk.sid }}
              </span>
              <div class="flex shrink-0 gap-1">
                <Badge
                  v-if="trunk.secure"
                  :label="__('Secure')"
                  variant="subtle"
                  theme="green"
                />
                <Badge
                  :label="
                    __('{0} number(s)', [trunk.phone_numbers?.length || 0])
                  "
                  variant="subtle"
                  theme="gray"
                />
              </div>
            </div>
            <div class="mt-1 text-p-sm text-ink-gray-6">
              {{ __('Termination') }}:
              <code class="text-ink-gray-8">{{
                trunk.termination_uri || '—'
              }}</code>
            </div>
            <p
              v-if="trunk.phone_numbers?.length"
              class="mt-1.5 text-p-sm text-ink-red-8"
            >
              {{
                __(
                  'Calls to these numbers go straight to your SIP infrastructure — Twilio ignores their voice webhook, so the answering service cannot run on them.',
                )
              }}
            </p>
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
    @changed="aggiornaLeRichieste"
  />
  <MoveNumberDialog
    v-if="trasloco"
    v-model="trasloco"
    :del-centro="stato.owner === 'Centre'"
    @moved="connessione.reload()"
    @verifica="verificaUnNumero"
  />
  <VerifyNumberDialog
    v-if="verifica"
    v-model="verifica"
    @changed="connessione.reload()"
  />
</template>
<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SceltaRadio from '@/components/Settings/Invoicing/SceltaRadio.vue'
import MoveNumberDialog from '@/components/Settings/Telephony/MoveNumberDialog.vue'
import NewNumberDialog from '@/components/Settings/Telephony/NewNumberDialog.vue'
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
  TWILIO,
  chiPaga,
  cosaManca,
  quanteVolte,
  quantiNellaVoce,
  righeDelControllo,
  statoDelConto,
} from '@/utils/twilio'
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

const codici = reactive({ account_sid: '', auth_token: '' })
const errore = ref('')
const controllo = ref(null)

const connessione = createResource({
  url: 'crm.telephony.collegamento.get_twilio_connection',
  auto: true,
})
const stato = computed(() => connessione.data)

// what the centre decides on calls: recording, its notice; the keys are the
// connection's, never typed here
const { document: twilio } = useDocument(
  'CRM Twilio Settings',
  'CRM Twilio Settings',
  {
    whitelistedMethods: {
      fetchSipTrunks: {
        method: 'fetch_sip_trunks',
        onSuccess: () => twilio.reload(),
      },
    },
  },
)

function dopo(dati, messaggio) {
  connessione.data = dati
  controllo.value = null
  setEnabled('twilio', Boolean(dati?.connected))
  twilio.reload()
  if (messaggio) toast.success(messaggio)
}

const collega = createResource({
  url: 'crm.telephony.collegamento.connect_twilio',
  method: 'POST',
  onSuccess: (dati) => {
    codici.account_sid = ''
    codici.auth_token = ''
    dopo(dati, __('Twilio is connected'))
    controllo.value = { ok: true, ...dati }
  },
  onError: (e) => (errore.value = e.messages?.[0] || e.message),
})

const collegaAgenzia = createResource({
  url: 'crm.telephony.collegamento.connect_agency_twilio',
  method: 'POST',
  onSuccess: (dati) => dopo(dati, __('Twilio is connected')),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const controlla = createResource({
  url: 'crm.telephony.collegamento.check_twilio_connection',
  method: 'POST',
  onSuccess: (dati) => {
    connessione.data = dati
    controllo.value = dati
  },
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const scollega = createResource({
  url: 'crm.telephony.collegamento.disconnect_twilio',
  method: 'POST',
  onSuccess: (dati) => dopo(dati, __('Twilio is disconnected')),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

function connetti() {
  errore.value = ''
  const manca = cosaManca(codici.account_sid, codici.auth_token)
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
    title: __('Disconnect Twilio?'),
    message: __(
      'Calls and messages from {brand} stop. The space and its numbers stay in your Twilio account, and the numbers keep costing until you release them.',
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
  const conto = s.main_account || {}
  const spazio = s.space || {}
  const tutte = [
    {
      label: __('Twilio account'),
      value: [conto.name, conto.sid].filter(Boolean).join(' · ') || '—',
    },
    {
      label: __("{brand}'s space"),
      value: [spazio.name, spazio.sid].filter(Boolean).join(' · ') || '—',
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

const statoDelContoInParole = computed(() => {
  const parola = statoDelConto(controllo.value?.status)
  const prova = controllo.value?.type === 'Trial'
  if (!parola) return ''
  return prova
    ? __('Twilio account: {0}, on trial', [__(parola)])
    : __('Twilio account: {0}', [__(parola)])
})

const numeriInParole = computed(() => {
  const s = stato.value || {}
  if (!s.numbers) return __('No number in the space yet.')
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

const trunks = computed(() => {
  try {
    return JSON.parse(twilio.doc?.sip_trunks || '[]')
  } catch {
    // a half-written cache must not blank the whole settings page
    return []
  }
})

// the numbers asked of Twilio, and what Twilio sells now (doc 52)
const offerta = createResource({
  url: 'crm.telephony.numeri.get_number_offer',
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})
watch(
  () => stato.value?.connected,
  (collegato) => {
    if (collegato) offerta.fetch()
  },
  { immediate: true },
)
const richieste = computed(() => offerta.data?.requests || [])
const nuovo = reactive({ aperto: false, richiesta: null })
// a number the centre already has, moved in or forwarded (doc 52)
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

const chiediATwilio = createResource({
  url: 'crm.telephony.numeri.refresh_number_requests',
  method: 'POST',
  onSuccess: (dati) => aggiornaLeRichieste(dati.requests),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

const togli = createResource({
  url: 'crm.telephony.numeri.delete_number_request',
  method: 'POST',
  onSuccess: (dati) => aggiornaLeRichieste(dati.requests),
  onError: (e) => toast.error(e.messages?.[0] || e.message),
})

function chiediDiTogliere(riga) {
  $dialog({
    title: __('Remove the request?'),
    message: __(
      'The documents written for it go, here and in Twilio. Nothing has been bought with them.',
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

// where calls may go: Italy to start with, the manager adds the others (doc 52)
const lingua = appLocale() || 'it'
const paesiScelti = computed(() => paesi(twilio.doc?.allowed_countries))

function aggiungiIlPaese(codice) {
  twilio.doc.allowed_countries = comeSalvati(
    conIlPaese(twilio.doc.allowed_countries, codice),
  )
}

function togliIlPaese(codice) {
  twilio.doc.allowed_countries = comeSalvati(
    senzaIlPaese(twilio.doc.allowed_countries, codice),
  )
}

// what the space spends and what went wrong in it (doc 52), for whoever pays
const consumi = createResource({
  url: 'crm.telephony.consumi.get_twilio_usage',
})
watch(
  () => stato.value?.connected,
  (collegato) => {
    if (collegato) consumi.fetch()
  },
  { immediate: true },
)
function soldi(valore) {
  return prezzoAlMese(valore, consumi.data?.month?.currency || 'USD', lingua)
}
// no alert is an empty field, not a 0
const avvisoDiSpesa = computed({
  get: () => twilio.doc?.spend_alert || '',
  set: (valore) => {
    twilio.doc.spend_alert =
      valore === '' || valore === null ? 0 : Number(valore)
  },
})

// who every SMS of the centre comes from (doc 52): its name, or one of its
// numbers that can send SMS; while nothing is chosen, the one the server uses
const opzioniSms = createResource({
  url: 'crm.telephony.sms.get_sms_sender_options',
})
watch(
  () => stato.value?.connected,
  (collegato) => {
    if (collegato) opzioniSms.fetch()
  },
  { immediate: true },
)
const numeriSms = computed(() =>
  (opzioniSms.data?.numbers || []).map((n) => ({
    label: n.label ? `${n.label} · ${n.number}` : n.number,
    value: n.number,
  })),
)
const mittente = computed({
  get() {
    if (twilio.doc?.sms_from) return twilio.doc.sms_from
    return opzioniSms.data?.sender?.startsWith('+') ? 'Number' : 'Name'
  },
  set(valore) {
    twilio.doc.sms_from = valore
    if (valore === 'Name' && !twilio.doc.sms_sender_name) {
      twilio.doc.sms_sender_name = opzioniSms.data?.name || ''
    }
    if (valore === 'Number' && !twilio.doc.sms_sender_number) {
      twilio.doc.sms_sender_number = numeriSms.value[0]?.value || ''
    }
  },
})

// while nothing is chosen the fields show the sender in use, and writing in
// them is choosing it
const inUso = computed(() => opzioniSms.data?.sender || '')
const nomeSms = computed({
  get() {
    if (twilio.doc?.sms_from || twilio.doc?.sms_sender_name) {
      return twilio.doc.sms_sender_name || ''
    }
    return inUso.value.startsWith('+') ? '' : inUso.value
  },
  set(valore) {
    twilio.doc.sms_from = 'Name'
    twilio.doc.sms_sender_name = valore
  },
})
const numeroSms = computed({
  get() {
    if (twilio.doc?.sms_sender_number) return twilio.doc.sms_sender_number
    return inUso.value.startsWith('+') ? inUso.value : ''
  },
  set(valore) {
    twilio.doc.sms_from = 'Number'
    twilio.doc.sms_sender_number = valore
  },
})

function update() {
  twilio.save.submit(null, {
    onSuccess: () => {
      twilio.reload()
      opzioniSms.reload()
    },
  })
}

const isDirty = computed(() => {
  const doc = twilio.doc
  const prima = twilio.originalDoc
  if (!doc || !prima) return false
  return (
    Boolean(doc.record_calls) !== Boolean(prima.record_calls) ||
    (doc.recording_notice || '') !== (prima.recording_notice || '') ||
    comeSalvati(doc.allowed_countries) !==
      comeSalvati(prima.allowed_countries) ||
    ['sms_from', 'sms_sender_name', 'sms_sender_number'].some(
      (campo) => (doc[campo] || '') !== (prima[campo] || ''),
    ) ||
    Number(doc.spend_alert || 0) !== Number(prima.spend_alert || 0)
  )
})
</script>
