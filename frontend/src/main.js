import './styles/main.css'
import { S } from './state.js'
import { api } from './api.js'
import { showError } from './utils.js'
import { renderCommon } from './views/CommonView.js'
import { renderProjects } from './views/ProjectView.js'
import { openModal, initModalEvents } from './views/Modal.js'
import {
  loadAndRenderProjectSankey,
  initProjectSankeyFilters,
} from './views/ProjectSankey.js'

const $ = id => document.getElementById(id)

// --- View switching ---

function showCommon() {
  $('commonView').classList.remove('hidden')
  $('projectView').classList.add('hidden')
  $('tabCommon').classList.add('active')
  $('tabProject').classList.remove('active')
  renderCommon()
}

function showProject() {
  $('commonView').classList.add('hidden')
  $('projectView').classList.remove('hidden')
  $('tabCommon').classList.remove('active')
  $('tabProject').classList.add('active')
  renderProjects()
}

// --- Nav events ---

$('tabCommon').addEventListener('click', showCommon)
$('tabProject').addEventListener('click', showProject)

$('resetBtn').addEventListener('click', async () => {
  if (!confirm('Reset demo data? This will seed two sample ADAS projects.')) return
  try {
    const result = await api.seedDemo()
    S.projects = []
    S.selectedProject = null
    showProject()
    alert(`Seeded ${result.seeded} project(s), skipped ${result.skipped}.`)
  } catch (err) {
    showError(`Seed failed: ${err.message}`)
  }
})

// --- Project view events ---

$('newProjectBtn').addEventListener('click', () => openModal('create'))

$('backBtn').addEventListener('click', () => {
  S.selectedProject = null
  S.selectedNode = null
  renderProjects()
})

$('editScopeBtn').addEventListener('click', () => {
  S.editId = S.selectedProject?.id
  openModal('edit')
})

$('exportBtn').addEventListener('click', async () => {
  const p = S.selectedProject
  if (!p) return
  try {
    const response = await fetch(`/api/v1/projects/${p.id}/export`)
    if (!response.ok) throw new Error(await response.text())
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${p.project_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    showError(`Export failed: ${err.message}`)
  }
})

$('deleteProjectBtn').addEventListener('click', async () => {
  const p = S.selectedProject
  if (!p) return
  if (!confirm(`Delete project "${p.name}"? This cannot be undone.`)) return
  try {
    await api.deleteProject(p.id)
    S.selectedProject = null
    S.projects = S.projects.filter(x => x.id !== p.id)
    showProject()
  } catch (err) {
    showError(`Delete failed: ${err.message}`)
  }
})

// Import
$('importBtn').addEventListener('click', () => $('importFileInput').click())
$('importFileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0]
  if (!file) return
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    const imported = await api.importProject(data)
    S.projects.unshift(imported)
    showError('')  // clear any previous error
    alert(`Project "${imported.project_id}" imported successfully.`)
    showProject()
  } catch (err) {
    showError(`Import failed: ${err.message}`)
  }
  e.target.value = ''  // reset so same file can be re-imported after delete
})

$('toggleTraceBtn').addEventListener('click', async () => {
  if (!S.selectedProject) return
  // Toggle visibility of Sankey panel
  const traceDiv = $('projectTrace')
  const isHidden = traceDiv.classList.contains('hidden')
  if (isHidden) {
    traceDiv.classList.remove('hidden')
    $('toggleTraceBtn').classList.add('active')
    await loadAndRenderProjectSankey()
  } else {
    traceDiv.classList.add('hidden')
    $('toggleTraceBtn').classList.remove('active')
  }
})

// --- Filter events ---
initProjectSankeyFilters()

// --- Modal events ---
initModalEvents()

// --- Init ---

document.addEventListener('DOMContentLoaded', async () => {
  // Pre-load common model so wizard Step 4 doesn't need to wait
  try {
    S.commonModel = await api.getCommonModel()
  } catch (err) {
    showError('Could not load common model from API. Check backend connection.')
  }
  showCommon()
})
