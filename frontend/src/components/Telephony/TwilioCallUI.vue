<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  The call in the browser, through the centre's Twilio space (doc 52). Before a
  call goes out the server says whether it may (the centre's countries, never a
  premium-rate number) and which numbers it may show: with more than one, the
  popup asks, the last one used chosen already. During the call, a keypad sends
  the tones an automatic switchboard asks for.
-->
<template>
  <div v-show="showCallPopup" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-20 flex cursor-move select-none flex-col rounded-lg bg-surface-gray-10 p-4 text-ink-gray-2 shadow-2xl"
      :class="scelta ? 'w-72' : 'w-60'"
      :style="style"
    >
      <div class="flex min-h-4 flex-row-reverse items-center gap-1">
        <!-- a button with its words: the icon took a click and no key -->
        <button
          v-if="!scelta"
          ref="riduci"
          type="button"
          class="touch-target rounded"
          :aria-label="__('Minimize')"
          @click="toggleCallWindow"
        >
          <MinimizeIcon class="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
      <div class="flex flex-col items-center justify-center gap-3">
        <Avatar
          v-if="contact?.image && !tastiera"
          :image="contact.image"
          :label="contact.full_name"
          class="relative flex !h-24 !w-24 items-center justify-center [&>div]:text-[30px]"
          :class="onCall || calling || scelta ? '' : 'pulse'"
        />
        <div class="flex flex-col items-center justify-center gap-1">
          <!-- the name keeps its line while the server is asked who it is:
               the buttons below do not move when it comes -->
          <div class="text-2xl-medium">
            {{ nomeDiChi || '\u00a0' }}
          </div>
          <!-- the number of the call, as it came or was dialled: the server's
               answer has the person's main mobile, not always the number that
               calls, and for nobody the digits without their country -->
          <div class="text-sm text-ink-gray-5">
            {{ phoneNumber }}
          </div>
        </div>
        <CountUpTimer ref="counterUp">
          <div v-if="onCall" class="my-1 text-base">
            {{ counterUp?.updatedTime }}
          </div>
        </CountUpTimer>
        <div v-if="!onCall && !scelta" class="my-1 text-base">
          {{
            callStatus == 'initiating'
              ? __('Initiating call...')
              : callStatus == 'ringing'
                ? __('Ringing...')
                : calling
                  ? __('Calling...')
                  : __('Incoming call...')
          }}
        </div>
        <div
          v-if="avvisoAgcom && !scelta && (calling || onCall)"
          class="flex gap-1.5 text-sm leading-snug"
        >
          <span
            class="lucide-triangle-alert mt-0.5 size-3.5 shrink-0 text-ink-amber-6"
            aria-hidden="true"
          />
          <span>{{ avvisoAgcom }}</span>
        </div>
        <div v-if="scelta" class="flex w-full flex-col gap-3">
          <div class="flex flex-col gap-1">
            <div id="numero-da-mostrare" class="text-sm text-ink-gray-5">
              {{ __('Call from') }}
            </div>
            <div
              role="radiogroup"
              aria-labelledby="numero-da-mostrare"
              class="flex flex-col gap-0.5"
            >
              <button
                v-for="n in numeri"
                :key="n.number"
                type="button"
                role="radio"
                :aria-checked="n.number === mostrato"
                class="touch-target flex items-center gap-2 rounded px-2 py-1.5 text-left hover:bg-surface-gray-9"
                :class="n.number === mostrato ? 'bg-surface-gray-9' : ''"
                @click="mostrato = n.number"
              >
                <div class="min-w-0 flex-1">
                  <div class="truncate text-base">
                    {{ n.label || n.number }}
                  </div>
                  <div class="truncate text-sm text-ink-gray-5">
                    {{
                      n.own
                        ? n.label
                          ? __('{0} · your line', [n.number])
                          : __('Your line')
                        : n.label
                          ? n.number
                          : ''
                    }}
                  </div>
                </div>
                <span
                  v-if="n.number === mostrato"
                  class="dc-scelto lucide-check size-4 shrink-0"
                  aria-hidden="true"
                />
              </button>
            </div>
          </div>
          <div v-if="avvisoAgcom" class="flex gap-1.5 text-sm leading-snug">
            <span
              class="lucide-triangle-alert mt-0.5 size-3.5 shrink-0 text-ink-amber-6"
              aria-hidden="true"
            />
            <span>{{ avvisoAgcom }}</span>
          </div>
          <div class="flex justify-center gap-2">
            <Button
              size="md"
              variant="solid"
              theme="green"
              :label="__('Call')"
              class="rounded-lg text-ink-base"
              :iconLeft="PhoneIcon"
              @click="chiama"
            />
            <Button
              size="md"
              :label="__('Cancel')"
              class="rounded-lg"
              @click="annullaLaScelta"
            />
          </div>
        </div>
        <div v-if="onCall && tastiera" class="flex flex-col items-center gap-2">
          <div
            class="min-h-6 max-w-full truncate text-xl tracking-widest"
            aria-live="polite"
          >
            {{ cifre }}
          </div>
          <div class="grid grid-cols-3 gap-2">
            <Button
              v-for="tasto in TASTI.flat()"
              :key="tasto"
              size="md"
              class="!size-11 rounded-full text-lg"
              :label="tasto"
              @click="premi(tasto)"
            />
          </div>
        </div>
        <div v-if="onCall" class="flex gap-2">
          <Button
            :aria-label="muted ? __('Unmute') : __('Mute')"
            :icon="muted ? 'mic-off' : 'mic'"
            class="rounded-full"
            @click="toggleMute"
          />
          <Button
            :aria-label="tastiera ? __('Hide the keypad') : __('Keypad')"
            class="rounded-full"
            :variant="tastiera ? 'solid' : 'subtle'"
            :tooltip="tastiera ? __('Hide the keypad') : __('Keypad')"
            :aria-pressed="tastiera"
            :icon="DialpadIcon"
            @click="apriLaTastiera"
          />
          <Button
            :aria-label="__('Add a Note')"
            class="cursor-pointer rounded-full"
            :tooltip="__('Add a Note')"
            :icon="NoteIcon"
            @click="openNoteModal"
          />
          <Button
            :aria-label="__('Hang Up')"
            class="rounded-full bg-surface-red-7 hover:bg-surface-red-8 text-ink-base"
            :tooltip="__('Hang Up')"
            @click="hangUpCall"
          >
            <template #icon>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
        <div v-else-if="scelta" />
        <div v-else-if="calling || callStatus == 'initiating'">
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Cancel')"
            class="rounded-lg text-ink-base"
            @click="cancelCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
        <div v-else class="flex gap-2">
          <Button
            size="md"
            variant="solid"
            theme="green"
            :label="__('Accept')"
            class="rounded-lg text-ink-base"
            :iconLeft="PhoneIcon"
            @click="acceptIncomingCall"
          />
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="__('Reject')"
            class="rounded-lg text-ink-base"
            @click="rejectIncomingCall"
          >
            <template #prefix>
              <PhoneIcon class="rotate-[135deg]" />
            </template>
          </Button>
        </div>
      </div>
    </div>
  </div>
  <!-- the bar opens the call from the name, a button stretched over it
       (.riga-stesa): a div with a click reached no key. The call's buttons
       come after it and are drawn over it -->
  <div
    v-show="showSmallCallWindow"
    class="relative ml-2 flex select-none items-center justify-between gap-3 rounded-lg bg-surface-gray-10 px-2 py-[7px] text-base text-ink-gray-2"
    v-bind="$attrs"
  >
    <div class="flex items-center gap-2">
      <Avatar
        v-if="contact?.image"
        :image="contact.image"
        :label="contact.full_name"
        class="relative flex !h-5 !w-5 items-center justify-center"
      />
      <button
        ref="espandi"
        type="button"
        class="riga-stesa max-w-[120px] truncate text-left after:rounded-lg"
        @click="toggleCallWindow"
      >
        {{ nomeDiChi }}
        <span class="sr-only">{{ __('Show the call') }}</span>
      </button>
    </div>
    <div v-if="onCall" class="flex items-center gap-2">
      <div class="my-1 min-w-[40px] text-center">
        {{ counterUp?.updatedTime }}
      </div>
      <Button
        :aria-label="__('Hang Up')"
        variant="solid"
        theme="red"
        class="relative !h-6 !w-6 rounded-full text-ink-base"
        @click.stop="hangUpCall"
      >
        <template #icon>
          <PhoneIcon class="rotate-[135deg]" />
        </template>
      </Button>
    </div>
    <div
      v-else-if="calling || callStatus == 'initiating'"
      class="flex items-center gap-3"
    >
      <div class="my-1">
        {{ callStatus == 'ringing' ? __('Ringing...') : __('Calling...') }}
      </div>
      <Button
        :aria-label="__('Hang Up')"
        variant="solid"
        theme="red"
        class="relative !h-6 !w-6 rounded-full text-ink-base"
        @click.stop="cancelCall"
      >
        <template #icon>
          <PhoneIcon class="rotate-[135deg]" />
        </template>
      </Button>
    </div>
    <div v-else class="flex items-center gap-2">
      <Button
        :aria-label="__('Accept Call')"
        variant="solid"
        theme="green"
        class="pulse relative !h-6 !w-6 rounded-full animate-pulse text-ink-base motion-reduce:animate-none"
        :tooltip="__('Accept Call')"
        :icon="PhoneIcon"
        @click.stop="acceptIncomingCall"
      />
      <Button
        :aria-label="__('Reject Call')"
        variant="solid"
        theme="red"
        class="relative !h-6 !w-6 rounded-full text-ink-base"
        :tooltip="__('Reject Call')"
        @click.stop="rejectIncomingCall"
      >
        <template #icon>
          <PhoneIcon class="rotate-[135deg]" />
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup>
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import DialpadIcon from '@/components/Icons/DialpadIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { useChiChiama } from '@/composables/chiChiama'
import { useDoctypeModal } from '@/composables/doctypeModal'
import {
  TASTI,
  bloccataInItalia,
  finestraOccupata,
  incertaInItalia,
  nuovaChiamata,
  numeroIniziale,
  siSceglie,
} from '@/utils/chiamate'
import {
  useDraggable,
  useEventListener,
  useResizeObserver,
  useWindowSize,
} from '@vueuse/core'
import { useTelemetry } from 'frappe-ui/frappe'
import { Avatar, call, toast } from 'frappe-ui'
import { computed, nextTick, ref } from 'vue'

