Resolves #ISSUE(s).
<!--- "Resolves #ISSUE" will automatically close #ISSUE when the PR is merged. However, if this PR won't 100% address the issue, you can use one of these patterns instead to simply link to the issue and not auto-close it:

Partially addresses:
- ISSUE(s)

Addresses sub-task (n) in:
- ISSUE(s)
-->


## Pre-merge checklist

<!--- Docs: A common case for documentation is the addition of new `make` goals. Descriptions should be documented for new goals both in the (i) `help` command at the bottom of the `mondo-ingest.Makefile` and (ii) `docs/developer/workflows.md`. -->

### PR Overview
<!--- Short paragraph or short bulleted list describing changes in this PR -->

This PR:
- One
- Two
- Three

=====================
### Documentation
- Was the documentation added/updated under `docs/`?
   - [ ] Yes
   - [ ] No, updates to the docs were not necessary after careful consideration

### QC
- Was the full pipeline run before submitting this PR using `sh run.sh make build-mondo-ingest` on this branch (after `docker pull obolibrary/odkfull:dev`), and no errors occurred?
   - [ ] Yes
   - [ ] No, there are no functional (code-related) changes to the pipeline in the PR, so no re-run is necessary
   
### New Packages
- Were any new *Python packages* added?
   - [ ] Yes, [requirements.txt.full](https://github.com/INCATools/ontology-development-kit/blob/master/requirements.txt.full) was updated and an [ODK issue](https://github.com/INCATools/ontology-development-kit/issues/new) submitted
   - [ ] No
</br>

- Were any other *non-Python packages* added?
   - [ ] Yes, [Dockerfile](https://github.com/INCATools/ontology-development-kit/blob/master/Dockerfile) updated and an [ODK issue](https://github.com/INCATools/ontology-development-kit/issues/new) submitted
   - [ ] No

### PR Review and Conversations Resolved
- Has the PR been sufficiently reviewed by at least one team member of the Mondo Technical team and all threads resolved?
   - [ ] Yes
