const $ = id => document.getElementById(id)

export function showError(msg) {
  const banner = $('errorBanner')
  if (!banner) return
  banner.textContent = msg
  banner.classList.remove('hidden')
  setTimeout(() => banner.classList.add('hidden'), 6000)
}
