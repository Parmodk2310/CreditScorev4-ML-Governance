# Apply this Phase 1 package to your branch

From your local repository root while on `phase/1-incident-baseline`:

```bash
# Extract the ZIP to a temporary directory first, then copy its contents over the repo.
cp -a /path/to/creditscorev4-phase1/. .

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make phase1-verify

git status
git add .
git commit -m "feat: implement phase 1 incident reproduction baseline"
git push -u origin phase/1-incident-baseline
```

Review `git diff --cached` before committing, especially if your repository already contains files from the older scaffold.
