/**
 * table.js — Trace chain management UI.
 *
 * Renders a collapsible tree:
 *   Scope Decision (Subcharacteristic)
 *     Quality Goal
 *       Quality Requirement → [Architecture Element]
 *         Sub-Quality Requirement → [Architecture Element]
 *         Test Case → Test Result
 *
 * Each node has inline Create / Edit / Delete controls.
 */
import { api } from '../api.js'
import { showError } from '../utils.js'

const $ = id => document.getElementById(id)

function statusBadge(v) {
  if (!v) return ''
  const cls = ['Pass', 'Complete', 'Low', 'Ready'].includes(v) ? 'ok'
    : ['Fail', 'Failed', 'High', 'Critical', 'Missing'].includes(v) ? 'risk'
    : 'warn'
  return `<span class="tag ${cls}">${v}</span>`
}

// ─── Public entry point ───────────────────────────────────────────────────────

/**
 * Render the full trace chain management panel into a container element.
 * @param {string} containerId  - DOM element ID to render into
 * @param {object} project      - full project object (includes scope[])
 * @param {object[]} archElems  - architecture elements for this project
 */
export async function renderTraceChain(containerId, project, archElems) {
  const container = $(containerId)
  if (!container) return

  container.innerHTML = '<div class="loading">Loading trace chain…</div>'

  try {
    // Build arch element lookup for dropdowns
    const aeMap = Object.fromEntries(archElems.map(ae => [ae.id, ae]))

    const scope = project.scope ?? []
    const included = scope.filter(d =>
      ['Applicable', 'Partially applicable', 'Deferred'].includes(d.applicability)
    )

    if (!included.length) {
      container.innerHTML = '<p style="color:#64748b;font-size:13px;padding:12px">No applicable scope items. Add scope decisions first.</p>'
      return
    }

    // Render each scope decision as a collapsible section
    container.innerHTML = included.map(d => `
      <div class="card section" style="margin-bottom:10px">
        <div class="projectHead" style="cursor:pointer" data-toggle="scope-${d.id}">
          <div>
            <b>${d.subchar_name ?? d.subchar_id}</b>
            <span class="tag" style="margin-left:8px">${d.applicability}</span>
          </div>
          <button class="soft" style="font-size:11px" data-add-goal="${d.id}" data-project="${project.id}" data-subchar="${d.subchar_id}">+ Goal</button>
        </div>
        <div id="scope-${d.id}" class="scope-body" style="margin-top:10px"></div>
      </div>
    `).join('')

    // Wire toggle + add goal buttons
    container.querySelectorAll('[data-toggle]').forEach(el => {
      el.addEventListener('click', e => {
        if (e.target.closest('button')) return  // don't toggle on button click
        const body = $(el.dataset.toggle)
        if (body) body.classList.toggle('hidden')
      })
    })

    container.querySelectorAll('[data-add-goal]').forEach(btn => {
      btn.addEventListener('click', () =>
        _openGoalForm(btn.dataset.project, btn.dataset.subchar, null, containerId, project, archElems)
      )
    })

    // Load goals for each scope decision
    await Promise.all(included.map(async d => {
      await _loadAndRenderGoals(`scope-${d.id}`, project.id, d.subchar_id, aeMap, containerId, project, archElems)
    }))

  } catch (err) {
    container.innerHTML = `<p class="error-banner">Failed to load trace chain: ${err.message}</p>`
  }
}

// ─── Goals ────────────────────────────────────────────────────────────────────

async function _loadAndRenderGoals(containerId, projectId, subcharId, aeMap, rootId, project, archElems) {
  const container = $(containerId)
  if (!container) return

  try {
    const goals = await api.getGoals(projectId, subcharId)
    _renderGoals(containerId, goals, projectId, subcharId, aeMap, rootId, project, archElems)
  } catch (err) {
    if (container) container.innerHTML = `<p style="color:#ef4444;font-size:12px">Error loading goals: ${err.message}</p>`
  }
}

