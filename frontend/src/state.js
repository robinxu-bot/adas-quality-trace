/**
 * Single application state object — equivalent to V5.9.1's global S.
 * All mutations call the appropriate render function explicitly (no reactivity framework).
 */
export const S = {
  view: 'common',           // 'common' | 'projects' | 'project-detail'
  commonChar: null,         // selected characteristic id in Common View
  commonModel: null,        // cached response from GET /api/v1/common/model
  commonNode: null,         // selected node id in Common Sankey
  projects: [],             // loaded from GET /api/v1/projects on init
  selectedProject: null,    // summary object from project list
  projectFull: null,        // normalized full data: { project, scope, goals, reqs, … }
  selectedNode: null,       // UUID of selected node in Project Sankey
  formScope: [],            // wizard in-memory scope decisions (not persisted until Step 5)
  formMode: 'create',       // 'create' | 'edit'
  editId: null,             // project UUID when editing
  showExcluded: false,      // show excluded scope items in wizard
  mAspect: 'All',
  mApp: 'All',
  filters: { char: 'All', aspect: 'All', risk: 'All', evidence: 'All', search: '' },
}

/**
 * normalize() converts the flat /full response into Maps for O(1) lookup.
 * Called once after GET /projects/:id/full; result stored in S.projectFull.
 *
 * @param {object} full - raw /full API response
 * @returns {object} normalized Maps
 */
export function normalize(full) {
  return {
    project:      full.project,
    scope:        new Map((full.scope ?? []).map(x => [x.subchar_id, x])),
    goals:        new Map((full.goals ?? []).map(x => [x.id, x])),
    reqs:         new Map((full.requirements ?? []).map(x => [x.id, x])),
    subReqs:      new Map((full.sub_requirements ?? []).map(x => [x.id, x])),
    archElems:    new Map((full.architecture_elements ?? []).map(x => [x.id, x])),
    modules:      new Map((full.software_modules ?? []).map(x => [x.id, x])),
    testCases:    new Map((full.test_cases ?? []).map(x => [x.id, x])),
    testResults:  new Map((full.test_results ?? []).map(x => [x.tc_id, x])),
    risks:        new Map((full.risks ?? []).map(x => [x.id, x])),
  }
}
