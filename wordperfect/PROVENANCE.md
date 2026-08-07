# WordPerfect corpus — provenance & licensing

A curated, version-verified set of WordPerfect-family files for exercising the WordPerfect extractor.
Every file is vendored from a permissively-licensed or public-domain upstream (Apache-2.0 / MPL-2.0 / CC0)
and is safe to redistribute. No file was hand-authored or fabricated.

Detection note: WordPerfect 5.0+ documents, graphics, and macros begin with the 16-byte WPC prefix
`FF 57 50 43` (`0xFF` `W` `P` `C`); the file-type byte at offset 9 distinguishes document / graphic /
macro / template. WordPerfect 4.2 and the Mac 1.x format predate that header — parsers must fall back on
structure, so those files are included on purpose.

## Files

| file | format / version | source | upstream path | rev | license |
|---|---|---|---|---|---|
| `wp42.wp` | WP 4.2 DOS (no WPC header) | LibreOffice/core | `writerperfect/qa/unit/data/writer/libwpd/pass/WP4.wp` | `b5c8452` | MPL-2.0 |
| `wp50.wp` | WP 5.0 | apache/tika | `…/tika-parser-miscoffice-module/src/test/resources/test-documents/testWordPerfect_5_0.wp` | `711be69` | Apache-2.0 |
| `wp51.wp` | WP 5.1 (dominant DOS format) | apache/tika | `…/test-documents/testWordPerfect_5_1.wp` | `711be69` | Apache-2.0 |
| `wp6.wpd` | WP 6.x | apache/tika | `…/test-documents/testWordPerfect.wpd` | `711be69` | Apache-2.0 |
| `corel_wp6.wpd` | WP 6.x (real-world, ~1 MB) | ross-spencer/opf-format-corpus | `format-corpus/office/wordprocessing/wpd/TOPOPREC.WPD` | `70d283c` | CC0 |
| `wp_mac1.wpd` | WordPerfect Mac 1.x | LibreOffice/core | `writerperfect/qa/unit/data/writer/libwpd/pass/WP1.wpd` | `b5c8452` | MPL-2.0 |
| `wp_mac3.wpd` | WordPerfect Mac 3.5 | LibreOffice/core | `writerperfect/qa/unit/data/writer/libwpd/pass/WP3.wpd` | `b5c8452` | MPL-2.0 |
| `graphic_v1.wpg` | WordPerfect Graphics 1.0 | LibreOffice/core | `writerperfect/qa/unit/data/draw/libwpg/pass/WPG1.wpg` | `b5c8452` | MPL-2.0 |
| `graphic_v2.wpg` | WordPerfect Graphics 2.0 | ImageMagick/ImageMagick | `PerlMagick/t/input.wpg` | `7b65dd1` | ImageMagick (Apache-2.0-derivative) |
| `cve_2015_1760_1.wpd` | malformed (error-path fixture) | LibreOffice/core | `writerperfect/qa/unit/data/writer/libwpd/pass/CVE-2015-1760-1.wpd` | `b5c8452` | MPL-2.0 |
| `cve_2015_1760_2.wpd` | malformed (error-path fixture) | LibreOffice/core | `writerperfect/qa/unit/data/writer/libwpd/pass/CVE-2015-1760-2.wpd` | `b5c8452` | MPL-2.0 |
| `cve_2007_1735_1.wpd` | malformed (error-path fixture) | LibreOffice/core | `writerperfect/qa/unit/data/writer/libwpd/pass/CVE-2007-1735-1.wpd` | `b5c8452` | MPL-2.0 |

Revisions are the upstream default-branch commit at fetch time (apache/tika `main`, LibreOffice/core
`master`, opf-format-corpus `master`).

Deliberately **not** vendored: the libwpd-regression `testset/` documents (real third-party German
business/medical files — Audi, Opel, invoices, medical forms) have no per-file license and are unsafe to
redistribute.

## Gaps (searched, no cleanly-licensed sample found)

These WordPerfect extensions were requested but have no *redistributable* genuine sample in the sources
checked (apache/tika, LibreOffice/core, OPF corpus, libwpg, ImageMagick, govdocs1, telparia/Jason-Scott
archive, Internet Archive, GitHub code search). Genuine files exist for the templates/macros, but only
under "All Rights Reserved"; the only openly-licensed hits were synthetic PRONOM/DROID skeleton stubs,
which are rejected (no fabricated files). Recorded here rather than faked:

- **`.wpt`** template — real samples exist (e.g. William Shunn's manuscript templates) but are
  copyrighted "All Rights Reserved"; not vendorable.
- **`.wcm`** (Corel/Windows macro) — same situation (Shunn, wptoolbox.com — all rights reserved).
- **`.wpm`** (DOS macro) — no genuine, cleanly-licensed sample located anywhere; both macro formats also
  carry no meaningful extractable text.

A govdocs1 (CC0) magic-byte scan would catch these if they surfaced (templates/macros share the WPC
header, file-type byte at offset 9), but they are far rarer than documents there. If a permissively-
licensed genuine sample turns up later, add it here with the same provenance fields.

## Ground truth

`ground_truth/wordperfect/<stem>.{md,txt}` is generated for the seven document files, and registered in
`ground_truth/ground_truth_mapping.json` under `wordperfect/<stem>`. Pipeline (reproducible):

1. `soffice --headless --convert-to docx <file>` — LibreOffice's writerperfect/libwpd import filter
   (best structure recovery: bold/italic, embedded images).
2. `pandoc <file>.docx -t gfm --wrap=none`.
3. Normalize to canonical GFM with `xberg/tools/benchmark-harness/scripts/normalize_gt.py`
   (`normalize(md, source="wp")` → `trailing_ws` + `blank_runs`), matching the rest of the corpus.
4. `.txt` companion via `wpd2text <file>` (libwpd).

No ground truth is produced for the `cve_*` files (malformed — they exercise error paths, not extraction)
or for `graphic_v1.wpg` (a vector graphic has no meaningful markdown text).
