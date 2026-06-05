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

function metricCard(label, value, hint = '', suffix = '') {
  return `
    <div class="card stat">
      ${typeof value === 'number' ? `<div class="num">${value}${suffix}</div>` : badge(value)}
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

function helpDetails(title, body) {
  return `
    <details class="helpDetails">
      <summary>${title}</summary>
      <div class="helpBody">${body}</div>
    </details>
  `
}

function definitionList(items) {
  return `
    <dl class="definitionList">
      ${items.map(([term, description]) => `
        <dt>${term}</dt>
        <dd>${description}</dd>
      `).join('')}
    </dl>
  `
}

function formula(text) {
  return `<div class="formula">${text}</div>`
}

function renderExecutiveLegend() {
  return helpDetails('Legend and calculation notes', `
    <div class="helpGrid">
      ${definitionList([
        ['Recommended Attention', 'Management attention level. It combines product risk, process maturity risk, gate progression signal, and risk confidence. It is not an approval decision.'],
        ['Product Risk', 'Current product risk exposure from open risks and evidence gaps. High means a product risk may affect gate readiness or release.'],
        ['Process Maturity Risk', 'Risk that lifecycle/process execution is not mature enough to trust the product risk judgement. Unknown means the system does not have enough reviewed process data for a reliable judgement.'],
        ['Gate Progression Signal', 'Dashboard signal for the current gate: Ready, Conditional, Blocked, or Unknown. It is Go/No-Go-like, but it is not a management approval record.'],
        ['Risk Confidence', 'How trustworthy this dashboard judgement is. Low means one or more baseline coverage thresholds are missed, so the dashboard should not be treated as a strong basis for low-risk conclusions.'],
      ])}
      ${definitionList([
        ['Integrated Score', 'Formal gate readiness score shown in this report. In this slice it is derived from readiness: Ready = 75, Conditionally ready = 55, Not ready = 25.'],
        ['Reviewed data', 'Assessment data that has been reviewed or approved and is allowed to affect this formal report.'],
      ])}
    </div>
  `)
}

function renderRiskConfidenceHelp() {
  return helpDetails('How Risk Confidence is calculated', `
    ${definitionList([
      ['Evidence coverage', 'Complete or Partial Evidence Items divided by total Evidence Items. If there are no Evidence Items, the fallback uses scoped quality characteristics minus evidence gaps.'],
      ['Trace coverage', 'Sub-quality requirements linked to at least one test case divided by total project sub-quality requirements.'],
      ['Assessment coverage', 'Formal scope assessment results divided by all included scope decisions. Items without a formal assessment result do not affect the report score.'],
      ['Review freshness', 'Included scope decisions updated within the last 30 days divided by all included scope decisions.'],
      ['Critical unknowns', 'Currently mapped to open Critical risks. Any critical unknown lowers confidence.'],
    ])}
    ${formula('High: evidence >= 85%, trace >= 85%, assessment coverage >= 90%, no critical unknowns. Medium: baseline thresholds are met. Low: evidence < 70%, trace < 70%, assessment coverage < 80%, or critical unknowns exist.')}
  `)
}

function renderGateMaturityHelp() {
  return helpDetails('How Quality Gate Maturity is calculated', `
    ${definitionList([
      ['Maturity', 'Gate-oriented aggregation of Activity x Gate maturity by quality aspect.'],
      ['Assessed', 'Formal Activity x Gate or scope-backed assessment inputs for this aspect divided by applicable items.'],
      ['Evidence', 'Requirements in this aspect with Complete or Partial evidence divided by all requirements in this aspect.'],
      ['Blocking gaps', 'Open High or Critical risks in this aspect. Any blocking gap can block the gate signal.'],
      ['Signal', 'Ready, Conditional, Blocked, or Unknown for the aspect at the current gate.'],
    ])}
    ${formula('Quality Gate Maturity is a Gate x Quality Aspect view over the same Activity x Gate result base used by Lifecycle Activity Maturity.')}
  `)
}

function renderProjectRiskHelp() {
  return helpDetails('How Project Risk Posture is calculated', `
    ${definitionList([
      ['Open Risks', 'Risk Items whose status is Open. Mitigated, Accepted, or Closed risks are excluded from the open risk count.'],
      ['Current Gate Impact', 'Open Critical/High risks plus risks whose target milestone references the current gate.'],
      ['Evidence Gap Summary', 'Combines failing/not-run test result gaps and Evidence Items marked Missing or Failed.'],
      ['Blocking gaps', 'Critical risks plus non-passing test evidence gaps used as gate blockers.'],
    ])}
  `)
}

function renderLifecycleHelp() {
  return helpDetails('How Lifecycle Activity Maturity is calculated', `
    ${definitionList([
      ['Lifecycle maturity score', 'Average maturity across assessed lifecycle activities. If there is no formal assessment coverage, the score is 0%.'],
      ['Activity x Gate', 'Minimum assessment unit: one lifecycle activity assessed at one quality gate.'],
      ['Unknown framework', 'The framework lacks enough formal activity assessment data for a judgement.'],
      ['High risk framework', 'A framework has blocking High/Critical risk or insufficient maturity.'],
    ])}
    ${formula('Lifecycle score = 70% assessment coverage + 30% evidence coverage, capped at 50% when blocking High/Critical risks exist. If assessment coverage is 0%, the score is 0.')}
  `)
}

function renderSubCharacteristicHelp() {
  return helpDetails('How Quality Sub-Characteristic Maturity is calculated', `
    ${definitionList([
      ['Quality Sub-Characteristic', 'ISO/IEC 25010 sub-characteristic in project quality scope, such as Functional completeness.'],
      ['Mapped aspects', 'QM, FuSA, CS, SOTIF, and AI Safety aspects where this sub-characteristic must be realised.'],
      ['Sub-characteristic maturity', 'Sub-characteristic-oriented aggregation of the same Activity x Gate maturity signals, evidence coverage, risks, and trace context.'],
      ['Weakest aspect', 'The quality aspect with the lowest maturity for this sub-characteristic; it is the first drill-down target.'],
    ])}
    ${formula('Quality Sub-Characteristic Maturity = aggregate(Quality Sub-Characteristic -> Quality Aspect -> Activity x Gate). It answers whether a sub-characteristic is actually realised across applicable aspects.')}
  `)
}

function renderTeamMatrixHelp() {
  return helpDetails('How Team Activity & Work Product Matrix is calculated', `
    ${definitionList([
      ['Rows', 'QM / FuSA / CS / SOTIF / AI Safety lifecycle activities at the current gate.'],
      ['Columns', 'Configurable ADAS teams. The current default columns use the project team structure agreed for this dashboard.'],
      ['Cell role', 'A = Accountable, C = Contributing, R = Reviewer / Approver, - = Not applicable.'],
      ['Work product status', 'Derived from the latest completed gate assessment result and required evidence defined in the gate checklist.'],
      ['Risk Confidence link', 'The matrix does not directly equal Risk Confidence, but missing accountable teams, missing work products, weak evidence, and blocking risks contribute to low confidence.'],
    ])}
    ${formula('Team matrix = assessment_gate_definitions + latest completed assessment_check_results + configured team mapping. If a responsible role is not mapped to a team, the matrix shows it as unmapped instead of guessing.')}
  `)
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
        ${metricCard('Open Risks', posture.open_risk_count ?? 0, 'Open Risk Items only')}
        ${metricCard('Critical Risks', criticalCount, 'Open risks at Critical level')}
        ${metricCard('High Risks', highCount, 'Open risks at High level')}
        ${metricCard('Current Gate Impact', gateImpact.risk_count ?? 0, `Gate ${gateImpact.gate ?? 'Unknown'} impact risks`)}
      </div>
      ${renderProjectRiskHelp()}
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
        ${metricCard('Scoped Aspects', scopedRows.length, 'Quality aspects included in current project scope')}
        ${metricCard('Average Maturity', average == null ? 'Unknown' : average, 'Average of scoped aspect maturity percentages', '%')}
        ${metricCard('Blocked Aspects', blocked, 'Aspects blocked by low maturity or High/Critical risk')}
        ${metricCard('Conditional Aspects', conditional, 'Aspects close to readiness but still with conditions')}
      </div>
      ${renderGateMaturityHelp()}
      ${tableWrap(`
      <table>
        <thead>
          <tr>
            <th>Aspect</th>
            <th>Gate</th>
            <th>Maturity</th>
            <th>Signal</th>
            <th>Risk</th>
            <th>Assessed</th>
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
    return '<tr><td colspan="6">No Activity x Gate data available.</td></tr>'
  }
  return activities.map(activity => `
    <tr>
      <td>${activity.lifecycle_phase ?? '-'}</td>
      <td>${activity.activity_name ?? '-'}</td>
      <td>${activity.gate ?? '-'}</td>
      <td>${maturityState(activity.official_maturity)}</td>
      <td>${badge(activity.judgement)}</td>
      <td>${activity.primary_reason ?? '-'}</td>
    </tr>
  `).join('')
}

