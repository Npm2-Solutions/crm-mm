// How long the Facebook connection has left.
//
// A long-lived token lasts about sixty days and nothing renews it by itself:
// past that date the ad spend and the lead-quality feedback stop without a
// word, while the leads keep arriving on the Pages' own tokens — so nothing
// looks broken. The screen warns a little before, when reconnecting is still a
// click and not an investigation.
export const EXPIRY_WARNING_DAYS = 10

const DAY = 24 * 60 * 60 * 1000

/**
 * `expiresAt` as the server sends it ("2026-11-20 10:00:00.123456"), read as a
 * date, and whether it is close enough to say so. `null` when there is no date
 * — a token without one does not expire.
 */
export function tokenExpiry(expiresAt, now = new Date()) {
  if (!expiresAt) return null
  const when = new Date(String(expiresAt).slice(0, 19).replace(' ', 'T'))
  if (Number.isNaN(when.getTime())) return null
  const expired = when <= now
  const days = Math.floor((when - now) / DAY)
  return {
    date: when,
    days,
    expired,
    soon: !expired && days < EXPIRY_WARNING_DAYS,
  }
}
