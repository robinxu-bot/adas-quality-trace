import { S } from '../state.js'
import { api } from '../api.js'
import { showError } from '../utils.js'
import { buildCommon, renderSankey, renderDetail } from '../components/sankey.js'

const $ = id => document.getElementById(id)

function tag(a) {
  return `<span class="tag">${a}</span>`
}

// Cached graph data for the common Sankey (rebuilt when model changes)
let _commonGraphData = null

export async function renderCommon() {
  // Load common model if not cached
  if (!S.commonModel) {
    try {
      S.commonModel = await api.getCommonModel()
      _commonGraphData = null  // invalidate graph cache when model reloads
    } catch (err) {
      showError(`Failed to load common model: ${err.message}`)
      return
    }
  }

  const { characteristics } = S.commonModel

  // Stats
  const subCount = characteristics.reduce((n, c) => n + c.subcharacteristics.length, 0)
  $('cChars').textContent = characteristics.length
  $('cSubs').textContent = subCount

  // Characteristic selector buttons
  if (!S.commonChar && characteristics.length) {
    S.commonChar = characteristics[0].id
  }
  $('commonButtons').innerHTML = characteristics.map(c =>
    `<button class="${S.commonChar === c.id ? 'active' : ''}" data-id="${c.id}">${c.name}</button>`
  ).join('')
  $('commonButtons').querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      S.commonChar = btn.dataset.id
      renderCommon()
    })
  })

  // Full model grid
  $('fullModel').innerHTML = characteristics.map(c => `
    <div class="modelItem">
      <b>${c.name}</b>
      <div>${c.subcharacteristics.map(s => `<span class="pill">${s.name}</span>`).join('')}</div>
    </div>
  `).join('')

  // Selected characteristic subcharacteristics
  const selected = characteristics.find(c => c.id === S.commonChar)
  if (selected) {
    $('selectedTitle').textContent = selected.name
    $('selectedHint').textContent = 'Original full ISO IEC 25010 subcharacteristics under selected characteristic.'
    $('subGrid').innerHTML = selected.subcharacteristics.map(s => `
      <div class="modelItem">
        <b>${s.name}</b>
        <p>${s.description ?? `Common ISO IEC 25010 description for ${s.name}.`}</p>
        ${(s.applicable_aspects ?? []).map(tag).join('')}
      </div>
    `).join('')
  }

  // Common Sankey
  _renderCommonSankey()
}

function _renderCommonSankey() {
  if (!_commonGraphData) {
    _commonGraphData = buildCommon(S.commonModel)
  }

  renderSankey('commonSankey', _commonGraphData, {
    common: true,
    selected: S.commonNode,
    onSelect: _toggleCommonNode,
    onClear: _clearCommonSelection,
  })

  renderDetail('commonDetail', _commonGraphData.nodes.find(n => n.id === S.commonNode) ?? null, _commonGraphData)
}

function _toggleCommonNode(node) {
  S.commonNode = S.commonNode === node.id ? null : node.id
  _renderCommonSankey()
}

function _clearCommonSelection() {
  if (!S.commonNode) return
  S.commonNode = null
  _renderCommonSankey()
}
