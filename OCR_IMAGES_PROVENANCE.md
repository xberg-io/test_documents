# OCR image fixtures: provenance

Per-file provenance for the real-ground-truth OCR images added on 2026-11-27. Licences and citations are in
`ATTRIBUTIONS.md`. Ground truth sits beside the other image GT in `ground_truth/jpg/<stem>.{txt,md}`.

## CORD (`cord_receipt_05..20`)

CC BY 4.0. Source: <https://huggingface.co/datasets/naver-clova-ix/cord-v2>, revision `7f0115a4b758a71d6473b8d085751692da2fef98`,
file `data/test-00000-of-00001-9c204eb3f4e11791.parquet` (sha256
`51c65f1788faff392abe2a0b55b023eb23e9be551c509138eaa3a832514224e7`). Each image is the row's PNG re-encoded to
JPEG with Pillow at quality 92, the encoding that reproduces `cord_receipt_01..04` (test image_id 0..3)
byte for byte. GT follows those four: txt has one line per menu `valid_line` and one per physical row
otherwise; md renders menu items as one table, key/value rows as a two-column table, and rows without a key
word as paragraphs. Annotation typos fixed after checking the image: 07 `CUS ARD` -> `CUSTARD`, 17
`IVANGGO`/`IVINERAL` -> `MANGGO`/`MINERAL`, 19 `Tofal` -> `Total`.

| file | split / image_id | size | bytes | sha256 |
|---|---|---|---:|---|
| `images/cord_receipt_05.jpg` | test / 4 | 864x1296 | 189267 | `79b54396275903de63ce685e6f6b61864c73e4ed5fbba93f3372cd12edfdaa46` |
| `images/cord_receipt_06.jpg` | test / 5 | 2304x4096 | 737767 | `e3f6bba29523e7e583292fcfd1b23a81bdbe9e54bcbacb7b21b945c9ab137495` |
| `images/cord_receipt_07.jpg` | test / 6 | 864x1296 | 306676 | `7d235fedf882557bb76772f1285ca22b55c6e389fffd01c1b3a1c5c8e19d43d8` |
| `images/cord_receipt_08.jpg` | test / 7 | 576x864 | 161826 | `9673171039b21b059c3bb8b336567d497be303fb70d23ee1b52bdf090522af26` |
| `images/cord_receipt_09.jpg` | test / 8 | 864x1296 | 265487 | `00e563de71c34ea43bf673253692848e04a7c3ffc1605b4f35b5eaf2482c2706` |
| `images/cord_receipt_10.jpg` | test / 9 | 576x864 | 109666 | `6ded2d0401278a27b235d993f42e896886d28f82df074ae60c9f9accd419b59b` |
| `images/cord_receipt_11.jpg` | test / 10 | 576x864 | 96287 | `a32452857114062651e9ccb8c865bcb7eeb1b9da51058bf69ed67ef2b594b514` |
| `images/cord_receipt_12.jpg` | test / 11 | 576x864 | 174974 | `2632b194eda48a223bcf73c5cf839aaa21e001fe47e1973ac3395400a7ac3fd9` |
| `images/cord_receipt_13.jpg` | test / 12 | 576x864 | 94865 | `0e26d34d8f51b1a8eacfdfafd82d184303ff42b5f6e3a1cc7e81662485c5aaa0` |
| `images/cord_receipt_14.jpg` | test / 13 | 864x1296 | 204871 | `85fbfc8683917238dcfb12fa614e024ed241697a4fca0d3e0fd9fa214c0046a2` |
| `images/cord_receipt_15.jpg` | test / 14 | 1836x3264 | 340715 | `14c16f270466d903199ad1103a99b033935c7825450cda613fe9e89bbff2cb1b` |
| `images/cord_receipt_16.jpg` | test / 15 | 576x864 | 119009 | `57566da33adb2f2eb9d10f73627681a743e9acc1b026415df2b2068b07b3a965` |
| `images/cord_receipt_17.jpg` | test / 16 | 864x1296 | 244850 | `bde0ae19a4a5081510870e0ce8d4e44bb7db6c9fe52e739c9c1c9140fba44e9f` |
| `images/cord_receipt_18.jpg` | test / 17 | 960x1280 | 165099 | `e7b7a8ca019dd0fa7ad2ae8c87faa0de7fe6b6bbc4151b4cbfbdb74a15db866a` |
| `images/cord_receipt_19.jpg` | test / 18 | 576x864 | 116211 | `6b6e4735cc14c9225ad5bb8d7edb9ac39db4d329dae7582f1b3cb32275068fb2` |
| `images/cord_receipt_20.jpg` | test / 19 | 576x864 | 86299 | `752dfab25a9e47ffd9c982ffb1051b780e177a9b8810f8b721a7c5bf66869b1f` |

## NDL (`ndl_meiji_vertical_06..20`, `ndl_horizontal_01..05`)

Public Domain Mark 1.0, per the official NDL repository <https://github.com/ndl-lab/pdmocrdataset-part1>.
Source archive: <https://lab.ndl.go.jp/dataset/pdm_ocr_dataset/line/tosho_all_linejson.zip> (5,177,184,446
bytes, last-modified 2022-04-20, ETag `653709611ad0186303312a7b75339e26-302`); members were read with HTTP
range requests, so the archive itself was not hashed. Images are the archive's JPEG bytes, unmodified; GT is
built from the matching `json/<decade>/<id>.json` line boxes.