function aspectBreakdownText(items = []) {
  if (!items.length) return '-'
  return items
    .map(item => `${item.aspect}: ${percent(item.score)}`)
    .join(' / ')
}

function aspectRationaleText(row = {}) {
  const reasons = row.aspect_mapping_reasons ?? {}
  const aspects = row.mapped_aspects ?? Object.keys(reasons)
  if (!aspects.length) return '-'
  return aspects
    .map(aspect => `${aspect}: ${reasons[aspect] ?? `Project-specific ${aspect} mapping selected in the quality scope; common mapping rationale is missing.`}`)
    .join(' / ')
}

function subCharacteristicRows(rows = []) {
  if (!rows.length) {
    return '<tr><td colspan="9">No quality sub-characteristic maturity data available.</td></tr>'
  }

  const sorted = [...rows].sort((a, b) => {
    const charCompare = String(a.quality_characteristic ?? '').localeCompare(String(b.quality_characteristic ?? ''))
    if (charCompare !== 0) return charCompare
    return String(a.quality_subcharacteristic ?? '').localeCompare(String(b.quality_subcharacteristic ?? ''))
  })

  let currentCharacteristic = ''
  return sorted.map(row => {
    const characteristic = row.quality_characteristic ?? 'Unassigned characteristic'
    const groupRow = characteristic === currentCharacteristic
      ? ''
      : `<tr class="groupRow"><td colspan="9">${characteristic}</td></tr>`
    currentCharacteristic = characteristic

    return `
      ${groupRow}
      <tr>
        <td>${row.quality_subcharacteristic ?? '-'}</td>
        <td>${row.gate ?? '-'}</td>
        <td>${aspectRationaleText(row)}</td>
        <td>${aspectBreakdownText(row.aspect_breakdown)}</td>
        <td>${percent(row.overall_maturity)} / ${row.maturity_band ?? '-'}</td>
        <td>${row.weakest_aspect ?? '-'}</td>
        <td>${percent(row.evidence_coverage)}</td>
        <td>${row.blocking_gap_count ?? 0}</td>
        <td>${row.main_weakness ?? '-'}</td>
      </tr>
    `
  }).join('')
}

