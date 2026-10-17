# Data Schema

Canonical schema for items written to `data/clean/`.

Every item lives at `data/clean/{content-type}/{stem}/` and consists of:

- `{stem}.md` — YAML frontmatter + markdown body
- `meta.json` — machine-readable metadata (same fields as frontmatter, plus any out-of-band additions from downstream consumers)

The `{stem}` is the source filename without extension (e.g.
`report-2026.pdf` → `report-2026`).

## Mandatory fields

Every item carries these fields in both the YAML frontmatter and `meta.json`:

| Field | Type | Description |
| --- | --- | --- |
| `stem` | string | The item's filesystem stem (also the directory name). |
| `content_type` | string | One of: `pdf-document`, `docx-document`. |
| `source_id` | string | The ingestor identifier (`pdf`, `docx`). |
| `source_type` | string | The file extension (`pdf`, `docx`). |
| `source_file` | string | Original filename including extension (`report-2026.pdf`). |
| `source_path` | string | Project-root-relative path to the original binary (`data/sources/pdf/report-2026.pdf`). |
| `ingested_at` | string (ISO-8601) | mtime of the original source file at the time of conversion. |
| `cleaned_at` | string (ISO-8601) | Timestamp the clean item was written. |
| `title` | string | First H1 in the source markdown; falls back to a humanised stem. |

## `meta.json` shape

```json
{
  "stem": "report-2026",
  "content_type": "pdf-document",
  "source_id": "pdf",
  "source_type": "pdf",
  "source_file": "report-2026.pdf",
  "source_path": "data/sources/pdf/report-2026.pdf",
  "ingested_at": "2026-09-01T12:34:56+00:00",
  "cleaned_at": "2026-09-01T12:34:57+00:00",
  "title": "Report 2026"
}
```

## `{stem}.md` shape

```
---
stem: "report-2026"
content_type: "pdf-document"
source_id: "pdf"
source_type: "pdf"
source_file: "report-2026.pdf"
source_path: "data/sources/pdf/report-2026.pdf"
ingested_at: "2026-09-01T12:34:56+00:00"
cleaned_at: "2026-09-01T12:34:57+00:00"
title: "Report 2026"
---

Body content here…
```

## `_index.json` shape

A flat array of `{stem, content_type, source_id, source_file, title, ingested_at}`
entries. Regenerated on every clean transform run. Suitable for
search/discovery without reading individual items:

```json
[
  {
    "stem": "report-2026",
    "slug": "report-2026",
    "content_type": "pdf-document",
    "source_id": "pdf",
    "source_file": "report-2026.pdf",
    "title": "Report 2026",
    "ingested_at": "2026-09-01T12:34:56+00:00"
  }
]
```

The `slug` field is an alias for `stem` (kept for forward compatibility
with consumers expecting that field name).