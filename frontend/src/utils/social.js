// A profile's platform, as its source brings it in: Meta brings Facebook Pages
// and their linked Instagram business accounts. A platform another source adds
// shows in grey until it has a colour here.
export const SOCIAL_PLATFORM_COLORS = {
  Facebook: '#1877F2',
  Instagram: '#E4405F',
}

export function platformColor(platform) {
  return SOCIAL_PLATFORM_COLORS[platform] || '#6b7280'
}

export function platformInitial(platform) {
  return (platform || '?')[0]
}
