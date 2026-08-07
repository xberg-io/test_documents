# Existing corpus slice 1 — provenance and ground-truth review

This slice registers files already present in `test_documents`; it does not add or replace source documents. The
SHA-256 values pin the exact reviewed bytes. Where the original import did not record an external upstream, that gap
is stated rather than inferred.

## `odp/libreoffice_impress.odp`

- SHA-256: `ecc8129a5b22c77b378504d87774ef26245d9e4146e8b15ec30a2f58fd0ebb93`
- Provenance: added in `fd05b332137d54c781e859459bfa83fddcca56f7` from the Apache Tika test corpus
  (Apache-2.0).
- GT basis: deterministic extraction of text nodes and presentation roles from `content.xml`. Slide 1 has a
  `presentation:class="title"` frame containing `This is` and a subtitle frame containing
  `An example Impress file`; slide 2 has empty placeholders only.

## `iwork/test.pages`

- SHA-256: `22ecf2c2cdb3168a59dc4bc95a5e57d490f4f83d8d76c9de81eefc822e9506c5`
- Provenance: present since initial corpus commit `c55c3b48ba29634d097c84cda220929a083e4553`; no external upstream
  or license was recorded.
- GT basis: extraction of the sole length-delimited UTF-8 field in `Index/Document.iwa`,
  `Hello World from Pages`. The Markdown GT conservatively records a paragraph because this minimal payload carries
  no independently verifiable heading role.

## `iwork/test.key`

- SHA-256: `e7b3cffa52ca4d67465a9fbf919a13808f1ddf74bc2fd250ea9ea877d9beecd1`
- Provenance: present since initial corpus commit `c55c3b48ba29634d097c84cda220929a083e4553`; no external upstream
  or license was recorded.
- GT basis: extraction of the sole length-delimited UTF-8 field in the only slide archive,
  `Index/Slide-0001.iwa`: `Hello World from Keynote`. The slide context supports an H2 slide-title block.

## `iwork/test.numbers`

- SHA-256: `b9e9772b2d2866c26d773fe46a173c373c7dc1dd3df6cefc7f0253b6ab50d4c3`
- Provenance: present since initial corpus commit `c55c3b48ba29634d097c84cda220929a083e4553`; no external upstream
  or license was recorded.
- GT basis: Apple QuickLook (`qlmanage -t -s 1600`) independently rendered the package as a 720×552 PNG with
  SHA-256 `caf25c0c8d099dbc92338681667554403c8f87dc840030b59777c1288cdcefbd`. The render agrees with the
  application-generated `preview.jpg` at package path `preview.jpg` (SHA-256
  `840411610bf3f737364651b319319d1420f03afa0a47882cc904b6e8da34426e`). Both show the same two named tables,
  exact headers, row labels, cell values, and grid topology used for the canonical GFM.

## `hwpx/simple.hwpx`

- SHA-256: `9ce4d481ad359329de269b61fe55536ca06ff3b8a51ed540492d59a1af004a5a`
- Provenance: present since initial corpus commit `c55c3b48ba29634d097c84cda220929a083e4553`; no external upstream
  or license was recorded.
- GT basis: deterministic extraction from `Contents/section0.xml`, which contains two `hp:p` elements with one
  exact `hp:t` text run each.

## `jsonl/simple.jsonl`

- SHA-256: `32e1bb03848039a3b526c8408fb2a26480dde0a0f9763debe9c2da1d803484bb`
- Provenance: added in corpus commit `cfd6902290a4e36e8e5cf77e8a3b93ba1a3d1720`; no external upstream is
  recorded.
- GT basis: exact parse of the three non-empty JSON lines into a three-element JSON array, serialized with
  two-space indentation while retaining source object-key order. `record_count: 3` in the descriptor records the
  exact semantic assertion.

## `jsonl/with_blanks.jsonl`

- SHA-256: `a842922742b0d5a3e621b8cb77db93b905135ca95eca0af5ada714681f9eb522`
- Provenance: added in corpus commit `cfd6902290a4e36e8e5cf77e8a3b93ba1a3d1720`; no external upstream is
  recorded.
- GT basis: exact parse of the three non-empty JSON lines into a three-element JSON array; two blank separator
  lines are intentionally ignored. The descriptor records exact `record_count: 3` and `blank_line_count: 2`
  assertions.

The JSONL fixtures intentionally have plaintext GT only. Their canonical value is structured JSON rather than
Markdown, so inventing Markdown blocks would create layout semantics absent from the sources.