const { capture } = useTelemetry()

let device = ''
let log = ref('Connecting...')
let _call = null
// each call going out is an attempt: one cancelled, or overtaken by another,
// while Twilio was still connecting it is hung up as soon as it exists
let tentativo = 0
// the calls ringing here behind the one the window shows, first come first:
// ignoring any of them stops the one tone Twilio plays for all
let inAttesa = []

let showCallPopup = ref(false)
let showSmallCallWindow = ref(false)
let onCall = ref(false)
let calling = ref(false)
let muted = ref(false)
let callPopup = ref(null)
let counterUp = ref(null)
let callStatus = ref('')

// the number the call is about and who it is, asked again at every call and
// every change of the number: never the last call's caller
const {
  numero: phoneNumber,
  contatto: contact,
  nome: nomeDiChi,
  perIlNumero,
} = useChiChiama()

const { showModal } = useDoctypeModal()
const note = ref({
  name: '',
  title: '',
  content: '',
})

function openNoteModal() {
  showModal({
    name: note.value.name || null,
    doctype: 'CRM Call Log',
    title: 'Call Log',
    callbacks: {
      afterInsert: (n) => updateNote(n, true),
      afterUpdate: updateNote,
    },
  })
}

async function updateNote(_note, isInsert = false) {
  note.value = _note
  if (isInsert && _note.name) {
    await call('crm.integrations.api.add_note_to_call_log', {
      call_sid: _call.parameters.CallSid,
      note: _note,
    })
    capture('note_created')
  } else {
    capture('note_updated')
  }
}

