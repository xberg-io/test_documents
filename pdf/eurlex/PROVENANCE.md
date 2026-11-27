# EUR-Lex multilingual PDFs: provenance and licence

Three EU acts, each in all 24 official EU languages (72 born-digital PDFs with a text layer), used as
native sources for the synthetic-scan OCR corpus (`tools/benchmark-harness/scripts/synth_ocr_corpus.py`
in xberg reads every PDF pinned in `corpus.lock.json`). Same content in 24 languages and three scripts
(Latin, Greek, Cyrillic) makes per-language OCR differences directly comparable.

- `32024L1306` (OJ L, 2024/1306, 8.5.2024): Directive (EU) 2024/1306 amending Directive 2013/34/EU as regards the time limits for the adoption of sustainability reporting standards. Layout: single-column legislative prose (recitals, articles).
- `32024R0737` (OJ L, 2024/737, 23.2.2024): Commission Implementing Regulation (EU) 2024/737 amending Regulation (EC) No 1484/95 as regards fixing representative prices in the poultrymeat and egg sectors and for egg albumin. Layout: annex price table (CN code, description, representative price, security).
- `C/2024/03243` (OJ C, C/2024/3243, 4.6.2024): Interest rate applied by the European Central Bank to its main refinancing operations: 4,50 % on 1 June 2024 - Euro exchange rates - 3 June 2024. Layout: single Official Journal C-series page: masthead, two-column currency table, footnotes.

## Licence

Source: EUR-Lex legal notice, <https://eur-lex.europa.eu/content/legal-notice/legal-notice.html>,
retrieved 2026-11-27:

> © European Union, 1998-2026
>
> The Commission's document reuse policy is based on Decision 2011/833/EU. Unless otherwise specified,
> you can re-use the legal documents published in EUR-Lex for commercial or non-commercial purposes.

