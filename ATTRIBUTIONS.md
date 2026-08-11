# Attributions

This benchmark corpus is derived from third-party datasets. Each is credited below as required
by its license. Per-document provenance (upstream id, source revision, license) is in
`ground_truth/corpus_manifest.json`.

## lazyc/READoc

- **Citation:** READoc: A Unified Benchmark for Realistic Document Structured Extraction (arXiv:2409.05137)
- **Source:** <https://huggingface.co/datasets/lazyc/READoc>
- **License:** MIT
- **Used here:** 2217 accepted documents (per-doc).
- **Modifications:** ground truth normalized to canonical GFM (see README → How the data was modified). Derived GT is a derivative work under the upstream license.

## llamaindex/ParseBench

- **Citation:** ParseBench: A Document Parsing Benchmark for AI Agents, Zhang et al. (arXiv:2604.08538)
- **Source:** <https://huggingface.co/datasets/llamaindex/ParseBench>
- **License:** Apache-2.0
- **Used here:** 304 accepted documents (reference).
- **Modifications:** ground truth normalized to canonical GFM (see README → How the data was modified). Derived GT is a derivative work under the upstream license.

## bsmock/FinTabNet.c

- **Citation:** Smock et al., "Aligning benchmark datasets for table structure recognition", ICDAR 2023 (arXiv:2303.00716)
- **Source:** <https://huggingface.co/datasets/bsmock/FinTabNet.c>
- **License:** CDLA-Permissive-2.0
- **Used here:** 80 accepted documents (vendor).
- **Modifications:** ground truth normalized to canonical GFM (see README → How the data was modified). Derived GT is a derivative work under the upstream license.

## federalregister.gov

- **Citation:** U.S. Federal Register (OFR/GPO), federalregister.gov — U.S. Government work, public domain (17 U.S.C. §105)
- **Source:** <https://www.federalregister.gov>
- **License:** US-PD (17 U.S.C. §105)
- **Used here:** 31 accepted documents (vendor).
- **Modifications:** ground truth normalized to canonical GFM (see README → How the data was modified). Derived GT is a derivative work under the upstream license.

## WordPerfect corpus (`wordperfect/`)

Vendored WordPerfect-family test files. Per-file provenance (upstream path, revision, format/version) is in
`wordperfect/PROVENANCE.md`.

### apache/tika

- **Source:** <https://github.com/apache/tika> — `tika-parser-miscoffice-module` test documents
- **License:** Apache-2.0
- **Used here:** `wp50.wp`, `wp51.wp`, `wp6.wpd` (WordPerfect 5.0 / 5.1 / 6.x).
- **Modifications:** none to the source files. Markdown/plaintext ground truth is derived (see `wordperfect/PROVENANCE.md`).

### LibreOffice/core (writerperfect)

- **Source:** <https://github.com/LibreOffice/core> — `writerperfect/qa/unit/data` (libwpd / libwpg test data)
- **License:** MPL-2.0
- **Used here:** `wp42.wp`, `wp_mac1.wpd`, `wp_mac3.wpd`, `graphic_v1.wpg`, `cve_2015_1760_1.wpd`, `cve_2015_1760_2.wpd`, `cve_2007_1735_1.wpd`.
- **Modifications:** none to the source files. Ground truth is derived where applicable.

### OPF format corpus

- **Source:** <https://github.com/ross-spencer/opf-format-corpus> — `format-corpus/office/wordprocessing/wpd`
- **License:** CC0 (public-domain dedication; corpus README)
- **Used here:** `corel_wp6.wpd` (from `TOPOPREC.WPD`).
- **Modifications:** none to the source file. Ground truth is derived (see `wordperfect/PROVENANCE.md`).

### ImageMagick

- **Source:** <https://github.com/ImageMagick/ImageMagick> — `PerlMagick/t/input.wpg`
- **License:** ImageMagick License (an Apache-2.0 derivative; permissive, attribution-only) — <https://imagemagick.org/license/>
- **Used here:** `graphic_v2.wpg` (WordPerfect Graphics 2.0).
- **Modifications:** none to the source file.