const { width, height } = useWindowSize()

let { style, x, y } = useDraggable(callPopup, {
  initialValue: { x: width.value - 280, y: height.value - 310 },
  preventDefault: true,
})

// the popup stays on the screen as it grows: the numbers to choose, the
// warning, the keypad
useResizeObserver(callPopup, () => {
  const popup = callPopup.value
  if (!popup?.offsetHeight) return
  const margine = 8
  y.value = Math.max(
    margine,
    Math.min(y.value, height.value - popup.offsetHeight - margine),
  )
  x.value = Math.max(
    margine,
    Math.min(x.value, width.value - popup.offsetWidth - margine),
  )
})

// before a call: the numbers it may show, the one chosen, the called country
const scelta = ref(false)
const numeri = ref([])
const mostrato = ref('')
const paeseChiamato = ref('')
const bloccata = computed(() =>
  bloccataInItalia(numeri.value, mostrato.value, paeseChiamato.value),
)
const incerta = computed(() =>
  incertaInItalia(numeri.value, mostrato.value, paeseChiamato.value),
)
const avvisoAgcom = computed(() => {
  if (bloccata.value)
    return siSceglie(numeri.value)
      ? __(
          'Calls to Italy showing an Italian mobile have been blocked since November 2025: choose a landline.',
        )
      : __(
          'Calls to Italy showing an Italian mobile have been blocked since November 2025: ask the manager for a landline.',
        )
  if (incerta.value)
    return __(
      'This number is only verified in Twilio: in Italy the call may arrive without it, as the operators allow since August 2025.',
    )
  return ''
})

