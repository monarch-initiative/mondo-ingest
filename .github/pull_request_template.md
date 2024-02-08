Resolves #ISSUE(s).
<!--- "Resolves #ISSUE" will automatically close #ISSUE when the PR is merged. However, if this PR won't 100% address the issue, you can use one of these patterns instead to simply link to the issue and not auto-close it:

Partially addresses:
- ISSUE(s)

Addresses sub-task (n) in:
- ISSUE(s)
-->


## Pre-merge checklist

<!--- Docs: A common case for documentation is the addition of new `make` goals. Descriptions should be documented for new goals both in the (i) `help` command at the bottom of the `mondo-ingest.Makefile` and (ii) `docs/developer/workflows.md`. -->

- [ ] Docs
   - `docs/` have been added/updated **OR**
   - No updates to the docs necessary after careful consideration.

- [ ] QC
   - `sh run.sh make build-mondo-ingest` has been run on this branch (after `docker pull obolibrary/odkfull:dev), and no errors occurred **OR**
   -  No functional (code-related) changes to the pipeline are suggested, so no re-run is necessary.

- [ ] Account for any new packages
  - Open an [ODK issue](https://github.com/INCATools/ontology-development-kit/issues/new) to request addition. Can also open a PR. Python package changes should occur in [[requirements.txt.full](https://github.com/INCATools/ontology-development-kit/blob/master/requirements.txt.full)](https://github.com/INCATools/ontology-development-kit/blob/master/requirements.txt.full), and non-Python packages in [Dockerfile](https://github.com/INCATools/ontology-development-kit/blob/master/Dockerfile).

- [ ] Reviewed
   - Has been sufficiently reviewed by at least one review from a different team member of the Mondo Technical team.

## Overview

This PR:

- One
- Two
- Three
