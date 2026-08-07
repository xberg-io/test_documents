# Real-GT OCR image slice — provenance and ground-truth review

This slice adds 14 image-OCR fixtures whose ground truth comes from **human/authoritative upstream
annotations** (not model-generated), to replace the model-generated (`mistral-pixtral`) GT in the
`ocr-images-fast` benchmark cohort. All datasets here are permissively licensed ("vendor" class per
`../LICENSES.md`); source images and derived GT are committed. SHA-256 values pin the exact reviewed
bytes. GT is the upstream human text linearized into reading order — word strings are verbatim,
nothing is fabricated. Each image ships both `ground_truth/jpg/<name>.md` (GFM) and
`ground_truth/jpg/<name>.txt` (raw text); for these OCR fixtures the content is plain linear text with
no markup, so the two are byte-identical — the split lets the harness score OCR text-F1 (`text_file`)
separately from structural SF1 (`markdown_file`).

**Excluded on license grounds:** HierText (Google, CC-BY-SA-4.0) images were prepared but are **not
committed** — ShareAlike falls in the non-committed "reference" class per `../LICENSES.md`. It remains
a documented reference source (see the LICENSES table) for non-redistributing local use only.

## NDL PDM OCR Dataset — vertical Japanese (Public Domain Mark 1.0)

Upstream: `ndl-lab/pdmocrdataset-part1`, archive `tosho_all_linejson.zip`. GT basis: NDL's human
line-level `text` boxes concatenated in vertical reading order (columns right-to-left, top-to-bottom).
Historical Meiji–Shōwa printed pages — a permissive real-GT source for vertical (tategaki) Japanese;
note the era stresses typography/variant kanji.

- `images/ndl_meiji_vertical_01.jpg` — SHA-256 `94e6cf1b5beb9219c17d0a161dbd064e454c6deb823b1db14207ab063be3a155` · upstream `tosho_1910_bunkei/1087303_R0000196`.
- `images/ndl_meiji_vertical_02.jpg` — SHA-256 `8c0324d53abb0a606738eb4ca06e987f66340b10ac28c90e28ccb44456fa1aef` · upstream `tosho_1900_bunkei/1079343_R0000058`.
- `images/ndl_meiji_vertical_03.jpg` — SHA-256 `8e932769b789ad3da818135e22741776d0f693b39981cfa9cdea785004fcd1a1` · upstream `tosho_1880_rikei/1081846_R0000242`.
- `images/ndl_meiji_vertical_04.jpg` — SHA-256 `195f9a8f6630227cd98cea1a79cc0b60c3ef74b4c54d8f066b9245adb446f328` · upstream `tosho_1930_bunkei/1036227_R0000118`.
- `images/ndl_meiji_vertical_05.jpg` — SHA-256 `0fe6353204e4ee5ca6d93cfe90cce51b95c94e4ce9c0a0e06f2dd33e0d2635f3` · upstream `tosho_1870_bunkei/1151978_R0000060`.

## CORD — receipts (CC-BY-4.0)

Upstream: `naver-clova-ix/cord-v2`, `test` split. GT basis: human `valid_line` word `text` joined in
reading order (lines top-to-bottom, words left-to-right). Images re-encoded JPEG q92 from the dataset
PIL image.

- `images/cord_receipt_01.jpg` — SHA-256 `7281a7b76327ed77867b20432717f1046bb8ab91371a80fac376ab45ccbf04f9`.
- `images/cord_receipt_02.jpg` — SHA-256 `ce405c567deaaec169b6700d758bcd3bb44a355c35af022f721a975f274a9f4f`.
- `images/cord_receipt_03.jpg` — SHA-256 `95b97f197b17c471988759c0e039a792b6eca5636dca85204c8ef4d19e04cd05`.
- `images/cord_receipt_04.jpg` — SHA-256 `c300405986f1a12bb714a1eb035179ff3c9b280ae93dba9ba2beb75e5094ce16`.

(CORD upstream per-row ids were not recorded; these are the first four qualifying receipts of the
streamed `test` split. GT is verbatim from each row's `ground_truth.valid_line`.)

## TextOCR — scene text (CC-BY-4.0)

Upstream: TextOCR (Meta), annotations `TextOCR_0.1_val.json`, images from TextVQA/Open Images
(`train_val_images.zip`, extracted via HTTP-range partial-zip). GT basis: human word `utf8_string`
values grouped into lines by geometry, concatenated in reading order; JPEG q90.

- `images/textocr_scene_01.jpg` — SHA-256 `14e051506881064812bd952e2abe5f6570790711d9dbf24b65ad873544a7bc29` · upstream image_id `e6c1a7b56123bbdb`.
- `images/textocr_scene_02.jpg` — SHA-256 `27c84ed9d5405d6b90890d5a9f8dce93e875d94661a87cac0f811865905df954` · upstream image_id `76f940b2603a49e7`.
- `images/textocr_scene_03.jpg` — SHA-256 `fad13da4cce41d7de954914bf5952b67eebb9e63b035160a7fe61a2726c8a620` · upstream image_id `855d76c85603018d`.

## DocLayNet — financial-report pages (CDLA-Permissive-1.0)

Upstream: `ds4sd/DocLayNet-v1.1`, `test` split. GT basis: DocLayNet's authoritative PDF text cells
linearized in reading order (top-to-bottom, then left-to-right within a line band). No OCR/model used.

- `images/doclaynet_page_01.jpg` — SHA-256 `cd74a2f31169a464ef883150ac70be2dd614ac7718ec0e233446794b9f819629` · upstream `NASDAQ_ATRI_2003.pdf` page 24.
- `images/doclaynet_page_02.jpg` — SHA-256 `0c76bd1ee2cea37f3a2c15f4b0a2fb2208fa3caca58c8f93f139c63ebc5af11a` · upstream `NYSE_MGM_2004.pdf` page 49. Note: its GT includes a stylized-signature graphic's embedded PDF-cell text ("Messe # Fon Cage") — DocLayNet's authoritative cell text, preserved verbatim, not an OCR error.
