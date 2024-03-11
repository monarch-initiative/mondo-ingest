Resolves #ISSUE(s).
<!--- "Resolves #ISSUE" will automatically close #ISSUE when the PR is merged. However, if this PR won't 100% address 
the issue and you don't want it to auto-close, you can write one of the following instead of "Resolves"
- Partially addresses
- Addresses sub-task (n) in
-->

## Overview
<!--- A few sentences describing changes / what problem is solved. Should describe the expected result of the changes. 
If applicable, point out the main change that solved the problem, e.g. fixed bug in method xyz. -->
This PR:
- One
- Two
- Three

## Pre-merge checklist
<!--- Docs: A common case for documentation is the addition of new `make` goals. Descriptions should be documented for 
new goals both in the (i) `help` command at the bottom of the `mondo-ingest.Makefile` and (ii) 
`docs/developer/workflows.md`. -->

### Documentation
Was the documentation added/updated under `docs/`?
- [ ] Yes
- [ ] No, updates to the docs were not necessary after careful consideration

### QC
Was the full pipeline run before submitting this PR using `sh run.sh make build-mondo-ingest` on this branch (after 
`docker pull obolibrary/odkfull:dev`), and no errors occurred?
- [ ] Yes
- [ ] No, there are no functional (code-related) changes to the pipeline in the PR, so no re-run is necessary
   
### New Packages
Were any new *Python packages* added?
- [ ] Yes, [requirements.txt.full](https://github.com/INCATools/ontology-development-kit/blob/master/requirements.txt.full) was updated and an [ODK issue](https://github.com/INCATools/ontology-development-kit/issues/new) submitted
- [ ] No

Were any other *non-Python packages* added?
- [ ] Yes, [Dockerfile](https://github.com/INCATools/ontology-development-kit/blob/master/Dockerfile) updated and an [ODK issue](https://github.com/INCATools/ontology-development-kit/issues/new) submitted
- [ ] No

### PR Review and Conversations Resolved
Has the PR been sufficiently reviewed by at least 1 team member of the Mondo Technical team and all threads resolved?
- [ ] Yes
