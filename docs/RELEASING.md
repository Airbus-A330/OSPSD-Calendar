# Versions and Releases

## Version numbers

The package version lives in one place, `version` in `pyproject.toml`.
`calendar_contract.__version__` reads it from the installed package metadata.

Versions follow [Semantic Versioning](https://semver.org/). Each release is an
annotated git tag named `v` plus the version, such as `v0.1.0`.

While the version is below 1.0.0:

- A release that changes contract semantics bumps the minor version
  (`0.1.0` to `0.2.0`). That covers everything listed under "Contract Changes"
  in `AGENTS.md`, and removing or renaming a public name.
- Any other release bumps the patch version (`0.1.0` to `0.1.1`): fixes,
  documentation, tests, and additions that leave agreed behavior unchanged.
- A version the teams want to try before relying on it gets a release
  candidate suffix, such as `0.2.0rc1` with tag `v0.2.0rc1`, and is published
  as a GitHub pre-release.

A tag is never moved or deleted. A defective release is fixed by releasing a
new version.

## Release steps

1. **Open a release PR.** Set the new `version` in `pyproject.toml`, then run
   `uv lock`: `uv.lock` records the package's own version, so
   `uv sync --locked` fails until it is updated. List the user-visible changes
   in the PR description, contract changes first.
2. **Get it reviewed.** The release PR needs one approval from each of Teams
   2, 5 and 7, none of them from its author, and CI must pass. Every team's
   service will depend on the release, so every team signs off on it.
3. **Merge it**, and wait for CI to pass on the merge commit on `master`.
4. **Tag that commit and push the tag:**

   ```bash
   git switch master
   git pull --ff-only
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin v0.1.0
   ```

5. **Publish a GitHub Release** from the tag, with the change list from the
   release PR as its notes. Add `--prerelease` for a release candidate:

   ```bash
   gh release create v0.1.0 --verify-tag --title v0.1.0 --notes-file notes.md
   ```

6. **Check that the tag installs**, from a fresh directory outside the
   repository. The last command prints the new version:

   ```bash
   cd "$(mktemp -d)"
   uv init --bare --python 3.12
   uv add "git+https://github.com/Airbus-A330/OSPSD-Calendar" --tag v0.1.0
   uv run python -c "import calendar_contract; print(calendar_contract.__version__)"
   ```

7. **Announce the release** on the shared email thread and in `#calendar`,
   with the install command from the README.
