import { createResource } from 'frappe-ui'

let meta = null

/**
 * What booking offers here — services, professionals, rooms, price lists —
 * fetched once and shared: the calendar needs all of it, and a person's page
 * needs to know whether there is anything to book at all before it offers to.
 */
export function useSchedulerMeta() {
  meta ||= createResource({
    url: 'crm.api.appointments.get_scheduler_meta',
    cache: 'crm-scheduler-meta',
    auto: true,
  })
  return meta
}