Commission Decision 2011/833/EU, Article 6(1)-(2) (<http://data.europa.eu/eli/dec/2011/833/oj>): documents
"shall be made available for reuse without application", subject to acknowledging the source, not
distorting the original meaning, and the Commission's non-liability. None of the three acts states special
conditions of use. Attribution: © European Union, <https://eur-lex.europa.eu>, 1998-2026. The files are
unmodified.

The OJ C page reproduces the ECB's euro reference rates; the ECB permits reproduction with the source
acknowledged, as the page itself does ("Source: reference exchange rate published by the ECB").

## Files

Retrieved 2026-11-27 from the Publications Office Cellar (the repository behind EUR-Lex): the work was
resolved by CELEX through the SPARQL endpoint <https://publications.europa.eu/webapi/rdf/sparql>, and each
language's PDF/A manifestation downloaded from the URL below. Every file opens with `pdfinfo` and has a
text layer on page 1.

| file | CELEX | lang | format | bytes | sha256 | url |
|---|---|---|---|---:|---|---|
| `eurlex_dir2024_1306_bg.pdf` | `32024L1306` | bg | pdfa2a | 899459 | `30246bc49c2c5e5ba71dc09537aa16d53e769224cc3f669558e867d7a54d5ea5` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0001.01/DOC_1> |
| `eurlex_dir2024_1306_cs.pdf` | `32024L1306` | cs | pdfa2a | 899392 | `22818eeaa42a61c951a6c70082436964bf50727bbcb7f94a7f085ae74dd55282` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0002.01/DOC_1> |
| `eurlex_dir2024_1306_da.pdf` | `32024L1306` | da | pdfa2a | 897919 | `9e08ca23e9a710fa22522b60d565aa7cf7806987fd05b86fe838eb9b846fed0d` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0003.01/DOC_1> |
| `eurlex_dir2024_1306_de.pdf` | `32024L1306` | de | pdfa2a | 899306 | `dae134fcbcdf725fba136c525ab5f125b2ba453e739bdc0294f96d659e51908a` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0004.01/DOC_1> |
| `eurlex_dir2024_1306_el.pdf` | `32024L1306` | el | pdfa2a | 900788 | `1316ddfb323a9ef55dc4432628a3f1d965aa2b40eaeb43eef2935660da957851` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0005.01/DOC_1> |
| `eurlex_dir2024_1306_en.pdf` | `32024L1306` | en | pdfa2a | 896586 | `4537fb9921f52151a0aebcc3d6a5206a6cf79df5c347c50cee08681c5d480816` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0006.01/DOC_1> |
| `eurlex_dir2024_1306_es.pdf` | `32024L1306` | es | pdfa2a | 899574 | `b83f7573db1cce41527648462522f3365490bf29f9fe69717b44ddf81032d201` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0023.01/DOC_1> |
| `eurlex_dir2024_1306_et.pdf` | `32024L1306` | et | pdfa2a | 896728 | `f83ddab29a81d83115fd18f5dbaca307f3d22992c105b64f4678beab758e0349` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0007.01/DOC_1> |
| `eurlex_dir2024_1306_fi.pdf` | `32024L1306` | fi | pdfa2a | 897474 | `87b184803492b9c0990a88705f770ab97ebbd3491e37e628f7cad7e0b47fd668` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0008.01/DOC_1> |
| `eurlex_dir2024_1306_fr.pdf` | `32024L1306` | fr | pdfa2a | 898991 | `f0fbb08768021a79f800340d4db439e5aaa9894b6c0fe951793b7dcced5a2a44` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0009.01/DOC_1> |
| `eurlex_dir2024_1306_ga.pdf` | `32024L1306` | ga | pdfa2a | 899200 | `c7f239df91e29351517cc2fb905dd378f90996982b2e75ed7dd2da8a3ef134f5` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0010.01/DOC_1> |
| `eurlex_dir2024_1306_hr.pdf` | `32024L1306` | hr | pdfa2a | 898074 | `91f91bd813f8daef99a6f397267e058163b6437cb9c444a672c3653d4fc827ef` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0011.01/DOC_1> |
| `eurlex_dir2024_1306_hu.pdf` | `32024L1306` | hu | pdfa2a | 900412 | `7efc3454185b0ef0b8e64362e9fce337c143919312c5e4f628461e74d36ae780` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0012.01/DOC_1> |
| `eurlex_dir2024_1306_it.pdf` | `32024L1306` | it | pdfa2a | 898455 | `4e99d988ab55bb3417d3d6d4eec29b85dc1e41e08a5ef724ba6862f153e94347` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0013.01/DOC_1> |
| `eurlex_dir2024_1306_lt.pdf` | `32024L1306` | lt | pdfa2a | 899506 | `1f7fefe83962c2233cb8fd505fafc34184428d0133c10a3f645124fa4f8f859d` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0015.01/DOC_1> |
| `eurlex_dir2024_1306_lv.pdf` | `32024L1306` | lv | pdfa2a | 898142 | `e37868b0a60f8d931395dbc3ae2cdb09f5c6d5eb44ef9c01f13acb6aed48567f` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0014.01/DOC_1> |
| `eurlex_dir2024_1306_mt.pdf` | `32024L1306` | mt | pdfa2a | 1013817 | `7f0922fb9ac9135980f2932579f60fb02e5e191069125d3b93b94d2114f790ab` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0016.01/DOC_1> |
| `eurlex_dir2024_1306_nl.pdf` | `32024L1306` | nl | pdfa2a | 897948 | `bf23527d352750554a918eb7c6fc0be395e558ded520c0304079de3817d8ac9a` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0017.01/DOC_1> |
| `eurlex_dir2024_1306_pl.pdf` | `32024L1306` | pl | pdfa2a | 901418 | `af34f6ea5d4d58bb56ea7aa2b9d67cc7b67d90de113ec9499749c460381f8fbc` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0018.01/DOC_1> |
| `eurlex_dir2024_1306_pt.pdf` | `32024L1306` | pt | pdfa2a | 898935 | `bbd96e244f4a0b18a675c549259fbb215d32618dcddb4db4b786a5ffd087a0ee` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0019.01/DOC_1> |
| `eurlex_dir2024_1306_ro.pdf` | `32024L1306` | ro | pdfa2a | 900216 | `bbbd8fc7d7f5f422a7e06c3a1a79f98eeee8e77b7dbca7be7d1adc74033c6720` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0020.01/DOC_1> |
| `eurlex_dir2024_1306_sk.pdf` | `32024L1306` | sk | pdfa2a | 899714 | `0312bfe7082f9204d208389fc6368b5da46435acdbfa41c64ed0c9ed8c21ab80` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0021.01/DOC_1> |
| `eurlex_dir2024_1306_sl.pdf` | `32024L1306` | sl | pdfa2a | 897919 | `88430d61f9219d07164ed9e01207e475933d435a043aa6de13260b37a5c63b0a` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0022.01/DOC_1> |
| `eurlex_dir2024_1306_sv.pdf` | `32024L1306` | sv | pdfa2a | 897292 | `106caae56b708a9ee4772fbf9c0c7f55eeb0d40a069b05910d74c48f58b58357` | <http://publications.europa.eu/resource/cellar/28f6136b-0cd4-11ef-a251-01aa75ed71a1.0024.01/DOC_1> |
| `eurlex_reg2024_737_bg.pdf` | `32024R0737` | bg | pdfa2a | 458898 | `536b75493954d5dfe6e5fbc5e07bdc33ae35bcf2d66952c60961c91dd4aea103` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0001.01/DOC_1> |
| `eurlex_reg2024_737_cs.pdf` | `32024R0737` | cs | pdfa2a | 458523 | `a6341ff68ab2b79197495dfc05fe5d0cd4819615a6ba8f0798c95d075dc8295c` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0002.01/DOC_1> |
| `eurlex_reg2024_737_da.pdf` | `32024R0737` | da | pdfa2a | 457614 | `8cdddccc53ef63aa2d5c0957e857928d99f13f6fc94b4b2d53f58bdb7d4d2f5e` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0003.01/DOC_1> |
| `eurlex_reg2024_737_de.pdf` | `32024R0737` | de | pdfa2a | 458415 | `af0b0d3603ff8987d1fd61aafc759c264f74d4c4eb6e51d23db6dc1b628b8fe7` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0004.01/DOC_1> |
| `eurlex_reg2024_737_el.pdf` | `32024R0737` | el | pdfa2a | 459723 | `0f8c7ecf09afed297a0a6efb98a69cdb0aa39b2b7a0ab335ca78e11abb3ca74a` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0005.01/DOC_1> |
| `eurlex_reg2024_737_en.pdf` | `32024R0737` | en | pdfa2a | 457231 | `9daae7c1097cc7e56115c1dbec29202cb16851e15debae6cf86542c7c335cf89` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0006.01/DOC_1> |
| `eurlex_reg2024_737_es.pdf` | `32024R0737` | es | pdfa2a | 459444 | `13a6bcf87ab50adb9a306560c6043f2591ba11c0591cba5b3caabe03638266f1` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0007.01/DOC_1> |
| `eurlex_reg2024_737_et.pdf` | `32024R0737` | et | pdfa2a | 457537 | `1e428ede0b705d095ccd6b6251eea8bb2e132a62d8598f3892a27eb8420bd4b9` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0008.01/DOC_1> |
| `eurlex_reg2024_737_fi.pdf` | `32024R0737` | fi | pdfa2a | 457278 | `65aaf674869bd31c61d659ec4c50c975be2ddd56b51e94da9269c14e032abc85` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0009.01/DOC_1> |
| `eurlex_reg2024_737_fr.pdf` | `32024R0737` | fr | pdfa2a | 459151 | `f88016e1436f90fd9884a6ee3f84476386d172d70c66a43f35eb4cc67016f8b9` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0010.01/DOC_1> |
| `eurlex_reg2024_737_ga.pdf` | `32024R0737` | ga | pdfa2a | 459352 | `eea8a95df7e8f1aa116081419ae06012aee1a1db3bec933f9befd703e253fab6` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0011.01/DOC_1> |
| `eurlex_reg2024_737_hr.pdf` | `32024R0737` | hr | pdfa2a | 457702 | `43f7f75d6dff137974b5ce4f8aeb4019f28e1b201d4ac11bdf9eee6a99c23b55` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0012.01/DOC_1> |
| `eurlex_reg2024_737_hu.pdf` | `32024R0737` | hu | pdfa2a | 459014 | `253442ef22894580f7f1bbf664bcc0ee3a51c9fec794ce00f47d14f434aa16c0` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0013.01/DOC_1> |
| `eurlex_reg2024_737_it.pdf` | `32024R0737` | it | pdfa2a | 458483 | `82b671afde0164ff139255ec23735f8b2004555759decda72d0268415110c6f2` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0014.01/DOC_1> |
| `eurlex_reg2024_737_lt.pdf` | `32024R0737` | lt | pdfa2a | 457855 | `116b566c5e19de58414c4a01100bc7bc975a0bc202f7e130c74736e2ad2f159d` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0015.01/DOC_1> |
| `eurlex_reg2024_737_lv.pdf` | `32024R0737` | lv | pdfa2a | 458041 | `b33950ba019b9b1098457508b9560efdc469963717298d8d9cffc737b045c064` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0016.01/DOC_1> |
| `eurlex_reg2024_737_mt.pdf` | `32024R0737` | mt | pdfa2a | 459488 | `e01e0a4598acbe7b29d6c275f417f639597774f705e4d680711bc35866300362` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0017.01/DOC_1> |
| `eurlex_reg2024_737_nl.pdf` | `32024R0737` | nl | pdfa2a | 458526 | `b81e1f600bc9665de7cc7b7eca6f4032003fa0e298a3216f3ac6444e232dc9b3` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0018.01/DOC_1> |
| `eurlex_reg2024_737_pl.pdf` | `32024R0737` | pl | pdfa2a | 459563 | `8d620d65acea16568e07d48eba6c76545915c600e8f05a3cac64416e1c761281` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0019.01/DOC_1> |
| `eurlex_reg2024_737_pt.pdf` | `32024R0737` | pt | pdfa2a | 459349 | `9631f8d1bee72b7bbb4f8e0c97a35954a723fa92ed6e910caf88cc391ea1b8dd` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0020.01/DOC_1> |
| `eurlex_reg2024_737_ro.pdf` | `32024R0737` | ro | pdfa2a | 458764 | `8a7202bd6dc7c61ca48eec10eb0cb59f4438b2680415178bdd5b60be4a0cdab7` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0021.01/DOC_1> |
| `eurlex_reg2024_737_sk.pdf` | `32024R0737` | sk | pdfa2a | 458891 | `547112acb97f10c341a79c5180540cb4dece7d4d4ea1e64207fef9987308b8d6` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0022.01/DOC_1> |
| `eurlex_reg2024_737_sl.pdf` | `32024R0737` | sl | pdfa2a | 457513 | `4168a7c9efe031c88802198ed8a6544a3b4a3829959daf9f14735a307872ebc8` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0023.01/DOC_1> |
| `eurlex_reg2024_737_sv.pdf` | `32024R0737` | sv | pdfa2a | 457838 | `334986d234f68e199327bb92b2e0c1bf7749ece7ca1475db21233c746a382fd2` | <http://publications.europa.eu/resource/cellar/92495357-d1ec-11ee-b9d9-01aa75ed71a1.0024.01/DOC_1> |
| `eurlex_ojc2024_03243_bg.pdf` | `C/2024/03243` | bg | pdfa2a | 456180 | `e73b51e3c13b8a2d97bab345b2ff2aa60d558e0a1a043b63de2344074555b7fb` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0001.01/DOC_1> |
| `eurlex_ojc2024_03243_cs.pdf` | `C/2024/03243` | cs | pdfa2a | 455767 | `ebd1b2dbbeb82364a0774ec70ffbf7548338a85711b39fd397e2cc456f1bb8ad` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0002.01/DOC_1> |
| `eurlex_ojc2024_03243_da.pdf` | `C/2024/03243` | da | pdfa2a | 454820 | `5c3fd8e0e8b1a3230f4b55371abb4eba813524cb8700dd84f1ae018bb8097889` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0003.01/DOC_1> |
| `eurlex_ojc2024_03243_de.pdf` | `C/2024/03243` | de | pdfa2a | 454917 | `c6e4bfb9012931362e3763f9ea5adb9898367d91c1c4132ee270bc21f037655f` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0004.01/DOC_1> |
| `eurlex_ojc2024_03243_el.pdf` | `C/2024/03243` | el | pdfa2a | 456309 | `f5a2f965844cb8f8e240876c7af7abc2b7d88927583b836e03fb759c934643fc` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0005.01/DOC_1> |
| `eurlex_ojc2024_03243_en.pdf` | `C/2024/03243` | en | pdfa2a | 454980 | `2801f880eee303d66a43e2ce07f1a356add7be0b2e5ffcec8f7671f65a3a03d0` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0006.01/DOC_1> |
| `eurlex_ojc2024_03243_es.pdf` | `C/2024/03243` | es | pdfa2a | 455268 | `896099ab774457991da143fd03a4bc401a8112b65063fde8c95643f659ee527a` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0007.01/DOC_1> |
| `eurlex_ojc2024_03243_et.pdf` | `C/2024/03243` | et | pdfa2a | 454546 | `b2eb6305f665cdc8d0e2e7304585630a4e3c41e62f46cb060cb82c92f06dba1a` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0008.01/DOC_1> |
| `eurlex_ojc2024_03243_fi.pdf` | `C/2024/03243` | fi | pdfa2a | 454527 | `cc8a7045094ddbf72446c757b52681f4fc5b3aee7e606d55e9218b12d78d7a7b` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0009.01/DOC_1> |
| `eurlex_ojc2024_03243_fr.pdf` | `C/2024/03243` | fr | pdfa2a | 455309 | `0cbdd5cf055e0d815c264ad465ef397d88dc1cae20b60cd830369994ea5181c2` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0010.01/DOC_1> |
| `eurlex_ojc2024_03243_ga.pdf` | `C/2024/03243` | ga | pdfa2a | 455769 | `22a7900c76fd57934863d9ea03a64abbf948f35c51e4e6c0aa3c90a4c30bb43e` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0011.01/DOC_1> |
| `eurlex_ojc2024_03243_hr.pdf` | `C/2024/03243` | hr | pdfa2a | 455403 | `8b3405c21592d1678b4fe51c233ce4973ba5c56a812d0467bc0bcd23d31c2759` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0012.01/DOC_1> |
| `eurlex_ojc2024_03243_hu.pdf` | `C/2024/03243` | hu | pdfa2a | 455745 | `45cfe6cfa031a6e757aa600b86ec711fa52ec2a6f75065fe87f65ff235d21c4e` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0013.01/DOC_1> |
| `eurlex_ojc2024_03243_it.pdf` | `C/2024/03243` | it | pdfa2a | 455142 | `6badcf5dd8214c2744e3b36be15ce034c6031fd1c58f69b8f57643ecf59ae330` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0014.01/DOC_1> |
| `eurlex_ojc2024_03243_lt.pdf` | `C/2024/03243` | lt | pdfa2a | 455927 | `7af93b0f964a841edba246e6dcd173428b8c02aba02f4e9ae182a9061f661059` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0015.01/DOC_1> |
| `eurlex_ojc2024_03243_lv.pdf` | `C/2024/03243` | lv | pdfa2a | 455564 | `033a52b6ec8864f41a1ab67606cfbb4616639b7ae797a4182dcb19d2539e568f` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0016.01/DOC_1> |
| `eurlex_ojc2024_03243_mt.pdf` | `C/2024/03243` | mt | pdfa2a | 456133 | `7fad5603639ae31aec1f0695012c3629cbee98a6f530b1d5c9728cbee4dbf098` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0017.01/DOC_1> |
| `eurlex_ojc2024_03243_nl.pdf` | `C/2024/03243` | nl | pdfa2a | 455004 | `5e5f87a9ba4bb6366a2cfd6421dc3f8f07c2571fe5872e478eeabe5c4a032fb3` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0018.01/DOC_1> |
| `eurlex_ojc2024_03243_pl.pdf` | `C/2024/03243` | pl | pdfa2a | 455601 | `f47abde7e988a0db288e77efbba4c0851658e7d13c800d1053387801a7693588` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0019.01/DOC_1> |
| `eurlex_ojc2024_03243_pt.pdf` | `C/2024/03243` | pt | pdfa2a | 454948 | `f44c7a2975460c04bb7956f2b94fd41ce7fd2114d645b33421b3db5bf49225d5` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0020.01/DOC_1> |
| `eurlex_ojc2024_03243_ro.pdf` | `C/2024/03243` | ro | pdfa2a | 455786 | `e13b36c2fd9a0d8cce7785335f9e2be57ddec755cef3078f18a97e58f46e54d3` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0021.01/DOC_1> |
| `eurlex_ojc2024_03243_sk.pdf` | `C/2024/03243` | sk | pdfa2a | 455711 | `facaadfff2d242300ea8a6d85a9f97000e6cd4b4ffe6081cd5b44c5a84847840` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0022.01/DOC_1> |
| `eurlex_ojc2024_03243_sl.pdf` | `C/2024/03243` | sl | pdfa2a | 455303 | `407fbba8ba0a5322f249ce766533471fd14df2596163641aad8879b8b9145476` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0023.01/DOC_1> |
| `eurlex_ojc2024_03243_sv.pdf` | `C/2024/03243` | sv | pdfa2a | 454823 | `b9e65bb4be7fb6111cf344cbc9f8fe9fe38dabea35eac63078ed643ea30da089` | <http://publications.europa.eu/resource/cellar/892d0188-220a-11ef-a251-01aa75ed71a1.0024.01/DOC_1> |
