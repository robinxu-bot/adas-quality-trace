/**
 * Create / Edit Project modal — 5-step wizard.
 *
 * All scope decisions are held in S.formScope (frontend memory) until
 * Step 5 confirm. A single POST /projects call persists everything atomically.
 */
import { S } from '../state.js'
import { api } from '../api.js'
import { showError } from '../utils.js'
import { ASPECTS } from '../constants/aspects.js'
import { renderProjects } from './ProjectView.js'

const $ = id => document.getElementById(id)

const APPLICABILITY_VALUES = [
  'Applicable',
  'Partially applicable',
  'Not applicable',
  'Deferred',
  'Covered by platform',
  'Covered by supplier',
  'Out of project scope',
]

function tag(a) {
  return `<span class="tag">${a}</span>`
}

export function openModal(mode = 'create') {
  S.formMode = mode
  S.formScope = []
  S.showExcluded = false
  S.mAspect = 'All'
  S.mApp = 'All'

  const p = mode === 'edit' ? S.selectedProject : null

  $('modalTitle').textContent = mode === 'edit' ? 'Edit Quality Scope' : 'Create Project'
  $('mId').value = p?.project_id ?? ''
  $('mName').value = p?.name ?? ''
  $('mProductType').value = p?.product_type ?? ''
  $('mPhase').value = p?.phase ?? 'Concept'
  $('mBoundary').value = p?.system_boundary ?? ''
  $('mAssessmentTarget').value = p?.assessment_target ?? ''
  $('mCustomer').value = p?.customer ?? ''
  $('mProduct').value = p?.product_line ?? 'ADAS'

  // Disable project_id field when editing
  $('mId').disabled = mode === 'edit'

  updateProductDesc()

  // Load aspects checkboxes
  renderAspectCheckboxes(p?.selected_aspects ?? ['QM', 'FuSA', 'SOTIF'])

  // Load scope — use existing scope when editing, else load from API
  if (mode === 'edit' && p?.scope?.length) {
    S.formScope = p.scope.map(d => ({ ...d }))
    renderScopeFilters()
    renderRows()
  } else {
    loadRecommendations($('mProduct').value)
  }

  $('modal').classList.add('active')
}

function updateProductDesc() {
  const descs = {
    ADAS: 'Camera radar fusion, AEB, LKA, HMI warning, diagnostics and degraded operation.',
    AreneTools: 'Engineering tools and traceability tooling.',
    WovenCity: 'Smart city mobility services and infrastructure integration.',
    CloudAI: 'Cloud platforms, AI inference service and operational monitoring.',
  }
  $('mProductDesc').textContent = descs[$('mProduct').value] ?? ''
}

function renderAspectCheckboxes(selected) {
  $('mAspects').innerHTML = ASPECTS.map(a => `
    <label style="display:inline-flex;align-items:center;gap:5px;margin:3px 6px 3px 0;font-size:12px">
      <input type="checkbox" value="${a}" ${selected.includes(a) ? 'checked' : ''}> ${a}
    </label>
  `).join('')
}

function selectedAspects() {
  return [...$('mAspects').querySelectorAll('input[type=checkbox]:checked')]
    .map(cb => cb.value)
}

async function loadRecommendations(productLine) {
  $('mScopeLoading').classList.remove('hidden')
  $('mRows').innerHTML = ''

  try {
    const [recs, model] = await Promise.all([
      api.getProductLineRecs(productLine),
      S.commonModel ?? api.getCommonModel().then(m => { S.commonModel = m; return m }),
    ])

    // Build subchar_id → { subchar_name, characteristic_name } lookup from common model
    const subcharInfo = {}
    for (const char of model.characteristics) {
      for (const sub of char.subcharacteristics) {
        subcharInfo[sub.id] = {
          subchar_name: sub.name,
          characteristic_id: char.id,
          characteristic_name: char.name,
        }
      }
    }

    // Build initial formScope from recommendations
    S.formScope = recs.map(r => ({
      subchar_id: r.subchar_id,
      subchar_name: subcharInfo[r.subchar_id]?.subchar_name ?? r.subchar_id,
      characteristic_name: subcharInfo[r.subchar_id]?.characteristic_name ?? '',
      applicability: r.recommended_applicability,
      recommended_applicability: r.recommended_applicability,
      rationale: r.default_rationale ?? '',
      selected_quality_aspects: r.recommended_aspects ?? [],
      manual_override: false,
      review_status: 'Draft',
    }))
  } catch (err) {
    showError(`Failed to load recommendations: ${err.message}`)
  } finally {
    $('mScopeLoading').classList.add('hidden')
  }

  renderScopeFilters()
  renderRows()
}