function _renderGoals(containerId, goals, projectId, subcharId, aeMap, rootId, project, archElems) {
  const container = $(containerId)
  if (!container) return

  if (!goals.length) {
    container.innerHTML = '<p style="color:#94a3b8;font-size:12px;padding:4px">No goals yet.</p>'
    return
  }

  container.innerHTML = goals.map(g => `
    <div style="border-left:3px solid #4f46e5;padding-left:12px;margin-bottom:10px">
      <div class="row">
        <span style="font-size:13px;font-weight:700">🎯 ${g.goal_text}</span>
        <button class="soft" style="font-size:10px" data-edit-goal="${g.id}" data-project="${projectId}" data-subchar="${subcharId}">Edit</button>
        <button class="soft" style="font-size:10px;color:#ef4444" data-del-goal="${g.id}" data-project="${projectId}" data-subchar="${subcharId}">Delete</button>
        <button class="soft" style="font-size:10px" data-add-req="${g.id}" data-project="${projectId}" data-subchar="${subcharId}">+ Requirement</button>
      </div>
      <div id="goal-${g.id}" style="margin-top:8px"></div>
    </div>
  `).join('')

  goals.forEach(g => {
    const editBtn = container.querySelector(`[data-edit-goal="${g.id}"]`)
    const delBtn = container.querySelector(`[data-del-goal="${g.id}"]`)
    const addReqBtn = container.querySelector(`[data-add-req="${g.id}"]`)

    editBtn?.addEventListener('click', () =>
      _openGoalForm(projectId, subcharId, g, rootId, project, archElems)
    )
    delBtn?.addEventListener('click', async () => {
      if (!confirm(`Delete goal "${g.goal_text}"?`)) return
      try {
        await api.deleteGoal(projectId, subcharId, g.id)
        await _loadAndRenderGoals(containerId, projectId, subcharId, aeMap, rootId, project, archElems)
      } catch (err) { showError(err.message) }
    })
    addReqBtn?.addEventListener('click', () =>
      _openReqForm(projectId, subcharId, g.id, null, aeMap, rootId, project, archElems)
    )

    // Load requirements for this goal
    _loadAndRenderRequirements(`goal-${g.id}`, projectId, subcharId, g.id, aeMap, rootId, project, archElems)
  })
}

// ─── Requirements ─────────────────────────────────────────────────────────────

async function _loadAndRenderRequirements(containerId, projectId, subcharId, goalId, aeMap, rootId, project, archElems) {
  const container = $(containerId)
  if (!container) return
  try {
    const reqs = await api.getRequirements(projectId, subcharId, goalId)
    _renderRequirements(containerId, reqs, projectId, subcharId, goalId, aeMap, rootId, project, archElems)
  } catch (err) {
    if (container) container.innerHTML = `<p style="color:#ef4444;font-size:11px">Error: ${err.message}</p>`
  }
}

function _renderRequirements(containerId, reqs, projectId, subcharId, goalId, aeMap, rootId, project, archElems) {
  const container = $(containerId)
  if (!container) return

  if (!reqs.length) {
    container.innerHTML = '<p style="color:#94a3b8;font-size:11px;padding:2px 0">No requirements yet.</p>'
    return
  }

  container.innerHTML = reqs.map(r => `
    <div style="border-left:3px solid #6366f1;padding-left:12px;margin-bottom:8px">
      <div class="row">
        <span style="font-size:12px;font-weight:600">📋 ${r.requirement_text.slice(0, 100)}${r.requirement_text.length > 100 ? '…' : ''}</span>
        ${statusBadge(r.risk_level)} ${statusBadge(r.evidence_status)}
        ${r.architecture_element_name ? `<span class="tag" style="border-color:#06b6d4;background:#ecfeff;color:#0e7490">${r.architecture_element_name}</span>` : ''}
        <button class="soft" style="font-size:10px" data-edit-req="${r.id}" data-goal="${goalId}">Edit</button>
        <button class="soft" style="font-size:10px;color:#ef4444" data-del-req="${r.id}" data-goal="${goalId}">Delete</button>
        <button class="soft" style="font-size:10px" data-add-subreq="${r.id}">+ Sub-Req</button>
      </div>
      <div id="req-${r.id}" style="margin-top:4px"></div>
    </div>
  `).join('')

  reqs.forEach(r => {
    container.querySelector(`[data-edit-req="${r.id}"]`)?.addEventListener('click', () =>
      _openReqForm(projectId, subcharId, goalId, r, aeMap, rootId, project, archElems)
    )
    container.querySelector(`[data-del-req="${r.id}"]`)?.addEventListener('click', async () => {
      if (!confirm(`Delete requirement "${r.req_id}"?`)) return
      try {
        await api.deleteRequirement(projectId, subcharId, goalId, r.id)
        await _loadAndRenderRequirements(containerId, projectId, subcharId, goalId, aeMap, rootId, project, archElems)
      } catch (err) { showError(err.message) }
    })
    container.querySelector(`[data-add-subreq="${r.id}"]`)?.addEventListener('click', () =>
      _openSubReqForm(projectId, r.id, null, aeMap, rootId, project, archElems)
    )

    _loadAndRenderSubReqs(`req-${r.id}`, projectId, r.id, aeMap, rootId, project, archElems)
  })
}

