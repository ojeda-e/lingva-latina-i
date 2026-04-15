
# LINGVA LATINA - PARS I

Personal study notes and solutions created while working through *[Lingua Latina per se Illustrata - FAMILIA ROMANA](https://www.culturaclasica.com/lingualatina/index.htm)* by [Hans H. Ørberg](https://en.wikipedia.org/wiki/Hans_%C3%98rberg) (Cultura Clásica).

*FAMILIA ROMANA*, the first part of Lingua Latina per se Illustrata, is the foundation of the introductory Latin course. It covers the essential rules of Latin grammar while gradually introducing a basic vocabulary of approximately 1,500 words.

<p align="center">
  <img src="docs/img/cavecanem.png" alt="Cave Canem" width="400"/>
</p>

## About the book

The book comprises 35 chapters, each structured as a continuous narrative depicting scenes from the life of a Roman family in the 2nd century AD. The entire book is written in Latin, but it is carefully graded so that each sentence can be understood per se from context alone. The meaning of new vocabulary and grammatical forms is made clear through context, illustrations, marginal notes, and previously acquired vocabulary, eliminating the need for translation or a dictionary.

Both vocabulary and grammar are acquired inductively through repeated exposure to numerous illustrative examples integrated into a coherent narrative.

The notes included in this repository are also based on the **Spanish student guide (*Manual del Alumno*)**, which I use as a companion to the main text.

## Repository layout

For each chapter of the book (CAPITVLVM), the following files are included in the corresponding folder:

| File | Content |
|------|---------|
| `compendium.md` | Chapter summary |
| `grammatica.md` | Grammar notes |
| `vocabulum.md` | New vocabulary |
| `exercitia/pensvm_*.md` | (My)Exercise solutions |

Chapter folders are located under `docs/capitula/CAP_01/` … `docs/capitula/CAP_35/`.

```bash
├── docs/
│   ├── index.md
│   ├── capitula/
│   │   └── CAP_01/             # study notes - Cap I
│   │       ├── grammatica.md
│   │       ├── compendium.md
│   │       ├── vocabulum.md
│   │       └── exercitia/
│   │           └── pensvm_1.md
│   └── stylesheets/
├── hooks/progress.py            # progress tracking
├── progress/progress.json
├── pyproject.toml
└── uv.lock
```


## MkDocs site

Notes are published as a static site with search, sidebar navigation, and a progress dashboard.

Uses [uv](https://docs.astral.sh/uv/) for the virtual environment and dependencies (`pyproject.toml`).

```bash
uv sync
uv run mkdocs serve     # http://127.0.0.1:8000 — live reload
uv run mkdocs build     # output → site/
```

Or via Make:

```bash
make sync serve
```

`mkdocs build` and `mkdocs serve` automatically regenerate `docs/progress.md` and chapter navigation via the pre-build hook — no separate step needed.

### Progress tracking

This project includes a pre-build hook to update the progress tracking without a full build:

```bash
make progress
```

Edit `progress/progress.json` to override status or set exercitia totals:

```json
{
  "chapters": {
    "1": {
      "grammatica": "done",
      "vocabulum": "in_progress",
      "exercitia_total": 3
    }
  }
}
```

Status values: `not_started`, `in_progress`, `done`.

### GitHub Pages

Build locally and deploy the `site/` folder, or use a CI workflow with `mkdocs gh-deploy`.

> [!IMPORTANT]
> **This repository does not reproduce or redistribute any original text or exercises from Lingua Latina per se Illustrata.** It contains only personal notes and self-written answers intended as a place to store my own work.
