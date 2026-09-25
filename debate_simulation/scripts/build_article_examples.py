"""Build the worked-example figures at the size the paper prints them.

The slide pages written by build_showcase.py are 16:9 and meant for a screen;
scaled down to one column of the paper, their text becomes unreadable. This
script draws the same example at print size (one column, fonts in real points)
and keeps a single turn per figure:

  exemplo_reformulacao.png  one candidate message and the text that replaced it
  exemplo_contencao.png     the same turn published without and with moderation

Reads only from disk, like build_showcase.py, and reuses its loaders. Text
longer than its box is cut in the middle, keeping the first and last
sentences, so that an insult closing a message is not the part that disappears.

Run from debate_simulation/, where the uv project lives:
    uv run python scripts/build_article_examples.py --reform-turn 3

or from the repo root, pointing uv at that project (the root has no
pyproject.toml, so a bare `uv run` there falls back to a Python without
matplotlib):
    uv run --project debate_simulation python debate_simulation/scripts/build_article_examples.py --reform-turn 3
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_DIR / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402

from analysis.metrics import load_cells  # noqa: E402
from analysis.selection import balance, select  # noqa: E402
from analysis.showcase import (  # noqa: E402
    CANDIDATE_BG,
    CONTROL_COLOR,
    INK,
    LEVEL_COLORS,
    MUTED,
    PAPER,
    PERSONA_PT,
    REFORM_BG,
    TREATMENT_COLOR,
    _load_texts,
    _run_of,
    pick_example,
)

EXPERIMENTS_DIR = _PROJECT_DIR / "experiments"
ANALYSIS_DIR = _PROJECT_DIR / "analysis"

RULE = "=" * 78

# One IEEE column is 3.5 in wide. Every size below is what ends up on paper.
COLUMN_WIDTH = 3.5
DPI = 300
BODY_PT = 7.6
META_PT = 6.5
CHIP_PT = 6.0
LINE = 1.38          # line height, in multiples of the body font size
MARGIN = 0.03        # figure edge to box, inches
PAD = 0.08           # box edge to text, inches
HEADER_H = 0.27
BOTTOM = 0.06        # last line to box edge, inches
# Measured widths run about 1% short of the rendered text; wrap a bit early.
WRAP_SLACK = 0.96
MAX_LINES = 6
OMISSION = " […] "


@dataclass(frozen=True, slots=True)
class Panel:
    """One message box: what it is, how it is coloured, and who scored it."""

    title: str
    color: str
    background: str
    text: str
    score: int | None
    scorer: str


def _width(text: str, size: float) -> float:
    """Rendered width of a line, in inches."""
    path = TextPath((0, 0), text, prop=FontProperties(size=size))
    return path.get_extents().width / 72


def _wrap(text: str, width: float, size: float) -> list[str]:
    """Greedy wrap by measured width, so lines never cross the box edge."""
    lines: list[str] = []
    current = ""
    for word in " ".join(text.split()).split(" "):
        trial = f"{current} {word}".strip()
        if current and _width(trial, size) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def _fit(text: str, width: float, size: float, max_lines: int) -> list[str]:
    """Wrap the text; when too long, drop middle sentences, keeping the ends.

    Sentences are added back from the end first, then from the start, while
    the result still fits. A message too long even for its first and last
    sentence falls back to a plain cut at the end.
    """
    lines = _wrap(text, width, size)
    if len(lines) <= max_lines:
        return lines

    sentences = [
        s for s in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if s
    ]

    def joined(head: list[str], tail: list[str]) -> list[str]:
        return _wrap(" ".join(head) + OMISSION + " ".join(tail), width, size)

    if len(sentences) >= 2 and len(joined(sentences[:1], sentences[-1:])) <= max_lines:
        head, tail = sentences[:1], sentences[-1:]
        start, end = 1, len(sentences) - 2
        grew = True
        while grew and start <= end:
            grew = False
            if len(joined(head, [sentences[end]] + tail)) <= max_lines:
                tail = [sentences[end]] + tail
                end -= 1
                grew = True
            if start <= end and len(joined(head + [sentences[start]], tail)) <= max_lines:
                head = head + [sentences[start]]
                start += 1
                grew = True
        return joined(head, tail)

    lines = lines[:max_lines]
    last = lines[-1]
    while last and _width(last + " …", size) > width:
        last = last.rsplit(" ", 1)[0] if " " in last else ""
    lines[-1] = last + " …"
    return lines


def _score_chip(ax, right: float, y: float, score: int | None, scorer: str) -> None:
    """The hostility level as a small coloured dot, labelled in grey."""
    if score is None:
        return
    radius = 0.068
    ax.add_patch(
        Circle((right - radius, y), radius,
               facecolor=LEVEL_COLORS.get(score, MUTED), linewidth=0)
    )
    ax.text(right - radius, y, str(score), fontsize=CHIP_PT + 0.4,
            fontweight="bold", color="white", ha="center", va="center")
    ax.text(right - 2 * radius - 0.05, y, f"hostilidade ({scorer})",
            fontsize=CHIP_PT, color=MUTED, ha="right", va="center")


def draw(panels: list[Panel], meta: str, connector: str | None, path: Path,
         width: float = COLUMN_WIDTH) -> None:
    """Stack the panels in one column-wide figure and save it."""
    inner = (width - 2 * MARGIN - 2 * PAD) * WRAP_SLACK
    bodies = [_fit(p.text, inner, BODY_PT, MAX_LINES) for p in panels]
    line_h = BODY_PT * LINE / 72
    heights = [HEADER_H + len(body) * line_h + BOTTOM for body in bodies]
    meta_h = 0.2
    gap = 0.34 if connector else 0.1
    total = 0.03 + meta_h + sum(heights) + gap * (len(panels) - 1) + 0.04

    fig = plt.figure(figsize=(width, total), dpi=DPI, facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width)
    ax.set_ylim(total, 0)   # inches, measured from the top
    ax.axis("off")

    box_w = width - 2 * MARGIN
    y = 0.03
    ax.text(MARGIN + 0.02, y + meta_h / 2, meta, fontsize=META_PT,
            color=MUTED, va="center")
    y += meta_h

    for index, (panel, body, height) in enumerate(zip(panels, bodies, heights)):
        ax.add_patch(
            FancyBboxPatch(
                (MARGIN, y), box_w, height,
                boxstyle="round,pad=0,rounding_size=0.05",
                linewidth=0.8, facecolor=panel.background,
                edgecolor=panel.color,
            )
        )
        header_y = y + 0.13
        ax.text(MARGIN + PAD, header_y, panel.title, fontsize=BODY_PT,
                fontweight="bold", color=panel.color, va="center")
        _score_chip(ax, MARGIN + box_w - PAD, header_y, panel.score,
                    panel.scorer)

        line_y = y + HEADER_H
        for line in body:
            ax.text(MARGIN + PAD, line_y, line, fontsize=BODY_PT, color=INK,
                    va="top")
            line_y += line_h
        y += height

        if index < len(panels) - 1:
            if connector:
                x = MARGIN + 0.3
                ax.annotate(
                    "", xy=(x, y + gap - 0.05), xytext=(x, y + 0.05),
                    arrowprops={"arrowstyle": "-|>", "color": MUTED,
                                "linewidth": 1.0, "mutation_scale": 8},
                )
                ax.text(x + 0.1, y + gap / 2, connector, fontsize=META_PT,
                        color=MUTED, style="italic", va="center")
            y += gap

    fig.savefig(path, dpi=DPI, facecolor=PAPER)
    plt.close(fig)


def _by_turn(turns: list, number: int):
    for turn in turns:
        if turn.turn == number:
            return turn
    raise LookupError(f"turn {number} not found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=8)
    parser.add_argument("--topic", help="force a topic (e.g. \"Abortion\")")
    parser.add_argument("--pair", help="force a pair (e.g. pair-03)")
    parser.add_argument(
        "--reform-turn", type=int,
        help="treatment turn for the reformulation figure "
             "(default: the reformulated turn with the largest drop "
             "from moderator score to judge score)",
    )
    parser.add_argument(
        "--contain-turn", type=int,
        help="turn for the control × treatment figure "
             "(default: the largest control − treatment judge score)",
    )
    parser.add_argument(
        "--run-name", default="metrics_balanced",
        help="analysis run directory to write into (default: metrics_balanced)",
    )
    args = parser.parse_args()

    selection = balance(select(EXPERIMENTS_DIR, expected_turns=args.turns))
    ranked = pick_example(load_cells(selection), topic=args.topic,
                          pair_id=args.pair)
    if not ranked:
        print("No cell matched the requested topic/pair.")
        return 1

    example = ranked[0]
    control = _load_texts(_run_of(selection, example, "control"))
    treatment = _load_texts(_run_of(selection, example, "treatment"))

    if args.reform_turn is not None:
        reform = _by_turn(treatment, args.reform_turn)
    else:
        rewritten = [t for t in treatment if t.reformulated and t.candidate
                     and t.moderator_score is not None and t.score is not None]
        reform = max(rewritten, key=lambda t: t.moderator_score - t.score)

    if args.contain_turn is not None:
        contain = args.contain_turn
    else:
        judged = {t.turn: t.score for t in treatment if t.score is not None}
        contain = max(
            (t for t in control if t.score is not None and t.turn in judged),
            key=lambda t: t.score - judged[t.turn],
        ).turn
    kept = _by_turn(control, contain)
    moderated = _by_turn(treatment, contain)

    out_dir = ANALYSIS_DIR / "runs" / args.run_name / "examples"
    out_dir.mkdir(parents=True, exist_ok=True)

    reform_path = out_dir / "exemplo_reformulacao.png"
    draw(
        [
            Panel("Mensagem candidata", CONTROL_COLOR, CANDIDATE_BG,
                  reform.candidate, reform.moderator_score, "moderador"),
            Panel("Texto publicado", TREATMENT_COLOR, REFORM_BG,
                  reform.published_text, reform.score, "juiz"),
        ],
        f"Turno {reform.turn} · "
        f"{PERSONA_PT.get(reform.persona_id, reform.persona_id)}",
        "reformulada pelo moderador D5",
        reform_path,
    )

    contain_path = out_dir / "exemplo_contencao.png"
    draw(
        [
            Panel("Sem moderação (controle)", CONTROL_COLOR, CANDIDATE_BG,
                  kept.published_text, kept.score, "juiz"),
            Panel("Com moderação D5 (tratamento)", TREATMENT_COLOR, REFORM_BG,
                  moderated.published_text, moderated.score, "juiz"),
        ],
        f"Turno {contain} · "
        f"{PERSONA_PT.get(kept.persona_id, kept.persona_id)} · texto publicado",
        None,
        contain_path,
    )

    print(RULE)
    print(" FIGURAS DO EXEMPLO PARA O ARTIGO")
    print(RULE)
    print(f"  célula       : {example.cell.topic} · {example.cell.pair_id} "
          f"· réplica {example.cell.replicate}")
    print(f"  reformulação : turno {reform.turn} · moderador "
          f"{reform.moderator_score} → juiz {reform.score}")
    print(f"  contenção    : turno {contain} · controle {kept.score} "
          f"× tratamento {moderated.score}")
    print(f"    {reform_path.name}")
    print(f"    {contain_path.name}")
    print(f"  saída        : {out_dir}")
    print(RULE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