function renderScopeFilters() {
  $('mAspectFilter').innerHTML = ['All', ...ASPECTS]
    .map(a => `<option>${a}</option>`).join('')
  $('mAspectFilter').value = S.mAspect

  $('mAppFilter').innerHTML = ['All', ...APPLICABILITY_VALUES]
    .map(a => `<option>${a}</option>`).join('')
  $('mAppFilter').value = S.mApp
}

function isExcluded(applicability) {
  return ['Not applicable', 'Covered by platform', 'Covered by supplier', 'Out of project scope']
    .includes(applicability)
}

export function renderRows() {
  const rows = S.formScope.filter(x => {
    if (!S.showExcluded && isExcluded(x.applicability)) return false
    if (S.mAspect !== 'All' && !(x.selected_quality_aspects ?? []).includes(S.mAspect)) return false
    if (S.mApp !== 'All' && x.applicability !== S.mApp) return false
    return true
  })

  $('mRows').innerHTML = rows.map(x => `
    <tr>
      <td style="font-size:11px;color:#64748b">${x.characteristic_name ?? ''}</td>
      <td><b>${x.subchar_name ?? x.subchar_id}</b></td>
      <td><span class="tag">${x.recommended_applicability ?? '—'}</span></td>
      <td>
        <select data-id="${x.subchar_id}" data-f="applicability">
          ${APPLICABILITY_VALUES.map(v =>
            `<option ${v === x.applicability ? 'selected' : ''}>${v}</option>`
          ).join('')}
        </select>
      </td>
      <td><textarea data-id="${x.subchar_id}" data-f="rationale" rows="2">${x.rationale ?? ''}</textarea></td>
      <td>${(x.selected_quality_aspects ?? []).map(tag).join('')}</td>
      <td>${x.manual_override ? '<span class="tag warn">Manual</span>' : '<span class="tag">Recommended</span>'}</td>
    </tr>
  `).join('')

  $('mRows').querySelectorAll('[data-id]').forEach(el => {
    el.addEventListener('change', () => {
      const item = S.formScope.find(x => x.subchar_id === el.dataset.id)
      if (!item) return
      item[el.dataset.f] = el.value
      item.manual_override = true
      renderRows()
    })
  })
}

export async function saveProject() {
  const projectId = $('mId').value.trim()
  const name = $('mName').value.trim()
  if (!projectId || !name) {
    showError('Project ID and Name are required.')
    return
  }

  const payload = {
    project_id: projectId,
    name,
    product_type: $('mProductType').value.trim() || 'ADAS ECU',
    product_line: $('mProduct').value,
    phase: $('mPhase').value,
    system_boundary: $('mBoundary').value.trim(),
    assessment_target: $('mAssessmentTarget').value.trim() || null,
    customer: $('mCustomer').value.trim() || null,
    selected_aspects: selectedAspects(),
    scope: S.formScope.map(d => ({
      subchar_id: d.subchar_id,
      applicability: d.applicability,
      rationale: d.rationale || null,
      selected_quality_aspects: d.selected_quality_aspects ?? [],
      manual_override: d.manual_override,
      review_status: d.review_status ?? 'Draft',
    })),
  }

  try {
    if (S.formMode === 'edit' && S.editId) {
      // Editing: update metadata + batch update scope separately
      await api.updateProject(S.editId, {
        name: payload.name,
        product_type: payload.product_type,
        phase: payload.phase,
        system_boundary: payload.system_boundary,
        assessment_target: payload.assessment_target,
        customer: payload.customer,
        selected_aspects: payload.selected_aspects,
      })
      await api.batchUpdateScope(S.editId, payload.scope)
      const updated = await api.getProject(S.editId)
      const idx = S.projects.findIndex(p => p.id === S.editId)
      if (idx >= 0) S.projects[idx] = updated
      S.selectedProject = updated
    } else {
      const created = await api.createProject(payload)
      S.projects.unshift(created)
      S.selectedProject = created
    }

    closeModal()
    renderProjects()
  } catch (err) {
    showError(`Failed to save project: ${err.message}`)
  }
}

export function closeModal() {
  $('modal').classList.remove('active')
  S.formScope = []
  S.editId = null
}

// Wire modal events (called from main.js)
export function initModalEvents() {
  $('closeModal').addEventListener('click', closeModal)
  $('cancelBtn').addEventListener('click', closeModal)
  $('saveBtn').addEventListener('click', saveProject)

  $('mProduct').addEventListener('change', () => {
    updateProductDesc()
    loadRecommendations($('mProduct').value)
  })

  $('mShowExcluded').addEventListener('click', () => {
    S.showExcluded = !S.showExcluded
    $('mShowExcluded').textContent = S.showExcluded ? 'Hide excluded' : 'Show excluded'
    renderRows()
  })

  $('mAspectFilter').addEventListener('change', () => {
    S.mAspect = $('mAspectFilter').value
    renderRows()
  })

  $('mAppFilter').addEventListener('change', () => {
    S.mApp = $('mAppFilter').value
    renderRows()
  })
}
