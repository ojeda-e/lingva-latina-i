#!/usr/bin/env python3

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CHAPTERS = DOCS / "capitula"
PROGRESS_JSON = ROOT / "progress" / "progress.json"
PROGRESS_MD = DOCS / "progress.md"

TOTAL_CHAPTERS = 35
AREAS = ("grammatica", "vocabulum", "exercitia")
STATUS_ORDER = {"not_started": 0, "in_progress": 1, "done": 2}
GRAMMATICA_SMALLCAPS_EXCLUDED = "capitula/CAP_01/grammatica.md"

def ordinal_to_roman(number: int) -> str:
    result = ""
    for value, numeral in zip(
        (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1),
        ("M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"),
    ):
        count, number = divmod(number, value)
        result += numeral * count
    return result


ROMAN = [ordinal_to_roman(n) for n in range(1, TOTAL_CHAPTERS + 1)]


@dataclass
class ChapterProgress:
    number: int
    roman: str
    nav_link: str
    grammatica: str
    vocabulum: str
    exercitia: str
    exercitia_done: int
    exercitia_total: int | None
    compendium: str
    exists: bool

    @property
    def overall_pct(self) -> float:
        parts = []
        for area in AREAS:
            if area == "exercitia":
                if self.exercitia_total and self.exercitia_total > 0:
                    parts.append(min(self.exercitia_done / self.exercitia_total, 1.0))
                elif self.exercitia == "done":
                    parts.append(1.0)
                elif self.exercitia == "in_progress":
                    parts.append(0.5)
                else:
                    parts.append(0.0)
            else:
                status = getattr(self, area)
                parts.append(
                    1.0 if status == "done" else (0.5 if status == "in_progress" else 0.0)
                )
        return round(100 * sum(parts) / len(parts), 1)


def chapter_slug(number: int) -> str:
    return f"CAP_{number:02d}"


def file_has_content(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return False
    if re.fullmatch(r"<!--.*?-->", text, flags=re.DOTALL):
        return False
    return True


def status_from_file(path: Path) -> str:
    return "in_progress" if file_has_content(path) else "not_started"


def merge_status(override: str | None, detected: str) -> str:
    if override in STATUS_ORDER:
        return override
    return detected


def count_exercitia_done(chapter_path: Path) -> int:
    exercitia_dir = chapter_path / "exercitia"
    if not exercitia_dir.is_dir():
        return 0
    return sum(
        1 for path in sorted(exercitia_dir.glob("pensvm_*.md")) if file_has_content(path)
    )


def exercitia_status(done: int, total: int | None, override: str | None) -> str:
    if override in STATUS_ORDER:
        return override
    if total and total > 0:
        if done >= total:
            return "done"
        if done > 0:
            return "in_progress"
        return "not_started"
    if done > 0:
        return "in_progress"
    return "not_started"


def load_overrides() -> dict:
    if not PROGRESS_JSON.is_file():
        return {}
    data = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
    return data.get("chapters", {})


def collect_chapters() -> list[ChapterProgress]:
    overrides = load_overrides()
    chapters: list[ChapterProgress] = []

    for number in range(1, TOTAL_CHAPTERS + 1):
        nav_link = chapter_slug(number)
        chapter_path = CHAPTERS / nav_link
        chapter_override = overrides.get(str(number), overrides.get(number, {}))
        exists = chapter_path.is_dir()

        grammatica = merge_status(
            chapter_override.get("grammatica"),
            status_from_file(chapter_path / "grammatica.md"),
        )
        vocabulum = merge_status(
            chapter_override.get("vocabulum"),
            status_from_file(chapter_path / "vocabulum.md"),
        )
        compendium = merge_status(
            chapter_override.get("compendium"),
            status_from_file(chapter_path / "compendium.md"),
        )

        exercitia_done = count_exercitia_done(chapter_path)
        exercitia_total = chapter_override.get("exercitia_total")
        if exercitia_total is not None:
            exercitia_total = int(exercitia_total)

        exercitia = exercitia_status(
            exercitia_done,
            exercitia_total,
            chapter_override.get("exercitia"),
        )

        chapters.append(
            ChapterProgress(
                number=number,
                roman=ROMAN[number - 1],
                nav_link=nav_link,
                grammatica=grammatica,
                vocabulum=vocabulum,
                exercitia=exercitia,
                exercitia_done=exercitia_done,
                exercitia_total=exercitia_total,
                compendium=compendium,
                exists=exists,
            )
        )

    return chapters


def status_icon(status: str) -> str:
    return {"done": "✅", "in_progress": "🟡", "not_started": "⬜"}[status]


def exercitia_label(ch: ChapterProgress) -> str:
    if ch.exercitia_total:
        return f"{ch.exercitia_done}/{ch.exercitia_total}"
    if ch.exercitia_done:
        return str(ch.exercitia_done)
    return "—"


def summary_stats(chapters: list[ChapterProgress]) -> dict:
    def area_done(area: str) -> int:
        if area == "exercitia":
            return sum(1 for ch in chapters if ch.exercitia == "done")
        return sum(1 for ch in chapters if getattr(ch, area) == "done")

    overall = round(sum(ch.overall_pct for ch in chapters) / len(chapters), 1)
    return {
        "overall_pct": overall,
        "grammatica_done": area_done("grammatica"),
        "vocabulum_done": area_done("vocabulum"),
        "exercitia_done": area_done("exercitia"),
        "chapters_started": sum(1 for ch in chapters if ch.overall_pct > 0),
        "chapters_complete": sum(1 for ch in chapters if ch.overall_pct == 100),
    }


def chapter_link(ch: ChapterProgress) -> str:
    if not ch.exists:
        return ch.roman
    return f"[{ch.roman}](capitula/{ch.nav_link}/grammatica.md)"


def render_progress_md(chapters: list[ChapterProgress], stats: dict) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Study progress",
        "",
        "Tracker for all 35 chapters of *Familia Romana*. "
        "",
        "!!! summary \"Overview\"",
        "    ",
        f"    - **Overall completion:** {stats['overall_pct']}%",
        f"    - **Chapters complete:** {stats['chapters_complete']} / 35",
        f"    - **Chapters started:** {stats['chapters_started']} / 35",
        f"    - **Grammatica done:** {stats['grammatica_done']} / 35",
        f"    - **vocabulum done:** {stats['vocabulum_done']} / 35",
        f"    - **Exercitia done:** {stats['exercitia_done']} / 35",
        "",
        "| Cap | Grammatica | vocabulum | Exercitia | Overall |",
        "|-----|:----------:|:------------:|:---------:|:-------:|",
    ]

    for ch in chapters:
        ex = exercitia_label(ch)
        if ch.exercitia == "done":
            ex_cell = f"✅ {ex}"
        elif ch.exercitia == "in_progress":
            ex_cell = f"🟡 {ex}"
        else:
            ex_cell = f"⬜ {ex}"

        lines.append(
            f"| {chapter_link(ch)} "
            f"| {status_icon(ch.grammatica)} "
            f"| {status_icon(ch.vocabulum)} "
            f"| {ex_cell} "
            f"| {ch.overall_pct}% |"
        )

    lines.extend(
        [
            "",
            "## Legend",
            "",
            "| Symbol | Meaning |",
            "|--------|---------|",
            "| ✅ | Done |",
            "| 🟡 | In progress |",
            "| ⬜ | Not started |",
            "",
            f"_Generated {generated}_",
            "",
        ]
    )
    return "\n".join(lines)


