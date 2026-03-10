const API_BASE = ''

export async function getStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`)
    return await res.json()
  } catch {
    return { running: false, total_screenshots: 0, pending_ocr: 0 }
  }
}

export async function getConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/config`)
    return await res.json()
  } catch {
    return {}
  }
}

export async function setConfig(config) {
  try {
    const res = await fetch(`${API_BASE}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })
    return await res.json()
  } catch (e) {
    return { success: false, message: e.message }
  }
}

export async function getScreenshots(page = 1, perPage = 50, search = '') {
  try {
    const params = new URLSearchParams({ page, per_page: perPage })
    if (search) params.append('search', search)
    const res = await fetch(`${API_BASE}/api/screenshots?${params}`)
    return await res.json()
  } catch {
    return []
  }
}

export function getScreenshotUrl(path) {
  if (!path) return ''
  // 将绝对路径转换为相对路径
  const relativePath = path.replace(/\\/g, '/').split('screenshots/').pop()
  return `${API_BASE}/screenshots/${relativePath}`
}
