# Licensing design discussion — not a license grant

No project license is changed by this document or by --refresh. These are design
notes for the requested restrictions, requiring the actual rights holder's approval
and legal review before being turned into binding terms.

Requested policy:
1. Allow use, including private modification, with paper/repository citation and
   author/team acknowledgment when research results are published.
2. Require prior written permission to distribute modified software; authorized
   distributions must be identified as approved versions of the original project.
3. Permit incorporating the unmodified component into another project with notices
   and citation, without implying that the new project's independent code belongs
   to the original author.

This would be a custom source-available license, not an OSI-approved open-source
license: open-source definitions require modification and redistribution rights.
Apache/MIT/GPL do not implement a permission requirement for every modified release.
Do not append these restrictions to Apache and still call the result Apache-2.0.

Important unresolved definitions:
- Separate publication of research RESULTS from redistribution/publication of CODE.
  Decide whether research using privately modified code needs permission (not just
  citation), and whether preprints, theses, talks and commercial reports are covered.
- Specify what can be distributed unchanged: source, binaries, containers or a
  dependency; whether compiling/packaging is an allowed technical transformation.
- Define whether wrappers/plugins are independent integration or modification.
- Specify the rights holder, permission contact, exact citation/DOI fallback,
  permission response process, approved-version naming and contributor credit.
- Keep source-code contributor credit separate from paper coauthorship. Scientific
  authorship depends on substantive contributions and journal policies, not simply
  using a tool. A Git branch does not confer coauthorship or grant repository access.
- Public GitHub repositories grant on-platform viewing/forking rights under GitHub
  terms. A blanket ban on all forks cannot be promised while hosting publicly there.
- Check third-party code and contributor rights. A new restriction cannot simply
  withdraw permissions already granted for earlier open-source releases.

Possible implementation AFTER decisions/legal review:
- LICENSE: counsel-reviewed custom terms with explicit grants and conditions.
- CITATION.cff + CITATION.md: canonical authors/team, software version, paper DOI
  or versioned software DOI/repository fallback; plain citation examples.
- NOTICE / AUTHORS: accurate copyright and contributor attribution.
- CONTRIBUTING.md: proposed changes via pull requests; permission and approval
  process for modified distribution; no automatic scientific coauthorship.
- Include approved license/citation files in package metadata and release allowlists.
  Do not silently apply the same license to all generated projects or dependencies.

References:
- https://opensource.org/osd (free redistribution and derived works)
- https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
  (public-repository viewing/forking permissions)
- https://aas.org/policies/ethics (publication and authorship)
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files
