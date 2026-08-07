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
