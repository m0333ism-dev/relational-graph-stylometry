"""Reconcile public graph points and results with the frozen private records."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SITE = PROJECT / 'site'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def near(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12), (x, y)


def check(study, csv_path):
    manifest = read(SITE / 'hosting-manifest.json')
    update = manifest['comparison_update']
    assert sha(csv_path) == manifest['source_csv_sha256'] == update['source_csv_sha256']
    for name, digest in update['asset_sha256'].items():
        assert sha(SITE / name) == digest, name
    for name, digest in update['source_record_sha256'].items():
        assert sha(study / name) == digest, name
    assert not update['research_refitted_for_hosting']
    public = read(SITE / 'data/capture-study.json')
    raw = read(study / 'AIJ_Benchmark_Result.json')
    graph = read(study / 'AIJ_Graph_Space_Result.json')
    saved = read(study / 'AIJ_Graph_Membership.json')
    with csv_path.open(encoding='utf-8-sig', newline='') as stream:
        records = list(csv.DictReader(stream))
    assert public['document_ids'] == [row['file'] for row in records]
    assert public['summary'] == read(study / 'AIJ_Study_Summary.json')
    assert len(public['external_references']) == 47
    assert all(r['url'].startswith('https://') for r in public['external_references'])
    assert len(public['sheets']) == 18
    cells = points = 0
    for family in ['R04', 'R06']:
        assert len(public['cells'][family]) == 12
        for key, cell in public['cells'][family].items():
            original = raw['families'][family][key]
            assert cell['models'] == original['models']
            assert cell['graph_models'] == graph['families'][family][key]['models']
            assert cell['scored_queries'] == original['scored_queries']
            assert cell['graph_queries'] == len(graph['families'][family][key]['query_rows'])
            if family == 'R06':
                assert cell['product_control'] == original['product_control']
            cells += 1
    for name, sheet in public['sheets'].items():
        original = saved['sheets'][name]
        assert sheet['axis_limits'] == original['axis_limits']
        assert sheet['color_limits'] == original['color_limits']
        assert sha(SITE / sheet['asset']) == original['sha256']
        for label, member in sheet['classes'].items():
            source = original['members'][label]
            for method, response in member['responses'].items():
                frozen = source['responses'][method]
                assert response['rows'] == frozen['displayed_queries']
                lookup = {row: i for i, row in enumerate(source['original_query_rows'])}
                for row, point in zip(response['rows'], response['points']):
                    index = lookup[row]
                    values, context = frozen['drawn_values'][index], records[row]
                    if sheet['family'] == 'R04':
                        mean = float(context['avg_sent_length'])
                        sigma = mean * float(context['sent_len_cv'])
                        expected = [math.log(1 + values[0] / sigma),
                                    math.log(1 + (values[1] - mean) / sigma),
                                    math.asinh((float(context['sent_len_median']) - mean) / sigma)]
                    elif sheet['view'] == 'depth':
                        expected = [values[1], values[2], values[0]]
                    else:
                        radii = [math.sqrt(float(context[a]) ** 2 + float(context[b]) ** 2)
                                 for a, b in [('adjective_ratio', 'dep_amod_ratio'), ('adverb_ratio', 'dep_advmod_ratio')]]
                        expected = [math.log(1 + radii[0] / .05), math.log(1 + radii[1] / .05), values[0]]
                    near(point, expected)
                    points += 1
                expected_rows = frozen['response_source_rows']
                assert response['response_source_rows'] == ([expected_rows[lookup[row]] for row in response['rows']]
                                                            if expected_rows is not None else None)
                if sheet['family'] == 'R06' and sheet['view'] == 'anchors':
                    observed = member['responses']['original']['points']
                    for point, query in zip(response['points'], observed):
                        near(point[:2], query[:2])
    index = (SITE / 'index.html').read_text(encoding='utf-8')
    assert index.count('id="capture-study"') == 1
    assert '35 references' not in index
    assert 'Raw-source identity' not in index
    assert 'manuscript and research downloads are excluded' in index
    assert all(not (SITE / name).exists() for name in ['downloads', 'reports'])
    record = {'status': 'PASS', 'cells_reconciled': cells, 'sheets_reconciled': 18,
              'saved_response_points_reconciled': points, 'common_axes_preserved': True,
              'external_references': 47, 'research_refitted': False,
              'manuscript_and_research_downloads': 0}
    (PROJECT / 'verification/Capture_Verification.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--study-root', required=True, type=Path)
    parser.add_argument('--csv', required=True, type=Path)
    args = parser.parse_args()
    check(args.study_root, args.csv)