// the number shown last, remembered in this browser only
const RICORDATO = 'dottorcloud:numero-da-mostrare'

function ricordato() {
  try {
    return localStorage.getItem(RICORDATO) || ''
  } catch {
    return ''
  }
}

function ricorda(numero) {
  try {
    if (numero) localStorage.setItem(RICORDATO, numero)
  } catch {
    // a browser that keeps nothing asks again next time
  }
}

// during the call: the keypad and what was pressed
const tastiera = ref(false)
const cifre = ref('')

function apriLaTastiera() {
  tastiera.value = !tastiera.value
}

function premi(tasto) {
  if (!_call) return
  _call.sendDigits(tasto)
  cifre.value += tasto
}

// what a call leaves behind: the keypad, what was pressed, the country called
function aChiamataFinita() {
  tastiera.value = false
  cifre.value = ''
  paeseChiamato.value = ''
}

async function startupClient() {
  log.value = 'Requesting Access Token...'

  try {
    const data = await call('crm.integrations.twilio.api.generate_access_token')
    // no key yet (not connected), or no line of one's own: no phone here
    if (!data?.token) {
      log.value = data?.detail || 'No access token.'
      return
    }
    log.value = 'Got a token.'
    await intitializeDevice(data.token)
  } catch (err) {
    log.value = 'An error occurred. ' + err.message
  }
}

async function intitializeDevice(token) {
  // the voice SDK comes once there is a line to call with: imported at the top
  // it was in every page's first download, for those without a phone too
  const { Device } = await import('@twilio/voice-sdk')
  device = new Device(token, {
    codecPreferences: ['opus', 'pcmu'],
    fakeLocalDTMF: true,
    enableRingingState: true,
  })

  addDeviceListeners()

  device.register()
}

function addDeviceListeners() {
  device.on('registered', () => {
    log.value = 'Ready to make and receive calls!'
  })

  device.on('unregistered', () => {
    log.value = 'Logged out'
  })

  device.on('error', (error) => {
    log.value = 'Twilio.Device Error: ' + error.message
  })

  device.on('incoming', handleIncomingCall)

  device.on('tokenWillExpire', async () => {
    const data = await call('crm.integrations.twilio.api.generate_access_token')
    device.updateToken(data.token)
  })
}

function toggleMute() {
  if (_call.isMuted()) {
    _call.mute(false)
    muted.value = false
  } else {
    _call.mute()
    muted.value = true
  }
}

