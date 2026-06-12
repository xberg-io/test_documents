# HEIF / HEIC / AVIF fixtures — CC-BY-SA-4.0

The following files in this directory were copied verbatim from the upstream
`libheif-rs` repository at <https://github.com/Cykooz/libheif-rs/tree/master/data>
under the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).

Attribution: Kirill Kuzminykh (Cykooz) and the libheif-rs contributors.

| File              | Upstream name        | Notes                                       |
| ----------------- | -------------------- | ------------------------------------------- |
| `test.heic`       | `test.heic`          | 8 bpc HEIC, HEVC-encoded primary image      |
| `test.heif`       | `test_nclx.heif`     | HEIF with NCLX color profile                |
| `test.avif`       | `test_nclx.avif`     | AVIF with NCLX color profile                |
| `alpha.heif`      | `alpha.heif`         | HEIF with alpha channel                     |

These fixtures back the integration tests for `kreuzberg-libheif` (the vendored
libheif bindings) and `kreuzberg` (HEIC → PNG → OCR pipeline). The kreuzberg
codebase contains no HEIC/HEIF/AVIF binaries of its own — everything lives here
in `test_documents`.
