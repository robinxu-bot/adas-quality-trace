/**
 * dashboard.js — renders the Project Detail dashboard panel.
 * Receives the dashboard API response and the project's scope array.
 */
import { ASPECTS } from '../constants/aspects.js'

const $ = id => document.getElementById(id)

function statusBadge(v) {
  if (v === null || v === undefined) return ''
  const s = String(v)
  const cls = ['Ready', 'Closed', 'Complete', 'Low', '0'].includes(s) ? 'ok'
    : ['Not ready', 'Open', 'High', 'Critical', 'Failed', 'Missing'].some(x => s.includes(x)) ? 'risk'
    : 'warn'
  return `<span class="tag ${cls}">${s}</span>`
}

function tag(a) { return `<span class="tag">${a}</span>` }

/**
 * Render dashboard stat cards into #pStats.
 * @param {object} dash - DashboardOut from GET /projects/:id/dashboard
 */
export function renderDashboardStats(dash) {
  $('pStats').innerHTML = [
    ['Selected Characteristics', dash.selected_characteristics_count],
    ['Selected Subcharacteristics', dash.selected_subchar_count],
    ['Excluded Items', dash.excluded_count],
    ['Open Risks', dash.open_risk_count],
    ['Evidence Gaps', dash.evidence_gap_count],
    ['Assessment Readiness', dash.assessment_readiness],
  ].map(([label, val]) => {
    const badge = typeof val === 'string'
      ? statusBadge(val)
      : `<div class="num">${val}</div>`
    return `<div class="card stat">${badge}<div class="label">${label}</div></div>`
  }).join('')
}

/**
 * Render Quality Aspect Distribution table into #aspectTable.
 * Rows are clickable to expand and show the subcharacteristics for that aspect.
 * @param {object} dash  - DashboardOut
 * @param {Array}  scope - project scope decisions array (from GET /projects/:id)
 */
export function renderAspectDistribution(dash, scope = []) {
  const dist = dash.aspect_distribution ?? {}

  // Build aspect → scope decisions lookup
  const aspectMap = {}
  for (const a of ASPECTS) aspectMap[a] = []
  for (const d of scope) {
    for (const a of (d.selected_quality_aspects ?? [])) {
      if (aspectMap[a]) aspectMap[a].push(d)
    }
  }

  const container = $('aspectTable')
  container.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Aspect</th>
          <th>Applicable</th>
          <th>Partial</th>
          <th>Excluded</th>
          <th style="width:24px"></th>
        </tr>
      </thead>
      <tbody>
        ${ASPECTS.map(a => {
          const d = dist[a] ?? { applicable: 0, partial: 0, not_applicable: 0 }
          const total = d.applicable + d.partial + d.not_applicable
          return `
            <tr style="cursor:${total > 0 ? 'pointer' : 'default'}" data-aspect="${a}">
              <td>${tag(a)}</td>
              <td>${d.applicable}</td>
              <td>${d.partial}</td>
              <td>${d.not_applicable}</td>
              <td style="color:#94a3b8;font-size:11px">${total > 0 ? '▶' : ''}</td>
            </tr>
            <tr id="aspect-detail-${a}" class="hidden">
              <td colspan="5" style="padding:0 8px 8px">
                <div style="background:#f8fafc;border-radius:10px;padding:8px">
                  ${aspectMap[a].length
                    ? aspectMap[a].map(d => `
                        <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 6px;border-bottom:1px solid #f1f5f9;font-size:12px">
                          <span><b>${d.subchar_name ?? d.subchar_id}</b>
                            <span style="font-size:10px;color:#94a3b8;margin-left:6px">${d.characteristic_name ?? ''}</span>
                          </span>
                          ${statusBadge(d.applicability)}
                        </div>
                      `).join('')
                    : '<p style="color:#94a3b8;font-size:12px;margin:4px">No subcharacteristics mapped to this aspect.</p>'
                  }
                </div>
              </td>
            </tr>
          `
        }).join('')}
      </tbody>
    </table>
  `

  // Wire expand/collapse clicks
  container.querySelectorAll('tr[data-aspect]').forEach(row => {
    row.addEventListener('click', () => {
      const a = row.dataset.aspect
      const detail = $(`aspect-detail-${a}`)
      if (!detail) return
      const isHidden = detail.classList.contains('hidden')
      detail.classList.toggle('hidden', !isHidden)
      const arrow = row.querySelector('td:last-child')
      if (arrow) arrow.textContent = isHidden ? '▼' : '▶'
    })
  })
}

/**
 * Render Risk and Evidence Summary into #riskTable.
 * @param {object} dash - DashboardOut
 */
export function renderRiskSummary(dash) {
  $('riskTable').innerHTML = `
    <table>
      <tbody>
        <tr><td>Open risks</td><td>${statusBadge(String(dash.open_risk_count))}</td></tr>
        <tr><td>High risks</td><td>${statusBadge(String(dash.high_risk_count))}</td></tr>
        <tr><td>Critical risks</td><td>${statusBadge(String(dash.critical_risk_count))}</td></tr>
        <tr><td>Evidence gaps</td><td>${statusBadge(String(dash.evidence_gap_count))}</td></tr>
        <tr><td>Missing evidence</td><td>${statusBadge(String(dash.missing_evidence_count))}</td></tr>
        <tr><td>Failed evidence</td><td>${statusBadge(String(dash.failed_evidence_count))}</td></tr>
        <tr><td>Open findings</td><td>${statusBadge(String(dash.open_finding_count))}</td></tr>
        <tr><td>Open actions</td><td>${statusBadge(String(dash.open_action_count))}</td></tr>
        <tr><td>Readiness</td><td>${statusBadge(dash.assessment_readiness)}</td></tr>
      </tbody>
    </table>
  `
}