function handleIncomingCall(call) {
  // one call at a time: the window keeps the call it shows, or the one being
  // placed
  const decisione = nuovaChiamata(
    _call,
    callStatus.value,
    call,
    _call?.status() === 'pending',
  )
  // a call on, or going out: this one rings on the centre's other phones - as
  // the SDK leaves an invite while a call is on
  if (decisione === 'ignora') {
    call.ignore()
    return
  }
  // the call shown still rings: this one waits behind it, ringing too
  if (decisione === 'aspetta') {
    aspetta(call)
    return
  }
  log.value = `Incoming call from ${call.parameters.From}`
  perIlNumero(call.parameters.From)
  // a call coming in takes the popup from a call not yet made
  scelta.value = false

  showCallPopup.value = true
  _call = call

  // add event listener to call object
  const finita = () => handleDisconnectedIncomingCall(call)
  call.on('cancel', finita)
  call.on('disconnect', finita)
  call.on('reject', finita)
}

// a call waiting leaves the line when it stops ringing here: its caller hung
// up, or a colleague answered it
function aspetta(chiamata) {
  inAttesa.push(chiamata)
  const togli = () => {
    inAttesa = inAttesa.filter((c) => c !== chiamata)
  }
  chiamata.on('cancel', togli)
  chiamata.on('reject', togli)
  chiamata.on('disconnect', togli)
}

async function acceptIncomingCall() {
  log.value = 'Accepted incoming call.'
  onCall.value = true
  // the calls waiting ring on the centre's other phones: here the tone stops,
  // as the SDK stops it at the answer
  const lasciate = inAttesa
  inAttesa = []
  for (const chiamata of lasciate) chiamata.ignore()
  await _call.accept()
  counterUp.value.start()
}

function rejectIncomingCall() {
  log.value = 'Rejected incoming call'
  showCallPopup.value = false
  showSmallCallWindow.value = false

  callStatus.value = ''
  muted.value = false
  // its 'reject' empties the window, and gives it to a call waiting
  _call.reject()
}

function hangUpCall() {
  _call.disconnect()
  log.value = 'Hanging up incoming call'
  onCall.value = false
  callStatus.value = ''
  muted.value = false
  aChiamataFinita()
  note.value = {
    name: '',
    title: '',
    content: '',
  }
  counterUp.value.stop()
}

function handleDisconnectedIncomingCall(chiamata) {
  // a call the window no longer shows closes nothing
  if (chiamata !== _call) return
  log.value = `Call ended from handle disconnected Incoming call.`
  showCallPopup.value = false
  showSmallCallWindow.value = false
  _call = null
  muted.value = false
  onCall.value = false
  aChiamataFinita()
  counterUp.value.stop()
  // ended unanswered: the first call still ringing behind it is shown, the one
  // whose tone sounds
  inAttesa = inAttesa.filter((c) => c.status() === 'pending')
  const prossima = inAttesa.shift()
  if (prossima) handleIncomingCall(prossima)
}

async function makeOutgoingCall(number) {
  if (!device) {
    log.value = 'Unable to make call.'
    toast.error(__('The phone is not ready yet: try again in a moment.'))
    return
  }
  if (finestraOccupata(_call, callStatus.value)) {
    toast.error(__('Finish the call in progress first.'))
    return
  }

  // the server says whether the call may go, and which numbers it may show
  let dati, esito
  try {
    ;[dati, esito] = await Promise.all([
      call('crm.telephony.uscita.get_outbound_numbers'),
      call('crm.telephony.uscita.check_number', { number }),
    ])
  } catch (error) {
    toast.error(
      error.messages?.[0] || __('The call could not start: try again.'),
    )
    return
  }
  // a call came in, or another started going out, while the server answered:
  // it keeps the window and its name
  if (finestraOccupata(_call, callStatus.value)) {
    toast.error(__('Finish the call in progress first.'))
    return
  }
  if (!esito.ok) {
    toast.error(esito.reason)
    return
  }

  perIlNumero(number)
  numeri.value = dati.numbers || []
  paeseChiamato.value = esito.country || ''
  mostrato.value = numeroIniziale(numeri.value, ricordato())

  if (siSceglie(numeri.value)) {
    scelta.value = true
    showCallPopup.value = true
    showSmallCallWindow.value = false
    return
  }
  connetti(number)
}