def write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def generate_chapter_pages(ch: ChapterProgress) -> None:
    chapter_path = CHAPTERS / ch.nav_link
    if not chapter_path.is_dir():
        return

    nav_lines = ["nav:"]
    for name in ("compendium.md", "grammatica.md", "vocabulum.md"):
        if (chapter_path / name).is_file():
            nav_lines.append(f"  - {name}")

    exercitia_dir = chapter_path / "exercitia"
    if exercitia_dir.is_dir() and any(exercitia_dir.glob("pensvm_*.md")):
        nav_lines.append("  - exercitia")

    write_yaml(
        chapter_path / ".pages",
        f"title: CAPITVLVM {ch.roman}\n" + "\n".join(nav_lines),
    )

    if exercitia_dir.is_dir():
        write_yaml(
            exercitia_dir / ".pages",
            "title: Exercitia\nglob: pensvm_*.md\nsort: asc\n",
        )


def generate_nav(chapters: list[ChapterProgress]) -> None:
    existing = [ch for ch in chapters if ch.exists]
    CHAPTERS.mkdir(parents=True, exist_ok=True)
    if existing:
        nav = "title: CAPITVLA\nnav:\n" + "\n".join(f"  - {ch.nav_link}" for ch in existing)
        write_yaml(CHAPTERS / ".pages", nav)
    elif (CHAPTERS / ".pages").is_file():
        (CHAPTERS / ".pages").unlink()

    for ch in existing:
        generate_chapter_pages(ch)


def generate_all() -> None:
    chapters = collect_chapters()
    stats = summary_stats(chapters)
    CHAPTERS.mkdir(parents=True, exist_ok=True)
    PROGRESS_MD.write_text(render_progress_md(chapters, stats), encoding="utf-8")
    generate_nav(chapters)


def on_pre_build(config, **kwargs) -> None:
    generate_all()


def on_post_page(output, page, config, **kwargs):
    path = page.file.src_path.replace("\\", "/")
    if not path.startswith("capitula/") or path == GRAMMATICA_SMALLCAPS_EXCLUDED:
        return output
    return output.replace("<body ", '<body class="capitulum-page" ', 1)


if __name__ == "__main__":
    generate_all()
    print(f"Wrote {PROGRESS_MD.relative_to(ROOT)}")
