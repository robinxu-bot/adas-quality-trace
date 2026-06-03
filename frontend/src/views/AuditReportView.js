import { api } from '../api.js'
import { showError } from '../utils.js'

const $ = id => document.getElementById(id)

function badge(value) {
  const text = value == null ? 'Unknown' : String(value)
  const cls = ['Ready', 'Normal', 'Low'].includes(text) ? 'ok'
    : ['Blocked', 'Critical', 'At Risk', 'Unknown', 'High'].includes(text) ? 'risk'
    : 'warn'
  return `<span class="tag ${cls}">${text}</span>`
}

function metricCard(label, value, hint = '') {
  return `
    <div class="card stat">
      ${typeof value === 'number' ? `<div class="num">${value}</div>` : badge(value)}
      <div class="label">${label}</div>
      ${hint ? `<p>${hint}</p>` : ''}
    </div>
  `
}

function emptySection(title, body) {
  return `
    <div class="card section">
      <h2>${title}</h2>
      <p>${body}</p>
    </div>
  `
}

function tableWrap(tableHtml) {
  return `<div class="tableWrap">${tableHtml}</div>`
}

function distributionRows(distribution = {}, suffix = '') {
  const entries = Object.entries(distribution)
  if (!entries.length) {
    return '<tr><td>No data</td><td>0</td></tr>'
  }
  return entries
    .map(([label, count]) => `<tr><td>${label}</td><td>${count}${suffix}</td></tr>`)
    .join('')
}

function riskRows(risks = []) {
  if (!risks.length) {
    return '<tr><td colspan="5">No open Critical/High risk for the current gate.</td></tr>'
  }
  return risks.map(risk => `
    <tr>
      <td>${risk.risk_id ?? '-'}</td>
      <td>${risk.title ?? '-'}</td>
      <td>${badge(risk.risk_level)}</td>
      <td>${(risk.quality_aspects ?? []).join(', ') || '-'}</td>
      <td>${risk.owner ?? '-'}</td>
    </tr>
  `).join('')
}

function renderProjectRiskPosture(posture = {}) {
  const evidence = posture.evidence_gap_summary ?? {}
  const gateImpact = posture.current_gate_impact ?? {}
  const severity = posture.severity_distribution ?? {}
  const criticalCount = severity.Critical ?? 0
  const highCount = severity.High ?? 0

  return `
    <div class="card section">
      <h2>Project Risk Posture</h2>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Open Risks', posture.open_risk_count ?? 0)}
        ${metricCard('Critical Risks', criticalCount)}
        ${metricCard('High Risks', highCount)}
        ${metricCard('Current Gate Impact', gateImpact.risk_count ?? 0, `Gate ${gateImpact.gate ?? 'Unknown'}`)}
      </div>
      <div class="grid2" style="margin-top:12px">
        <div>
          <h3>Severity Distribution</h3>
          <table><tbody>${distributionRows(severity)}</tbody></table>
        </div>
        <div>
          <h3>Quality Aspect Distribution</h3>
          <table><tbody>${distributionRows(posture.aspect_distribution)}</tbody></table>
        </div>
      </div>
      <div class="grid2" style="margin-top:12px">
        <div>
          <h3>Evidence Gap Summary</h3>
          <table>
            <tbody>
              <tr><td>Missing evidence</td><td>${evidence.missing_evidence_count ?? 0}</td></tr>
              <tr><td>Failed evidence</td><td>${evidence.failed_evidence_count ?? 0}</td></tr>
              <tr><td>Test evidence gaps</td><td>${evidence.evidence_gap_count ?? 0}</td></tr>
              <tr><td>Blocking gaps</td><td>${gateImpact.blocking_gap_count ?? 0}</td></tr>
            </tbody>
          </table>
        </div>
        <div>
          <h3>Evidence Item Status</h3>
          <table><tbody>${distributionRows(evidence.evidence_item_status)}</tbody></table>
        </div>
      </div>
      <h3 style="margin-top:12px">Current Gate Risk Drivers</h3>
      <table>
        <thead>
          <tr><th>Risk ID</th><th>Title</th><th>Level</th><th>Aspect</th><th>Owner</th></tr>
        </thead>
        <tbody>${riskRows(gateImpact.risks)}</tbody>
      </table>
      <h3 style="margin-top:12px">Top Open Critical/High Risks</h3>
      <table>
        <thead>
          <tr><th>Risk ID</th><th>Title</th><th>Level</th><th>Aspect</th><th>Owner</th></tr>
        </thead>
        <tbody>${riskRows(posture.top_open_risks)}</tbody>
      </table>
    </div>
  `
}

