# 14 V5.9 Persistence Enhancement Notes

# Purpose

V5.9 enhances the V5.8 project workspace prototype with local persistence and JSON exchange.

## Added Capabilities

- Save project quality scope locally
- Restore project changes after browser refresh
- Reset sample data
- Export project JSON
- Import project JSON
- Mark unsaved changes
- Update project dashboard after tailoring changes
- Filter Project Trace View based on tailored project quality scope

## Local Persistence

The prototype uses browser localStorage.

Storage key:

```text
pqrets_v59_project_data
```

Stored data includes:

```text
Project
ProjectQualityScope
QualityRequirements
ISO IEC 25010 common model
Quality aspects
```

## Export and Import

Export creates a JSON file containing the current project data.

Import expects a JSON file containing at least:

```text
project
projectQualityScope
qualityRequirements
```

## Important Limitation

localStorage is browser local data. It is not shared with other users and is not a database.

This is suitable for concept validation, not enterprise deployment.

## Next Recommended Version

V6.0 should separate data files:

```text
index.html
data/
  iso25010-common-model.json
  product-line-recommendation-rules.json
  adas-quality-aspect-mapping.json
  sample-project-adas.json
```

V6.0 should also improve the Sankey style trace view.
