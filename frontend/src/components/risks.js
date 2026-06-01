/**
 * risks.js — Risk Items, Evidence Items, Assessment Findings, Action Items UI.
 *
 * Each section renders as a collapsible table with inline Create / Edit / Delete.
 * Uses simple prompt()-based forms to keep the UI lightweight (full form modal is Slice 7+).
 */
import { api } from '../api.js'
import { showError } from '../utils.js'

function badge(v) {
  if (!v) return ''
  const cls = ['Low', 'Closed', 'Complete', 'Pass', '0'].includes(v) ? 'ok'
    : ['Critical', 'High', 'Open', 'Failed', 'Missing'].includes(v) ? 'risk'
    : 'warn'
  return `<span class="tag ${cls}">${v}</span>`
}

// ─────────────────────────────────────────────────────────────────────────────
// Risks
// ─────────────────────────────────────────────────────────────────────────────

export async function renderRisks(containerId, projectId) {
  const container = document.getElementById(containerId)
  if (!container) return
  container.innerHTML = '<div class="loading">Loading risks…</div>'

  let items = []
  try { items = await api.getRisks(projectId) } catch (e) { showError(e.message); container.innerHTML = ''; return }

  container.innerHTML = `
    <div class="row" style="margin-bottom:8px">
      <button class="soft" style="font-size:11px" id="addRisk_${projectId}">+ Add Risk</button>
    </div>
    ${items.length
      ? `<div class="tableWrap"><table>
          <thead><tr><th>ID</th><th>Title</th><th>Level</th><th>Status</th><th>Aspects</th><th>Owner</th><th></th></tr></thead>
          <tbody>${items.map(r => `
            <tr>
              <td style="font-size:10px;color:#64748b">${r.risk_id}</td>
              <td>${r.title}</td>
              <td>${badge(r.risk_level)}</td>
              <td>${badge(r.status)}</td>
              <td>${(r.quality_aspects ?? []).map(a => `<span class="tag" style="font-size:9px">${a}</span>`).join('')}</td>
              <td style="font-size:11px">${r.owner ?? '—'}</td>
              <td>
                <button class="soft" style="font-size:10px" data-edit-risk="${r.id}">Edit status</button>
                <button class="soft" style="font-size:10px;color:#ef4444" data-del-risk="${r.id}">Del</button>
              </td>
            </tr>
          `).join('')}</tbody>
        </table></div>`
      : '<p style="color:#94a3b8;font-size:12px">No risks recorded.</p>'
    }
  `

  document.getElementById(`addRisk_${projectId}`)?.addEventListener('click', () =>
    _addRisk(projectId, containerId)
  )
  container.querySelectorAll('[data-edit-risk]').forEach(btn =>
    btn.addEventListener('click', () => _editRiskStatus(projectId, btn.dataset.editRisk, containerId, items))
  )
  container.querySelectorAll('[data-del-risk]').forEach(btn =>
    btn.addEventListener('click', async () => {
      if (!confirm('Delete risk?')) return
      try { await api.deleteRisk(projectId, btn.dataset.delRisk); await renderRisks(containerId, projectId) }
      catch (e) { showError(e.message) }
    })
  )
}

async function _addRisk(projectId, containerId) {
  const title = prompt('Risk title:')
  if (!title) return
  const riskId = prompt('Risk ID (e.g. RISK-001):', `RISK-${Date.now().toString().slice(-4)}`)
  if (!riskId) return
  const desc = prompt('Description:', '') ?? ''
  const sev = prompt('Severity (Critical/High/Medium/Low):', 'Medium')
  const lik = prompt('Likelihood (Critical/High/Medium/Low):', 'Medium')

  try {
    await api.createRisk(projectId, {
      risk_id: riskId, title, description: desc,
      severity: sev ?? 'Medium', likelihood: lik ?? 'Medium',
    })
    await renderRisks(containerId, projectId)
  } catch (e) { showError(e.message) }
}

async function _editRiskStatus(projectId, riskId, containerId, items) {
  const risk = items.find(r => r.id === riskId)
  if (!risk) return
  const newStatus = prompt('New status (Open/Mitigated/Accepted/Closed):', risk.status)
  if (!newStatus) return
  try {
    await api.updateRisk(projectId, riskId, { status: newStatus })
    await renderRisks(containerId, projectId)
  } catch (e) { showError(e.message) }
}

// ─────────────────────────────────────────────────────────────────────────────
// Evidence Items
// ─────────────────────────────────────────────────────────────────────────────