// ─── Sub-Requirements ─────────────────────────────────────────────────────────

async function _loadAndRenderSubReqs(containerId, projectId, reqId, aeMap, rootId, project, archElems) {
  const container = $(containerId)
  if (!container) return
  try {
    const subs = await api.getSubRequirements(projectId, reqId)
    _renderSubReqs(containerId, subs, projectId, reqId, aeMap, rootId, project, archElems)
  } catch (err) {
    if (container) container.innerHTML = `<p style="color:#ef4444;font-size:11px">Error: ${err.message}</p>`
  }
}

function _renderSubReqs(containerId, subs, projectId, reqId, aeMap, rootId, project, archElems) {
  const container = $(containerId)
  if (!container || !subs.length) return

  container.innerHTML = subs.map(s => `
    <div style="border-left:2px solid #a855f7;padding-left:10px;margin:4px 0;font-size:11px">
      <div class="row">
        <span>✔ ${s.acceptance_criterion ?? s.sub_req_id}</span>
        ${s.architecture_element_id && aeMap[s.architecture_element_id]
          ? `<span class="tag" style="font-size:9px">${aeMap[s.architecture_element_id].name}</span>` : ''}
        <button class="soft" style="font-size:9px" data-edit-subreq="${s.id}" data-req="${reqId}">Edit</button>
        <button class="soft" style="font-size:9px;color:#ef4444" data-del-subreq="${s.id}" data-req="${reqId}">Del</button>
      </div>
    </div>
  `).join('')

  subs.forEach(s => {
    container.querySelector(`[data-edit-subreq="${s.id}"]`)?.addEventListener('click', () =>
      _openSubReqForm(projectId, reqId, s, aeMap, rootId, project, archElems)
    )
    container.querySelector(`[data-del-subreq="${s.id}"]`)?.addEventListener('click', async () => {
      if (!confirm('Delete sub-requirement?')) return
      try {
        await api.deleteSubRequirement(projectId, reqId, s.id)
        await _loadAndRenderSubReqs(containerId, projectId, reqId, aeMap, rootId, project, archElems)
      } catch (err) { showError(err.message) }
    })
  })
}

// ─── Inline forms ─────────────────────────────────────────────────────────────

function _openGoalForm(projectId, subcharId, existing, rootId, project, archElems) {
  const text = prompt(
    existing ? 'Edit goal text:' : 'New goal text:',
    existing?.goal_text ?? ''
  )
  if (text === null) return
  const goalId = existing ? null : prompt('Goal ID (e.g. QG-001):', `QG-${Date.now().toString().slice(-4)}`)
  if (!existing && !goalId) return

  ;(existing
    ? api.updateGoal(projectId, subcharId, existing.id, { goal_text: text })
    : api.createGoal(projectId, subcharId, { goal_id: goalId, goal_text: text })
  )
    .then(() => renderTraceChain(rootId, project, archElems))
    .catch(err => showError(err.message))
}

function _openReqForm(projectId, subcharId, goalId, existing, aeMap, rootId, project, archElems) {
  const text = prompt(
    existing ? 'Edit requirement text:' : 'New requirement text:',
    existing?.requirement_text ?? ''
  )
  if (text === null) return

  if (existing) {
    api.updateRequirement(projectId, subcharId, goalId, existing.id, { requirement_text: text })
      .then(() => renderTraceChain(rootId, project, archElems))
      .catch(err => showError(err.message))
  } else {
    const reqId = prompt('Requirement ID (e.g. QR-001):', `QR-${Date.now().toString().slice(-4)}`)
    if (!reqId) return
    api.createRequirement(projectId, subcharId, goalId, { req_id: reqId, requirement_text: text })
      .then(() => renderTraceChain(rootId, project, archElems))
      .catch(err => showError(err.message))
  }
}

function _openSubReqForm(projectId, reqId, existing, aeMap, rootId, project, archElems) {
  const text = prompt(
    existing ? 'Edit acceptance criterion:' : 'New acceptance criterion:',
    existing?.acceptance_criterion ?? ''
  )
  if (text === null) return

  if (existing) {
    api.updateSubRequirement(projectId, reqId, existing.id, { acceptance_criterion: text })
      .then(() => renderTraceChain(rootId, project, archElems))
      .catch(err => showError(err.message))
  } else {
    const subId = prompt('Sub-Req ID (e.g. SQR-001):', `SQR-${Date.now().toString().slice(-4)}`)
    if (!subId) return
    api.createSubRequirement(projectId, reqId, { sub_req_id: subId, acceptance_criterion: text })
      .then(() => renderTraceChain(rootId, project, archElems))
      .catch(err => showError(err.message))
  }
}
