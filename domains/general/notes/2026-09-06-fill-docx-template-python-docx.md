---
title: Fill a .docx template in place with python-docx, preserving formatting
domain: general
tags: [python-docx, docx, word, templates, formatting]
source: session
date: 2026-09-06
---

## Problem
Fill answers into a supplied Word template (a customer-development plan) so the
result is submittable — identical layout, fonts, headings, and tables, "no change
to the format" — rather than regenerating the doc from scratch.

## Solution / code
Use `python-docx`. Inspect the paragraph/table structure first, then write **only
into the blank slots and content tables**, and save as a **new** file so the
blank template is preserved.

```python
from docx import Document
doc = Document("template.docx")

# 1. inspect: find the blank paragraphs / table cells to fill
for i, p in enumerate(doc.paragraphs):
    print(i, repr(p.text), p.style.name)

# 2. write plain runs — they inherit the document's default style, so they
#    match the existing body text exactly (don't set font/size explicitly)
doc.paragraphs[idx].add_run("the answer text")

# 3. tables: address cells directly
doc.tables[0].rows[1].cells[1].text = "value"

doc.save("template - FILLED.docx")   # new file, template untouched
```

## Gotchas
- **Plain runs inherit the default style** — that's what makes them match. Setting
  an explicit font/size is what *breaks* visual consistency; check the body's
  default font first, then add unstyled runs.
- Write only into blank spaces + intended tables; leave sections marked for
  someone else (e.g. a "Chapter Leader use" checklist) empty.
- **Save as a new `.docx`, never overwrite the template** — keep the blank.
- Read the file back after writing to verify the answers landed in the right slots.
- Same app-cache trap as [[edit-office-files-app-open]]: if Word has the file
  open it shows a stale copy and its save can clobber your edits — close it first.