export async function renderEvidence(containerId, projectId) {
  const container = document.getElementById(containerId)
  if (!container) return
  container.innerHTML = '<div class="loading">Loading evidence…</div>'

  let items = []
  try { items = await api.getEvidence(projectId) } catch (e) { showError(e.message); container.innerHTML = ''; return }

  container.innerHTML = `
    <div class="row" style="margin-bottom:8px">
      <button class="soft" style="font-size:11px" id="addEv_${projectId}">+ Add Evidence</button>
    </div>
    ${items.length
      ? `<div class="tableWrap"><table>
          <thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Status</th><th>Link</th><th></th></tr></thead>
          <tbody>${items.map(e => `
            <tr>
              <td style="font-size:10px;color:#64748b">${e.evidence_id}</td>
              <td>${e.title}</td>
              <td style="font-size:11px">${e.evidence_type ?? '—'}</td>
              <td>${badge(e.status)}</td>
              <td style="font-size:11px">${e.source_link ? `<a href="${e.source_link}" target="_blank" style="color:#2563eb">Link</a>` : '—'}</td>
              <td>
                <button class="soft" style="font-size:10px" data-edit-ev="${e.id}">Edit</button>
                <button class="soft" style="font-size:10px;color:#ef4444" data-del-ev="${e.id}">Del</button>
              </td>
            </tr>
          `).join('')}</tbody>
        </table></div>`
      : '<p style="color:#94a3b8;font-size:12px">No evidence items.</p>'
    }
  `

  document.getElementById(`addEv_${projectId}`)?.addEventListener('click', () =>
    _addEvidence(projectId, containerId)
  )
  container.querySelectorAll('[data-edit-ev]').forEach(btn =>
    btn.addEventListener('click', () => _editEvidenceStatus(projectId, btn.dataset.editEv, containerId, items))
  )
  container.querySelectorAll('[data-del-ev]').forEach(btn =>
    btn.addEventListener('click', async () => {
      if (!confirm('Delete evidence item?')) return
      try { await api.deleteEvidence(projectId, btn.dataset.delEv); await renderEvidence(containerId, projectId) }
      catch (e) { showError(e.message) }
    })
  )
}

async function _addEvidence(projectId, containerId) {
  const title = prompt('Evidence title:')
  if (!title) return
  const evId = prompt('Evidence ID (e.g. EV-001):', `EV-${Date.now().toString().slice(-4)}`)
  if (!evId) return
  const evType = prompt('Type (Test Report / Review Record / Analysis / Other):', 'Test Report')
  const link = prompt('Source link (URL or reference):', '') ?? ''

  try {
    await api.createEvidence(projectId, {
      evidence_id: evId, title,
      evidence_type: evType ?? 'Test Report',
      status: 'Missing',
      source_link: link || null,
    })
    await renderEvidence(containerId, projectId)
  } catch (e) { showError(e.message) }
}

async function _editEvidenceStatus(projectId, evId, containerId, items) {
  const ev = items.find(e => e.id === evId)
  if (!ev) return
  const newStatus = prompt('New status (Complete/Partial/Missing/Failed):', ev.status)
  if (!newStatus) return
  try {
    await api.updateEvidence(projectId, evId, { status: newStatus })
    await renderEvidence(containerId, projectId)
  } catch (e) { showError(e.message) }
}

// ─────────────────────────────────────────────────────────────────────────────
// Assessment Findings
// ─────────────────────────────────────────────────────────────────────────────

export async function renderFindings(containerId, projectId) {
  const container = document.getElementById(containerId)
  if (!container) return
  container.innerHTML = '<div class="loading">Loading findings…</div>'

  let items = []
  try { items = await api.getFindings(projectId) } catch (e) { showError(e.message); container.innerHTML = ''; return }

  container.innerHTML = `
    <div class="row" style="margin-bottom:8px">
      <button class="soft" style="font-size:11px" id="addFinding_${projectId}">+ Add Finding</button>
    </div>
    ${items.length
      ? `<div class="tableWrap"><table>
          <thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Severity</th><th>Status</th><th>Owner</th><th></th></tr></thead>
          <tbody>${items.map(f => `
            <tr>
              <td style="font-size:10px;color:#64748b">${f.finding_id}</td>
              <td>${f.title}</td>
              <td style="font-size:11px">${f.finding_type ?? '—'}</td>
              <td>${badge(f.severity)}</td>
              <td>${badge(f.status)}</td>
              <td style="font-size:11px">${f.owner ?? '—'}</td>
              <td>
                <button class="soft" style="font-size:10px" data-edit-finding="${f.id}">Edit</button>
                <button class="soft" style="font-size:10px;color:#ef4444" data-del-finding="${f.id}">Del</button>
              </td>
            </tr>
          `).join('')}</tbody>
        </table></div>`
      : '<p style="color:#94a3b8;font-size:12px">No findings recorded.</p>'
    }
  `

  document.getElementById(`addFinding_${projectId}`)?.addEventListener('click', () =>
    _addFinding(projectId, containerId)
  )
  container.querySelectorAll('[data-edit-finding]').forEach(btn =>
    btn.addEventListener('click', () => _editFindingStatus(projectId, btn.dataset.editFinding, containerId, items))
  )
  container.querySelectorAll('[data-del-finding]').forEach(btn =>
    btn.addEventListener('click', async () => {
      if (!confirm('Delete finding?')) return
      try { await api.deleteFinding(projectId, btn.dataset.delFinding); await renderFindings(containerId, projectId) }
      catch (e) { showError(e.message) }
    })
  )
}

