"""Phase 0 reproducible archive integrity, clean-source and fixture provenance checks."""
import argparse, csv, hashlib, json, pathlib, re, shutil, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
def sha(data): return hashlib.sha256(data).hexdigest()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outer', type=pathlib.Path, default=ROOT/'inputs/Praxis_Caller_Astra_Pack.zip')
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    evidence = ROOT / 'evidence'
    evidence.mkdir(exist_ok=True)
    rows, sources, fixtures = [], [], []
    for label, archive, target in [('pack', args.outer, ROOT), ('sdk', ROOT/'android-sdk.zip', ROOT/'vendor')]:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None, f'CRC failed: {archive}'
            for item in z.infolist():
                if item.is_dir(): continue
                path = pathlib.PurePosixPath(item.filename)
                assert not path.is_absolute() and '..' not in path.parts
                data = z.read(item)
                category = 'control'
                if label == 'sdk':
                    category = 'generated/cache' if any(p in ('build','.gradle','.kotlin') for p in path.parts) else 'source/config/test'
                    assert (target / item.filename).read_bytes() == data, f'Vendor changed: {item.filename}'
                    if category == 'source/config/test':
                        rel = pathlib.Path(*path.parts[1:])
                        dest = ROOT/'sdk'/rel
                        if args.prepare:
                            dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
                        assert dest.read_bytes() == data, f'Source changed: {rel}'
                        sources.append(str(rel).replace('\\','/'))
                    if '/processDebugUnitTestJavaRes/out/' in item.filename and (path.suffix == '.json' or path.name == 'README.md'):
                        dest = ROOT/'contracts/examples'/path.name
                        if args.prepare:
                            dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
                        assert dest.read_bytes() == data, f'Fixture changed: {dest.name}'
                        if dest.suffix == '.json': json.loads(data)
                        fixtures.append({'name':dest.name,'archive_entry':item.filename,'sha256':sha(data)})
                rows.append(dict(archive=label,path=item.filename,bytes=len(data),sha256=sha(data),category=category))
    with (evidence/'archive-inventory.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    summary = {'outer_sha256':sha(args.outer.read_bytes()),'sdk_sha256':sha((ROOT/'android-sdk.zip').read_bytes()),'archive_file_count':len(rows),'sdk_file_count':sum(r['archive']=='sdk' for r in rows),'source_config_test_files':sources,'fixture_provenance':fixtures,'vendor_integrity':'PASS','clean_source_integrity':'PASS','fixture_integrity':'PASS'}
    (evidence/'input-verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    contracts=ROOT/'sdk/praxis/src/main/kotlin/io/praxis/sdk/contracts/Contracts.kt'
    lines=contracts.read_text().splitlines()
    entries=[]
    for i,line in enumerate(lines):
        match=re.match(r'(?:data class|enum class) (\w+)',line)
        if match: entries.append((match.group(1),i+1))
    doc=['# Supplied contract type index','','Generated from the supplied `Contracts.kt`; these are DTOs/enums, not additional client methods. Field names and defaults below are copied from source. The canonical generator/schema sources are absent.','']
    for n,(name,start) in enumerate(entries):
        end=entries[n+1][1]-3 if n+1<len(entries) else len(lines)
        doc += [f'## {name} — Contracts.kt:{start}','```kotlin','\n'.join(lines[start-1:end]).rstrip(),'```','']
    (ROOT/'docs/SDK_CONTRACT_TYPES.md').write_text('\n'.join(doc),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('fixture_provenance','source_config_test_files')},indent=2))
    print(f'Source/config/test files: {len(sources)}; recovered resources: {len(fixtures)}; contract types: {len(entries)}')
if __name__ == '__main__': main()
