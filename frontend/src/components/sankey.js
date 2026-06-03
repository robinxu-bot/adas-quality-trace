/**
 * sankey.js — Sankey graph construction and D3 rendering.
 *
 * Two build paths:
 *   buildCommon(commonModel)       — for the Common View (ISO model, no real trace data)
 *   buildProject(normalizedData)   — for the Project Sankey (real DB data via /full)
 *
 * renderSankey, branch, filter, rows, renderDetail are adapted from V5.9.1.
 * Key differences from V5.9.1:
 *   - No mock data generation (reqs(), eStatus(), rLevel(), rStatus() removed)
 *   - Node IDs are either short deterministic keys (Common View) or DB UUIDs (Project)
 *   - D3 and d3-sankey loaded as npm packages, not CDN globals
 */

import * as d3Base from 'd3'
import { sankey as d3Sankey, sankeyLinkHorizontal } from 'd3-sankey'

// d3-sankey is a UMD bundle that may attach to window.d3 — use the named import directly
const d3 = d3Base

const LAYERS = [
  'Product Quality',
  'Quality Characteristic',
  'Quality Subcharacteristic',
  'Quality Goal',
  'Quality Requirement',
  'Sub Quality Requirement',
  'Architecture Element',
  'Software Module',
  'Test Case',
  'Test Result',
  'Risk Status',
]

function makeNode(id, type, label, source, desc, extra = {}) {
  return { id, type, label, source, desc, ...extra }
}

function makeLink(source, target) {
  return { source, target, value: 1 }
}

function nodeColor(n) {
  const map = {
    Standard: '#0f172a',
    QualityCharacteristic: '#2563eb',
    QualitySubCharacteristic: '#7c3aed',
    QualityGoal: '#4f46e5',
    QualityRequirement: '#6366f1',
    SubQualityRequirement: '#a855f7',
    ArchitectureElement: '#06b6d4',
    SoftwareModule: '#14b8a6',
    TestCase: '#64748b',
    TestResult: '#10b981',
    RiskStatus: '#ef4444',
  }
  return map[n.type] ?? '#94a3b8'
}

// ─────────────────────────────────────────────
// buildCommon — Common View Sankey
// Uses the /common/model API response (no real trace data below QualitySubCharacteristic).
// Generates placeholder Goal, Requirement, SubReq, ArchElem, Module, TestCase, TestResult,
// RiskStatus nodes to show the full 11-layer trace structure as a reference.
// ─────────────────────────────────────────────

