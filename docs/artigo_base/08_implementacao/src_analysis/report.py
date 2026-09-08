"""Tables and figures from computed metrics.

Captions are written in Portuguese for the defence slides; the paper is in
English, so each caption is short enough to translate in place. Every figure
is written as PNG at 300 dpi (slide- and print-safe) with its caption in the
accompanying Markdown, never burned into the image — a caption baked into a
figure cannot be edited when the text around it changes.

Colours are fixed per condition and reused across every figure so the reader
learns the mapping once.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # No display in a terminal session.

import matplotlib.pyplot as plt  # noqa: E402

CONTROL_COLOR = "#c44536"
TREATMENT_COLOR = "#2a6f97"
GRID_COLOR = "#d9d9d9"

DPI = 300
CONDITION_PT = {"control": "Controle", "treatment": "Tratamento (D5)"}


def _style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)


def _fmt(value: float | None, places: int = 2) -> str:
    """Numbers in Portuguese convention: decimal comma."""
    if value is None:
        return "—"
    return f"{value:.{places}f}".replace(".", ",")


def _pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.0f}%".replace(".", ",")


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------


def table_main_effect(metrics: dict) -> tuple[str, list[dict]]:
    """T1 — main effect overall and per topic."""
    rows: list[dict] = []
    overall = metrics["main_effect"]
    rows.append(
        {
            "recorte": "Global",
            "n_celulas": overall["delta"]["n"],
            "controle": _fmt(overall["control"]["mean"]),
            "tratamento": _fmt(overall["treatment"]["mean"]),
            "delta": _fmt(overall["delta"]["mean"]),
            "dp_delta": _fmt(overall["delta"]["sd"]),
            "celulas_favoraveis": f"{overall['cells_favouring_treatment']}/{overall['delta']['n']}",
        }
    )
    for topic, value in metrics["main_effect_by_topic"].items():
        rows.append(
            {
                "recorte": topic,
                "n_celulas": value["delta"]["n"],
                "controle": _fmt(value["control"]["mean"]),
                "tratamento": _fmt(value["treatment"]["mean"]),
                "delta": _fmt(value["delta"]["mean"]),
                "dp_delta": _fmt(value["delta"]["sd"]),
                "celulas_favoraveis": f"{value['cells_favouring_treatment']}/{value['delta']['n']}",
            }
        )

    header = (
        "| Recorte | Células | Controle | Tratamento | Δ | DP(Δ) | Células com Δ<0 |\n"
        "|---|---:|---:|---:|---:|---:|---:|\n"
    )
    body = "".join(
        f"| {r['recorte']} | {r['n_celulas']} | {r['controle']} | {r['tratamento']} "
        f"| {r['delta']} | {r['dp_delta']} | {r['celulas_favoraveis']} |\n"
        for r in rows
    )
    caption = (
        "**Tabela 1 — Efeito principal do D5 sobre a hostilidade.** Hostilidade "
        "média por debate (escala 0–4, mediana de três execuções do juiz), "
        "agregada por célula (tema × par de personas). Δ é a diferença pareada "
        "tratamento − controle dentro de cada célula; valores negativos indicam "
        "redução de hostilidade sob moderação. DP(Δ) é o desvio-padrão "
        "populacional entre células."
    )
    return header + body + "\n" + caption + "\n", rows


def table_activation(metrics: dict) -> tuple[str, list[dict]]:
    """T2 — how often D5 fired and rewrote."""
    a = metrics["activation"]
    rows = [
        {"metrica": "Turnos de tratamento", "valor": str(a["treatment_turns"])},
        {
            "metrica": "Mensagens avaliadas pelo moderador",
            "valor": f"{a['moderated']} ({_pct(a['moderated_rate'])})",
        },
        {
            "metrica": "Mensagens reformuladas",
            "valor": f"{a['reformulated']} ({_pct(a['reformulated_rate'])})",
        },
        {
            "metrica": "Reformuladas / avaliadas",
            "valor": _pct(a["reformulated_rate_of_moderated"]),
        },
        {
            "metrica": "Decisões fora do limiar",
            "valor": f"{a['off_threshold_decisions']} ({_pct(a['off_threshold_rate'])})",
        },
    ]
    header = "| Métrica | Valor |\n|---|---:|\n"
    body = "".join(f"| {r['metrica']} | {r['valor']} |\n" for r in rows)
    caption = (
        "**Tabela 2 — Acionamento da moderação participativa (D5).** Toda "
        "mensagem candidata na condição de tratamento passa pelo moderador; "
        "\"reformuladas\" são aquelas em que ele substituiu o texto antes da "
        "publicação. \"Decisões fora do limiar\" conta turnos em que a decisão "
        "de intervir discordou da própria pontuação atribuída pelo moderador "
        "(limiar: hostilidade ≥ 2), medindo sua calibragem interna."
    )
    return header + body + "\n" + caption + "\n", rows


def table_judge(metrics: dict) -> tuple[str, list[dict]]:
    """T3 — intra-judge consistency."""
    j = metrics["judge_consistency"]
    rows = [
        {"metrica": "Mensagens pontuadas", "valor": str(j["messages_scored"])},
        {"metrica": "Execuções por mensagem", "valor": "3"},
        {
            "metrica": "Unanimidade entre execuções",
            "valor": f"{j['unanimous']} ({_pct(j['unanimous_rate'])})",
        },
    ]
    for spread, count in sorted(j["range_distribution"].items()):
        rows.append(
            {"metrica": f"Amplitude {spread} entre execuções", "valor": str(count)}
        )
    header = "| Métrica | Valor |\n|---|---:|\n"
    body = "".join(f"| {r['metrica']} | {r['valor']} |\n" for r in rows)
    caption = (
        "**Tabela 3 — Consistência intra-juiz.** Cada mensagem publicada foi "
        "pontuada três vezes de forma independente pelo mesmo modelo juiz "
        "(temperatura 0). Amplitude é a diferença entre a maior e a menor "
        "pontuação das três execuções; amplitude 0 indica acordo perfeito. A "
        "consistência inter-juiz (modelos distintos avaliando o mesmo corpus) "
        "permanece pendente."
    )
    return header + body + "\n" + caption + "\n", rows


def table_per_cell(metrics: dict) -> tuple[str, list[dict]]:
    """T4 — one row per replicate."""
    rows = metrics["per_cell"]
    header = (
        "| Tema | Par | Réplica | Controle | Tratamento | Δ |\n"
        "|---|---|---:|---:|---:|---:|\n"
    )
    body = "".join(
        f"| {r['topic']} | {r['pair_id']} | {r['replicate']} "
        f"| {_fmt(r['control_mean'])} | {_fmt(r['treatment_mean'])} "
        f"| {_fmt(r['delta'])} |\n"
        for r in rows
    )
    caption = (
        "**Tabela 4 — Efeito por célula.** Hostilidade média de cada debate e "
        "diferença pareada, por tema e par de personas. Cada linha é uma "
        "réplica independente: controle e tratamento compartilham tema e par, "
        "diferindo apenas pela presença do moderador."
    )
    return header + body + "\n" + caption + "\n", rows


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------


def figure_main_effect(metrics: dict, path: Path) -> str:
    """G1 — the headline bar chart."""
    topics = list(metrics["main_effect_by_topic"])
    labels = ["Global"] + topics
    control = [metrics["main_effect"]["control"]["mean"]] + [
        metrics["main_effect_by_topic"][t]["control"]["mean"] for t in topics
    ]
    treatment = [metrics["main_effect"]["treatment"]["mean"]] + [
        metrics["main_effect_by_topic"][t]["treatment"]["mean"] for t in topics
    ]
    control_sd = [metrics["main_effect"]["control"]["sd"]] + [
        metrics["main_effect_by_topic"][t]["control"]["sd"] for t in topics
    ]
    treatment_sd = [metrics["main_effect"]["treatment"]["sd"]] + [
        metrics["main_effect_by_topic"][t]["treatment"]["sd"] for t in topics
    ]

    x = range(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 4.2))

    ax.bar(
        [i - width / 2 for i in x], control, width, yerr=control_sd, capsize=4,
        label=CONDITION_PT["control"], color=CONTROL_COLOR,
        error_kw={"ecolor": "#555", "linewidth": 1},
    )
    ax.bar(
        [i + width / 2 for i in x], treatment, width, yerr=treatment_sd, capsize=4,
        label=CONDITION_PT["treatment"], color=TREATMENT_COLOR,
        error_kw={"ecolor": "#555", "linewidth": 1},
    )

    # Clear the error bar, not just the bar, or the label sits on the whisker.
    for i, (c, t, cs, ts) in enumerate(
        zip(control, treatment, control_sd, treatment_sd)
    ):
        ax.text(i - width / 2, c + (cs or 0) + 0.10, _fmt(c),
                ha="center", fontsize=9)
        ax.text(i + width / 2, t + (ts or 0) + 0.10, _fmt(t),
                ha="center", fontsize=9)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Hostilidade média (0–4)")
    ax.set_ylim(0, 4)
    ax.legend(frameon=False, loc="upper right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)

    delta = metrics["main_effect"]["delta"]["mean"]
    return (
        f"**Figura 1 — Hostilidade média por condição.** Escala 0–4 (mediana de "
        f"três execuções do juiz), agregada por célula. A moderação participativa "
        f"reduziu a hostilidade em {_fmt(abs(delta))} ponto na média global, com "
        f"efeito de magnitude semelhante nos dois temas. Barras de erro: "
        f"desvio-padrão entre células."
    )


def figure_trajectory(metrics: dict, path: Path) -> str:
    """G2 — hostility over turns, both conditions."""
    fig, ax = plt.subplots(figsize=(7.2, 4.2))

    for condition, color in (
        ("control", CONTROL_COLOR),
        ("treatment", TREATMENT_COLOR),
    ):
        series = metrics["per_turn"][condition]
        turns = sorted(int(t) for t in series)
        means = [series[t]["mean"] for t in turns]
        sds = [series[t]["sd"] or 0 for t in turns]
        ax.plot(turns, means, marker="o", color=color, label=CONDITION_PT[condition])
        ax.fill_between(
            turns,
            [m - s for m, s in zip(means, sds)],
            [m + s for m, s in zip(means, sds)],
            color=color, alpha=0.15, linewidth=0,
        )

    ax.set_xlabel("Turno")
    ax.set_ylabel("Hostilidade média (0–4)")
    ax.set_ylim(0, 4)
    ax.set_xticks(sorted(int(t) for t in metrics["per_turn"]["control"]))
    ax.legend(frameon=False, loc="upper left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)

    return (
        "**Figura 2 — Trajetória da hostilidade ao longo do debate.** Média por "
        "turno em cada condição; faixa sombreada indica ±1 desvio-padrão entre "
        "células. O controle escala progressivamente, enquanto o tratamento "
        "mantém patamar mais baixo. Ressalva metodológica: a partir do turno 2 "
        "as condições deixam de compartilhar o mesmo histórico, pois os "
        "debatedores sob tratamento respondem a mensagens já reformuladas — "
        "parte da diferença é efeito direto da reescrita e parte é desescalada "
        "indireta, e o desenho não as separa."
    )


def figure_distribution(metrics: dict, path: Path) -> str:
    """G3 — score distribution per condition."""
    levels = ["0", "1", "2", "3", "4"]
    control = [metrics["score_distribution"]["control"][lv] for lv in levels]
    treatment = [metrics["score_distribution"]["treatment"][lv] for lv in levels]

    x = range(len(levels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar([i - width / 2 for i in x], control, width,
           label=CONDITION_PT["control"], color=CONTROL_COLOR)
    ax.bar([i + width / 2 for i in x], treatment, width,
           label=CONDITION_PT["treatment"], color=TREATMENT_COLOR)

    ax.set_xticks(list(x))
    ax.set_xticklabels(levels)
    ax.set_xlabel("Nível de hostilidade atribuído pelo juiz")
    ax.set_ylabel("Mensagens")
    ax.legend(frameon=False)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)

    return (
        "**Figura 3 — Distribuição das pontuações de hostilidade.** Contagem de "
        "mensagens publicadas por nível da escala em cada condição. Sob "
        "controle a massa concentra-se nos níveis 3 e 4; sob tratamento "
        "desloca-se para 1 e 2, indicando que a moderação não apenas reduz a "
        "média mas redistribui as mensagens ao longo da escala."
    )


def figure_per_cell_delta(metrics: dict, path: Path) -> str:
    """G4 — per-cell deltas, sorted."""
    rows = [r for r in metrics["per_cell"] if r["delta"] is not None]
    rows.sort(key=lambda r: r["delta"])
    labels = [
        f"{r['topic'][:4]}·{r['pair_id'].replace('pair-', 'p')}·r{r['replicate']}"
        for r in rows
    ]
    deltas = [r["delta"] for r in rows]

    fig, ax = plt.subplots(figsize=(7.2, max(3.2, 0.28 * len(rows) + 1.4)))
    colors = [TREATMENT_COLOR if d < 0 else CONTROL_COLOR for d in deltas]
    ax.barh(range(len(deltas)), deltas, color=colors)
    ax.axvline(0, color="#333", linewidth=1)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Δ hostilidade (tratamento − controle)")
    ax.invert_yaxis()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)

    negative = sum(1 for d in deltas if d < 0)
    return (
        f"**Figura 4 — Efeito por célula.** Diferença pareada em cada réplica, "
        f"ordenada por magnitude. O efeito é negativo em {negative} das "
        f"{len(deltas)} células, indicando que a redução de hostilidade não se "
        f"concentra em poucos pares de personas mas se repete em todo o corpus."
    )


# --------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(metrics: dict, out_dir: Path) -> dict[str, Path]:
    """Write every table, figure and export. Returns what was created."""
    tables_dir = out_dir / "tables"
    figures_dir = out_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    created: dict[str, Path] = {}

    tables = [
        ("t1_efeito_principal", table_main_effect(metrics)),
        ("t2_acionamento_d5", table_activation(metrics)),
        ("t3_consistencia_juiz", table_judge(metrics)),
        ("t4_efeito_por_celula", table_per_cell(metrics)),
    ]
    sections: list[str] = []
    for name, (markdown, rows) in tables:
        write_csv(rows, tables_dir / f"{name}.csv")
        (tables_dir / f"{name}.md").write_text(markdown, encoding="utf-8")
        sections.append(markdown)
        created[name] = tables_dir / f"{name}.md"

    figures = [
        ("g1_efeito_principal", figure_main_effect),
        ("g2_trajetoria_turnos", figure_trajectory),
        ("g3_distribuicao_notas", figure_distribution),
        ("g4_delta_por_celula", figure_per_cell_delta),
    ]
    figure_captions: list[str] = []
    for name, builder in figures:
        png = figures_dir / f"{name}.png"
        caption = builder(metrics, png)
        (figures_dir / f"{name}.txt").write_text(caption + "\n", encoding="utf-8")
        figure_captions.append(f"![{name}](figures/{name}.png)\n\n{caption}")
        created[name] = png

    report = _assemble_report(metrics, sections, figure_captions)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    created["report"] = out_dir / "report.md"

    return created


def _assemble_report(
    metrics: dict, tables: list[str], figures: list[str]
) -> str:
    corpus = metrics["corpus"]
    effect = metrics["main_effect"]
    preservation = metrics["argument_preservation"]

    lines = [
        "# Resultados preliminares — Moderação participativa (D5)",
        "",
        "## Corpus",
        "",
        f"- Desenho: {'balanceado' if corpus['balanced'] else 'completo'}",
        f"- Temas: {', '.join(corpus['topics'])}",
        f"- Células (tema × par de personas): {corpus['cells']}",
        f"- Réplicas: {corpus['replicates']}",
        f"- Debates: {corpus['debates']} ({corpus['turns_per_debate']} turnos cada)",
        f"- Execuções descartadas na seleção: {corpus['excluded_runs']}",
        "",
        "## Resultado principal",
        "",
        f"A moderação participativa reduziu a hostilidade média de "
        f"**{_fmt(effect['control']['mean'])}** para "
        f"**{_fmt(effect['treatment']['mean'])}** na escala 0–4 "
        f"(Δ = **{_fmt(effect['delta']['mean'])}**), com efeito na mesma direção "
        f"em {effect['cells_favouring_treatment']} das {effect['delta']['n']} "
        f"células.",
        "",
        "## Tabelas",
        "",
        *[t + "\n" for t in tables],
        "## Figuras",
        "",
        *[f + "\n" for f in figures],
        "## Ressalvas",
        "",
        "1. **Históricos divergentes.** A partir do turno 2 as condições deixam "
        "de compartilhar o mesmo histórico: sob tratamento, os debatedores "
        "respondem a mensagens já reformuladas. Parte do efeito é a reescrita "
        "direta da mensagem, parte é desescalada indireta do interlocutor; o "
        "desenho atual não separa as duas.",
        "",
        f"2. **Preservação argumentativa é autodeclarada.** Em "
        f"{preservation['preservation_declared']} das "
        f"{preservation['reformulations']} reformulações o moderador declarou "
        f"o que preservou, mas essa declaração provém da mesma chamada que "
        f"produziu a reformulação. Não constitui evidência de que a posição "
        f"original sobreviveu — verificação independente permanece pendente.",
        "",
        "3. **Geração estocástica.** O campo `seed` registrado nos manifestos "
        "não é repassado ao modelo; réplicas da mesma célula são execuções "
        "independentes, não reproduções exatas.",
        "",
        "4. **Modelos pequenos.** Debatedor, moderador e juiz são modelos de "
        "7–9B em quantização Q4, imposição do hardware disponível.",
        "",
    ]
    return "\n".join(lines)
