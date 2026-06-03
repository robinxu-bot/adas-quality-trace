/**
 * table.js - Trace Chain Management UI.
 *
 * This panel renders the same end-to-end project trace graph used by the
 * Project Sankey view, but as an expandable management tree.
 */
import { api } from '../api.js'
import { S, normalize } from '../state.js'
import { showError } from '../utils.js'
import { buildProject } from './sankey.js'

const $ = id => document.getElementById(id)

const INCLUDED_APPLICABILITY = new Set(['Applicable', 'Partially applicable', 'Deferred'])

function esc(v) {
  return String(v ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function statusBadge(v) {
  if (!v) return ''
  const s = String(v)
  const cls = ['Pass', 'Complete', 'Low', 'Ready', 'Closed'].includes(s) ? 'ok'
    : ['Fail', 'Failed', 'High', 'Critical', 'Missing', 'Open'].includes(s) ? 'risk'
    : 'warn'
  return `<span class="tag ${cls}">${esc(s)}</span>`
}

function typeLabel(type) {
  const labels = {
    QualityCharacteristic: 'Quality Characteristic',
    QualitySubCharacteristic: 'Quality Subcharacteristic',
    QualityGoal: 'Quality Goal',
    QualityRequirement: 'Quality Requirement',
    SubQualityRequirement: 'Sub-Requirement',
    ArchitectureElement: 'Architecture Element',
    SoftwareModule: 'Software Module',
    TestCase: 'Test Case',
    TestResult: 'Test Result',
    RiskStatus: 'Risk Status',
  }
  return labels[type] ?? type
}

function nodeMeta(node) {
  return [
    ...(node.aspects ?? []).map(a => `<span class="tag">${esc(a)}</span>`),
    statusBadge(node.riskLevel),
    statusBadge(node.evidence),
    statusBadge(node.riskStatus),
  ].join('')
}

function childMap(graph) {
  const out = new Map()
  for (const link of graph.links) {
    const source = link.source?.id ?? link.source
    const target = link.target?.id ?? link.target
    if (!out.has(source)) out.set(source, [])
    const targetNode = graph.nodes.find(n => n.id === target)
    if (targetNode) out.get(source).push(targetNode)
  }
  return out
}

async function ensureProjectFull(projectId, forceReload = false) {
  if (!forceReload && S.projectFull?.project?.id === projectId) return S.projectFull
  const fullData = await api.getProjectFull(projectId)
  S.projectFull = normalize(fullData)
  return S.projectFull
}

function scopeDecisionForNode(full, node) {
  return [...full.scope.values()].find(d => d.id === node.id || d.subchar_id === node.subchar_id)
}

function renderNodeLine(node, controls = '') {
  return `
    <div class="trace-node-line">
      <div>
        <span class="trace-node-type">${typeLabel(node.type)}</span>
        <span class="trace-node-label">${esc(node.label)}</span>
        ${nodeMeta(node)}
      </div>
      <div class="row">${controls}</div>
    </div>
  `
}

function renderReadonlyNode(node, depth) {
  return `
    <div class="trace-node trace-depth-${depth}">
      ${renderNodeLine(node)}
      ${node.desc ? `<div class="trace-node-desc">${esc(node.desc)}</div>` : ''}
    </div>
  `
}

function renderExpandableNode(node, depth, controls, childrenHtml) {
  return `
    <details class="trace-details trace-depth-${depth}">
      <summary class="trace-node">
        ${renderNodeLine(node, controls)}
        ${node.desc ? `<div class="trace-node-desc">${esc(node.desc)}</div>` : ''}
      </summary>
      <div class="trace-children">
        ${childrenHtml}
      </div>
    </details>
  `
}

function renderRiskTail(out, tr, depth) {
  const riskNodes = out.get(tr.id)?.filter(n => n.type === 'RiskStatus') ?? []
  return riskNodes.map(rs => renderReadonlyNode(rs, depth)).join('')
}

function renderTestResults(out, tc, depth) {
  const results = out.get(tc.id)?.filter(n => n.type === 'TestResult') ?? []
  if (!results.length) {
    return `<div class="trace-missing trace-depth-${depth}">No test result linked.</div>`
  }
  return results.map(tr => `
    ${renderExpandableNode(tr, depth, '', renderRiskTail(out, tr, depth + 1))}
  `).join('')
}

function renderTestCases(out, mod, depth) {
  const testCases = out.get(mod.id)?.filter(n => n.type === 'TestCase') ?? []
  if (!testCases.length) {
    return `<div class="trace-missing trace-depth-${depth}">No test case linked.</div>`
  }
  return testCases.map(tc => `
    ${renderExpandableNode(tc, depth, '', renderTestResults(out, tc, depth + 1))}
  `).join('')
}

function renderModules(out, ae, depth) {
  const modules = out.get(ae.id)?.filter(n => n.type === 'SoftwareModule') ?? []
  if (!modules.length) {
    return `<div class="trace-missing trace-depth-${depth}">No software module linked.</div>`
  }
  return modules.map(mod => `
    ${renderExpandableNode(mod, depth, '', renderTestCases(out, mod, depth + 1))}
  `).join('')
}

function renderArchitecture(out, subReq, depth) {
  const archElems = out.get(subReq.id)?.filter(n => n.type === 'ArchitectureElement') ?? []
  if (!archElems.length) {
    return `<div class="trace-missing trace-depth-${depth}">No architecture element linked.</div>`
  }
  return archElems.map(ae => `
    ${renderExpandableNode(ae, depth, '', renderModules(out, ae, depth + 1))}
  `).join('')
}

function renderSubRequirement(out, subReq, req, ctx, depth) {
  const controls = `
    <button class="soft" data-edit-subreq="${esc(subReq.id)}" data-req="${esc(req.id)}">Edit</button>
    <button class="soft danger" data-del-subreq="${esc(subReq.id)}" data-req="${esc(req.id)}">Del</button>
  `
  return renderExpandableNode(subReq, depth, controls, renderArchitecture(out, subReq, depth + 1))
}

function renderRequirement(out, req, goal, ctx, depth) {
  const subReqs = out.get(req.id)?.filter(n => n.type === 'SubQualityRequirement') ?? []
  const controls = `
    <button class="soft" data-edit-req="${esc(req.id)}" data-goal="${esc(goal.id)}">Edit</button>
    <button class="soft danger" data-del-req="${esc(req.id)}" data-goal="${esc(goal.id)}">Delete</button>
    <button class="soft" data-add-subreq="${esc(req.id)}">+ Sub-Req</button>
  `
  const children = subReqs.length
      ? subReqs.map(subReq => renderSubRequirement(out, subReq, req, ctx, depth + 1)).join('')
      : `<div class="trace-missing trace-depth-${depth + 1}">No sub-requirement linked.</div>`
  return renderExpandableNode(req, depth, controls, children)
}

function renderGoal(out, goal, subchar, ctx, depth) {
  const decision = scopeDecisionForNode(ctx.full, subchar)
  const subcharId = decision?.subchar_id ?? subchar.subchar_id
  const reqs = out.get(goal.id)?.filter(n => n.type === 'QualityRequirement') ?? []
  const controls = `
    <button class="soft" data-edit-goal="${esc(goal.id)}" data-subchar="${esc(subcharId)}">Edit</button>
    <button class="soft danger" data-del-goal="${esc(goal.id)}" data-subchar="${esc(subcharId)}">Delete</button>
    <button class="soft" data-add-req="${esc(goal.id)}" data-subchar="${esc(subcharId)}">+ Requirement</button>
  `
  const children = reqs.length
      ? reqs.map(req => renderRequirement(out, req, goal, ctx, depth + 1)).join('')
      : `<div class="trace-missing trace-depth-${depth + 1}">No requirement linked.</div>`
  return renderExpandableNode(goal, depth, controls, children)
}

function renderSubcharacteristic(out, subchar, ctx, depth) {
  const decision = scopeDecisionForNode(ctx.full, subchar)
  const subcharId = decision?.subchar_id ?? subchar.subchar_id
  const goals = out.get(subchar.id)?.filter(n => n.type === 'QualityGoal') ?? []
  const controls = `
    <button class="soft" data-add-goal="${esc(subcharId)}">+ Goal</button>
  `
  const node = {
    ...subchar,
    evidence: decision?.applicability ?? subchar.evidence,
  }
  const children = goals.length
      ? goals.map(goal => renderGoal(out, goal, subchar, ctx, depth + 1)).join('')
      : `<div class="trace-missing trace-depth-${depth + 1}">No quality goal linked.</div>`
  return renderExpandableNode(node, depth, controls, children)
}

function renderCharacteristic(out, ch, ctx) {
  const subs = out.get(ch.id)?.filter(n => n.type === 'QualitySubCharacteristic') ?? []
  return `
    <details class="card section trace-characteristic trace-root">
      <summary class="trace-node">
        ${renderNodeLine(ch)}
      </summary>
      <div class="trace-tree">
        ${subs.map(sub => renderSubcharacteristic(out, sub, ctx, 1)).join('')}
      </div>
    </details>
  `
}

/**
 * Render the project trace graph as an editable tree.
 * @param {string} containerId
 * @param {object} project
 * @param {object[]} archElems retained for compatibility with older callers
 * @param {boolean} forceReload refetch /full before rendering
 */
export async function renderTraceChain(containerId, project, archElems = [], forceReload = false) {
  const container = $(containerId)
  if (!container || !project) return

  container.innerHTML = '<div class="loading">Loading trace chain...</div>'

  try {
    const full = await ensureProjectFull(project.id, forceReload)
    const graph = buildProject(full, S.filters?.showExcluded ?? false)
    const out = childMap(graph)
    const chars = out.get('STD')?.filter(n => n.type === 'QualityCharacteristic') ?? []

    if (!chars.length) {
      const hasIncludedScope = [...full.scope.values()]
        .some(d => INCLUDED_APPLICABILITY.has(d.applicability))
      container.innerHTML = hasIncludedScope
        ? '<p style="color:#64748b;font-size:13px;padding:12px">No trace graph nodes yet. Add quality goals under applicable scope items.</p>'
        : '<p style="color:#64748b;font-size:13px;padding:12px">No applicable scope items. Add scope decisions first.</p>'
      return
    }

    container.innerHTML = `
      <div class="trace-hint">
        This tree uses the same project trace graph as the Sankey view: quality characteristic to risk status.
      </div>
      ${chars.map(ch => renderCharacteristic(out, ch, { full, project, archElems })).join('')}
    `

    wireTraceActions(container, containerId, project, archElems)
  } catch (err) {
    container.innerHTML = `<p class="error-banner">Failed to load trace chain: ${esc(err.message)}</p>`
  }
}

async function refreshTraceViews(rootId, project, archElems) {
  await renderTraceChain(rootId, project, archElems, true)
  const sankey = await import('../views/ProjectSankey.js').catch(() => null)
  sankey?.invalidateProjectSankeyGraph?.()
  sankey?.rerenderProjectSankey?.()
}

function wireTraceActions(container, rootId, project, archElems) {
  container.querySelectorAll('summary button').forEach(btn => {
    btn.addEventListener('click', event => event.stopPropagation())
  })

  container.querySelectorAll('[data-add-goal]').forEach(btn => {
    btn.addEventListener('click', () =>
      _openGoalForm(project.id, btn.dataset.addGoal, null, rootId, project, archElems)
    )
  })

  container.querySelectorAll('[data-edit-goal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const existing = S.projectFull.goals.get(btn.dataset.editGoal)
      _openGoalForm(project.id, btn.dataset.subchar, existing, rootId, project, archElems)
    })
  })

  container.querySelectorAll('[data-del-goal]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const existing = S.projectFull.goals.get(btn.dataset.delGoal)
      if (!confirm(`Delete goal "${existing?.goal_text ?? btn.dataset.delGoal}"?`)) return
      try {
        await api.deleteGoal(project.id, btn.dataset.subchar, btn.dataset.delGoal)
        await refreshTraceViews(rootId, project, archElems)
      } catch (err) { showError(err.message) }
    })
  })

  container.querySelectorAll('[data-add-req]').forEach(btn => {
    btn.addEventListener('click', () =>
      _openReqForm(project.id, btn.dataset.subchar, btn.dataset.addReq, null, rootId, project, archElems)
    )
  })

  container.querySelectorAll('[data-edit-req]').forEach(btn => {
    btn.addEventListener('click', () => {
      const goal = S.projectFull.goals.get(btn.dataset.goal)
      const subcharId = scopeDecisionForGoal(goal)?.subchar_id
      const existing = S.projectFull.reqs.get(btn.dataset.editReq)
      _openReqForm(project.id, subcharId, btn.dataset.goal, existing, rootId, project, archElems)
    })
  })

  container.querySelectorAll('[data-del-req]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const goal = S.projectFull.goals.get(btn.dataset.goal)
      const subcharId = scopeDecisionForGoal(goal)?.subchar_id
      const existing = S.projectFull.reqs.get(btn.dataset.delReq)
      if (!confirm(`Delete requirement "${existing?.req_id ?? btn.dataset.delReq}"?`)) return
      try {
        await api.deleteRequirement(project.id, subcharId, btn.dataset.goal, btn.dataset.delReq)
        await refreshTraceViews(rootId, project, archElems)
      } catch (err) { showError(err.message) }
    })
  })

  container.querySelectorAll('[data-add-subreq]').forEach(btn => {
    btn.addEventListener('click', () =>
      _openSubReqForm(project.id, btn.dataset.addSubreq, null, rootId, project, archElems)
    )
  })

  container.querySelectorAll('[data-edit-subreq]').forEach(btn => {
    btn.addEventListener('click', () => {
      const existing = S.projectFull.subReqs.get(btn.dataset.editSubreq)
      _openSubReqForm(project.id, btn.dataset.req, existing, rootId, project, archElems)
    })
  })

  container.querySelectorAll('[data-del-subreq]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete sub-requirement?')) return
      try {
        await api.deleteSubRequirement(project.id, btn.dataset.req, btn.dataset.delSubreq)
        await refreshTraceViews(rootId, project, archElems)
      } catch (err) { showError(err.message) }
    })
  })
}