export function buildCommon(commonModel) {
  const nodes = []
  const links = []

  nodes.push(makeNode('STD', 'Standard', 'ISO IEC 25010 Product Quality', 'ISO IEC 25010', 'Product Quality root.'))

  for (const char of commonModel.characteristics) {
    if (!char.subcharacteristics.length) continue

    nodes.push(makeNode(char.id, 'QualityCharacteristic', char.name, 'ISO IEC 25010', char.description ?? ''))
    links.push(makeLink('STD', char.id))

    // One shared placeholder arch/module per characteristic (same as V5.9.1 ARCH pattern)
    const aeId = `AE_COMMON_${char.id}`
    const swId = `SW_COMMON_${char.id}`
    nodes.push(makeNode(aeId, 'ArchitectureElement', `${char.name} Element`, 'Common Architecture', `Architecture element for ${char.name}.`))
    nodes.push(makeNode(swId, 'SoftwareModule', `${char.name.toLowerCase().replace(/\s+/g, '_')}.c`, 'Common Software', `Software module for ${char.name}.`))
    links.push(makeLink(aeId, swId))

    for (const sub of char.subcharacteristics) {
      const aspects = sub.applicable_aspects ?? []

      nodes.push(makeNode(sub.id, 'QualitySubCharacteristic', sub.name, 'Common Model', sub.description ?? '', {
        aspects,
        evidence: 'Complete',
        riskLevel: 'Low',
        riskStatus: 'Closed',
      }))
      links.push(makeLink(char.id, sub.id))

      const qgId = `QG_COMMON_${sub.id}`
      nodes.push(makeNode(qgId, 'QualityGoal', `${sub.name} goal`, 'Common Quality Goal', `Goal for ${sub.name}.`, {
        aspects, evidence: 'Complete', riskLevel: 'Low', riskStatus: 'Closed',
      }))
      links.push(makeLink(sub.id, qgId))

      const qrId = `QR_COMMON_${sub.id}_1`
      nodes.push(makeNode(qrId, 'QualityRequirement', `${sub.name} requirement`, 'Common Requirement',
        `Requirement derived from ${sub.name}.`, {
          aspects, evidence: 'Complete', riskLevel: 'Low', riskStatus: 'Closed',
        }))
      links.push(makeLink(qgId, qrId))

      const sqrId = `SQR_COMMON_${sub.id}_1_1`
      nodes.push(makeNode(sqrId, 'SubQualityRequirement', `${sub.name} criterion`, 'Common Sub Requirement',
        `Acceptance criterion for ${sub.name}.`, {
          aspects, evidence: 'Complete', riskLevel: 'Low', riskStatus: 'Closed',
        }))
      links.push(makeLink(qrId, sqrId))
      links.push(makeLink(sqrId, aeId))

      const tcId = `TC_COMMON_${sub.id}_1_1`
      nodes.push(makeNode(tcId, 'TestCase', `${sub.name} test`, 'Common Verification',
        `Test case for ${sub.name}.`, {
          aspects, evidence: 'Complete', riskLevel: 'Low', riskStatus: 'Closed',
        }))
      links.push(makeLink(swId, tcId))

      const trId = `TR_COMMON_${sub.id}_1_1`
      nodes.push(makeNode(trId, 'TestResult', `PASS ${sub.name}`, 'Common Test Report',
        'Evidence status Complete.', {
          aspects, evidence: 'Complete', riskLevel: 'Low', riskStatus: 'Closed',
        }))
      links.push(makeLink(tcId, trId))

      const rsId = `RS_COMMON_${sub.id}_1_1`
      nodes.push(makeNode(rsId, 'RiskStatus', 'Closed / Low', 'Common Quality Risk',
        'Risk status for this subcharacteristic.', {
          aspects, evidence: 'Complete', riskLevel: 'Low', riskStatus: 'Closed',
        }))
      links.push(makeLink(trId, rsId))
    }
  }

  return { nodes, links }
}

// ─────────────────────────────────────────────
// buildProject — Project Sankey
// Uses normalizedData from state.normalize() — all Maps keyed by UUID.
// Only includes subcharacteristics with Applicable / Partially applicable / Deferred scope.
// ─────────────────────────────────────────────

const INCLUDED_APPLICABILITY = new Set(['Applicable', 'Partially applicable', 'Deferred'])