function percent(value) {
  return typeof value === 'number' ? `${value}%` : '-'
}

function renderQualityGateMaturity(rows = []) {
  if (!rows.length) {
    return emptySection('Quality Gate Maturity', 'No quality gate maturity data available.')
  }

  const scopedRows = rows.filter(row => (row.scope_count ?? 0) > 0)
  const blocked = scopedRows.filter(row => row.gate_progression_signal === 'Blocked').length
  const conditional = scopedRows.filter(row => row.gate_progression_signal === 'Conditional').length
  const ready = scopedRows.filter(row => row.gate_progression_signal === 'Ready').length
  const average = scopedRows.length
    ? Math.round(scopedRows.reduce((sum, row) => sum + (row.official_maturity ?? 0), 0) / scopedRows.length)
    : null

  return `
    <div class="card section">
      <h2>Quality Gate Maturity</h2>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Scoped Aspects', scopedRows.length)}
        ${metricCard('Average Maturity', average == null ? 'Unknown' : average)}
        ${metricCard('Blocked Aspects', blocked)}
        ${metricCard('Conditional Aspects', conditional)}
      </div>
      ${tableWrap(`
      <table>
        <thead>
          <tr>
            <th>Aspect</th>
            <th>Gate</th>
            <th>Maturity</th>
            <th>Signal</th>
            <th>Risk</th>
            <th>Reviewed</th>
            <th>Evidence</th>
            <th>Blocking Gaps</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(row => `
            <tr>
              <td>${row.aspect ?? '-'}</td>
              <td>${row.gate ?? '-'}</td>
              <td>${percent(row.official_maturity)}</td>
              <td>${badge(row.gate_progression_signal)}</td>
              <td>${badge(row.process_maturity_risk)}</td>
              <td>${row.reviewed_count ?? 0}/${row.scope_count ?? 0}</td>
              <td>${percent(row.evidence_coverage)}</td>
              <td>${row.blocking_gap_count ?? 0}</td>
              <td>${row.primary_reason ?? '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      `)}
    </div>
  `
}

function maturityState(value) {
  const labels = {
    0: '0 Not assessed',
    1: '1 Insufficient',
    2: '2 In progress',
    3: '3 Evidence complete',
    4: '4 Deliverable accepted',
  }
  return labels[value] ?? '-'
}

function activityRows(activities = []) {
  if (!activities.length) {
    return '<tr><td colspan="7">No Activity x Gate data available.</td></tr>'
  }
  return activities.map(activity => `
    <tr>
      <td>${activity.lifecycle_phase ?? '-'}</td>
      <td>${activity.activity_name ?? '-'}</td>
      <td>${activity.gate ?? '-'}</td>
      <td>${maturityState(activity.official_maturity)}</td>
      <td>${maturityState(activity.draft_maturity)}</td>
      <td>${badge(activity.judgement)}</td>
      <td>${activity.primary_reason ?? '-'}</td>
    </tr>
  `).join('')
}

function renderLifecycleProcessMaturity(frameworks = []) {
  if (!frameworks.length) {
    return emptySection('Lifecycle & Process Maturity', 'No lifecycle process maturity data available.')
  }

  const officialAverage = Math.round(
    frameworks.reduce((sum, item) => sum + (item.official_score ?? 0), 0) / frameworks.length
  )
  const draftAverage = Math.round(
    frameworks.reduce((sum, item) => sum + (item.draft_score ?? 0), 0) / frameworks.length
  )
  const highRisk = frameworks.filter(item => item.process_maturity_risk === 'High').length
  const unknownRisk = frameworks.filter(item => item.process_maturity_risk === 'Unknown').length

  return `
    <div class="card section">
      <h2>Lifecycle & Process Maturity</h2>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Official Average', officialAverage)}
        ${metricCard('Draft Average', draftAverage)}
        ${metricCard('High Risk Frameworks', highRisk)}
        ${metricCard('Unknown Frameworks', unknownRisk)}
      </div>
      ${tableWrap(`
      <table>
        <thead>
          <tr>
            <th>Framework</th>
            <th>Standard</th>
            <th>Official</th>
            <th>Draft</th>
            <th>Risk</th>
            <th>Coverage</th>
            <th>Pending</th>
            <th>Main Blocker</th>
          </tr>
        </thead>
        <tbody>
          ${frameworks.map(item => `
            <tr>
              <td>${item.framework ?? '-'}</td>
              <td>${item.standard_context ?? '-'}</td>
              <td>${item.official_score ?? 0}% / ${item.maturity_band ?? '-'}</td>
              <td>${item.draft_score ?? 0}% / ${item.draft_band ?? '-'}</td>
              <td>${badge(item.process_maturity_risk)}</td>
              <td>${item.official_coverage ?? 0}% reviewed / ${item.evidence_coverage ?? 0}% evidence</td>
              <td>${item.pending_human_confirmation_count ?? 0}</td>
              <td>${item.main_blocker ?? '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      `)}
      ${frameworks.map(item => `
        <h3 style="margin-top:12px">${item.framework ?? '-'}</h3>
        ${tableWrap(`
        <table>
          <thead>
            <tr>
              <th>Phase</th>
              <th>Activity</th>
              <th>Gate</th>
              <th>Official</th>
              <th>Draft</th>
              <th>Judgement</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>${activityRows(item.activities)}</tbody>
        </table>
        `)}
      `).join('')}
    </div>
  `
}

export async function loadAndRenderAuditReport(projectId) {
  const panel = $('auditReportPanel')
  if (!panel || !projectId) return

  panel.innerHTML = '<div class="loading">Loading audit report dashboard...</div>'

  try {
    const report = await api.getAuditReportDashboard(projectId)
    renderAuditReport(report)
  } catch (err) {
    panel.innerHTML = ''
    showError(`Audit report dashboard unavailable: ${err.message}`)
  }
}

export function renderAuditReport(report) {
  const panel = $('auditReportPanel')
  if (!panel) return

  const snapshot = report.audit_snapshot ?? {}
  const gate = snapshot.gate_readiness ?? {}
  const confidence = snapshot.risk_confidence ?? {}

  panel.innerHTML = `
    <div class="card section">
      <div class="projectHead">
        <div>
          <h2>Audit Report Dashboard</h2>
          <p>Snapshot ${report.snapshot_at ?? '-'} / Current gate ${report.current_gate ?? 'Unknown'}</p>
        </div>
        <div>${badge(snapshot.recommended_attention_level)}</div>
      </div>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Recommended Attention', snapshot.recommended_attention_level)}
        ${metricCard('Product Risk', snapshot.product_risk)}
        ${metricCard('Process Maturity Risk', snapshot.process_maturity_risk)}
        ${metricCard('Gate Progression Signal', gate.gate_progression_signal)}
        ${metricCard('Risk Confidence', confidence.level, confidence.primary_reason)}
        ${metricCard('Official Integrated Score', snapshot.official_integrated_score)}
        ${metricCard('Draft Integrated Score', snapshot.draft_integrated_score)}
        ${metricCard('Pending Human Confirmation', snapshot.pending_human_confirmation_count)}
      </div>
    </div>

    <div class="grid2">
      <div class="card section">
        <h2>Gate Readiness</h2>
        <table>
          <tbody>
            <tr><td>Official maturity</td><td>${gate.official_maturity ?? 0}%</td></tr>
            <tr><td>P0 status</td><td>${badge(gate.p0_status)}</td></tr>
            <tr><td>Blocking gaps</td><td>${gate.blocking_gap_count ?? 0}</td></tr>
            <tr><td>Progression signal</td><td>${badge(gate.gate_progression_signal)}</td></tr>
          </tbody>
        </table>
      </div>
      <div class="card section">
        <h2>Risk Confidence</h2>
        <table>
          <tbody>
            <tr><td>Evidence coverage</td><td>${confidence.evidence_coverage ?? 0}%</td></tr>
            <tr><td>Trace coverage</td><td>${confidence.trace_coverage ?? 0}%</td></tr>
            <tr><td>Official assessment coverage</td><td>${confidence.official_assessment_coverage ?? 0}%</td></tr>
            <tr><td>Review freshness</td><td>${confidence.review_freshness ?? 0}%</td></tr>
            <tr><td>Critical unknowns</td><td>${confidence.critical_unknown_count ?? 0}</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    ${renderQualityGateMaturity(report.quality_gate_maturity)}
    ${renderProjectRiskPosture(report.project_risk_posture)}
    ${renderLifecycleProcessMaturity(report.lifecycle_process_maturity)}
  `
}
