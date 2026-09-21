# Architecture Figure Index

CreditScoreV4 keeps committed architecture sources and rendered assets under `docs/assets/diagrams/`.

The v1 documentation uses two diagram classes:

- **system-level diagrams** — the canonical README/architecture views;
- **phase-specific diagrams** — implementation/evidence views retained for technical and historical review.

---

## Primary v1 system architecture

| Figure | Mermaid source | Rendered SVG |
|---|---|---|
| **System overview** | [`system-overview.mmd`](assets/diagrams/system-overview.mmd) | [`system-overview.svg`](assets/diagrams/system-overview.svg) |
| **Governance & release model** | [`governance-release-model.mmd`](assets/diagrams/governance-release-model.mmd) | [`governance-release-model.svg`](assets/diagrams/governance-release-model.svg) |
| **Delivery controls** | [`delivery-controls.mmd`](assets/diagrams/delivery-controls.mmd) | [`delivery-controls.svg`](assets/diagrams/delivery-controls.svg) |

These are the primary architecture diagrams for the current v1 repository.

- `system-overview` shows the complete control-plane architecture.
- `governance-release-model` separates eligibility decisions from runtime release safety.
- `delivery-controls` separates automatic merge verification from the manual fail-closed AWS mutation path.

---

## Phase-specific architecture

Phase-specific diagrams are retained in Mermaid, Graphviz, and rendered SVG form.

| Figure | Mermaid | Graphviz | Rendered SVG |
|---|---|---|---|
| Phase 1 — Incident baseline & reproduction | [`phase1-incident-baseline.mmd`](assets/diagrams/phase1-incident-baseline.mmd) | [`phase1-incident-baseline.dot`](assets/diagrams/phase1-incident-baseline.dot) | [`phase1-incident-baseline.svg`](assets/diagrams/phase1-incident-baseline.svg) |
| Phase 2 — Data-quality governance | [`phase2-data-quality-governance.mmd`](assets/diagrams/phase2-data-quality-governance.mmd) | [`phase2-data-quality-governance.dot`](assets/diagrams/phase2-data-quality-governance.dot) | [`phase2-data-quality-governance.svg`](assets/diagrams/phase2-data-quality-governance.svg) |
| Phase 3 — Drift governance | [`phase3-drift-governance.mmd`](assets/diagrams/phase3-drift-governance.mmd) | [`phase3-drift-governance.dot`](assets/diagrams/phase3-drift-governance.dot) | [`phase3-drift-governance.svg`](assets/diagrams/phase3-drift-governance.svg) |
| Phase 4 — Fairness & explainability | [`phase4-fairness-explainability.mmd`](assets/diagrams/phase4-fairness-explainability.mmd) | [`phase4-fairness-explainability.dot`](assets/diagrams/phase4-fairness-explainability.dot) | [`phase4-fairness-explainability.svg`](assets/diagrams/phase4-fairness-explainability.svg) |
| Phase 5 — Governance registry | [`phase5-governance-registry.mmd`](assets/diagrams/phase5-governance-registry.mmd) | [`phase5-governance-registry.dot`](assets/diagrams/phase5-governance-registry.dot) | [`phase5-governance-registry.svg`](assets/diagrams/phase5-governance-registry.svg) |
| Phase 6 — Serving & safe release | [`phase6-serving-safe-release.mmd`](assets/diagrams/phase6-serving-safe-release.mmd) | [`phase6-serving-safe-release.dot`](assets/diagrams/phase6-serving-safe-release.dot) | [`phase6-serving-safe-release.svg`](assets/diagrams/phase6-serving-safe-release.svg) |
| Phase 7 — Automation & deployment controls | [`phase7-automation-deployment.mmd`](assets/diagrams/phase7-automation-deployment.mmd) | [`phase7-automation-deployment.dot`](assets/diagrams/phase7-automation-deployment.dot) | [`phase7-automation-deployment.svg`](assets/diagrams/phase7-automation-deployment.svg) |
| Phase 8 — Governance evidence review | [`phase8-governance-evidence.mmd`](assets/diagrams/phase8-governance-evidence.mmd) | [`phase8-governance-evidence.dot`](assets/diagrams/phase8-governance-evidence.dot) | [`phase8-governance-evidence.svg`](assets/diagrams/phase8-governance-evidence.svg) |
| Phase 9 — Business impact | [`phase9-business-impact.mmd`](assets/diagrams/phase9-business-impact.mmd) | [`phase9-business-impact.dot`](assets/diagrams/phase9-business-impact.dot) | [`phase9-business-impact.svg`](assets/diagrams/phase9-business-impact.svg) |
| Phase 10 — Root-cause ablation | [`phase10-root-cause.mmd`](assets/diagrams/phase10-root-cause.mmd) | [`phase10-root-cause.dot`](assets/diagrams/phase10-root-cause.dot) | [`phase10-root-cause.svg`](assets/diagrams/phase10-root-cause.svg) |
| Phase 11 — Monitoring orchestration | [`phase11-orchestration.mmd`](assets/diagrams/phase11-orchestration.mmd) | [`phase11-orchestration.dot`](assets/diagrams/phase11-orchestration.dot) | [`phase11-orchestration.svg`](assets/diagrams/phase11-orchestration.svg) |
| Phase 12 — Intersectional fairness & proxy risk | [`phase12-fairness-proxy.mmd`](assets/diagrams/phase12-fairness-proxy.mmd) | [`phase12-fairness-proxy.dot`](assets/diagrams/phase12-fairness-proxy.dot) | [`phase12-fairness-proxy.svg`](assets/diagrams/phase12-fairness-proxy.svg) |
| Phase 13 — Incident operations & SLA evidence | [`phase13-incident-ops.mmd`](assets/diagrams/phase13-incident-ops.mmd) | [`phase13-incident-ops.dot`](assets/diagrams/phase13-incident-ops.dot) | [`phase13-incident-ops.svg`](assets/diagrams/phase13-incident-ops.svg) |
| Historical Phase 1–13 sequence | [`phase1-13-end-to-end.mmd`](assets/diagrams/phase1-13-end-to-end.mmd) | [`phase1-13-end-to-end.dot`](assets/diagrams/phase1-13-end-to-end.dot) | [`phase1-13-end-to-end.svg`](assets/diagrams/phase1-13-end-to-end.svg) |

---

## Supplemental state diagram

| Figure | Mermaid | Graphviz | Rendered SVG |
|---|---|---|---|
| Registry/release state machine | [`release-state.mmd`](assets/diagrams/release-state.mmd) | [`release-state.dot`](assets/diagrams/release-state.dot) | [`release-state.svg`](assets/diagrams/release-state.svg) |

---

## Validation policy

The committed SVG files are the documentation renderings used by GitHub.

Run:

```bash
make diagram-validate
```

The validator checks:

- required architecture assets exist;
- Mermaid sources stay inside the repository's GitHub-safe subset;
- committed SVG files are valid XML/SVG;
- Graphviz phase diagrams remain structurally valid;
- Graphviz render checks run when `dot` is installed;
- README and `ARCHITECTURE.md` reference the primary v1 diagrams;
- this index contains every required diagram.

When Graphviz is installed, regenerate Graphviz-backed SVGs with:

```bash
make diagram-render
```
