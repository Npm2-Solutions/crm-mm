// Modifications copyright (c) 2026, NPM2 Solutions Srl

import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { useEvent } from '@/composables/event'
import { dayjs } from 'frappe-ui'
import isBetween from 'dayjs/plugin/isBetween'
import { useStorage } from '@vueuse/core'
import { getUserSettings, useUserSettings } from '@/data/userSettings'
import {
  avvisiDaTenere,
  eDellUtente,
  soloIlNecessario,
} from '@/utils/avvisiDegliEventi'
import { adessoDelCentro, oraDelCentro } from '@/utils/scheduler'
import { ref, computed, onUnmounted, onMounted } from 'vue'

dayjs.extend(isBetween)

export const useEventNotifications = () => {
  const { user } = sessionStore()

  return useEvent({
    filters: {
      status: 'Open',
      owner: user,
      ends_on: ['>=', dayjs().toISOString()],
    },
    notifications: false,
  })
}

// The reminders that came, kept in this browser between pages: one list for
// whoever signs in on it, so it holds only the session's, only what the popup
// draws - never an event's description, an appointment's notes on its calendar
// copy - and nothing done or over (utils/avvisiDegliEventi.js). Its key stays:
// signing out clears it.
const eventNotificationAlerts = useStorage('eventNotificationAlerts', [])

// The events the session put away, as their settings keep them: one list for
// the popup and for the listener, so one closed in the popup does not come back
// with the next reminder of it.
const completedEvents = ref([])

export const useEventNotificationAlert = () => {
  const session = sessionStore()
  const { getUser } = usersStore()
  const { save: saveUserSettings } = useUserSettings()

  function cheCosaTenere() {
    return {
      utente: session.user,
      completati: completedEvents.value,
      adesso: oraDelCentro(adessoDelCentro()),
    }
  }

  // The list read again, as it may stay: when it is read, when the settings
  // come, every five minutes
  function tieniSoloIlNecessario() {
    const prima = eventNotificationAlerts.value
    const dopo = avvisiDaTenere(prima, cheCosaTenere())
    if (JSON.stringify(dopo) !== JSON.stringify(prima)) {
      eventNotificationAlerts.value = dopo
    }
  }

  tieniSoloIlNecessario()

  // Load user settings on initialization
  const loadNotificationSettings = async () => {
    try {
      const settings = await getUserSettings('Event', 'notifications')
      if (settings) {
        completedEvents.value = settings.completedEvents || []
      }
      tieniSoloIlNecessario()
    } catch (error) {
      console.error('Error loading notification settings:', error)
    }
  }

  // Save completed events to user settings
  const saveNotificationSettings = async () => {
    try {
      await saveUserSettings('Event', 'notifications', {
        completedEvents: completedEvents.value,
        lastUpdated: dayjs().format('YYYY-MM-DD HH:mm:ss'),
      })
    } catch (error) {
      console.error('Error saving notification settings:', error)
    }
  }

  // Check if event has already been completed/acknowledged
  const isEventCompleted = (eventId) => completedEvents.value.includes(eventId)

  // The session's alerts still to show: neither put away nor over
  const activeAlerts = computed(() =>
    avvisiDaTenere(eventNotificationAlerts.value, cheCosaTenere()),
  )

  function handleEventNotification(event) {
    const utente = session.user
    if (!utente || !event?.event_name) return
    // the server sends each their own: an event the session neither owns nor
    // takes part in is not shown, nor kept
    if (!eDellUtente(event, utente, getUser(utente)?.email)) return
    if (isEventCompleted(event.event_name)) return

    addEventNotificationAlert(event)
  }

  function addEventNotificationAlert(data) {
    const utente = session.user
    if (!utente || !data?.event_name) return
    // Don't add if already exists and not completed
    const existingAlert = eventNotificationAlerts.value.find(
      (alert) =>
        alert.id === data.event_name &&
        alert.utente === utente &&
        !alert.completed,
    )

    if (existingAlert) return

    eventNotificationAlerts.value.push({
      id: data.event_name,
      // whom it was taken for: the list is the browser's, not the user's
      utente,
      completed: false,
      notification: soloIlNecessario(data),
      createdAt: dayjs().toISOString(),
    })
  }

  async function completeEventNotificationAlert(id) {
    let alert = eventNotificationAlerts.value.find((a) => a.id === id)
    if (alert) {
      alert.completed = true
    }

    // Add to completed events in user settings
    if (!completedEvents.value.includes(id)) {
      completedEvents.value.push(id)
      await saveNotificationSettings()
    }
  }

  function removeCompletedEventNotificationAlerts() {
    eventNotificationAlerts.value = eventNotificationAlerts.value.filter(
      (alert) => !alert.completed,
    )
  }

  function clearAllEventNotificationAlerts() {
    eventNotificationAlerts.value = []
  }

  async function clearCompletedEvents() {
    completedEvents.value = []
    await saveNotificationSettings()
  }

  // An event over goes from the list: the server sends no reminder of it again,
  // so there is nothing to keep in the settings either
  function cleanupExpiredEventAlerts() {
    tieniSoloIlNecessario()
  }

  const cleanupInterval = setInterval(cleanupExpiredEventAlerts, 5 * 60 * 1000)

  onMounted(() => {
    loadNotificationSettings()
    cleanupExpiredEventAlerts()
  })

  onUnmounted(() => clearInterval(cleanupInterval))

  return {
    eventNotificationAlerts,
    activeAlerts,
    completedEvents,
    isEventCompleted,
    handleEventNotification,
    addEventNotificationAlert,
    completeEventNotificationAlert,
    removeCompletedEventNotificationAlerts,
    clearAllEventNotificationAlerts,
    clearCompletedEvents,
    cleanupExpiredEventAlerts,
    loadNotificationSettings,
    saveNotificationSettings,
  }
}