Selection (seed 20261127): vertical pages from the 1870s–1900s (Meiji era) with at least 98% vertical boxes,
20–60 boxes, at least 600 characters and at least 75% of boxes 10+ characters long, i.e. running prose rather
than tables; two per decade/subject class, 15 kept. Horizontal pages from the 1920s onward with at least 95%
horizontal boxes. Vertical GT: boxes grouped into columns by horizontal overlap (boxes in one column must not
overlap vertically), columns right to left, boxes top to bottom, concatenated. This reproduces
`ndl_meiji_vertical_02..04` exactly; 01 and 05 have tables whose existing GT was ordered by hand. Horizontal GT:
page blocks left to right, rows top to bottom, boxes in a row left to right.

| file | archive member | bytes | sha256 |
|---|---|---:|---|
| `images/ndl_meiji_vertical_06.jpg` | `tosho_1870_bunkei/753057_R0000294.jpg` | 1750737 | `a62725c35ff954165ae05becf27f9ed4e8597cc0317c75ae00bc2f59f5a6085e` |
| `images/ndl_meiji_vertical_07.jpg` | `tosho_1870_bunkei/753057_R0000325.jpg` | 1631801 | `66ed855ceef8dacfc317cb6226c5e727c7b708a929413373376f832f6f6e93f4` |
| `images/ndl_meiji_vertical_08.jpg` | `tosho_1870_rikei/829033_R0000003.jpg` | 2956365 | `9a437efc16e8c8d0a641f2e7b1523105149bc820b239db4ed5b38b229eb3ee07` |
| `images/ndl_meiji_vertical_09.jpg` | `tosho_1880_bunkei/766938_R0000476.jpg` | 1996178 | `40f9fb0f27abd273e6fcb4bc039603125a98a9476ee220ad8c5b89afd06f996b` |
| `images/ndl_meiji_vertical_10.jpg` | `tosho_1880_bunkei/783460_R0000086.jpg` | 2553194 | `e0c69aab15c99f4fb48adaa0300da5497e2b31a501fbf2cae4c96087d30e7f40` |
| `images/ndl_meiji_vertical_11.jpg` | `tosho_1880_rikei/831426_R0000013.jpg` | 1417909 | `ec7b2922114c379aa42e8cd78cdb660d89fac9428a9d503ba65453321c6b4fba` |
| `images/ndl_meiji_vertical_12.jpg` | `tosho_1880_rikei/834959_R0000029.jpg` | 2026688 | `3706231a97788e883b7b6d517fdbcf5e63c2eca2d112f36dad93713ba043c7e2` |
| `images/ndl_meiji_vertical_13.jpg` | `tosho_1890_bunkei/789269_R0000146.jpg` | 2542619 | `59c4bf9754a281999565364a2038e8a0634fc5e2055c43c6c9b0d95e77d5a3ad` |
| `images/ndl_meiji_vertical_14.jpg` | `tosho_1890_bunkei/790039_R0000125.jpg` | 1651039 | `6ad8c2527879ff05b3464a52247bfcd051929b7ac3300a0d7edf1032590a241f` |
| `images/ndl_meiji_vertical_15.jpg` | `tosho_1890_rikei/801956_R0000096.jpg` | 3142409 | `17fb6d33579ac307e4a694731bec96576c391a349faf098fb9e315226226b629` |
| `images/ndl_meiji_vertical_16.jpg` | `tosho_1890_rikei/802977_R0000113.jpg` | 3064455 | `3c8bcd3f2aed06f9a91d1715f93cb8590411d3a10c7bf5f121f3d54e15863b2b` |
| `images/ndl_meiji_vertical_17.jpg` | `tosho_1900_bunkei/2937434_R0000183.jpg` | 5031850 | `f04f07795ac04cabb707557ea9e07d3bf8b181486efb8ff37bfa46ee98cf42fb` |
| `images/ndl_meiji_vertical_18.jpg` | `tosho_1900_bunkei/800415_R0000123.jpg` | 3712801 | `59e4854c15fe48f2b7dcfc64bfc3235168344e94dee35d58d1a37c8c495f9cf0` |
| `images/ndl_meiji_vertical_19.jpg` | `tosho_1900_rikei/803274_R0000194.jpg` | 3414633 | `5e9cb233793a039c62c724ffdcc16cdfb6ad26546614420f33a274108c851a60` |
| `images/ndl_meiji_vertical_20.jpg` | `tosho_1900_rikei/804129_R0000195.jpg` | 2756481 | `914a0b5a181cdd9d9b2aba407ca2ee86ebbeba08b72a84f7a557b43d1325b6b6` |
| `images/ndl_horizontal_01.jpg` | `tosho_1920_rikei/931126_R0000253.jpg` | 888410 | `88fed5082e8ecdd99669408094ea185a5d13355e3bc1a375c87b7d4dc1c6eee5` |
| `images/ndl_horizontal_02.jpg` | `tosho_1920_rikei/931473_R0000012.jpg` | 1373738 | `4fb736c84755b6d570ad697e5f35661c1b55cdf170e3cadb8c12d10eb0340068` |
| `images/ndl_horizontal_03.jpg` | `tosho_1920_rikei/935831_R0000176.jpg` | 979659 | `9d7b154db456f947844e76f902346b8466fa152041bf7709258afd7a7dc57ebf` |
| `images/ndl_horizontal_04.jpg` | `tosho_1920_rikei/960174_R0000077.jpg` | 1325693 | `f253ab151c446e33e758e12779394921bc3a8b681a5df7d3ac9670f4a2b52438` |
| `images/ndl_horizontal_05.jpg` | `tosho_1920_rikei/961155_R0000112.jpg` | 1110572 | `02c794946af4e1d136131a7fc02ea37882c6e7f9ceb9bda3f36a12b250e200be` |
