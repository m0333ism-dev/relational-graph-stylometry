# Relational Graph Stylometry

This portal accompanies graph-led discovery of recurring
stylometric feature configurations in Human and AI writing across genres.
Its empirical input is the fixed 5,046-row, 132-feature CSV and graphs derived
from that table. The study is exploratory; its genre exceptions and incomplete
formula captures remain visible.

The portal includes the original feature explorer, collective configuration
views, reconstructed responses, preserved-block structural controls and
on-page results. The browser receives the numeric payloads required to draw
and inspect these interactive graphs.

The 22 October 2026 update adds saved comparisons for the five-feature
sentence envelope (R04) and eight-feature modifier/depth configuration (R06)
in all six genres, 18 inspected comparison sheets, five overview figures and
47 external references. Its results keep log-response energy, graph-coordinate
energy and branch occupancy separate. Reconstructions remain partial, and
papers remain a small descriptive cohort. The graph-coordinate check was an
adaptive follow-up with fitted responses frozen.

## Research records

The displayed original feature values and graph images retain the identities
checked in the local completed study. Hosting changes do not refit formulas or
recalculate research findings. The public hosting manifest records these
identities. The manuscript, experiment notebook, feature exports, parameter
archives and research source archive are excluded from this public repository
and website.

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

The Plotly distribution retains its original MIT licence notice. The research
materials retain the authorship and terms stated in those materials.

