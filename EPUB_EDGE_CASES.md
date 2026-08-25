# EPUB edge-case corpus

One or more EPUB files for each defect that xberg-io/xberg pull request #1498 fixes, so each fix has a regression file. The pull request covers eight issues: #1488, #1489, #1490, #1491, #1492, #1493, #1494 and #1486. A real published file is used wherever one exhibits the case. A synthesized file stands in only where no public file does, and the table says so.

## Where the bytes are

The files live under `epub/edge-cases/<case>/`. They are corpus binaries: published to the bucket, pinned by `corpus.lock.json`, never committed. `scripts/epub-edge-cases.json` records each file with its sha256, size and source, and `scripts/fetch_epub_edge_cases.py` puts every file at its path:

```sh
python3 scripts/fetch_epub_edge_cases.py
python3 scripts/publish_corpus.py --bucket xberg-test-documents
```

Three kinds of source appear in the manifest. A `url` entry is a published file downloaded as is. A `members` entry is an EPUB that its source publishes as an unpacked directory (the epubcheck test suite); each member is fetched from a pinned commit and the container is written deterministically. A `generated` entry is built by `scripts/build_epub_edge_cases.py`, which is deterministic, so the manifest pins its bytes too. `scripts/test_epub_edge_cases.py` checks that pin against a fresh build.

## No ground truth

These files ship without `ground_truth/` files, for the reason `MATH_PROVENANCE.md` and `REGRESSION_PROVENANCE.md` give: they bring no upstream ground truth, and recording the extractor's own output would make a golden file that cannot fail. Their value is the measured before and after below. A future run that reproduces the "before" column on a fixed build is the regression.

## How each file was measured

Two xberg CLI builds ran over every file on 2026-08-25: the base of the pull request (`c0aa8575e2`) and its head (`96bc550345`, the same eight commits). Each file was extracted twice, `xberg extract <file> --format json --no-config-discovery` for plain text and again with `--config-json '{"output_format":"markdown"}'`. The columns below quote what changed: a spine item present or absent in the plain text, a metadata field, a warning, or the process exit code. Spine presence was probed by searching the plain output for the first and last forty non-whitespace characters of each spine member's visible text, which is the same probe the pull request's 41-file corpus gate uses.

## Lanes

All 36 files are in the vendor lane. Each licence was read from the file's own package document or from the source repository's licence file, as the "licence" column says.

Sources and evidence:

- Project Gutenberg: `<dc:rights>Public domain in the USA.</dc:rights>` in each file's `content.opf`.
- Standard Ebooks: `<dc:rights>` in `content.opf` dedicates the edition to the public domain under CC0 1.0.
- IDPF epub3-samples: the collection's default is CC-BY-SA, so only `childrens-literature` is used, whose `package.opf` states `<dc:rights>Public domain in the USA.</dc:rights>`.
- W3C epub-tests: `LICENSE.md` places every packaged test under the W3C Software and Document License.
- w3c/epubcheck test resources: `LICENSE.md`, BSD-3-Clause.
- futurepress/epub.js: the repository `license` file (BSD) plus `<dc:rights>Public domain in the USA.</dc:rights>` in the file.
- psiegman/epublib: Apache-2.0 (repository `LICENSE`).
- Internet Archive: scans of works published in 1886 and 1923 in the `americana` collection, public domain in the United States by date; the items carry no rights statement.
- Synthesized files: generated for this corpus, MIT, as our own work.