export function buildProject(normalizedData, showExcluded = false) {
  const { project, scope, goals, reqs, subReqs, archElems, modules, testCases, testResults, risks } = normalizedData
  const nodes = []
  const links = []

  nodes.push(makeNode('STD', 'Standard', 'ISO IEC 25010 Product Quality', 'ISO IEC 25010', 'Product Quality root.'))

  // Group scope decisions by characteristic (we need a characteristic_id from scope decision)
  const charGroups = new Map()
  for (const [subcharId, decision] of scope) {
    if (!showExcluded && !INCLUDED_APPLICABILITY.has(decision.applicability)) continue
    const charId = decision.characteristic_id
    if (!charId) continue
    if (!charGroups.has(charId)) {
      charGroups.set(charId, { name: decision.characteristic_name ?? charId, decisions: [] })
    }
    charGroups.get(charId).decisions.push(decision)
  }

  // Collect architecture elements and modules used in this project
  const usedAeIds = new Set()
  for (const req of reqs.values()) {
    if (req.architecture_element_id) usedAeIds.add(req.architecture_element_id)
  }

  for (const [charId, { name: charName, decisions }] of charGroups) {
    // Only include decisions that have at least one goal, OR include all if no goals exist at all
    const hasAnyGoals = goals.size > 0
    const decisionsWithGoals = hasAnyGoals
      ? decisions.filter(d => [...goals.values()].some(g => g.scope_decision_id === d.id))
      : decisions
    const decisionsToShow = decisionsWithGoals.length > 0 ? decisionsWithGoals : decisions

    nodes.push(makeNode(charId, 'QualityCharacteristic', charName, 'ISO IEC 25010', `Quality characteristic ${charName}.`))
    links.push(makeLink('STD', charId))

    for (const decision of decisionsToShow) {
      const aspects = decision.selected_quality_aspects ?? []

      nodes.push(makeNode(decision.id, 'QualitySubCharacteristic', decision.subchar_name ?? decision.subchar_id,
        'Project Quality Scope', '', {
          aspects,
          evidence: 'Missing',
          riskLevel: 'Low',
          riskStatus: 'Open',
          subchar_id: decision.subchar_id,
        }))
      links.push(makeLink(charId, decision.id))

      // Goals under this scope decision
      for (const goal of goals.values()) {
        if (goal.scope_decision_id !== decision.id) continue

        nodes.push(makeNode(goal.id, 'QualityGoal', goal.goal_text, 'Project Quality Goal', goal.description ?? '', {
          aspects,
        }))
        links.push(makeLink(decision.id, goal.id))

        // Requirements under this goal
        for (const req of reqs.values()) {
          if (req.goal_id !== goal.id) continue
          const reqAspects = req.applicable_aspects ?? aspects

          nodes.push(makeNode(req.id, 'QualityRequirement', req.requirement_text, 'Project Requirement', req.scenario ?? '', {
            aspects: reqAspects,
            evidence: req.evidence_status ?? 'Missing',
            riskLevel: req.risk_level ?? 'Low',
          }))
          links.push(makeLink(goal.id, req.id))

          // Architecture element link
          const ae = req.architecture_element_id ? archElems.get(req.architecture_element_id) : null

          // Sub-requirements
          for (const subReq of subReqs.values()) {
            if (subReq.req_id !== req.id) continue

            nodes.push(makeNode(subReq.id, 'SubQualityRequirement',
              subReq.acceptance_criterion ?? `${req.requirement_text} criterion`,
              'Project Sub Requirement', subReq.verification_condition ?? '', {
                aspects: reqAspects,
              }))
            links.push(makeLink(req.id, subReq.id))

            if (ae) links.push(makeLink(subReq.id, ae.id))
          }

          // Ensure arch element node exists
          if (ae && !nodes.find(n => n.id === ae.id)) {
            nodes.push(makeNode(ae.id, 'ArchitectureElement', ae.name, 'Project Architecture', ae.description ?? ''))

            // Software modules under this arch element
            for (const mod of modules.values()) {
              if (mod.architecture_element_id !== ae.id) continue
              if (!nodes.find(n => n.id === mod.id)) {
                nodes.push(makeNode(mod.id, 'SoftwareModule', mod.name, 'Project Software', mod.description ?? ''))
                links.push(makeLink(ae.id, mod.id))
              }

              // Test cases under this module
              for (const tc of testCases.values()) {
                if (tc.software_module_id !== mod.id) continue
                const tr = testResults.get(tc.id)
                const result = tr?.result ?? 'Not run'
                const evidence = result === 'Pass' ? 'Complete' : result === 'Fail' ? 'Failed' : result === 'Blocked' ? 'Failed' : 'Missing'

                nodes.push(makeNode(tc.id, 'TestCase', tc.description, 'Project Verification', tc.test_objective ?? '', {
                  aspects: reqAspects,
                  evidence,
                }))
                links.push(makeLink(mod.id, tc.id))

                const trId = tr ? tr.id : `TR_MISSING_${tc.id}`
                nodes.push(makeNode(trId, 'TestResult',
                  `${result.toUpperCase()} ${tc.tc_id}`,
                  'Project Test Report', tr?.conclusion ?? `Result: ${result}`, {
                    aspects: reqAspects,
                    evidence,
                  }))
                links.push(makeLink(tc.id, trId))

                const rsId = `RS_${tc.id}`
                nodes.push(makeNode(rsId, 'RiskStatus', `${evidence === 'Complete' ? 'Closed' : 'Open'} / ${req.risk_level ?? 'Low'}`,
                  'Project Quality Risk', `Risk status for ${tc.tc_id}.`, {
                    aspects: reqAspects,
                    evidence,
                    riskLevel: req.risk_level ?? 'Low',
                    riskStatus: evidence === 'Complete' ? 'Closed' : 'Open',
                  }))
                links.push(makeLink(trId, rsId))
              }
            }
          }
        }
      }
    }
  }

  // Deduplicate nodes (arch elements and modules can appear multiple times)
  const seen = new Set()
  const dedupedNodes = nodes.filter(n => {
    if (seen.has(n.id)) return false
    seen.add(n.id)
    return true
  })

  return { nodes: dedupedNodes, links }
}

