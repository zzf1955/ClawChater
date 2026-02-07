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

// ============ 对话管理 API ============

export async function getConversations() {
  try {
    const res = await fetch(`${API_BASE}/api/conversations`)
    return await res.json()
  } catch (e) {
    return { conversations: [] }
  }
}

export async function createConversation(title = '新对话') {
  try {
    const res = await fetch(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    })
    return await res.json()
  } catch (e) {
    return { success: false, error: e.message }
  }
}

export async function deleteConversation(conversationId) {
  try {
    const res = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
      method: 'DELETE'
    })
    return await res.json()
  } catch (e) {
    return { success: false, error: e.message }
  }
}

export async function setActiveConversation(conversationId) {
  try {
    const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/active`, {
      method: 'POST'
    })
    return await res.json()
  } catch (e) {
    return { success: false, error: e.message }
  }
}

export async function getConversationMessages(conversationId) {
  try {
    const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`)
    return await res.json()
  } catch (e) {
    return { messages: [] }
  }
}

// ============ 聊天 API ============

export async function sendMessage(message, conversationId = null) {
  try {
    const body = { message }
    if (conversationId) body.conversation_id = conversationId
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    return await res.json()
  } catch (e) {
    return { error: e.message }
  }
}

export async function getAIMessages(sinceId = 0, conversationId = null) {
  try {
    let url = `${API_BASE}/api/ai/messages?since_id=${sinceId}`
    if (conversationId) url += `&conversation_id=${conversationId}`
    const res = await fetch(url)
    return await res.json()
  } catch (e) {
    return { messages: [], last_id: sinceId }
  }
}

export async function getAIHistory(limit = 50) {
  try {
    const res = await fetch(`${API_BASE}/api/ai/history?limit=${limit}`)
    return await res.json()
  } catch (e) {
    return { messages: [] }
  }
}

export async function getAILogs(limit = 100) {
  try {
    const res = await fetch(`${API_BASE}/api/ai/logs?limit=${limit}`)
    return await res.json()
  } catch (e) {
    return { logs: [] }
  }
}
