/**
 * ProjectSankey.js — Project Specific Sankey Trace View (Slice 5).
 *
 * Data flow:
 *   api.getProjectFull(id) → normalize() → S.projectFull
 *   buildProject(S.projectFull, showExcluded) → graphData
 *   filterGraph(graphData, S.filters) → filteredData
 *   renderSankey('projectSankey', filteredData, { selected, onSelect })
 *   onSelect → branch() → renderSankey() + renderDetail()
 */
import { S, normalize } from '../state.js'
import { api } from '../api.js'
import { showError } from '../utils.js'
import { ASPECTS } from '../constants/aspects.js'
import {
  buildProject,
  filterGraph,
  renderSankey,
  renderDetail,
  branch,
} from '../components/sankey.js'

const $ = id => document.getElementById(id)

// Raw unfiltered graph for the current project (rebuilt when /full data changes)
let _rawGraph = null

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Load /full data for the selected project and render the Project Sankey.
 * Called once when the user opens the Project Sankey view.
 */
export async function loadAndRenderProjectSankey() {
  const project = S.selectedProject
  if (!project) return

  $('projectSankey').innerHTML = '<div class="loading">Loading trace data…</div>'

  try {
    const fullData = await api.getProjectFull(project.id)
    S.projectFull = normalize(fullData)
    _rawGraph = null  // invalidate cache
    S.selectedNode = null
  } catch (err) {
    showError(`Failed to load project trace data: ${err.message}`)
    $('projectSankey').innerHTML = '<p style="color:#ef4444;padding:12px">Failed to load Sankey data.</p>'
    return
  }

  _rebuildAndRender()
  _renderFilters()
}

/**
 * Re-render the Sankey with current filters (no API call).
 * Called after filter changes.
 */
export function rerenderProjectSankey() {
  if (!S.projectFull) return
  _rebuildAndRender()
}

// ─── Internal ─────────────────────────────────────────────────────────────────

function _rebuildAndRender() {
  if (!S.projectFull) return

  // Build graph from normalized data
  if (!_rawGraph) {
    _rawGraph = buildProject(S.projectFull, S.filters?.showExcluded ?? false)
  }

  // Apply filters
  const filtered = filterGraph(_rawGraph, {
    char: S.filters?.char ?? 'All',
    aspect: S.filters?.aspect ?? 'All',
    risk: S.filters?.risk ?? 'All',
    evidence: S.filters?.evidence ?? 'All',
    search: S.filters?.search ?? '',
  })

  renderSankey('projectSankey', filtered, {
    selected: S.selectedNode,
    onSelect: (node) => {
      S.selectedNode = node.id
      renderDetail('projectNodeDetail', node, _rawGraph)
      // Re-render to update highlight — use full unfiltered graph for branch()
      const reFiltered = filterGraph(_rawGraph, {
        char: S.filters?.char ?? 'All',
        aspect: S.filters?.aspect ?? 'All',
        risk: S.filters?.risk ?? 'All',
        evidence: S.filters?.evidence ?? 'All',
        search: S.filters?.search ?? '',
      })
      renderSankey('projectSankey', reFiltered, {
        selected: S.selectedNode,
        onSelect: (n) => {
          S.selectedNode = n.id
          renderDetail('projectNodeDetail', n, _rawGraph)
          rerenderProjectSankey()
        },
      })
    },
  })

  const _onSelectFromDetail = (node) => {
    S.selectedNode = node.id
    rerenderProjectSankey()
  }

  renderDetail(
    'projectNodeDetail',
    S.selectedNode ? _rawGraph.nodes.find(n => n.id === S.selectedNode) ?? null : null,
    _rawGraph,
    _onSelectFromDetail,
  )
}

function _renderFilters() {
  const charSelect = $('fChar')
  const aspectSelect = $('fAspect')
  const riskSelect = $('fRisk')
  const evidenceSelect = $('fEvidence')
  const searchInput = $('fSearch')
  const showExcBtn = $('fShowExcluded')

  if (!charSelect) return

  // Populate characteristic options from common model
  const chars = S.commonModel?.characteristics ?? []
  charSelect.innerHTML = '<option value="All">All Characteristics</option>' +
    chars.map(c => `<option value="${c.id}">${c.name}</option>`).join('')
  charSelect.value = S.filters?.char ?? 'All'

  aspectSelect.innerHTML = '<option value="All">All Aspects</option>' +
    ASPECTS.map(a => `<option>${a}</option>`).join('')
  aspectSelect.value = S.filters?.aspect ?? 'All'

  riskSelect.innerHTML = ['All', 'Critical', 'High', 'Medium', 'Low']
    .map(v => `<option>${v}</option>`).join('')
  riskSelect.value = S.filters?.risk ?? 'All'

  evidenceSelect.innerHTML = ['All', 'Complete', 'Partial', 'Missing', 'Failed']
    .map(v => `<option>${v}</option>`).join('')
  evidenceSelect.value = S.filters?.evidence ?? 'All'

  searchInput.value = S.filters?.search ?? ''

  // Show/hide excluded button state
  if (showExcBtn) {
    showExcBtn.textContent = (S.filters?.showExcluded) ? 'Hide excluded items' : 'Show excluded items'
    showExcBtn.className = (S.filters?.showExcluded) ? 'active' : 'soft'
  }
}

// ─── Filter event wiring — called from main.js ───────────────────────────────

export function initProjectSankeyFilters() {
  const charSelect = $('fChar')
  const aspectSelect = $('fAspect')
  const riskSelect = $('fRisk')
  const evidenceSelect = $('fEvidence')
  const searchInput = $('fSearch')
  const showExcBtn = $('fShowExcluded')

  if (!charSelect) return

  function _updateFilters() {
    S.filters = {
      char: charSelect.value,
      aspect: aspectSelect.value,
      risk: riskSelect.value,
      evidence: evidenceSelect.value,
      search: searchInput.value,
      showExcluded: S.filters?.showExcluded ?? false,
    }
    // Invalidate raw graph when showExcluded changes (affects which nodes are built)
    rerenderProjectSankey()
  }

  ;[charSelect, aspectSelect, riskSelect, evidenceSelect].forEach(el =>
    el.addEventListener('change', _updateFilters)
  )
  searchInput.addEventListener('input', _updateFilters)

  showExcBtn?.addEventListener('click', () => {
    S.filters = { ...(S.filters ?? {}), showExcluded: !(S.filters?.showExcluded ?? false) }
    _rawGraph = null  // rebuild with new showExcluded setting
    _rebuildAndRender()
    _renderFilters()
  })
}