// ─────────────────────────────────────────────
// rows — extract structured trace chain rows from graph data
// Adapted verbatim from V5.9.1 rows()
// ─────────────────────────────────────────────

function incoming(d, id) {
  return d.links
    .filter(l => (l.target?.id ?? l.target) === id)
    .map(l => d.nodes.find(n => n.id === (l.source?.id ?? l.source)))
    .filter(Boolean)
}

function outgoing(d, id) {
  return d.links
    .filter(l => (l.source?.id ?? l.source) === id)
    .map(l => d.nodes.find(n => n.id === (l.target?.id ?? l.target)))
    .filter(Boolean)
}

export function rows(d) {
  const out = []
  d.nodes.filter(n => n.type === 'QualityRequirement').forEach(qr => {
    const qg = incoming(d, qr.id)[0]
    const sub = qg && incoming(d, qg.id).find(n => n.type === 'QualitySubCharacteristic')
    const ch = sub && incoming(d, sub.id).find(n => n.type === 'QualityCharacteristic')

    outgoing(d, qr.id).filter(n => n.type === 'SubQualityRequirement').forEach(sqr => {
      outgoing(d, sqr.id).filter(n => n.type === 'ArchitectureElement').forEach(ae => {
        outgoing(d, ae.id).filter(n => n.type === 'SoftwareModule').forEach(sw => {
          const tc = outgoing(d, sw.id).find(n => n.type === 'TestCase')
          const tr = tc && outgoing(d, tc.id).find(n => n.type === 'TestResult')
          const rs = tr && outgoing(d, tr.id).find(n => n.type === 'RiskStatus')
          out.push({
            ch, sub, qg, qr, sqr, ae, sw, tc, tr, rs,
            nodes: [ch, sub, qg, qr, sqr, ae, sw, tc, tr, rs].filter(Boolean),
          })
        })
      })
    })
  })
  return out
}

// ─────────────────────────────────────────────
// branch — compute highlighted trace chain for a selected node
// Adapted verbatim from V5.9.1 branch()
// ─────────────────────────────────────────────

export function branch(id, d) {
  const ids = new Set()
  const keys = new Set()
  if (!id) return { ids, keys }
  const chainRows = rows(d).filter(r => r.nodes.some(n => n.id === id))
  chainRows.forEach(r => {
    const seq = [{ id: 'STD' }, r.ch, r.sub, r.qg, r.qr, r.sqr, r.ae, r.sw, r.tc, r.tr, r.rs].filter(Boolean)
    seq.forEach(n => ids.add(n.id))
    for (let i = 0; i < seq.length - 1; i++) keys.add(seq[i].id + '->' + seq[i + 1].id)
  })
  return { ids, keys }
}

// ─────────────────────────────────────────────
// filter — apply filters to graph data
// Adapted verbatim from V5.9.1 filter()
// ─────────────────────────────────────────────

export function filterGraph(d, f) {
  let keep = new Set(d.nodes.map(n => n.id))

  if (f.char && f.char !== 'All') {
    const allow = new Set(['STD', f.char])
    const fw = {}
    d.links.forEach(l => {
      const src = l.source?.id ?? l.source
      const tgt = l.target?.id ?? l.target;
      (fw[src] ??= []).push(tgt)
    })
    const q = [f.char]
    while (q.length) {
      (fw[q.shift()] || []).forEach(n => {
        if (!allow.has(n)) { allow.add(n); q.push(n) }
      })
    }
    keep = new Set([...keep].filter(id => allow.has(id)))
  }

  ;['aspect', 'risk', 'evidence'].forEach(k => {
    const v = f[k]
    if (v && v !== 'All') {
      keep = new Set([...keep].filter(id => {
        const n = d.nodes.find(x => x.id === id)
        if (!n || n.type === 'Standard') return true
        if (k === 'aspect') return (n.aspects ?? []).includes(v)
        if (k === 'risk') return n.riskLevel === v
        return n.evidence === v
      }))
    }
  })

  if (f.search) {
    const s = f.search.toLowerCase()
    const m = new Set(
      d.nodes
        .filter(n => (n.id + n.label + n.type + n.desc).toLowerCase().includes(s))
        .map(n => n.id)
    )
    const c = new Set(m)
    d.links.forEach(l => {
      const src = l.source?.id ?? l.source
      const tgt = l.target?.id ?? l.target
      if (m.has(src)) c.add(tgt)
      if (m.has(tgt)) c.add(src)
    })
    keep = new Set([...keep].filter(id => c.has(id)))
  }

  return {
    nodes: d.nodes.filter(n => keep.has(n.id)),
    links: d.links.filter(l => keep.has(l.source?.id ?? l.source) && keep.has(l.target?.id ?? l.target)),
  }
}

