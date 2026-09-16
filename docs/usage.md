# Workflow reference

1. Run `project-setup --project NAME` in the desired parent directory.
2. Add your application to `script/` or a package directory, data to `data/`,
   documentation to `docs/`, and tests to `testdirectory/`.
3. Update `release-files.txt` to include the install mechanism and runtime assets.
4. Run tests, then `script/project-update --version --release --message "Description"`.
5. Configure origin with `git remote add origin URL` if needed.
6. Run `script/project-update --git-push` to commit nonignored changes and publish.
7. Run `script/project-update --git-push 0.0.2` to publish that version's tag.

For a remote update, use `script/project-update --git-pull` with a clean tree.
A version pull fetches a tag without changing your checkout.

## Recovering from errors

- Existing project: choose a different name; the tool never merges or overwrites.
- Missing Git identity: configure `git config user.name` and `git config user.email`
  inside the new repository, then run the updater's push when origin is ready.
- Push fails: inspect origin/authentication, then retry only `--git-push`.
- Release already exists: keep it and choose a new version.
- Pull diverges: reconcile history manually; this tool will not discard changes.
- Incomplete scaffold after an I/O or Git error: files are retained for inspection;
  do not expect rerunning setup to overwrite them.

## Portability

Python 3.9+ and Git 2.28+ must be installed on macOS or Linux. No runtime pip
dependencies, shell-specific scripts, OS package managers, or GNU-only utilities
are required. The stdlib installer needs no network. The optional pip packaging
path uses setuptools as its build backend.