function scopeDecisionForGoal(goal) {
  if (!goal) return null
  return [...S.projectFull.scope.values()].find(d => d.id === goal.scope_decision_id)
}

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
    .then(() => refreshTraceViews(rootId, project, archElems))
    .catch(err => showError(err.message))
}

function _openReqForm(projectId, subcharId, goalId, existing, rootId, project, archElems) {
  const text = prompt(
    existing ? 'Edit requirement text:' : 'New requirement text:',
    existing?.requirement_text ?? ''
  )
  if (text === null) return

  if (existing) {
    api.updateRequirement(projectId, subcharId, goalId, existing.id, { requirement_text: text })
      .then(() => refreshTraceViews(rootId, project, archElems))
      .catch(err => showError(err.message))
  } else {
    const reqId = prompt('Requirement ID (e.g. QR-001):', `QR-${Date.now().toString().slice(-4)}`)
    if (!reqId) return
    api.createRequirement(projectId, subcharId, goalId, { req_id: reqId, requirement_text: text })
      .then(() => refreshTraceViews(rootId, project, archElems))
      .catch(err => showError(err.message))
  }
}

function _openSubReqForm(projectId, reqId, existing, rootId, project, archElems) {
  const text = prompt(
    existing ? 'Edit acceptance criterion:' : 'New acceptance criterion:',
    existing?.acceptance_criterion ?? ''
  )
  if (text === null) return

  if (existing) {
    api.updateSubRequirement(projectId, reqId, existing.id, { acceptance_criterion: text })
      .then(() => refreshTraceViews(rootId, project, archElems))
      .catch(err => showError(err.message))
  } else {
    const subId = prompt('Sub-Req ID (e.g. SQR-001):', `SQR-${Date.now().toString().slice(-4)}`)
    if (!subId) return
    api.createSubRequirement(projectId, reqId, { sub_req_id: subId, acceptance_criterion: text })
      .then(() => refreshTraceViews(rootId, project, archElems))
      .catch(err => showError(err.message))
  }
}