function renderQualitySubCharacteristicMaturity(rows = []) {
  if (!rows.length) {
    return emptySection('Quality Sub-Characteristic Maturity', 'No quality sub-characteristic maturity data available.')
  }

  const average = Math.round(
    rows.reduce((sum, row) => sum + (row.overall_maturity ?? 0), 0) / rows.length
  )
  const weak = rows.filter(row => (row.overall_maturity ?? 0) < 50).length
  const conditional = rows.filter(row => (row.overall_maturity ?? 0) >= 50 && (row.overall_maturity ?? 0) < 70).length
  const blocked = rows.reduce((sum, row) => sum + (row.blocking_gap_count ?? 0), 0)

  return `
    <div class="card section">
      <h2>Quality Sub-Characteristic Maturity</h2>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Sub-Characteristic Average', average, 'Average maturity across listed quality sub-characteristics', '%')}
        ${metricCard('Weak Sub-Characteristics', weak, 'Sub-characteristics below 50% maturity')}
        ${metricCard('Conditional Sub-Characteristics', conditional, 'Sub-characteristics between 50% and 69% maturity')}
        ${metricCard('Sub-Characteristic Blockers', blocked, 'High/Critical risk blockers mapped to sub-characteristics')}
      </div>
      ${renderSubCharacteristicHelp()}
      ${tableWrap(`
      <table>
        <thead>
          <tr>
            <th>Quality Sub-Characteristic</th>
            <th>Gate</th>
            <th>Mapped Aspects & Rationale</th>
            <th>Aspect Realisation</th>
            <th>Maturity</th>
            <th>Weakest Aspect</th>
            <th>Evidence</th>
            <th>Blockers</th>
            <th>Main Weakness</th>
          </tr>
        </thead>
        <tbody>
          ${subCharacteristicRows(rows)}
        </tbody>
      </table>
      `)}
    </div>
  `
}

