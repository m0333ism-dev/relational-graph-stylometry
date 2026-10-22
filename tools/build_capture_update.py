"""Publish saved graph comparisons; never fit, resample, or read document text.

The comparison workbench and the exact feature CSV are private build inputs.
Only displayed points, aggregate results, graph images and external citations
are added to the public portal. Existing scientific payloads stay byte exact.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import shutil
import struct
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SITE = PROJECT / 'site'
EXPECTED = '5068c83649471c0ac2daff34841c5ab6622eb13c49547875b750a95c745a2ff4'
GENRES = ['email', 'review', 'legal', 'abstracts', 'articles', 'papers']
LABELS = ['human', 'ai']
BEGIN = '<!-- BEGIN SAVED GRAPH COMPARISONS -->'
END = '<!-- END SAVED GRAPH COMPARISONS -->'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, allow_nan=False,
                                    separators=(',', ':')) + '\n', encoding='utf-8')


def graph_point(row, response, family, view):
    """The frozen display transformations, not a new statistical analysis."""
    if family == 'R04':
        mean = float(row['avg_sent_length'])
        sigma = mean * float(row['sent_len_cv'])
        if float(row['sent_len_cv']) <= 1e-10:
            return None
        return [math.log1p(response[0] / sigma),
                math.log1p((response[1] - mean) / sigma),
                math.asinh((float(row['sent_len_median']) - mean) / sigma)]
    if view == 'anchors':
        return [math.log1p(math.hypot(float(row['adjective_ratio']), float(row['dep_amod_ratio'])) / .05),
                math.log1p(math.hypot(float(row['adverb_ratio']), float(row['dep_advmod_ratio'])) / .05),
                response[0]]
    return [response[1], response[2], response[0]]


def original_response(row, family):
    fields = (['sent_len_iqr', 'sent_len_max'] if family == 'R04' else
              ['avg_dependency_tree_depth', 'tree_depth_median', 'tree_depth_max'])
    return [float(row[name]) for name in fields]


def valid(row, family):
    if family == 'R04':
        return (float(row['avg_sent_length']) > 0 and float(row['sent_len_median']) > 0
                and float(row['sent_len_cv']) > 1e-10 and float(row['sent_len_iqr']) >= 0
                and float(row['sent_len_max']) > 0)
    return (math.hypot(float(row['adjective_ratio']), float(row['dep_amod_ratio'])) > 0
            and math.hypot(float(row['adverb_ratio']), float(row['dep_advmod_ratio'])) > 0)


def representatives(records, features, genre, label):
    seen, rows = set(), []
    for index, row in enumerate(records):
        if row['genre'].strip() != genre or row['label'].strip().lower() != label:
            continue
        values = [float(row[name]) for name in features]
        digest = hashlib.sha256(struct.pack('<132d', *[0. if v == 0 else v for v in values])).digest()
        if digest not in seen:
            rows.append(index)
            seen.add(digest)
    return rows


def image_asset(path, expected=None):
    digest = sha(path)
    if expected:
        assert digest == expected, path.name
    relative = 'assets/evidence/' + digest + '.png'
    shutil.copyfile(path, SITE / relative)
    return relative


def table_markup(table):
    escape = lambda value: html.escape(str(value))
    head = ''.join('<th scope="col">' + escape(v) + '</th>' for v in table['headers'])
    body = ''.join('<tr>' + ''.join('<td>' + escape(v) + '</td>' for v in row) + '</tr>'
                   for row in table['rows'])
    return ('<div class="capture-table-scroll" tabindex="0"><table><caption>' +
            escape(table['caption']) + '</caption><thead><tr>' + head +
            '</tr></thead><tbody>' + body + '</tbody></table></div>')


def main(study, csv_path):
    study, csv_path = study.resolve(), csv_path.resolve()
    assert sha(csv_path) == EXPECTED, 'The pinned CSV has changed.'
    manifest = read(SITE / 'hosting-manifest.json')
    assert manifest['source_csv_sha256'] == EXPECTED
    assert manifest['public_scope'] == 'INTERACTIVE_PORTAL_ONLY_NO_RESEARCH_DOWNLOADS'
    before = {name: sha(SITE / 'data' / name) for name in
              ['original-tuples.json', 'pattern-register.json', 'branch-study.json',
               'microscope-context.json', 'expanded-context.json']}
    names = ['AIJ_Benchmark_Result.json', 'AIJ_Graph_Space_Result.json',
             'AIJ_Graph_Membership.json', 'AIJ_Scientific_Graph_Review.json',
             'AIJ_Study_Summary.json', 'AIJ_References.json', 'AIJ_Article_Tables.json',
             'AIJ_Benchmark_Protocol.json', 'AIJ_Graph_Coordinate_Amendment.json']
    sources = {name: read(study / name) for name in names}
    benchmark, graph = sources[names[0]], sources[names[1]]
    assert benchmark['source_sha256'] == EXPECTED
    assert benchmark['protocol_sha256'] == sha(study / 'AIJ_Benchmark_Protocol.json')
    assert graph['new_model_fits'] == 0
    with csv_path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        features = [name for name in reader.fieldnames if name not in ['file', 'genre', 'label']]
        records = list(reader)
    assert len(features) == 132 and len(records) == 5046
    assert all(math.isfinite(float(row[name])) for row in records for name in features)
    public = {'schema': 'exp03.saved_graph_comparisons.v1', 'date': '2026-10-22',
              'source_csv_sha256': EXPECTED, 'row_index_base': 0,
              'document_ids': [row['file'] for row in records],
              'display_seed': sources[names[2]]['defined_display_seed'],
              'summary': sources[names[4]], 'cells': {}, 'sheets': {}}
    images = set()
    for family in ['R04', 'R06']:
        public['cells'][family] = {}
        for genre in GENRES:
            for label in LABELS:
                key = genre + '__' + label
                raw, mapped = benchmark['families'][family][key], graph['families'][family][key]
                cell = {k: raw[k] for k in ['genre', 'label', 'query_count', 'scored_queries', 'models']}
                cell['graph_models'] = mapped['models']
                cell['graph_queries'] = len(mapped['query_rows'])
                cell['unsupported_queries'] = len(raw['query_rows_without_compatible_atoms'])
                if 'product_control' in raw:
                    cell['product_control'] = raw['product_control']
                public['cells'][family][key] = cell
    for name, saved in sources[names[2]]['sheets'].items():
        family, genre, view = saved['family'], saved['genre'], saved['view']
        asset = image_asset(study / 'figures' / name, saved['sha256'])
        images.add(asset)
        sheet = {k: saved[k] for k in ['family', 'genre', 'view', 'axis_limits', 'color_limits']}
        review = sources[names[3]]['sheets'][name]
        assert review['sha256'] == saved['sha256']
        sheet.update(asset=asset, observation=review['observation'], classes={})
        for label, member in saved['members'].items():
            context_rows = [q for q in representatives(records, features, genre, label) if valid(records[q], family)]
            context = {'rows': context_rows, 'points': [graph_point(records[q], original_response(records[q], family), family, view)
                                                       for q in context_rows]}
            responses = {}
            query_rows = member['original_query_rows']
            for method, response in member['responses'].items():
                assert len(query_rows) == len(response['drawn_values'])
                displayed = set(response['displayed_queries'])
                indexes = [i for i, q in enumerate(query_rows) if q in displayed]
                responses[method] = {
                    'rows': [query_rows[i] for i in indexes],
                    'points': [graph_point(records[query_rows[i]], response['drawn_values'][i], family, view) for i in indexes],
                    'response_source_rows': ([response['response_source_rows'][i] for i in indexes]
                                             if response['response_source_rows'] is not None else None)}
                assert all(point is not None and all(math.isfinite(v) for v in point)
                           for point in responses[method]['points'])
            sheet['classes'][label] = {'context': context, 'responses': responses,
                                       'query_count': len(query_rows), 'unavailable_rows': member['unavailable_rows']}
        public['sheets'][name] = sheet
    assert len(public['sheets']) == 18
    references = [r for r in sources[names[5]]['records'] if r['url'].startswith('https://')]
    assert len(references) == 47
    public['external_references'] = references
    payload_path = SITE / 'data/capture-study.json'
    write(payload_path, public)

    fragment = (PROJECT / 'tools/capture-study.html').read_text(encoding='utf-8')
    tables = sources[names[6]]['tables']
    fragment = fragment.replace('{{EARLIER_WIDTH_TABLE}}', table_markup(next(t for t in tables if t['number'] == 7)))
    fragment = fragment.replace('{{SENSITIVITY_TABLE}}', table_markup(next(t for t in tables if t['number'] == 6)))
    citations = []
    for reference in references:
        citations.append('<li><a href="' + html.escape(reference['url'], quote=True) + '">' +
                         html.escape(reference['citation']) + '</a><p>' +
                         html.escape(reference['use']) + '</p><small>Access record: ' +
                         html.escape(reference.get('verification', 'Metadata inspected')) + '</small></li>')
    fragment = fragment.replace('{{REFERENCES}}', '\n'.join(citations))
    figures = []
    captions = {
        'AIJ_Original_Graph_Targets': 'Original collective configurations and the response geometry to capture.',
        'AIJ_Energy_Coordinate_Comparison': 'The same fitted responses give different comparisons in log-response and graph coordinates.',
        'AIJ_Envelope_Reconstruction': 'Original envelope shapes and the partial reconstructions.',
        'AIJ_Branch_Support_Floors': 'Unseen branches impose support floors; remaining occupancy error is also visible.',
        'AIJ_Product_Response_Control': 'Preserving marginal responses while removing their joint dependence gives mixed results.'}
    for name, caption in captions.items():
        asset = image_asset(study / 'publication_figures' / (name + '.png'))
        images.add(asset)
        figures.append('<figure><img loading="lazy" decoding="async" src="' + asset + '" alt="' +
                       html.escape(caption, quote=True) + '"><figcaption>' + caption + '</figcaption></figure>')
    fragment = fragment.replace('{{SUMMARY_FIGURES}}', '\n'.join(figures))
    assert '{{' not in fragment
    page = (SITE / 'index.html').read_text(encoding='utf-8')
    if BEGIN in page:
        page = re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), '', page, flags=re.S)
    page = page.replace('<section class="record" id="branch-study">', BEGIN + fragment + END +
                        '<section class="record" id="branch-study">', 1)
    if 'href="#capture-study"' not in page.split('</header>', 1)[0]:
        page = page.replace('<a class="header-link" href="#branch-study">Completed research</a>',
                            '<a class="header-link" href="#capture-study">Latest graph comparisons</a> '
                            '<a class="header-link" href="#branch-study">Earlier discovery round</a>', 1)
    css = '<link rel="stylesheet" href="assets/capture-study.css">'
    if css not in page:
        page = page.replace('</head>', css + '</head>', 1)
    page = page.replace('The paper contains 35 references.', 'The latest comparison and its external references are recorded above.')
    page = page.replace('Raw-source identity remains unresolved from the earlier source audit.', '')
    page = page.replace('The manuscript and downloadable research reports remain available through their links.',
                        'Static graph sheets and on-page findings remain readable below.')
    # Update one nomination's status, while preserving its earlier observations.
    def update_m09(match):
        return match.group(0).replace('<strong>Formula:</strong> not designed.',
            '<strong>Formula:</strong> later developed into the five-feature R04 envelope coordinates; '
            '<a href="#capture-study">inspect the partial conditional reconstructions</a>.')
    page = re.sub(r'<article\b[^>]*>.*?</article>',
                  lambda m: update_m09(m) if re.search(r'\bM09\b', m.group(0)) else m.group(0), page, flags=re.S)
    page = page.replace('the completed study above gives the final results.',
                        'the earlier discovery results and the latest saved comparisons above record separate stages.')
    def update_m11(match):
        text = match.group(0)
        note = '<p>The later eight-member R06 study examines the joint three-depth response; '
        if note not in text:
            text = text.replace('</article>', note + '<a href="#capture-study">see the latest comparison and its counterexamples</a>.</p></article>')
        return text
    page = re.sub(r'<article\b[^>]*>.*?</article>',
                  lambda m: update_m11(m) if re.search(r'\bM11\b', m.group(0)) else m.group(0), page, flags=re.S)
    (SITE / 'index.html').write_text(page, encoding='utf-8')
    atlas_path = SITE / 'assets/js/atlas.js'
    atlas = atlas_path.read_text(encoding='utf-8').replace(
        'Counts were recovered from stored feature redundancies, not independently verified from raw text.',
        'Counts are reconstructed from redundancies in the fixed CSV.')
    atlas_path.write_text(atlas, encoding='utf-8')
    shutil.copyfile(PROJECT / 'tools/bootstrap.js', SITE / 'assets/js/bootstrap.js')
    for name, digest in before.items():
        assert sha(SITE / 'data' / name) == digest
    assets = ['data/capture-study.json', 'assets/capture-study.css', 'assets/js/capture-study.js'] + sorted(images)
    manifest['comparison_update'] = {
        'date': '2026-10-22', 'scope': 'Saved graph displays and on-page results only',
        'adaptive_graph_coordinate_followup': True, 'research_refitted_for_hosting': False,
        'source_csv_sha256': EXPECTED, 'external_references': 47, 'scientific_sheets': 18,
        'summary_figures': 5, 'display_seed': public['display_seed'],
        'source_record_sha256': {name: sha(study / name) for name in names},
        'asset_sha256': {name: sha(SITE / name) for name in assets}}
    (SITE / 'hosting-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False,
                                                        indent=2, allow_nan=False) + '\n', encoding='utf-8')
    report = {'status': 'BUILT', 'public_downloads': 0, 'legacy_payloads_unchanged': 5,
              'sheets': 18, 'summary_figures': 5, 'external_references': 47,
              'payload_bytes': payload_path.stat().st_size, 'research_refitted': False}
    (PROJECT / 'verification').mkdir(exist_ok=True)
    write(PROJECT / 'verification/Capture_Build.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--study-root', required=True, type=Path)
    parser.add_argument('--csv', required=True, type=Path)
    args = parser.parse_args()
    main(args.study_root, args.csv)
