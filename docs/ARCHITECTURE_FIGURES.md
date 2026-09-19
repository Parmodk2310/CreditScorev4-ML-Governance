# Architecture Figure Index

All diagrams have three representations:

- `.mmd` — Mermaid source for Markdown-oriented editing
- `.dot` — Graphviz source for deterministic rendering
- `.svg` — rendered vector figure for GitHub README/docs

Files live in `docs/assets/diagrams/`.

| Figure | Mermaid | Graphviz | Rendered SVG |
|---|---|---|---|
| Phase 1 — Incident baseline | `phase1-incident-baseline.mmd` | `phase1-incident-baseline.dot` | `phase1-incident-baseline.svg` |
| Phase 2 — Data quality | `phase2-data-quality-governance.mmd` | `phase2-data-quality-governance.dot` | `phase2-data-quality-governance.svg` |
| Phase 3 — Drift | `phase3-drift-governance.mmd` | `phase3-drift-governance.dot` | `phase3-drift-governance.svg` |
| Phase 4 — Fairness + SHAP | `phase4-fairness-explainability.mmd` | `phase4-fairness-explainability.dot` | `phase4-fairness-explainability.svg` |
| Phase 5 — Governance registry | `phase5-governance-registry.mmd` | `phase5-governance-registry.dot` | `phase5-governance-registry.svg` |
| Phase 6 — Serving / safe release | `phase6-serving-safe-release.mmd` | `phase6-serving-safe-release.dot` | `phase6-serving-safe-release.svg` |
| Phase 7 — Automation / AWS | `phase7-automation-deployment.mmd` | `phase7-automation-deployment.dot` | `phase7-automation-deployment.svg` |
| End-to-end Phase 1–7 | `phase1-7-end-to-end.mmd` | `phase1-7-end-to-end.dot` | `phase1-7-end-to-end.svg` |
| Release state machine | `release-state.mmd` | `release-state.dot` | `release-state.svg` |

## Regenerating the SVGs

Graphviz is deterministic and does not require a browser:

```bash
for dotfile in docs/assets/diagrams/*.dot; do
  dot -Tsvg "$dotfile" -o "${dotfile%.dot}.svg"
done
```

If Mermaid CLI is installed, the `.mmd` files can also be rendered separately, but the committed SVGs in this patch are generated from the Graphviz sources so the repo has a single deterministic rendered form.
