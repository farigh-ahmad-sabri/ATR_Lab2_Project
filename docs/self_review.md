# Critical technical review of the draft (Prompt 16)

Reviewer stance: a sceptical reviewer who has read the code. Page numbers refer to
`paper/Final_Paper.pdf`.

## MAJOR

| # | Concern | Where | Why it matters | Remedy | Status |
|---|---|---|---|---|---|
| M1 | The study is motivated by human trust but measures only detector performance. | §1, §7 | A reader could take "surface form is uninformative" as evidence about people. | State plainly that detectors are an upper bound for an idealised reader, and keep the human experiment as future work. | Done (§1, Limitations) |
| M2 | Part of the HALLMARK signal is benchmark artefact (DOI prefixes, venue length, arXiv-DOI pattern). | §6.1, §6.3, §6.4 | Headline AUROC 0.797 overstates what surface cues reveal about real fabrications. | Report the X1 refit, name the artefacts, centre conclusions on the W&W set. | Done; X1 labelled exploratory |
| M3 | The external set is small (341) and only journal articles. | §3, §6.2 | Wide CIs; may not generalise to conference papers or books. | Report CIs; avoid claims of "no signal" (grouped CV does find 0.68). | Done. A second human-coded external set would be the best follow-up. |
| M4 | Reference points are not baselines I validated (released outputs, earlier runs, possibly earlier labels). | §4.3, Table 3 | Comparisons with LLM readers or the lookup tool could be biased. | Re-score per entry against v1.2.4 labels; label them "reference points"; do not test differences against them. | Done |
| M5 | Threshold transfer to W&W fails (FPR 0.98). Is AUROC the fair metric there? | §6.2 | Reporting only DR/FPR would exaggerate the failure; reporting only AUROC would hide it. | Report both and explain the calibration collapse. | Done |

## MINOR

| # | Concern | Remedy | Status |
|---|---|---|---|
| m1 | Seeds barely change GBM results (SD ≤ 0.005), so "5 seeds" can look like padding. | Say so in the caption; the seed variation is real only in grouped CV. | Done (Table 3 caption) |
| m2 | M1 vs M2 difference not significant; avoid ranking them. | Paired bootstrap reported; text says they cannot be separated. | Done |
| m3 | Naser comparison could read as a refutation. | Explicitly say corpus/features/CV differ and his data are unavailable. | Done |
| m4 | Three post-hoc protocol changes. | Listed in §8 and `research_decisions.md`; run-1 outputs kept. | Done |
| m5 | Completeness rule is a crude proxy for "a reader who trusts complete references". | Acknowledge; it is meant as the simplest form of the heuristic in the review. | Partly; could add a weighted variant in future |
| m6 | No test of a model fine-tuned on citation strings. | Listed as a limitation. | Open |

## Author-response summary
All MAJOR items are addressed in the text. The main open weakness is the size and
scope of the external set (M3), which cannot be fixed without new human-coded data.
