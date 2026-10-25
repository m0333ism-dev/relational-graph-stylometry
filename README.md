# Relational Graph Stylometry

This portal presents the identification and mathematical characterization of
recurring feature-interaction patterns in Human and AI writing across genres.
The empirical findings are the primary contribution; formulas and the analysis
system support their description and evaluation. Recurrence concerns specified
relationships, with genre exceptions, rather than identical feature levels or
universal invariance.

The original-corpus explorer uses the fixed 5,046-row, 132-feature CSV and graphs
derived from it. That study remains exploratory. The separate [RAID explorer](https://m0333ism-dev.github.io/relational-graph-stylometry/raid/)
shows discovery, structural development and frozen evaluation within one recorded
historical ChatGPT configuration across eight genres. Its four primary average
components were evaluated on 1,195 new source pairs after exact-overlap exclusions.
All eight genres had already appeared in development.

The portal includes the original feature explorer, collective configuration
views, reconstructed responses, preserved-block structural controls and
on-page results. The browser receives the numeric payloads required to draw
and inspect these interactive graphs.

The 25 October 2026 update adds the RAID explorer, a complete all-genre tuple
atlas, frozen component results and secondary nonlinear comparators. Its 6,388
numeric rows and 132 measurements are split into lazily loaded evidence stages.
The final results retain following reversals, uncertain individual genre effects,
limited length-comparable support and incomplete geometric reconstruction.
Nonlinear pair scores discriminate better than the three-member score, while
the joint formula improves the stated mean-response criterion. These are distinct
empirical outcomes. No estimator, formula, membership or result was refitted for
hosting.

The earlier 22 October update added saved comparisons for the five-feature
sentence envelope (R04) and eight-feature modifier/depth configuration (R06)
in all six genres, 18 inspected comparison sheets, five overview figures and
47 external references. Its results keep log-response energy, graph-coordinate
energy and branch occupancy separate. Reconstructions remain partial, and
papers remain a small descriptive cohort. The graph-coordinate check was an
adaptive follow-up with fitted responses frozen.

## Research records

The displayed original and RAID feature values and graph images retain the
identities checked in the completed studies. Hosting changes do not refit formulas
or recalculate research findings. The public hosting manifest records numerical
payload and image identities. Browsers receive numerical measurements and record
identifiers needed to draw the interactive graphs. The manuscripts, experiment
notebooks, CSV feature exports, parameter archives and research source archive
are excluded from this public repository and website.

New notes made in this hosted portal are private to the visitor's browser.
They can be exported as JSON, with the exact feature selection, view, source
hash and row identifiers. Hosted notes do not modify the local experiment
notebook.

## Hosting

GitHub Pages serves `site/` through `.github/workflows/pages.yml`. All internal
URLs are relative so project-site paths work. Graph images and JavaScript are
separate, cacheable assets. Scientific payloads are loaded before the explorer
starts. The portal makes no calls to the former localhost Python API.

For a local preview:

```text
python -m http.server 8875 --directory site
```

Open `http://127.0.0.1:8875/`.

## Updating from the research output

```text
python tools/build_public_portal.py --research-root "PATH_TO_COMPLETED_RESEARCH" --owner YOUR_GITHUB_LOGIN
python tools/verify_public_portal.py
```

To add the later saved comparisons to an existing portal build:

```text
python tools/build_capture_update.py --study-root "PATH_TO_SAVED_COMPARISON_STUDY" --csv "PATH_TO_PINNED_FEATURE_CSV"
python tools/verify_capture_update.py --study-root "PATH_TO_SAVED_COMPARISON_STUDY" --csv "PATH_TO_PINNED_FEATURE_CSV"
python tools/verify_public_portal.py
```

For a complete rebuild, `build_public_portal.py` also accepts
`--comparison-study` and `--csv`. The comparison builder reads saved numerical
results, membership records and graph assets. It does not execute the research
scripts, refit a model, generate new response draws or read document text.

The builder copies only portal assets and displayed scientific payloads.
It does not inspect source text documents or rerun statistical analysis.
Preserved local attempts, machine-specific runtime files and credentials are
not part of the site directory.

For the RAID update after building the original explorer, run:

```text
python tools/build_raid_update.py --explorer-root PATH_TO_VERIFIED_NUMERIC_EXPLORER --atlas-root PATH_TO_ATLAS_IMAGES --atlas-index PATH_TO_ATLAS_INDEX_JSON --frozen-root PATH_TO_FINAL_NUMERIC_EVIDENCE --summary-figure PATH_TO_FROZEN_COMPONENT_PNG
python tools/verify_raid_update.py --explorer-root PATH_TO_VERIFIED_NUMERIC_EXPLORER --frozen-root PATH_TO_FINAL_NUMERIC_EVIDENCE
```

The builder copies recorded measurements, ranks, scales and results. It removes
private research links, preserves the different data roles and separates cohort
payloads for browser loading. The published all-genre atlas uses the unchanged
final graph images. New source groups within already-observed genres are distinct
from evaluation on an independently unseen genre. The same formulas are not
required to transfer between the original corpus and the RAID study.

The Plotly distribution retains its original MIT licence notice. The research
materials retain the authorship and terms stated in those materials.