// ─────────────────────────────────────────────
// renderSankey — D3 Sankey SVG rendering
// Adapted from V5.9.1 sankey() — renamed to avoid collision with d3-sankey's sankey symbol.
// ─────────────────────────────────────────────

export function renderSankey(elementId, data, opts = {}) {
  const box = d3.select(`#${elementId}`)
  box.html('')

  if (!data.nodes.length) {
    box.html("<div class='card chart'><p>No data.</p></div>")
    return
  }

  const W = opts.mini ? 360 : opts.common ? 2500 : 2550
  const H = opts.mini
    ? 82
    : Math.max(opts.common ? 760 : 820, data.nodes.length * (opts.common ? 4.8 : 6.8))
  const M = { top: opts.mini ? 10 : 40, right: 30, bottom: 20, left: 30 }

  const layout = d3Sankey()
    .nodeId(x => x.id)
    .nodeWidth(opts.mini ? 8 : 16)
    .nodePadding(opts.mini ? 4 : 9)
    .extent([[M.left, M.top], [W - M.right, H - M.bottom]])

  // d3-sankey mutates nodes and links — pass copies
  const graph = layout({
    nodes: data.nodes.map(x => ({ ...x })),
    links: data.links.map(x => ({ ...x })),
  })

  const br = branch(opts.selected ?? null, data)

  const svg = box
    .append('div')
    .attr('class', opts.mini ? '' : 'card chart')
    .append('svg')
    .attr('viewBox', `0 0 ${W} ${H}`)
    .style('min-width', opts.mini ? '0' : opts.common ? '2100px' : '2200px')
    .style('height', `${H}px`)
    .on('click', () => opts.onClear && opts.onClear())

  // Layer header lines
  if (!opts.mini) {
    LAYERS.forEach((l, i) => {
      const x = M.left + i * ((W - M.left - M.right) / (LAYERS.length - 1))
      svg.append('text')
        .attr('x', x).attr('y', 22)
        .attr('text-anchor', 'middle')
        .attr('fill', '#64748b').attr('font-size', 11).attr('font-weight', 700)
        .text(l)
      svg.append('line')
        .attr('x1', x).attr('y1', 34).attr('x2', x).attr('y2', H - 12)
        .attr('stroke', '#e2e8f0').attr('stroke-dasharray', '4 6')
    })
  }

  // Links
  svg.append('g')
    .selectAll('path')
    .data(graph.links)
    .join('path')
    .attr('d', sankeyLinkHorizontal())
    .attr('fill', 'none')
    .attr('stroke', l => {
      const k = `${l.source.id}->${l.target.id}`
      const rel = !opts.selected || br.keys.has(k)
      const dir = opts.selected && rel && (l.source.id === opts.selected || l.target.id === opts.selected)
      return dir ? '#f97316' : rel ? '#2563eb' : '#e2e8f0'
    })
    .attr('stroke-width', l =>
      opts.mini ? 1.6 : ((!opts.selected || br.keys.has(`${l.source.id}->${l.target.id}`)) ? 1.35 : 0.4)
    )
    .attr('opacity', l =>
      opts.mini ? 0.65 : ((!opts.selected || br.keys.has(`${l.source.id}->${l.target.id}`)) ? 0.62 : 0.04)
    )

  // Nodes
  const ng = svg.append('g')
    .selectAll('g')
    .data(graph.nodes)
    .join('g')
    .style('cursor', 'pointer')
    .style('opacity', n =>
      opts.mini ? 1 : (!opts.selected || n.id === opts.selected || br.ids.has(n.id) ? 1 : 0.15)
    )
    .on('click', (e, n) => {
      e.stopPropagation()
      opts.onSelect && opts.onSelect(n)
    })

  ng.append('rect')
    .attr('x', n => n.x0).attr('y', n => n.y0)
    .attr('width', n => n.x1 - n.x0)
    .attr('height', n => Math.max(opts.mini ? 3 : 8, n.y1 - n.y0))
    .attr('rx', opts.mini ? 3 : 6)
    .attr('fill', n => nodeColor(n))
    .attr('stroke', n =>
      opts.selected === n.id ? '#f97316' : br.ids.has(n.id) ? '#2563eb' : 'transparent'
    )
    .attr('stroke-width', n =>
      opts.selected === n.id ? 3 : br.ids.has(n.id) ? 1.5 : 0
    )

  if (!opts.mini) {
    ng.append('text')
      .attr('x', n => n.x0 < W / 2 ? n.x1 + 8 : n.x0 - 8)
      .attr('y', n => (n.y0 + n.y1) / 2)
      .attr('dy', '.35em')
      .attr('text-anchor', n => n.x0 < W / 2 ? 'start' : 'end')
      .attr('font-size', 10).attr('font-weight', 700)
      .text(n => n.label.length > 48 ? n.label.slice(0, 48) + '…' : n.label)
  }
}

