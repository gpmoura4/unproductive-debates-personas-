"""A worked example of one debate, rendered as slides.

The aggregate figures answer "how much"; they cannot show what a hostility
level 4 message actually reads like, or what the moderator did to it. This
module takes one cell and walks through it turn by turn: the control side
escalating unchecked, then the treatment side with the same personas and the
same topic, where each candidate is shown next to what replaced it.

Output is one PNG per page, numbered in presentation order, plus a Markdown
version of the same material for the paper. Pages are 16:9 at 300 dpi.

Choosing the cell: by default the one whose control side escalates most
cleanly while its delta stays near the corpus average — an example that is
legible without being unrepresentative. `pick_example` returns the ranking so
the choice can be inspected rather than trusted.
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from analysis.metrics import CellRecord, load_cells  # noqa: E402
from analysis.selection import Selection  # noqa: E402

# 16:9 at 300 dpi — fills a slide without rescaling.
PAGE = (13.333, 7.5)
DPI = 300

CONTROL_COLOR = "#c44536"
TREATMENT_COLOR = "#2a6f97"
INK = "#1a1a1a"
MUTED = "#6b6b6b"
PAPER = "#ffffff"
CANDIDATE_BG = "#f7e6e4"
REFORM_BG = "#e3edf4"

# Hostility level -> colour, shared by every page so the reader learns it once.
LEVEL_COLORS = {
    0: "#4a7c59",
    1: "#7fa650",
    2: "#d9a441",
    3: "#d1662f",
    4: "#b5292b",
}

PERSONA_PT = {"persona_1": "Persona A (esquerda)", "persona_2": "Persona B (direita)"}


@dataclass(frozen=True, slots=True)
class Example:
    """One cell chosen to be walked through."""

    cell: CellRecord
    escalation: int      # control: last turn score minus first
    delta: float
    distance_from_mean: float


def pick_example(
    cells: list[CellRecord], topic: str | None = None, pair_id: str | None = None
) -> list[Example]:
    """Rank cells by how well they illustrate the effect.

    Preference order: a control side that escalates (the story needs a rise to
    show), then a delta close to the corpus mean (so the example does not
    overstate the result). An explicit topic/pair overrides the ranking.
    """
    usable = [c for c in cells if c.delta is not None]
    if not usable:
        return []

    mean_delta = sum(c.delta for c in usable) / len(usable)

    examples = []
    for cell in usable:
        scores = [t.score for t in cell.control.turns if t.score is not None]
        escalation = (scores[-1] - scores[0]) if len(scores) >= 2 else 0
        examples.append(
            Example(
                cell=cell,
                escalation=escalation,
                delta=cell.delta,
                distance_from_mean=abs(cell.delta - mean_delta),
            )
        )

    if topic or pair_id:
        examples = [
            e for e in examples
            if (topic is None or e.cell.topic == topic)
            and (pair_id is None or e.cell.pair_id == pair_id)
        ]

    # Escalation descending, then closeness to the mean delta ascending.
    examples.sort(key=lambda e: (-e.escalation, e.distance_from_mean))
    return examples


def _wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width)) if text else ""


def _truncate(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _page(title: str, subtitle: str = "") -> tuple:
    fig = plt.figure(figsize=PAGE, dpi=DPI, facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(6, 92, title, fontsize=24, fontweight="bold", color=INK, va="top")
    if subtitle:
        ax.text(6, 86.5, subtitle, fontsize=13, color=MUTED, va="top")
    return fig, ax


def _score_badge(ax, x: float, y: float, score: int | None, label: str = "") -> None:
    """The hostility level, as a filled chip."""
    if score is None:
        return
    color = LEVEL_COLORS.get(score, MUTED)
    ax.add_patch(
        FancyBboxPatch(
            (x, y), 7.0, 4.6,
            boxstyle="round,pad=0.3", linewidth=0, facecolor=color,
            transform=ax.transData,
        )
    )
    ax.text(x + 3.5, y + 2.3, str(score), fontsize=17, fontweight="bold",
            color="white", ha="center", va="center")
    if label:
        ax.text(x + 3.5, y - 1.4, label, fontsize=8, color=MUTED, ha="center")


def _message_box(
    ax, x: float, y: float, width: float, height: float,
    text: str, facecolor: str, edgecolor: str, fontsize: float = 10.5,
) -> None:
    """A text box that wraps to its own width and clips to its own height.

    Both limits are derived from the box geometry rather than passed in: a
    character count tuned for one box silently overflows the next one when the
    layout changes, and an overflowing message lands on top of the score badge.
    """
    ax.add_patch(
        FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.6", linewidth=1.2,
            facecolor=facecolor, edgecolor=edgecolor, alpha=0.95,
        )
    )

    # Axes are 100 units wide over PAGE[0] inches; at ~0.55 em average glyph
    # width this converts a box width into a character count that fits.
    inches_per_unit = PAGE[0] / 100
    char_width_inches = fontsize * 0.55 / 72
    columns = max(20, int((width - 2.8) * inches_per_unit / char_width_inches))

    line_height = fontsize * 1.45 / 72 / (PAGE[1] / 100)
    max_lines = max(1, int((height - 2.4) / line_height))

    lines = textwrap.wrap(" ".join((text or "").split()), width=columns)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max(0, columns - 1)].rstrip() + "…"

    ax.text(
        x + 1.4, y + height - 1.6, "\n".join(lines),
        fontsize=fontsize, color=INK, va="top", linespacing=1.45,
    )


def page_cover(example: Example, path: Path) -> str:
    """Page 1 — which debate this is, and what happened in it."""
    cell = example.cell
    fig, ax = _page(
        "Um debate, duas condições",
        f"{cell.topic} · {cell.pair_id} · réplica {cell.replicate}",
    )

    control_mean = cell.control.mean_hostility
    treatment_mean = cell.treatment.mean_hostility

    ax.text(6, 74, "Mesmas personas. Mesmo tema. Mesmos modelos.",
            fontsize=16, color=INK)
    ax.text(6, 69, "A única diferença é a presença do moderador D5.",
            fontsize=16, color=MUTED)

    for i, (label, value, color) in enumerate(
        [
            ("Controle\nsem moderação", control_mean, CONTROL_COLOR),
            ("Tratamento\ncom D5", treatment_mean, TREATMENT_COLOR),
        ]
    ):
        x = 14 + i * 38
        ax.add_patch(
            FancyBboxPatch(
                (x, 26), 28, 30,
                boxstyle="round,pad=0.8", linewidth=0, facecolor=color, alpha=0.12,
            )
        )
        ax.text(x + 14, 48, label, fontsize=14, color=INK,
                ha="center", va="center", linespacing=1.5)
        ax.text(x + 14, 35, f"{value:.2f}".replace(".", ","),
                fontsize=42, fontweight="bold", color=color, ha="center", va="center")
        ax.text(x + 14, 29.5, "hostilidade média (0–4)",
                fontsize=10, color=MUTED, ha="center")

    ax.annotate(
        "", xy=(52, 41), xytext=(42, 41),
        arrowprops={"arrowstyle": "-|>", "linewidth": 2.5, "color": INK},
    )
    ax.text(47, 44.5, f"Δ {example.delta:+.2f}".replace(".", ","),
            fontsize=15, fontweight="bold", color=INK, ha="center")

    ax.text(6, 14, "As páginas seguintes mostram as mensagens publicadas em "
                   "cada condição, turno a turno,",
            fontsize=12, color=MUTED)
    ax.text(6, 10, "com a pontuação de hostilidade atribuída pelo juiz "
                   "(mediana de três execuções).",
            fontsize=12, color=MUTED)

    fig.savefig(path, dpi=DPI, facecolor=PAPER)
    plt.close(fig)
    return (
        f"**Página 1 — O caso.** Debate sobre {cell.topic} entre o par "
        f"{cell.pair_id}. Controle e tratamento compartilham personas, tema e "
        f"modelos; diferem apenas pela presença do moderador."
    )


def page_turns(
    example: Example,
    condition: str,
    turns: list,
    page_number: int,
    total_pages: int,
    path: Path,
) -> str:
    """A page of published messages under one condition."""
    cell = example.cell
    is_control = condition == "control"
    color = CONTROL_COLOR if is_control else TREATMENT_COLOR
    title = (
        "Sem moderação: a hostilidade escala"
        if is_control
        else "Com moderação (D5): a hostilidade é contida"
    )
    fig, ax = _page(
        title,
        f"{cell.topic} · {cell.pair_id} · turnos "
        f"{turns[0].turn}–{turns[-1].turn} de {len(getattr(cell, condition).turns)}",
    )

    ax.add_patch(
        FancyBboxPatch(
            (5.4, 12), 89, 68,
            boxstyle="round,pad=0.4", linewidth=0, facecolor=color, alpha=0.05,
        )
    )

    height = 66 / len(turns)
    for index, turn in enumerate(turns):
        top = 78 - index * height
        y = top - height + 2.5

        ax.text(7, top - 1.5, f"Turno {turn.turn}", fontsize=11,
                fontweight="bold", color=INK, va="top")
        ax.text(7, top - 5.2, PERSONA_PT.get(turn.persona_id, turn.persona_id),
                fontsize=9.5, color=MUTED, va="top")

        _message_box(
            ax, 21, y, 60, height - 4.5,
            turn.published_text, "white", color,
        )
        _score_badge(ax, 85, y + (height - 4.5) / 2 - 2.3, turn.score, "juiz")

    ax.text(6, 6, f"Página {page_number} de {total_pages}",
            fontsize=9, color=MUTED)

    fig.savefig(path, dpi=DPI, facecolor=PAPER)
    plt.close(fig)

    scores = [t.score for t in turns if t.score is not None]
    trend = (
        f"pontuações {' → '.join(str(s) for s in scores)}" if scores else "sem notas"
    )
    label = "controle" if is_control else "tratamento"
    return (
        f"**Página {page_number} — Mensagens publicadas ({label}), turnos "
        f"{turns[0].turn}–{turns[-1].turn}.** {trend.capitalize()}."
    )


def page_reformulations(
    example: Example, turns: list, page_number: int, total_pages: int, path: Path
) -> str:
    """Candidate beside reformulation, for turns the moderator rewrote."""
    cell = example.cell
    fig, ax = _page(
        "O que o moderador fez",
        f"{cell.topic} · {cell.pair_id} · mensagem candidata × texto publicado",
    )

    ax.text(24, 81, "Candidato (gerado pelo debatedor)", fontsize=12,
            fontweight="bold", color=CONTROL_COLOR, ha="center")
    ax.text(68, 81, "Publicado (reformulado pelo D5)", fontsize=12,
            fontweight="bold", color=TREATMENT_COLOR, ha="center")

    height = 62 / max(len(turns), 1)
    for index, turn in enumerate(turns):
        top = 77 - index * height
        y = top - height + 3

        ax.text(6, top - 2, f"T{turn.turn}", fontsize=11,
                fontweight="bold", color=INK, va="top")
        _score_badge(ax, 4.5, y + (height - 5) / 2 - 2.3,
                     turn.moderator_score, "moderador")

        _message_box(ax, 14, y, 38, height - 5,
                     turn.candidate, CANDIDATE_BG, CONTROL_COLOR, 9.5)
        ax.annotate(
            "", xy=(57.5, y + (height - 5) / 2), xytext=(54, y + (height - 5) / 2),
            arrowprops={"arrowstyle": "-|>", "linewidth": 2, "color": MUTED},
        )
        _message_box(ax, 59, y, 35, height - 5,
                     turn.published_text, REFORM_BG, TREATMENT_COLOR, 9.5)

    ax.text(6, 6, f"Página {page_number} de {total_pages}",
            fontsize=9, color=MUTED)
    ax.text(30, 6, "A pontuação à esquerda é a leitura do moderador sobre o "
                   "candidato, antes da reescrita.",
            fontsize=9, color=MUTED)

    fig.savefig(path, dpi=DPI, facecolor=PAPER)
    plt.close(fig)
    return (
        f"**Página {page_number} — Intervenção do moderador.** Mensagem "
        f"candidata e texto efetivamente publicado, para turnos em que houve "
        f"reformulação."
    )


def page_comparison(
    example: Example, page_number: int, total_pages: int, path: Path
) -> str:
    """Final page — both trajectories on one axis."""
    cell = example.cell
    fig = plt.figure(figsize=PAGE, dpi=DPI, facecolor=PAPER)
    ax_title = fig.add_axes([0, 0, 1, 1])
    ax_title.set_xlim(0, 100)
    ax_title.set_ylim(0, 100)
    ax_title.axis("off")
    ax_title.text(6, 92, "As duas trajetórias, lado a lado",
                  fontsize=24, fontweight="bold", color=INK, va="top")
    ax_title.text(6, 86.5, f"{cell.topic} · {cell.pair_id}",
                  fontsize=13, color=MUTED, va="top")
    ax_title.text(6, 6, f"Página {page_number} de {total_pages}",
                  fontsize=9, color=MUTED)

    ax = fig.add_axes([0.09, 0.16, 0.84, 0.60])
    for condition, color, label in (
        ("control", CONTROL_COLOR, "Controle"),
        ("treatment", TREATMENT_COLOR, "Tratamento (D5)"),
    ):
        debate = getattr(cell, condition)
        turns = [t.turn for t in debate.turns if t.score is not None]
        scores = [t.score for t in debate.turns if t.score is not None]
        ax.plot(turns, scores, marker="o", markersize=9, linewidth=2.5,
                color=color, label=label)
        for x, y in zip(turns, scores):
            ax.annotate(str(y), (x, y), textcoords="offset points",
                        xytext=(0, 11), ha="center", fontsize=10, color=color)

    ax.set_xlabel("Turno", fontsize=12)
    ax.set_ylabel("Hostilidade (0–4)", fontsize=12)
    ax.set_ylim(-0.4, 4.6)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_xticks([t.turn for t in cell.control.turns])
    ax.legend(frameon=False, fontsize=12, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.6)
    ax.set_axisbelow(True)

    fig.savefig(path, dpi=DPI, facecolor=PAPER)
    plt.close(fig)
    return (
        f"**Página {page_number} — Comparação.** Pontuação de hostilidade turno "
        f"a turno nas duas condições para o mesmo par de personas "
        f"(Δ = {example.delta:+.2f}).".replace(".", ",")
    )


@dataclass(frozen=True, slots=True)
class ShowcaseTurn:
    """A turn with the texts the slides need, joined from disk."""

    turn: int
    persona_id: str
    published_text: str
    candidate: str
    score: int | None
    moderator_score: int | None
    reformulated: bool


def _load_texts(run) -> list[ShowcaseTurn]:
    """Transcript texts joined with the judge scores already computed."""
    from analysis.metrics import load_debate

    debate = load_debate(run)
    transcript = json.loads((run.path / "transcript.json").read_text(encoding="utf-8"))
    by_turn = {t.get("turn"): t for t in transcript.get("turns", [])}

    out = []
    for record in debate.turns:
        entry = by_turn.get(record.turn, {})
        out.append(
            ShowcaseTurn(
                turn=record.turn,
                persona_id=record.persona_id,
                published_text=entry.get("published_text", ""),
                candidate=entry.get("candidate", ""),
                score=record.score,
                moderator_score=record.moderator_score,
                reformulated=record.reformulated,
            )
        )
    return out


def build_showcase(
    selection: Selection,
    out_dir: Path,
    topic: str | None = None,
    pair_id: str | None = None,
    turns_per_page: int = 3,
) -> dict:
    """Write the slide sequence. Returns what was created and which cell won."""
    cells = load_cells(selection)
    ranked = pick_example(cells, topic=topic, pair_id=pair_id)
    if not ranked:
        return {"pages": [], "example": None}

    example = ranked[0]
    out_dir.mkdir(parents=True, exist_ok=True)

    control_turns = _load_texts(_run_of(selection, example, "control"))
    treatment_turns = _load_texts(_run_of(selection, example, "treatment"))

    control_pages = _chunk(control_turns, turns_per_page)
    treatment_pages = _chunk(treatment_turns, turns_per_page)
    reformulated = [t for t in treatment_turns if t.reformulated and t.candidate]
    reform_pages = _chunk(reformulated[:4], 2) if reformulated else []

    total = 1 + len(control_pages) + len(treatment_pages) + len(reform_pages) + 1

    captions: list[str] = []
    pages: list[Path] = []
    number = 1

    path = out_dir / f"p{number:02d}_capa.png"
    captions.append(page_cover(example, path))
    pages.append(path)
    number += 1

    for chunk in control_pages:
        path = out_dir / f"p{number:02d}_controle.png"
        captions.append(
            page_turns(example, "control", chunk, number, total, path)
        )
        pages.append(path)
        number += 1

    for chunk in treatment_pages:
        path = out_dir / f"p{number:02d}_tratamento.png"
        captions.append(
            page_turns(example, "treatment", chunk, number, total, path)
        )
        pages.append(path)
        number += 1

    for chunk in reform_pages:
        path = out_dir / f"p{number:02d}_reformulacao.png"
        captions.append(
            page_reformulations(example, chunk, number, total, path)
        )
        pages.append(path)
        number += 1

    path = out_dir / f"p{number:02d}_comparacao.png"
    captions.append(page_comparison(example, number, total, path))
    pages.append(path)

    _write_markdown(example, control_turns, treatment_turns, captions, out_dir)

    return {
        "pages": pages,
        "example": example,
        "ranking": ranked[:5],
    }


def _run_of(selection: Selection, example: Example, condition: str):
    """The Run object behind one side of the chosen cell."""
    for replicate in selection.replicates:
        if (
            replicate.topic == example.cell.topic
            and replicate.pair_id == example.cell.pair_id
            and replicate.index == example.cell.replicate
        ):
            return getattr(replicate, condition)
    raise LookupError("replicate not found in selection")


def _chunk(items: list, size: int) -> list[list]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _write_markdown(
    example: Example,
    control_turns: list[ShowcaseTurn],
    treatment_turns: list[ShowcaseTurn],
    captions: list[str],
    out_dir: Path,
) -> None:
    """The same walkthrough as text, for the paper."""
    cell = example.cell
    lines = [
        f"# Exemplo trabalhado — {cell.topic}, {cell.pair_id}",
        "",
        f"- Controle: hostilidade média **{cell.control.mean_hostility:.2f}**",
        f"- Tratamento: hostilidade média **{cell.treatment.mean_hostility:.2f}**",
        f"- Δ: **{example.delta:+.2f}**",
        "",
        "## Controle — sem moderação",
        "",
        "| Turno | Persona | Juiz | Mensagem publicada |",
        "|---:|---|---:|---|",
    ]
    for turn in control_turns:
        text = _truncate(turn.published_text, 240).replace("|", "\\|")
        lines.append(
            f"| {turn.turn} | {PERSONA_PT.get(turn.persona_id, turn.persona_id)} "
            f"| {turn.score} | {text} |"
        )

    lines += [
        "",
        "## Tratamento — com moderação D5",
        "",
        "| Turno | Persona | Moderador | Juiz | Reformulado | Mensagem publicada |",
        "|---:|---|---:|---:|:---:|---|",
    ]
    for turn in treatment_turns:
        text = _truncate(turn.published_text, 200).replace("|", "\\|")
        mark = "sim" if turn.reformulated else "não"
        lines.append(
            f"| {turn.turn} | {PERSONA_PT.get(turn.persona_id, turn.persona_id)} "
            f"| {turn.moderator_score} | {turn.score} | {mark} | {text} |"
        )

    lines += ["", "## Legendas das páginas", ""]
    lines += [f"{caption}\n" for caption in captions]

    (out_dir / "exemplo.md").write_text("\n".join(lines), encoding="utf-8")
