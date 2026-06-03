import { S } from '../state.js'
import { api } from '../api.js'
import { showError } from '../utils.js'
import { renderDashboardStats, renderAspectDistribution, renderRiskSummary } from '../components/dashboard.js'
import { renderTraceChain } from '../components/table.js'
import { renderRisks, renderEvidence, renderFindings, renderActions } from '../components/risks.js'

const $ = id => document.getElementById(id)

function statusBadge(v) {
  const s = String(v)
  const cls = ['Ready', 'Closed', 'Complete', 'Low', '0'].includes(s) ? 'ok'
    : ['Not ready', 'Open', 'High', 'Critical', 'Failed', 'Missing'].some(x => s.includes(x)) ? 'risk'
    : 'warn'
  return `<span class="tag ${cls}">${s}</span>`
}

// ─── Project list ───────────────────────────────────────────────────────────

export async function renderProjects() {
  if (S.selectedProject) {
    $('projectList').classList.add('hidden')
    $('projectDetail').classList.remove('hidden')
    await renderProjectDetail()
  } else {
    $('projectDetail').classList.add('hidden')
    $('projectList').classList.remove('hidden')
    await renderProjectCards()
  }
}

async function renderProjectCards() {
  const container = $('projectCards')
  container.innerHTML = '<div class="loading">Loading projects…</div>'

  try {
    S.projects = await api.getProjects()
  } catch (err) {
    showError(`Failed to load projects: ${err.message}`)
    container.innerHTML = ''
    return
  }

  if (!S.projects.length) {
    container.innerHTML = '<p style="color:#64748b;font-size:13px;padding:12px">No projects yet. Click + to create one.</p>'
    return
  }

  container.innerHTML = S.projects.map(p => `
    <div class="card projectCard" data-id="${p.id}">
      <div class="projectHead">
        <div>
          <h3>${p.name}</h3>
          <p>${p.product_line} · ${p.phase}</p>
        </div>
        ${statusBadge(p.assessment_readiness)}
      </div>
      <p style="margin-top:6px;font-size:12px;color:#475569">${p.system_boundary}</p>
      <div style="margin-top:10px">
        ${statusBadge(p.selected_subchar_count + ' scope items')}
        ${statusBadge(p.open_risk_count + ' open risks')}
        ${statusBadge(p.evidence_gap_count + ' evidence gaps')}
      </div>
      <div class="mini" id="mini_${p.id}"></div>
    </div>
  `).join('')

  container.querySelectorAll('.projectCard').forEach(card => {
    card.addEventListener('click', async () => {
      const summary = S.projects.find(p => p.id === card.dataset.id)
      // Load full project detail (includes scope) before showing detail view
      try {
        S.selectedProject = await api.getProject(summary.id)
      } catch {
        S.selectedProject = summary
      }
      S.selectedNode = null
      renderProjects()
    })
  })
}

// ─── Project detail ──────────────────────────────────────────────────────────

export async function renderProjectDetail() {
  const p = S.selectedProject
  if (!p) return

  $('pTitle').textContent = p.name
  $('pInfo').textContent = `${p.product_line} · ${p.phase} · ${p.system_boundary}`

  const auditPanel = $('auditReportPanel')
  if (auditPanel) {
    auditPanel.classList.add('hidden')
    auditPanel.innerHTML = ''
  }
  const auditBtn = $('toggleAuditReportBtn')
  if (auditBtn) auditBtn.classList.remove('active')

  // Load dashboard metrics from API
  try {
    const dash = await api.getDashboard(p.id)
    renderDashboardStats(dash)
    renderAspectDistribution(dash, p.scope ?? [])
    renderRiskSummary(dash)
  } catch (err) {
    $('pStats').innerHTML = [
      ['Selected Subcharacteristics', p.selected_subchar_count ?? '—'],
      ['Open Risks', p.open_risk_count ?? '—'],
      ['Evidence Gaps', p.evidence_gap_count ?? '—'],
      ['Assessment Readiness', p.assessment_readiness ?? '—'],
    ].map(([label, val]) => `
      <div class="card stat">
        <div class="num">${val}</div>
        <div class="label">${label}</div>
      </div>
    `).join('')
    showError(`Dashboard metrics unavailable: ${err.message}`)
  }

  // Load risks, evidence, findings, actions in parallel
  const pid = p.id
  await Promise.all([
    renderRisks('riskItemsPanel', pid),
    renderEvidence('evidencePanel', pid),
    renderFindings('findingsPanel', pid),
    renderActions('actionsPanel', pid),
  ])

  // Auto-load Project Sankey first so Trace Chain Management can reuse /full data
  const { loadAndRenderProjectSankey } = await import('./ProjectSankey.js')
  await loadAndRenderProjectSankey()

  // Load trace chain management panel from the same normalized graph data
  await _renderTracePanel(p)
}

async function _renderTracePanel(project) {
  const panel = $('traceChainPanel')
  if (!panel) return

  let archElems = []
  try {
    archElems = await api.getArchElements(project.id)
  } catch {
    // arch elements may not exist yet — pass empty array
  }

  await renderTraceChain('traceChainPanel', project, archElems)

  // Wire refresh button
  const refreshBtn = $('refreshTraceBtn')
  if (refreshBtn) {
    refreshBtn.onclick = async () => {
      let ae = []
      try { ae = await api.getArchElements(project.id) } catch { /* ok */ }
      await renderTraceChain('traceChainPanel', project, ae, true)
    }
  }
}
