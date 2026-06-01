const BASE = '/api/v1'

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body != null ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw { status: res.status, message: err.detail ?? res.statusText }
  }
  return res.status === 204 ? null : res.json()
}

export const api = {
  // Health
  health: () => request('GET', '/health'),

  // Projects
  getProjects: () => request('GET', '/projects'),
  getProject: (id) => request('GET', `/projects/${id}`),
  getProjectFull: (id) => request('GET', `/projects/${id}/full`),
  createProject: (data) => request('POST', '/projects', data),
  updateProject: (id, data) => request('PUT', `/projects/${id}`, data),
  deleteProject: (id) => request('DELETE', `/projects/${id}`),
  exportProject: (id) => request('GET', `/projects/${id}/export`),
  importProject: (data) => request('POST', '/projects/import', data),
  getDashboard: (id) => request('GET', `/projects/${id}/dashboard`),

  // Scope
  getScope: (pid) => request('GET', `/projects/${pid}/scope`),
  updateScopeDecision: (pid, scid, data) => request('PATCH', `/projects/${pid}/scope/${scid}`, data),
  batchUpdateScope: (pid, data) => request('PUT', `/projects/${pid}/scope`, data),
  resetScope: (pid) => request('POST', `/projects/${pid}/scope/reset`),

  // Architecture elements & software modules
  getArchElements: (pid) => request('GET', `/projects/${pid}/architecture-elements`),
  createArchElement: (pid, data) => request('POST', `/projects/${pid}/architecture-elements`, data),
  updateArchElement: (pid, eid, data) => request('PUT', `/projects/${pid}/architecture-elements/${eid}`, data),
  deleteArchElement: (pid, eid) => request('DELETE', `/projects/${pid}/architecture-elements/${eid}`),
  getSoftwareModules: (pid, eid) => request('GET', `/projects/${pid}/architecture-elements/${eid}/software-modules`),
  createSoftwareModule: (pid, eid, data) => request('POST', `/projects/${pid}/architecture-elements/${eid}/software-modules`, data),
  updateSoftwareModule: (pid, eid, mid, d) => request('PUT', `/projects/${pid}/architecture-elements/${eid}/software-modules/${mid}`, d),
  deleteSoftwareModule: (pid, eid, mid) => request('DELETE', `/projects/${pid}/architecture-elements/${eid}/software-modules/${mid}`),

  // Quality goals
  getGoals: (pid, scid) => request('GET', `/projects/${pid}/scope/${scid}/goals`),
  createGoal: (pid, scid, data) => request('POST', `/projects/${pid}/scope/${scid}/goals`, data),
  updateGoal: (pid, scid, gid, d) => request('PUT', `/projects/${pid}/scope/${scid}/goals/${gid}`, d),
  deleteGoal: (pid, scid, gid) => request('DELETE', `/projects/${pid}/scope/${scid}/goals/${gid}`),

  // Quality requirements
  getRequirements: (pid, scid, gid) => request('GET', `/projects/${pid}/scope/${scid}/goals/${gid}/requirements`),
  createRequirement: (pid, scid, gid, d) => request('POST', `/projects/${pid}/scope/${scid}/goals/${gid}/requirements`, d),
  updateRequirement: (pid, scid, gid, rid, d) => request('PUT', `/projects/${pid}/scope/${scid}/goals/${gid}/requirements/${rid}`, d),
  deleteRequirement: (pid, scid, gid, rid) => request('DELETE', `/projects/${pid}/scope/${scid}/goals/${gid}/requirements/${rid}`),

  // Sub-requirements
  getSubRequirements: (pid, rid) => request('GET', `/projects/${pid}/requirements/${rid}/sub-requirements`),
  createSubRequirement: (pid, rid, data) => request('POST', `/projects/${pid}/requirements/${rid}/sub-requirements`, data),
  updateSubRequirement: (pid, rid, sid, d) => request('PUT', `/projects/${pid}/requirements/${rid}/sub-requirements/${sid}`, d),
  deleteSubRequirement: (pid, rid, sid) => request('DELETE', `/projects/${pid}/requirements/${rid}/sub-requirements/${sid}`),

  // Test cases & results
  getTestCases: (pid, mid) => request('GET', `/projects/${pid}/software-modules/${mid}/test-cases`),
  createTestCase: (pid, mid, data) => request('POST', `/projects/${pid}/software-modules/${mid}/test-cases`, data),
  updateTestCase: (pid, mid, tid, d) => request('PUT', `/projects/${pid}/software-modules/${mid}/test-cases/${tid}`, d),
  deleteTestCase: (pid, mid, tid) => request('DELETE', `/projects/${pid}/software-modules/${mid}/test-cases/${tid}`),
  getTestResult: (pid, tid) => request('GET', `/projects/${pid}/test-cases/${tid}/result`),
  updateTestResult: (pid, tid, data) => request('PUT', `/projects/${pid}/test-cases/${tid}/result`, data),

  // Risks
  getRisks: (pid, params) => request('GET', `/projects/${pid}/risks${params ? '?' + new URLSearchParams(params) : ''}`),
  createRisk: (pid, data) => request('POST', `/projects/${pid}/risks`, data),
  updateRisk: (pid, rid, data) => request('PUT', `/projects/${pid}/risks/${rid}`, data),
  deleteRisk: (pid, rid) => request('DELETE', `/projects/${pid}/risks/${rid}`),

  // Evidence
  getEvidence: (pid) => request('GET', `/projects/${pid}/evidence`),
  createEvidence: (pid, data) => request('POST', `/projects/${pid}/evidence`, data),
  updateEvidence: (pid, eid, data) => request('PUT', `/projects/${pid}/evidence/${eid}`, data),
  deleteEvidence: (pid, eid) => request('DELETE', `/projects/${pid}/evidence/${eid}`),

  // Assessment findings
  getFindings: (pid) => request('GET', `/projects/${pid}/findings`),
  createFinding: (pid, data) => request('POST', `/projects/${pid}/findings`, data),
  updateFinding: (pid, fid, data) => request('PUT', `/projects/${pid}/findings/${fid}`, data),
  deleteFinding: (pid, fid) => request('DELETE', `/projects/${pid}/findings/${fid}`),

  // Action items
  getActions: (pid) => request('GET', `/projects/${pid}/actions`),
  createAction: (pid, data) => request('POST', `/projects/${pid}/actions`, data),
  updateAction: (pid, aid, data) => request('PUT', `/projects/${pid}/actions/${aid}`, data),
  deleteAction: (pid, aid) => request('DELETE', `/projects/${pid}/actions/${aid}`),

  // Common model
  getCommonModel: () => request('GET', '/common/model'),
  getProductLineRecs: (pl) => request('GET', `/common/product-lines/${pl}/recommendations`),

  // Admin
  seedDemo: () => request('POST', '/admin/seed-demo'),
}