function renderLifecycleProcessMaturity(frameworks = []) {
  if (!frameworks.length) {
    return emptySection('Lifecycle Activity Maturity', 'No lifecycle activity maturity data available.')
  }

  const officialAverage = Math.round(
    frameworks.reduce((sum, item) => sum + (item.official_score ?? 0), 0) / frameworks.length
  )
  const highRisk = frameworks.filter(item => item.process_maturity_risk === 'High').length
  const unknownRisk = frameworks.filter(item => item.process_maturity_risk === 'Unknown').length

  return `
    <div class="card section">
      <h2>Lifecycle Activity Maturity</h2>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Lifecycle Maturity Score', officialAverage, 'Average maturity across assessed lifecycle activities', '%')}
        ${metricCard('High Risk Areas', highRisk, 'Lifecycle areas with blocking risk or insufficient maturity')}
        ${metricCard('Unknown Areas', unknownRisk, 'Lifecycle areas without enough formal activity assessment data')}
        ${metricCard('Frameworks', frameworks.length, 'Lifecycle frameworks included in this report')}
      </div>
      ${renderLifecycleHelp()}
      ${tableWrap(`
      <table>
        <thead>
          <tr>
            <th>Framework</th>
            <th>Standard</th>
            <th>Score</th>
            <th>Risk</th>
            <th>Coverage</th>
            <th>Main Blocker</th>
          </tr>
        </thead>
        <tbody>
          ${frameworks.map(item => `
            <tr>
              <td>${item.framework ?? '-'}</td>
              <td>${item.standard_context ?? '-'}</td>
              <td>${item.official_score ?? 0}% / ${item.maturity_band ?? '-'}</td>
              <td>${badge(item.process_maturity_risk)}</td>
              <td>${item.official_coverage ?? 0}% assessed / ${item.evidence_coverage ?? 0}% evidence</td>
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
              <th>Maturity</th>
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

function defaultTeamColumns() {
  return [
    'PdM/PgM/PjM AD/ADAS',
    '360 deg Perception AD/ADAS Safety',
    'Map (Vehicle) CA & AD/ADAS Non-Safety',
    'LaneLevelLocalization AD/ADAS Non-Safety',
    'MotionPlanner AD/ADAS Safety-Rule',
    'MotionPlanner AD/ADAS Safety-ML (SWC: DDTP)',
    'InterCommBev (Application Framework)',
    'Controller AD/ADAS Safety',
    'Product Integrity',
    'Product Delivery (Optional)',
  ]
}

function matrixColumns(rows = []) {
  const columns = []
  rows.forEach(row => {
    ;(row.cells ?? []).forEach(cell => {
      if (cell.team && !columns.includes(cell.team)) columns.push(cell.team)
    })
  })
  return columns.length ? columns : defaultTeamColumns()
}

function matrixCell(row, team) {
  const cell = (row.cells ?? []).find(item => item.team === team)
  if (!cell || cell.role === '-') {
    return '<span class="matrixEmpty">-</span>'
  }
  if (cell.role === 'N/A') {
    return '<span class="matrixEmpty">N/A</span>'
  }
  const maturity = cell.maturity_state == null ? '-' : maturityState(cell.maturity_state)
  const blocker = cell.blocking_risk_count ? `<div class="matrixReason">${cell.blocking_risk_count} blocker</div>` : ''
  const weakness = cell.main_weakness ? `<div class="matrixReason">${cell.main_weakness}</div>` : ''
  return `
    <div class="matrixCell">
      <div>${badge(cell.role)} ${maturity}</div>
      <div class="matrixMeta">${cell.work_product_status ?? '-'} / ${cell.evidence_status ?? '-'}</div>
      ${blocker}
      ${weakness}
    </div>
  `
}

function shortText(text = '', max = 150) {
  const value = String(text || '-')
  return value.length > max ? `${value.slice(0, max)}...` : value
}

function renderTeamActivityWorkProductMatrix(rows = []) {
  if (!rows.length) {
    return emptySection('Team Activity & Work Product Matrix', 'No configured gate assessment definitions or team activity assignments are available for the current gate.')
  }

  const columns = matrixColumns(rows)
  const accountableGaps = rows.filter(row => !(row.cells ?? []).some(cell => cell.role === 'A')).length
  const blockedRows = rows.filter(row => (row.blocking_risk_count ?? 0) > 0 || row.judgement === 'Fail').length
  const acceptedRows = rows.filter(row => row.judgement === 'Pass').length
  const average = Math.round(rows.reduce((sum, row) => sum + ((row.maturity_state ?? 0) / 4 * 100), 0) / rows.length)

  return `
    <div class="card section">
      <h2>Team Activity & Work Product Matrix</h2>
      <p>Rows are lifecycle activities. Columns are ADAS teams. Cells show responsibility, activity maturity, work product status, evidence status, and blocking context.</p>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Activity Rows', rows.length, 'Applicable lifecycle activities shown in the matrix')}
        ${metricCard('Average Activity Maturity', average, 'Average maturity of matrix rows', '%')}
        ${metricCard('Blocked / Failed Rows', blockedRows, 'Rows with Fail judgement or blocking risk context')}
        ${metricCard('Accountable Gaps', accountableGaps, 'Rows without an accountable team in the activity-team responsibility model')}
      </div>
      ${renderTeamMatrixHelp()}
      ${tableWrap(`
      <table class="teamMatrixTable">
        <thead>
          <tr>
            <th>Framework / Activity</th>
            ${columns.map(team => `<th>${team}</th>`).join('')}
            <th>Assessment Detail</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(row => `
            <tr>
              <td>
                <strong>${row.framework ?? '-'}</strong><br>
                ${row.activity_name ?? '-'}<br>
                <span class="matrixMeta">${row.gate ?? '-'} / ${row.quality_characteristic ?? '-'} / ${row.quality_subcharacteristic ?? '-'}</span>
              </td>
              ${columns.map(team => `<td>${matrixCell(row, team)}</td>`).join('')}
              <td>
                ${badge(row.judgement)} ${maturityState(row.maturity_state)}<br>
                <span class="matrixMeta">Responsible Role: ${row.responsible_role ?? '-'}</span><br>
                <span class="matrixMeta">Expected: ${row.expected_maturity ?? '-'}</span><br>
                <span class="matrixMeta">Work Product: ${row.required_work_product ?? '-'}</span><br>
                <span class="matrixMeta" title="${row.check_detail ?? ''}">Check: ${shortText(row.check_detail, 120)}</span><br>
                ${row.mapped_team ? `<span class="matrixMeta">Mapped team: ${row.mapped_team}</span>` : `<span class="matrixReason">${row.team_assignment_status ?? 'Needs team assignment'}</span>`}
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
      `)}
      <p>Accepted activity rows: ${acceptedRows}. Product Integrity can appear as Reviewer / Approver, but it does not replace the accountable activity owner.</p>
    </div>
  `
}

export async function loadAndRenderAuditReport(projectId) {
  const panel = $('auditReportPanel')
  if (!panel || !projectId) return

  panel.innerHTML = '<div class="loading">Loading assessment dashboard...</div>'

  try {
    const report = await api.getAssessmentDashboard(projectId)
    renderAuditReport(report)
  } catch (err) {
    panel.innerHTML = ''
    showError(`Assessment dashboard unavailable: ${err.message}`)
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
          <h2>Assessment Dashboard</h2>
          <p>Snapshot ${report.snapshot_at ?? '-'} / Current gate ${report.current_gate ?? 'Unknown'}</p>
        </div>
        <div>${badge(snapshot.recommended_attention_level)}</div>
      </div>
      <div class="grid4" style="margin-top:12px">
        ${metricCard('Recommended Attention', snapshot.recommended_attention_level, 'Combined management attention signal')}
        ${metricCard('Product Risk', snapshot.product_risk, 'Risk exposure from product risks and evidence gaps')}
        ${metricCard('Process Maturity Risk', snapshot.process_maturity_risk, 'Risk caused by weak lifecycle activity maturity or missing formal assessment data')}
        ${metricCard('Gate Progression Signal', gate.gate_progression_signal, 'Current gate readiness signal, not an approval decision')}
        ${metricCard('Risk Confidence', confidence.level, confidence.primary_reason)}
        ${metricCard('Integrated Score', snapshot.official_integrated_score, 'Formal gate readiness score for this report', '%')}
        ${metricCard('Open Risks', snapshot.open_risk_count, 'Open project risks in this report snapshot')}
        ${metricCard('Evidence Gaps', snapshot.evidence_gap_count, 'Non-passing or missing evidence gaps')}
      </div>
      ${renderExecutiveLegend()}
    </div>

    <div class="grid2">
      <div class="card section">
        <h2>Gate Readiness</h2>
        <table>
          <tbody>
            <tr><td>Gate maturity</td><td>${gate.official_maturity ?? 0}%</td></tr>
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
            <tr><td>Assessment coverage</td><td>${confidence.official_assessment_coverage ?? 0}%</td></tr>
            <tr><td>Review freshness</td><td>${confidence.review_freshness ?? 0}%</td></tr>
            <tr><td>Critical unknowns</td><td>${confidence.critical_unknown_count ?? 0}</td></tr>
          </tbody>
        </table>
        ${renderRiskConfidenceHelp()}
      </div>
    </div>

    ${renderQualityGateMaturity(report.quality_gate_maturity)}
    ${renderProjectRiskPosture(report.project_risk_posture)}
    ${renderQualitySubCharacteristicMaturity(report.quality_subcharacteristic_maturity)}
    ${renderLifecycleProcessMaturity(report.lifecycle_process_maturity)}
    ${renderTeamActivityWorkProductMatrix(report.team_activity_work_product_matrix)}
  `
}