## OpenDocument Presentation fixture (`odp/libreoffice_impress.odp`)

- **Source:** Apache Tika test corpus.
- **License:** Apache-2.0.
- **Used here:** `libreoffice_impress.odp`.
- **Modifications:** none to the source file. Markdown/plaintext ground truth is derived from the presentation XML
  text nodes and title/subtitle roles.

## Apple iWork fixtures (`iwork/`)

- **Source:** existing Xberg test corpus, present since corpus commit `c55c3b48ba29634d097c84cda220929a083e4553`.
- **Original upstream/license:** not recorded in the import history; no external source is inferred here.
- **Used here:** `test.pages`, `test.key`, and `test.numbers`.
- **Modifications:** none to the source files. Pages and Keynote GT comes from their sole length-delimited UTF-8 IWA
  payloads; Numbers GT uses Apple QuickLook and the package's matching application-generated preview as independent
  visual oracles.

## HWPX fixture (`hwpx/simple.hwpx`)

- **Source:** existing Xberg test corpus, present since corpus commit `c55c3b48ba29634d097c84cda220929a083e4553`.
- **Original upstream/license:** not recorded in the import history; no external source is inferred here.
- **Used here:** `simple.hwpx`.
- **Modifications:** none to the source file. Ground truth is derived from the paragraph and text-run nodes in
  `Contents/section0.xml`.

## JSONL fixtures (`jsonl/`)

- **Source:** added directly to the Xberg test corpus in commit
  `cfd6902290a4e36e8e5cf77e8a3b93ba1a3d1720` with no external upstream recorded.
- **Used here:** `simple.jsonl` and `with_blanks.jsonl`.
- **Modifications:** none to the source files. Ground truth is the exact canonical JSON array represented by each
  newline-delimited input; blank separator lines have no semantic value.

## ndl-lab/pdmocrdataset-part1 (NDL PDM OCR Dataset)

- **Citation:** National Diet Library (Japan), "NDL古典籍OCR / PDM OCR Dataset (tosho_all)", 2022.
- **Source:** <https://github.com/ndl-lab/pdmocrdataset-part1> (data: <https://lab.ndl.go.jp/dataset/pdm_ocr_dataset/line/tosho_all_linejson.zip>)
- **License:** Public Domain Mark 1.0 (source works are copyright-expired; NDL releases openly).
- **Used here:** 5 page images (`images/ndl_meiji_vertical_01..05.jpg`) — historical Japanese printed pages (Meiji–Shōwa, 1870–1930), predominantly vertical text.
- **Modifications:** each page's line-level `text` boxes (NDL human transcription) concatenated in vertical reading order (right-to-left columns, top-to-bottom within a column) into canonical GT. Word strings are verbatim NDL annotations; no fabrication.

## naver-clova-ix/cord-v2 (CORD)

- **Citation:** Park et al., "CORD: A Consolidated Receipt Dataset for Post-OCR Parsing", NeurIPS 2019 Workshop on Document Intelligence.
- **Source:** <https://huggingface.co/datasets/naver-clova-ix/cord-v2>
- **License:** CC-BY-4.0
- **Used here:** 4 receipt images (`images/cord_receipt_01..04.jpg`) from the `test` split.
- **Modifications:** `valid_line` word `text` (human annotation) joined in reading order (lines top-to-bottom, words left-to-right) into GT. Verbatim.

## TextOCR (Meta)

- **Citation:** Singh et al., "TextOCR: Towards large-scale end-to-end reasoning for arbitrary-shaped scene text", CVPR 2021.
- **Source:** <https://textvqa.org/textocr/> (images: TextVQA / Open Images; <https://huggingface.co/datasets/facebook/textvqa>)
- **License:** CC-BY-4.0
- **Used here:** 3 scene-text images (`images/textocr_scene_01..03.jpg`); image_ids `e6c1a7b56123bbdb`, `76f940b2603a49e7`, `855d76c85603018d`.
- **Modifications:** human word `utf8_string` values grouped into lines by geometry and concatenated in reading order into GT. Verbatim (null "." markers dropped).