async function _addFinding(projectId, containerId) {
  const title = prompt('Finding title:')
  if (!title) return
  const fId = prompt('Finding ID (e.g. AF-001):', `AF-${Date.now().toString().slice(-4)}`)
  if (!fId) return
  const desc = prompt('Description:', '') ?? ''
  const fType = prompt('Type (Gap/Non-conformance/Observation):', 'Gap') ?? 'Gap'
  const sev = prompt('Severity (Critical/High/Medium/Low):', 'Low') ?? 'Low'

  try {
    await api.createFinding(projectId, {
      finding_id: fId, title, description: desc,
      finding_type: fType, severity: sev,
    })
    await renderFindings(containerId, projectId)
  } catch (e) { showError(e.message) }
}

async function _editFindingStatus(projectId, findingId, containerId, items) {
  const f = items.find(x => x.id === findingId)
  if (!f) return
  const newStatus = prompt('New status (Open/In Progress/Resolved/Closed):', f.status)
  if (!newStatus) return
  try {
    await api.updateFinding(projectId, findingId, { status: newStatus })
    await renderFindings(containerId, projectId)
  } catch (e) { showError(e.message) }
}

// ─────────────────────────────────────────────────────────────────────────────
// Action Items
// ─────────────────────────────────────────────────────────────────────────────

export async function renderActions(containerId, projectId) {
  const container = document.getElementById(containerId)
  if (!container) return
  container.innerHTML = '<div class="loading">Loading actions…</div>'

  let items = []
  try { items = await api.getActions(projectId) } catch (e) { showError(e.message); container.innerHTML = ''; return }

  container.innerHTML = `
    <div class="row" style="margin-bottom:8px">
      <button class="soft" style="font-size:11px" id="addAction_${projectId}">+ Add Action</button>
    </div>
    ${items.length
      ? `<div class="tableWrap"><table>
          <thead><tr><th>ID</th><th>Title</th><th>Priority</th><th>Status</th><th>Owner</th><th>Due</th><th></th></tr></thead>
          <tbody>${items.map(a => `
            <tr>
              <td style="font-size:10px;color:#64748b">${a.action_id}</td>
              <td>${a.title}</td>
              <td>${badge(a.priority)}</td>
              <td>${badge(a.status)}</td>
              <td style="font-size:11px">${a.owner ?? '—'}</td>
              <td style="font-size:11px">${a.due_date ?? '—'}</td>
              <td>
                <button class="soft" style="font-size:10px" data-edit-action="${a.id}">Edit</button>
                <button class="soft" style="font-size:10px;color:#ef4444" data-del-action="${a.id}">Del</button>
              </td>
            </tr>
          `).join('')}</tbody>
        </table></div>`
      : '<p style="color:#94a3b8;font-size:12px">No action items.</p>'
    }
  `

  document.getElementById(`addAction_${projectId}`)?.addEventListener('click', () =>
    _addAction(projectId, containerId)
  )
  container.querySelectorAll('[data-edit-action]').forEach(btn =>
    btn.addEventListener('click', () => _editActionStatus(projectId, btn.dataset.editAction, containerId, items))
  )
  container.querySelectorAll('[data-del-action]').forEach(btn =>
    btn.addEventListener('click', async () => {
      if (!confirm('Delete action item?')) return
      try { await api.deleteAction(projectId, btn.dataset.delAction); await renderActions(containerId, projectId) }
      catch (e) { showError(e.message) }
    })
  )
}

async function _addAction(projectId, containerId) {
  const title = prompt('Action title:')
  if (!title) return
  const aId = prompt('Action ID (e.g. AI-001):', `AI-${Date.now().toString().slice(-4)}`)
  if (!aId) return
  const priority = prompt('Priority (Critical/High/Medium/Low):', 'Medium') ?? 'Medium'
  const owner = prompt('Owner:', '') ?? ''
  const due = prompt('Due date (YYYY-MM-DD):', '') ?? ''

  try {
    await api.createAction(projectId, {
      action_id: aId, title, priority,
      owner: owner || null,
      due_date: due || null,
    })
    await renderActions(containerId, projectId)
  } catch (e) { showError(e.message) }
}

async function _editActionStatus(projectId, actionId, containerId, items) {
  const a = items.find(x => x.id === actionId)
  if (!a) return
  const newStatus = prompt('New status (Open/In Progress/Closed):', a.status)
  if (!newStatus) return
  try {
    await api.updateAction(projectId, actionId, { status: newStatus })
    await renderActions(containerId, projectId)
  } catch (e) { showError(e.message) }
}
