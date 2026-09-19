# GitHub Repository Metadata

## Recommended description

Use:

> Production-style ML governance case study for credit-risk incident remediation, drift/fairness controls, safe model release, and gated AWS deployment.

Shorter alternative:

> Production-style ML governance: incident remediation, drift/fairness controls, safe release, and gated AWS deployment.

## Recommended topics

Use a focused set rather than every library in the repo:

```text
machine-learning
mlops
ml-governance
model-governance
credit-risk
data-quality
data-drift
fairness
explainable-ai
shap
fastapi
docker
terraform
aws
ecs
github-actions
```

Optional swaps if GitHub's topic limit becomes an issue:

```text
great-expectations
fairlearn
xgboost
model-monitoring
```

## Homepage toggles

Recommended current settings:

| Setting | Recommendation | Reason |
|---|---|---|
| Releases | **ON** | v0.8.0 is the current verified code milestone; publish the tag after main verification |
| Deployments | **OFF for now** | do not imply a live cloud deployment without runtime evidence |
| Packages | **OFF for now** | no package/container registry publication is currently part of the public project story |

Turn Deployments on after a real staging environment exists and GitHub records deployment activity. Turn Packages on after you intentionally publish a reusable package/container artifact.

## Private vs public

If the repository remains private, give recruiters/senior engineers explicit access before sending the link. If you later make it public, first run a final secret/history audit and remove internal or redundant historical material that does not support the case-study story.