## ds4sd/DocLayNet (IBM)

- **Citation:** Pfitzmann et al., "DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis", KDD 2022.
- **Source:** <https://huggingface.co/datasets/ds4sd/DocLayNet-v1.1>
- **License:** CDLA-Permissive-1.0
- **Used here:** 2 financial-report pages (`images/doclaynet_page_01..02.jpg`) from the `test` split (`NASDAQ_ATRI_2003.pdf` p24, `NYSE_MGM_2004.pdf` p49).
- **Modifications:** authoritative PDF text cells linearized in reading order (top-to-bottom, then left-to-right). No OCR and no model used; text is DocLayNet's verbatim PDF-layer cell text.

## Diagram fixtures (this repository)

- **Source:** authored here, not derived from any third-party dataset. The first four Graphviz fixtures were contributed by Parman Mohammadalizadeh (@MannXo) in xberg-io/test_documents#1.
- **License:** same as this repository.
- **Used here:** `diagrams/svg/*.svg`, `diagrams/pdf/*.pdf` and `diagrams/png/*.png` plus their `diagrams/src/*.{dot,mmd,puml,fodg,html}` sources, `diagrams/manifest.json`, and `ground_truth/dot/*.dot`.
- **Rendering tools:** the source graphs are ours; the SVGs and PDFs are what each renderer emitted from them. Graphviz 15.1.1 (`dot`/`neato`) is EPL-1.0, Mermaid CLI 11.16.0 is MIT, PlantUML 1.2026.0 is GPL, LibreOffice 26.2.5.2 is MPL-2.0, librsvg 2.62.3 (`rsvg-convert`, used for both PDF and PNG output) is LGPL-2.1-or-later, qpdf 12.3.2 is Apache-2.0, and Google Chrome 151 is proprietary. None of these licenses reaches the output: rendering a document is not a derivative work of the renderer, and PlantUML says so explicitly in its FAQ. No tool binary, jar or stylesheet is redistributed here.
- **Embedded fonts:** a PDF carries subsetted glyph outlines of whatever fonts the renderer reached for, so the fixtures under `diagrams/pdf/` do redistribute font data. Each family was checked against the OS/2 `fsType` bit of the system font it came from, which is where a font states its own embedding terms: Helvetica and Liberation Sans report 0 (installable, no restriction), Times New Roman and Trebuchet MS report 8 (editable embedding). All four permit it. `scripts/build_diagram_pdfs.py` holds that allowlist and fails a build that reaches for anything outside it. That check is why `graphviz_cjk` ships as SVG only: macOS's Songti reports `fsType` 2, restricted, which forbids embedding without the owner's permission, so no CJK PDF is published until an open-licensed CJK face is available to render one. The raster fixtures under `diagrams/png/` redistribute no font data at all, since a PNG holds an image of text rather than the outlines that drew it, which is why `graphviz_cjk` does ship as raster.
- **Modifications:** every fixture whose producer states its own graph also ships as a `*_geometry.svg` variant with that metadata removed by `scripts/strip_svg_graph_metadata.py` — Graphviz writes the node ids and the full edge list into `<title>` elements and again into XML comments; Mermaid into `id="L_start_auth_0"`, again into `data-id`, and the edge's waypoints into `data-points`; PlantUML into `id="Read config-to-Open input"`, again into a comment, again into a `data-entity-1`/`data-entity-2` pair, and once more into a `<?plantuml-src?>` processing instruction carrying its whole deflated source; and LibreOffice by tagging each group with its shape kind, which across a whole file is the node/edge partition. A fixture that names its own answer cannot measure geometry recovery. Stripping removes no geometry: each variant renders to a byte-identical PNG. `nested_transforms.svg`, `icon_nodes.svg`, `mixed_page.svg`, `two_diagrams.svg` and the three `negative_*.svg` files are hand-written. Ground truth is the source graph restated by node label, so it is independent of any recogniser's numbering.