// ─────────────────────────────────────────────
// renderDetail — node detail panel
// Adapted from V5.9.1 detail()
// ─────────────────────────────────────────────

function statusBadge(v) {
  if (!v) return ''
  const cls = ['Ready', 'Closed', 'Complete', 'Low'].includes(v) ? 'ok'
    : ['Open', 'High', 'Critical', 'Failed', 'Missing', 'Not ready'].includes(v) ? 'risk'
    : 'warn'
  return `<span class="tag ${cls}">${v}</span>`
}

function tag(a) { return `<span class="tag">${a}</span>` }

function stepBox(title, n) {
  return `<button class="stepBox" data-node="${n?.id ?? ''}">
    <div class="stepTitle">${title}</div>
    <div class="stepLabel">${n ? n.label.slice(0, 82) : 'Not linked'}</div>
    <div class="stepId">${n?.id ?? ''}</div>
  </button>`
}

export function renderDetail(elementId, node, data, onSelect = null) {
  const box = document.getElementById(elementId)
  if (!node) {
    box.innerHTML = '<h2>Node detail</h2><p>Select a node in the Sankey.</p>'
    return
  }

  const chainRows = rows(data).filter(r => r.nodes.some(x => x.id === node.id))

  box.innerHTML = `
    <h2>${node.label}</h2>
    <p style="font-size:11px;color:#64748b">${node.id}</p>
    <div class="grid2">
      <div class="box"><div class="k">Type</div>${node.type}</div>
      <div class="box"><div class="k">Source</div>${node.source}</div>
    </div>
    <div class="desc" style="margin-top:8px">${node.desc}</div>
    ${node.aspects ? `<div style="margin:10px 0">
      ${node.aspects.map(tag).join('')}
      ${statusBadge(node.evidence)}
      ${statusBadge(node.riskLevel)}
      ${statusBadge(node.riskStatus)}
    </div>` : ''}
    <h3>Trace Chain</h3>
    <div class="chain">
      ${chainRows.length
        ? chainRows.map((r, i) => `
            <div class="chainRow">
              <b>${i + 1}. ${r.sub?.label ?? ''} → ${r.rs?.label ?? ''}</b>
              <div class="chainSteps">
                ${stepBox('Quality Requirement', r.qr)}
                ${stepBox('Sub Quality Requirement', r.sqr)}
                ${stepBox('Architecture Element', r.ae)}
                ${stepBox('Software Module', r.sw)}
                ${stepBox('Test Case', r.tc)}
                ${stepBox('Test Result', r.tr)}
                ${stepBox('Risk Status', r.rs)}
              </div>
            </div>
          `).join('')
        : "<div class='desc'>No trace chain for this node.</div>"
      }
    </div>
  `

  // Wire stepBox clicks to select nodes in the Sankey
  if (onSelect) {
    box.querySelectorAll('.stepBox[data-node]').forEach(btn => {
      const nodeId = btn.dataset.node
      if (!nodeId) return
      btn.addEventListener('click', () => {
        const target = data.nodes.find(n => n.id === nodeId)
        if (target) onSelect(target)
      })
    })
  }
}