## Issue #1488: entities, byte order marks and chapters that do not parse

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/entities/synthetic_entity_style.epub` | synthesized: the reproduction from the issue, `<link rel="stylesheet"/>` before an empty `<title/>` and `&nbsp;` in the first paragraph, plus a second chapter with `style` attributes | MIT | chapter 1 absent from the plain text; the book starts at chapter 2 | both chapters present, `First para ENTITY-CHAPTER-ONE` |
| `epub/edge-cases/entities/synthetic_bom_prelude.epub` | synthesized: UTF-8 byte order mark before `<?xml` | MIT | the byte order mark is its own paragraph; markdown prints `?xml version="1.0" encoding="utf-8"?>` as prose | plain text is the chapter only; markdown has no prelude text |
| `epub/edge-cases/entities/synthetic_unparseable_chapter.epub` | synthesized: one chapter with a mismatched closing tag | MIT | no warning | one warning: `Spine item 'OEBPS/broken.xhtml' is not well-formed XML (expected 'b' tag, not 'p' at 2:51); its text was recovered by stripping tags` |

No public file was found for these. Current Project Gutenberg builds resolve named entities to characters, and a scan of forty EPUBs from Gutenberg, Standard Ebooks, IDPF, W3C, epubcheck, Apache Tika and epublib found no byte order mark before a content document. Apache Tika's `testEPUB_xml_ext.epub` carries `&nbsp;` next to a stylesheet link, but its text is an excerpt of a work still in copyright, and the base build extracts it in full, so it does not reproduce the defect.

## Issue #1489: navigation heuristic, image-only pages, SVG spine documents

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/navigation/pg14838_epub3.epub` | [Project Gutenberg 14838, The Tale of Peter Rabbit, EPUB 3](https://www.gutenberg.org/ebooks/14838.epub3.images) | Public domain in the USA | the licence page `*_14838-h-1.htm.xhtml` (8 `<li>`, 3 `<a>`, no `<p>`) is absent; 5,704 characters of plain text | present; 20,968 characters |
| `epub/edge-cases/navigation/pg28885_epub3.epub` | [Project Gutenberg 28885, Alice's Adventures in Wonderland illustrated by Rackham, EPUB 3](https://www.gutenberg.org/ebooks/28885.epub3.images) | Public domain in the USA | the contents page `*-h-0.htm.xhtml` and the licence page `*-h-13.htm.xhtml` are absent; 117,596 characters | both present; 134,890 characters |
| `epub/edge-cases/navigation/idpf_childrens_literature.epub` | [IDPF epub3-samples, childrens-literature](https://github.com/IDPF/epub3-samples/releases/download/20230704/childrens-literature.epub) | Public domain in the USA (package document) | `nav.xhtml` is in the spine with `properties="nav scripted"`; the image-only `cover.xhtml` yields no image, 0 images | the cover reaches the image pipeline, 1 image, `Cover Image` |
| `epub/edge-cases/navigation/epubjs_alice.epub` | [futurepress/epub.js test fixture alice.epub](https://github.com/futurepress/epub.js/blob/master/test/fixtures/alice.epub) | BSD, public domain text | `cover.xhtml` holds only `<img alt="Cover Image">`; 27 images | 28 images, the cover first |
| `epub/edge-cases/navigation/w3c_nav_spine_in_spine.epub` | [W3C epub-tests nav-spine_in-spine](https://w3c.github.io/epub-tests/tests/nav-spine_in-spine.epub) | W3C Software and Document License | the navigation document is first in the spine with `properties="nav"`; excluded by the heuristic | excluded from the package declaration; identical output, the control for the new rule |
| `epub/edge-cases/navigation/pg1661_epub2.epub` | [Project Gutenberg 1661, The Adventures of Sherlock Holmes, EPUB 2](https://www.gutenberg.org/ebooks/1661.epub.noimages) | Public domain in the USA | `<guide><reference type="toc">` points into a spine item; the item is kept on both builds. 13 chapters are partial because of the heading defect in #1493 | all chapters present |
| `epub/edge-cases/navigation/w3c_lay_pp_image_only.epub` | [W3C epub-tests lay-pp-spine-overrides_image-only-pp](https://w3c.github.io/epub-tests/tests/lay-pp-spine-overrides_image-only-pp.epub) | W3C Software and Document License | the fixed-layout page that is only an `<img>` produces nothing | its alt text appears: `[Image: This test passes if this page is displayed as fixed layout, ...]` |
| `epub/edge-cases/navigation/w3c_pkg_spine_order_svg.epub` | [W3C epub-tests pkg-spine-order-svg](https://w3c.github.io/epub-tests/tests/pkg-spine-order-svg.epub) | W3C Software and Document License | four SVG spine items skipped with `no renderable XHTML/DTBook fallback found for media type 'image/svg+xml'`; 0 characters | all four present; 0 warnings |
| `epub/edge-cases/navigation/w3c_cnt_svg_support.epub` | [W3C epub-tests cnt-svg-support](https://w3c.github.io/epub-tests/tests/cnt-svg-support.epub) | W3C Software and Document License | the single SVG spine item skipped, 0 characters | present, 89 characters |

## Issue #1490: deep nesting

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/depth/synthetic_nested_30000.epub` | synthesized: one chapter with 30,000 nested `<span>` elements around one word, between two paragraphs | MIT | `thread 'main' has overflowed its stack`, the process aborts (SIGABRT) in plain and markdown output | exit 0; the lead and tail paragraphs and the nested word are present; one warning: `Spine item 'OEBPS/deep.xhtml' is nested deeper than 1024 elements; only its plain text was kept` |

Synthesized by necessity: no published book nests elements thirty thousand deep. The generator is `nested_30000` in `scripts/build_epub_edge_cases.py`; the depth is the one the issue measured as fatal (20,000 passes).

## Issue #1491: per-item failures

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/unsafe-href/epubcheck_ocf_url_leaking_in_opf.epub` | [w3c/epubcheck test `ocf-url-leaking-in-opf-error`](https://github.com/w3c/epubcheck/tree/82b174ec319ea3e6c9d2488f84155fa4a9171fc2/src/test/resources/epub3/04-ocf/files/ocf-url-leaking-in-opf-error), packaged | BSD-3-Clause | the spine item's href `../../../../EPUB/content_001.xhtml` fails the whole book: exit 1, `Unsafe manifest href for spine item 'content_001'`, no metadata | exit 0, title `Minimal EPUB 3.0`, one warning: `Skipping spine item 'content_001' ... unsafe manifest href` |
| `epub/edge-cases/unsafe-href/epubcheck_ocf_url_path_absolute.epub` | [w3c/epubcheck test `ocf-url-path-absolute-error`](https://github.com/w3c/epubcheck/tree/82b174ec319ea3e6c9d2488f84155fa4a9171fc2/src/test/resources/epub3/04-ocf/files/ocf-url-path-absolute-error), packaged | BSD-3-Clause | href `/EPUB/content_001.xhtml`; the chapter is read on both builds, no warning | identical; a control that an absolute path inside the container is not treated as unsafe |
| `epub/edge-cases/unsafe-href/synthetic_remote_url_spine_item.epub` | synthesized: a spine item whose href is `https://example.org/remote.xhtml`, next to a local chapter | MIT | one warning, the local chapter present | identical; a control that a remote item was already a per-item warning |

The iteration limit is 10,000,000 (`SecurityBudget::max_iterations`), which no file of a size this corpus accepts can reach, so the "iteration limit names the skipped items" part of the fix has no file here.

## Issue #1492: Dublin Core and covers

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/metadata/se_frankenstein.epub` | [Standard Ebooks, Frankenstein](https://standardebooks.org/ebooks/mary-shelley/frankenstein) | CC0 1.0 | three `dc:title` elements (`main`, `subtitle`, `expanded`); title is `Frankenstein, or the Modern Prometheus`, the last one; no keywords | title `Frankenstein`; 7 subjects as keywords |
| `epub/edge-cases/navigation/idpf_childrens_literature.epub` | as above | Public domain in the USA | second `dc:title` wins: `A Textbook of Sources for Teachers and Teacher-Training Classes`; authors `Erle Elsworth Clippinger` only; `properties="cover-image"` with no `<meta name="cover">` finds no cover, 0 images | title `Children's Literature`; authors `Charles Madison Curry, Erle Elsworth Clippinger`; 1 image |
| `epub/edge-cases/metadata/epublib_testbook1.epub` | [psiegman/epublib testbook1.epub](https://github.com/psiegman/epublib/blob/master/epublib-core/src/test/resources/testbook1.epub) | Apache-2.0 | EPUB 2 with two plain `dc:title` elements; title `test2` | title `Epublib test book 1` |
| `epub/edge-cases/metadata/pg27805_epub2.epub` | [Project Gutenberg 27805, The Wind in the Willows, EPUB 2](https://www.gutenberg.org/ebooks/27805.epub.noimages) | Public domain in the USA | `<dc:date opf:event="publication">` and `opf:event="conversion"`; `created_at` is the conversion timestamp `2026-08-11T14:38:33`; 8 `dc:subject`, no keywords | `created_at` `2009-01-14`; 8 keywords |
| `epub/edge-cases/metadata/synthetic_dublin_core_epub2.epub` | synthesized: two titles, `opf:role="aut"` and `opf:role="ill"` creators, three subjects, `publication` and `modification` dates | MIT | title `Subtitle`, authors `Ivan Illustrator`, `created_at` `2020-02-02`, no keywords | title `Main Title`, authors `Alice Author, Ivan Illustrator`, `created_at` `1999-01-01`, 3 keywords |
| `epub/edge-cases/metadata/synthetic_cover_meta_xhtml.epub` | synthesized: `<meta name="cover" content="cover-page">` where `cover-page` is the cover XHTML | MIT | 1 image of format `png` whose bytes are the XHTML page (they start with `<?xml version=`), `page_number` 0 | 1 image, the real PNG from the cover page's `<img>`, description `COVER-ALT front cover` |

Two cases are synthesized. Project Gutenberg and Standard Ebooks put illustrators in `dc:contributor`, never `dc:creator`, and Gutenberg's second date event is `conversion`, not `modification`; the synthesized file carries the exact forms the issue names. No public file with `<meta name="cover">` pointing at an XHTML page was found under a redistributable licence; the closest, epublib's `test1.opf`, is a bare package document.

## Issue #1493: rendering

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/rendering/pg39292_epub2.epub` | [Project Gutenberg 39292, A Greek Primer, EPUB 2](https://www.gutenberg.org/ebooks/39292.epub.noimages) | Public domain in the USA | a table nested in a `<td>`; the enclosing row `(1) Mutes` is absent from the plain text | present, followed by the nested table's rows |
| `epub/edge-cases/rendering/pg98_epub2.epub` | [Project Gutenberg 98, A Tale of Two Cities, EPUB 2](https://www.gutenberg.org/ebooks/98.epub.noimages) | Public domain in the USA | 45 headings of the form `<h2>CHAPTER I.<br/>The Period</h2>`; 45 U+0001 bytes in the plain text, one per chapter heading | 0 U+0001 bytes |
| `epub/edge-cases/rendering/w3c_ocf_url_link_leaking_relative.epub` | [W3C epub-tests ocf-url_link-leaking-relative](https://w3c.github.io/epub-tests/tests/ocf-url_link-leaking-relative.epub) | W3C Software and Document License | `<img src="../../../../media/imgs/monastery.jpg" alt="Photograph of a medieval monastery">` cannot be resolved; the alt text is absent from the plain text | `[Image: Photograph of a medieval monastery]` |
| `epub/math/cnt_mathml_support_a20d9b.epub` (already in the corpus) | W3C epub-tests cnt-mathml-support | W3C Software and Document License | markdown output carries 1 `<!-- MathML: ... -->` comment | 0 |
| `epub/math/quadratic_functions_4ebefc.epub` (already in the corpus) | Connexions collection col11284 | CC-BY-3.0 | markdown output carries 266 `<!-- MathML: ... -->` comments | 0 |

The MathML rows reuse files the math corpus already holds; both were measured from the same source URLs on the same day, and no new file is added for them.

## Issue #1494: encodings and DRM

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/encoding/synthetic_latin1.epub` | synthesized: chapter declared `iso-8859-1` with accented bytes | MIT | chapter absent, warning `stream did not contain valid UTF-8` | present, 0 warnings |
| `epub/edge-cases/encoding/synthetic_cp1252.epub` | synthesized: chapter declared `windows-1252` with `€`, curly quotes and `œ` | MIT | absent, same warning | present |
| `epub/edge-cases/encoding/synthetic_shift_jis.epub` | synthesized: chapter declared `Shift_JIS` with Japanese text | MIT | absent, same warning | present |
| `epub/edge-cases/encoding/synthetic_utf16le.epub` | synthesized: chapter written in UTF-16LE with a byte order mark | MIT | absent, same warning | present |
| `epub/edge-cases/encoding/synthetic_utf16be.epub` | synthesized: chapter written in UTF-16BE with a byte order mark | MIT | absent, same warning | present |
| `epub/edge-cases/encoding/synthetic_opf_latin1.epub` | synthesized: the package document itself in Latin-1 | MIT | the whole book fails: exit 1, `Failed to read file from EPUB: stream did not contain valid UTF-8` | exit 0; title `Éléments d'un livre`, author `Zoë Ångström`, chapter present |
| `epub/edge-cases/encoding/ia_whyiamsocialist441besa_lcp.epub` | [Internet Archive, Why I am a socialist (1886), LCP derivative](https://archive.org/details/whyiamsocialist441besa) | Public domain (1886, `americana`) | Readium LCP: `encryption.xml` lists 10 spine items under `aes256-cbc`; 10 warnings, each `stream did not contain valid UTF-8` | one warning: `The EPUB is encrypted (DRM): 10 of 11 spine items are listed in META-INF/encryption.xml and were skipped` |
| `epub/edge-cases/encoding/epubcheck_ocf_encryption_unknown_valid.epub` | [w3c/epubcheck test `ocf-encryption-unknown-valid`](https://github.com/w3c/epubcheck/tree/82b174ec319ea3e6c9d2488f84155fa4a9171fc2/src/test/resources/epub3/04-ocf/files/ocf-encryption-unknown-valid), packaged | BSD-3-Clause | `encryption.xml` declares the only spine item under `kw-aes128` although its bytes are plain XHTML; the chapter is extracted, no warning | the chapter is skipped with the DRM warning (`1 of 1 spine items`) |
| `epub/edge-cases/encoding/w3c_ocf_font_obfuscation.epub` | [W3C epub-tests ocf-font_obfuscation](https://w3c.github.io/epub-tests/tests/ocf-font_obfuscation.epub) | W3C Software and Document License | `encryption.xml` lists one font under `http://www.idpf.org/2008/embedding`; no warning, chapter present | identical; the control that font obfuscation alone does not warn |
| `epub/edge-cases/encoding/epubcheck_ocf_obfuscation_valid.epub` | [w3c/epubcheck test `ocf-obfuscation-valid`](https://github.com/w3c/epubcheck/tree/82b174ec319ea3e6c9d2488f84155fa4a9171fc2/src/test/resources/epub3/04-ocf/files/ocf-obfuscation-valid), packaged | BSD-3-Clause | same shape, an OTF font only; no warning | identical |

The encoding files are synthesized: the search found no redistributable EPUB whose content document is declared in a legacy charset and contains non-ASCII bytes in it. Old Internet Archive uploads, Aozora Bunko conversions and the epubcheck suite all declare UTF-8 or are pure ASCII. epubcheck holds a UTF-16 content document as a bare file, not inside a package. No Adobe `http://ns.adobe.com/pdf/enc#RC` specimen was found.

## Issue #1486: spine media types

| path | source | licence | before | after |
|---|---|---|---|---|
| `epub/edge-cases/media-types/ia_foodresearchinst00stan.epub` | [Internet Archive, Food Research Institute (1923)](https://archive.org/details/foodresearchinst00stan), generated by `Ebook-lib 0.17.1` | Public domain (1923, `americana`) | every spine item is `media-type="text/html"`; 9 items skipped with `no renderable XHTML/DTBook fallback found for media type 'text/html'`; 0 characters | see below |
| `epub/edge-cases/media-types/synthetic_media_type_labels.epub` | synthesized: six spine items labelled `text/html`, `text/xml`, `application/xml`, `application/xhtml+xml; charset=utf-8`, `APPLICATION/XHTML+XML` and `media-type=""` | MIT | all six skipped, one warning each; 0 characters | see below |

The head of pull request #1498 measured here (`96bc550345`) contains no commit for the media types, although its description says it supersedes #1487. Both files extract 0 characters with the same warnings on both builds. The "before" column is measured; the "after" column is what the pull request text promises and awaits a build that carries the change. Internet Archive EPUBs regenerated after mid-2025 declare `application/xhtml+xml`; older items such as this one still carry `text/html`. No public file with `text/xml`, `application/xml`, a parameter, uppercase or an empty media type was found, so those five labels are synthesized.

## Recorded, not hosted

These files showed a case during the search but cannot be vendored, and none is added:

| document | case | licence |
|---|---|---|
| IDPF epub3-samples `linear-algebra.epub` | nine chapter overview pages dropped by the navigation heuristic (#1489) | GNU FDL 1.2 |
| IDPF epub3-samples `moby-dick-mo.epub` | the "Brief Contents" page dropped (#1489) | CC-BY-SA 3.0 |
| IDPF epub3-samples `svg-in-spine.epub` | six SVG spine items skipped (#1489) | CC-BY-SA 3.0 |
| IDPF epub3-samples `georgia-pls-ssml.epub` | subtitle `11th Edition` reported as the title (#1492) | CC-BY-SA 3.0 |
| IDPF epub3-samples `regime-anticancer-arabic.epub`, `page-blanche.epub` | only the last of three (two) creators reported (#1492) | CC-BY-SA 3.0 |
| archive.org `BSCS_Biology_A_Molecular_Approach...epub`, `The Insects, An Outline of Entomology.epub` | 891 and 628 `text/html` spine items (#1486) | in copyright |
| Apache Tika `testEPUB_xml_ext.epub` | `&nbsp;` beside a stylesheet link (#1488); does not reproduce on the base build | Apache-2.0 fixture around an in-copyright excerpt |