function chiama() {
  scelta.value = false
  ricorda(mostrato.value)
  connetti(phoneNumber.value)
}

function annullaLaScelta() {
  scelta.value = false
  showCallPopup.value = false
  perIlNumero('')
}

// while the number is asked: Enter calls, Escape gives up - one key per call in
// a dialer session; a field being written in keeps its keys
useEventListener(
  window,
  'keydown',
  (evento) => {
    if (!scelta.value || evento.isComposing) return
    if (evento.target?.closest?.('input, textarea, select, [contenteditable]'))
      return
    if (evento.key === 'Enter') {
      evento.preventDefault()
      evento.stopPropagation()
      chiama()
    } else if (evento.key === 'Escape') {
      evento.preventDefault()
      annullaLaScelta()
    }
  },
  { capture: true },
)

async function connetti(number) {
  log.value = `Attempting to call ${number} ...`
  // the popup says the call is starting while Twilio connects it
  callStatus.value = 'initiating'
  showCallPopup.value = true
  const questo = ++tentativo

  try {
    const params = { To: number }
    if (mostrato.value) params.CallFrom = mostrato.value
    const nuova = await device.connect({ params })
    if (questo !== tentativo) {
      nuova.disconnect()
      return
    }
    _call = nuova

    capture('make_outgoing_call')

    _call.on('messageReceived', (message) => {
      let info = message.content
      callStatus.value = info.CallStatus

      log.value = `Call status: ${info.CallStatus}`

      if (info.CallStatus == 'in-progress') {
        log.value = `Call in progress.`
        calling.value = false
        onCall.value = true
        counterUp.value.start()
      }
    })

    _call.on('accept', () => {
      log.value = `Initiated call!`
      showCallPopup.value = true
      calling.value = true
      onCall.value = false
    })
    _call.on('disconnect', () => {
      log.value = `Call ended from makeOutgoing call disconnect.`
      calling.value = false
      onCall.value = false
      showCallPopup.value = false
      showSmallCallWindow.value = false
      _call = null
      callStatus.value = ''
      muted.value = false
      aChiamataFinita()
      counterUp.value.stop()
      note.value = {
        name: '',
        title: '',
        content: '',
      }
    })
    _call.on('cancel', () => {
      log.value = `Call ended from makeOutgoing call cancel.`
      calling.value = false
      onCall.value = false
      showCallPopup.value = false
      showSmallCallWindow.value = false
      _call = null
      callStatus.value = ''
      muted.value = false
      aChiamataFinita()
      note.value = {
        name: '',
        title: '',
        content: '',
      }
      counterUp.value.stop()
    })
  } catch (error) {
    log.value = `Could not connect call: ${error.message}`
    // an attempt given up already has nothing left on the screen
    if (questo !== tentativo) return
    callStatus.value = ''
    showCallPopup.value = false
    aChiamataFinita()
    toast.error(__('The call could not start: try again.'))
  }
}

function cancelCall() {
  if (_call) _call.disconnect()
  else tentativo += 1
  showCallPopup.value = false
  showSmallCallWindow.value = false
  calling.value = false
  onCall.value = false
  callStatus.value = ''
  muted.value = false
  aChiamataFinita()
  note.value = {
    name: '',
    title: '',
    content: '',
  }
}

// the popup and the bar take each other's place: the keyboard goes with them,
// or it was left on a button no longer drawn
const riduci = ref(null)
const espandi = ref(null)

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value
  showSmallCallWindow.value = !showSmallCallWindow.value
  nextTick(() => (showCallPopup.value ? riduci : espandi).value?.focus())
}

defineExpose({ makeOutgoingCall, setup: startupClient })
</script>

<style scoped>
.pulse::before {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
}

.pulse::after {
  content: '';
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

/* the rings stand still for whoever asked for less motion: they went on as
   long as a call rang */
@media (prefers-reduced-motion: reduce) {
  .pulse::before,
  .pulse::after {
    animation: none;
  }
}
</style>
