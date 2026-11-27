# Reference OCR fixtures (private bucket)

Licence-restricted OCR fixtures that must stay out of git and out of the public `xberg-test-documents`
bucket. Only this note, the pattern file and the lock (paths, sha256, sizes) are committed. The bytes live in
the private bucket `gs://xberg-benchmark-corpus` under `objects/<sha256>`, published and fetched with the
corpus tooling's private-corpus mode into the gitignored `.reference-ocr-cache/`, which the public publisher
refuses to enumerate.

```sh
python3 scripts/fetch_corpus.py --manifest reference_ocr/corpus.lock.json --root .reference-ocr-cache \
  --bucket xberg-benchmark-corpus --auth
python3 scripts/publish_corpus.py --bucket xberg-benchmark-corpus --root .reference-ocr-cache \
  --manifest reference_ocr/corpus.lock.json --patterns reference_ocr/corpus-patterns.txt
```

Fetching needs read access to the bucket (Application Default Credentials). Use is limited to
non-commercial benchmarking of the open-source library, per `LICENSES.md`; nothing here may be
redistributed.

## XFUND (`images/xfund_<lang>_01..20.jpg`)

- **Source:** <https://github.com/doc-analysis/XFUND>, release `v1.0`, `val` split, retrieved 2026-11-27.
- **Licence:** CC BY-NC-SA 4.0 (<https://creativecommons.org/licenses/by-nc-sa/4.0/>). Repository README: "The
  content of this project itself is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International
  (CC BY-NC-SA 4.0)". Non-commercial and ShareAlike, so `reference` class.
- **Citation:** Xu et al., "XFUND: A Benchmark Dataset for Multilingual Visually Rich Form Understanding",
  Findings of ACL 2022.
- **Content:** form templates into which "human annotators manually fill synthetic information" (LayoutXLM
  paper, arXiv:2104.08836), not real personal records.
- **Selection:** the first 20 documents of each language's `val` split by file index (`<lang>_val_0..19`).
- **Images:** the release zip's JPEG bytes, unmodified.
- **Ground truth:** `ground_truth/jpg/xfund_<lang>_NN.{txt,md}`, identical text: every annotated entity's
  `text` (human transcription), entities grouped into visual lines by vertical overlap, lines top to bottom,
  entities left to right, joined by one space. Derived from CC BY-NC-SA annotations, so held under the same
  licence in the private bucket.

### Release assets

| asset | url | sha256 |
|---|---|---|
| `de.val.json` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/de.val.json> | `c51f7b1de2622ec404ac46a457bcf3dad57894df45962b3a2b23608a66c9f230` |
| `de.val.zip` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/de.val.zip> | `13dd9929bf6854a4c6a97889c277358b803609043a1e35335a8e2a1ac3f3eccc` |
| `es.val.json` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/es.val.json> | `780acc900d7996210819ed4a205b32f64bc0e4ee3d1088de0e8e67fa7fe4139d` |
| `es.val.zip` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/es.val.zip> | `8c0994e9132396d80175da9261dba5c3cb4f8083139b92c02bd30b4e5401aa0c` |
| `fr.val.json` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/fr.val.json> | `67f031aff9be4df9563dd3ef820e95ef9e62a25b8a6b1a22b4f247c60ea2356c` |
| `fr.val.zip` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/fr.val.zip> | `596857f8b51ed827b0c7ef2160eeb05bfd3cf15de9edc9e53ef547834e8f39b0` |
| `it.val.json` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/it.val.json> | `3a3d505790607b7cf3e2c581c29ba317abec9a4059f04f378cbb8c3fba47bb7a` |
| `it.val.zip` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/it.val.zip> | `4e2232d9abb562bbd2b394cf8a2932ceda20f7402eeb61a7ef65859bbead9d16` |
| `ja.val.json` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/ja.val.json> | `fd92f2482abbd3987ea56a944768e457da70ae909dee1e4121698ed76f5bd01f` |
| `ja.val.zip` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/ja.val.zip> | `ede7df922809e2675965a513002c4cc24132e5c5df6770331e1496a46f4954cd` |
| `pt.val.json` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/pt.val.json> | `10fd07ef1d9f66b0d72e55cb329a0172eee408d62e6f1dd271e1ff1a95a06c7b` |
| `pt.val.zip` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/pt.val.zip> | `4c50146dfa75afa3dcacf4c850fb54359bf28e221ffb779eb4957c4d226535f6` |
| `zh.val.json` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/zh.val.json> | `b11140881255916a16670ea5006295d0185b8376287aa4aa76ae4e1107f61e3d` |
| `zh.val.zip` | <https://github.com/doc-analysis/XFUND/releases/download/v1.0/zh.val.zip> | `a30e6e5c274ea8236c9b00c46ab96d59829a5bcd08baee966fa433028b644456` |

### Files

| file | lang | source | size | bytes | sha256 |
|---|---|---|---|---:|---|
| `images/xfund_zh_01.jpg` | zh | `zh_val_0.jpg` | 2480x3508 | 1615174 | `4636f88abc9c7ad301d438eb4325ea2653c34779bcab2f2a8cdc22ff3c85fd81` |
| `images/xfund_zh_02.jpg` | zh | `zh_val_1.jpg` | 2480x3508 | 1851132 | `f636f02d1d653a2c05ac5b04cafb25cd45aadf7c7a8172333c419987dba04147` |
| `images/xfund_zh_03.jpg` | zh | `zh_val_2.jpg` | 2480x3508 | 1282565 | `65367f49bbc348a085f2f862b0bae21650d2d73da5aeb00f6108719895c27a28` |
| `images/xfund_zh_04.jpg` | zh | `zh_val_3.jpg` | 2480x3508 | 1188355 | `2a1f0df4e404c8352e348b20018e97168f5e4fe92d770bf97df030b1ac82ab10` |
| `images/xfund_zh_05.jpg` | zh | `zh_val_4.jpg` | 2480x3508 | 760745 | `290685942ccdb28e568ab8df867c17b698dbb4de65ab3bbe1ed6770353a370dc` |
| `images/xfund_zh_06.jpg` | zh | `zh_val_5.jpg` | 2480x3508 | 1008439 | `ac085617d2fc5f3f4c767d8da972c05088f98fe6fa23f625457459f9affe4644` |
| `images/xfund_zh_07.jpg` | zh | `zh_val_6.jpg` | 2480x3508 | 1461207 | `0b5388e99f0e7b0b9dd576f294b639e523c11907df9ce135fd6723cfae501fe1` |
| `images/xfund_zh_08.jpg` | zh | `zh_val_7.jpg` | 2480x3508 | 1132362 | `89e5bd27f20c32925078395df514b7228a00e910b0af5de63c7bfc6e2ee6904d` |
| `images/xfund_zh_09.jpg` | zh | `zh_val_8.jpg` | 2480x3508 | 1680053 | `6f8b99ca280e8cf307176af0b7cf66aa62031b5d58c7ec8330c44d55d5203295` |
| `images/xfund_zh_10.jpg` | zh | `zh_val_9.jpg` | 2480x3508 | 1217983 | `fe1a95b6967e588dfad2f928836e421f9836cd39e816c363989f20a89f87a4c0` |
| `images/xfund_zh_11.jpg` | zh | `zh_val_10.jpg` | 2480x3508 | 1216246 | `d6f710f74e5a864a8d4069341459c3d009998afe39b1605558827979703dbd08` |
| `images/xfund_zh_12.jpg` | zh | `zh_val_11.jpg` | 3508x2480 | 895003 | `bae9ebbca3b649065de80d92a3b50b35c51137996e36e4d0558baa2493ef5465` |
| `images/xfund_zh_13.jpg` | zh | `zh_val_12.jpg` | 3508x2480 | 1167459 | `34d390c5758bca60204a5747936e480fbc1f1b4b9d6e4b00ac848282876aa4af` |
| `images/xfund_zh_14.jpg` | zh | `zh_val_13.jpg` | 2480x3508 | 793343 | `70d1a929fe6483c70137bbd5865c30616d9043db5c36d7db9bd5293fc454bd97` |
| `images/xfund_zh_15.jpg` | zh | `zh_val_14.jpg` | 2480x3508 | 1417724 | `fca9b52ccfad52d40df4b67365319df0db39e64ab0d4b0b0c23cf429290160c3` |
| `images/xfund_zh_16.jpg` | zh | `zh_val_15.jpg` | 2480x3508 | 1388832 | `1893e04e87f62965e88b5e40180e24e65eaa98184fe84e87c1856da889ffbad1` |
| `images/xfund_zh_17.jpg` | zh | `zh_val_16.jpg` | 2480x3508 | 1213778 | `434759681abf2ec525f840431f46842e221132d3e92e9f0953f969ac1764a5ec` |
| `images/xfund_zh_18.jpg` | zh | `zh_val_17.jpg` | 2480x3508 | 920114 | `6e4d418ca8bdd7e28c7d474c3d7f39ffb87a50fc457530f5f3e105a6273acb2d` |
| `images/xfund_zh_19.jpg` | zh | `zh_val_18.jpg` | 2480x3508 | 1604952 | `eb7c1711451ad6ce3fbc338054fd1f0c115252fba5c5e59d0d7fbd6343afdc80` |
| `images/xfund_zh_20.jpg` | zh | `zh_val_19.jpg` | 2480x3508 | 964172 | `29b4bcac5097c9610304bdb5906ff0aabe8b96929ce0f280cc7f22cf07c8ed6c` |
| `images/xfund_ja_01.jpg` | ja | `ja_val_0.jpg` | 3507x2550 | 848585 | `735863af44c005079919f7ec803f9120e48dfd2291913b6a592fc7462d7dd417` |
| `images/xfund_ja_02.jpg` | ja | `ja_val_1.jpg` | 2480x3508 | 608333 | `eea095bb875313b19101f461c200d1f4df17bb2444125c3997ff5eb0e5d8355a` |
| `images/xfund_ja_03.jpg` | ja | `ja_val_2.jpg` | 2480x3508 | 519629 | `65321f14d1030baf24195fa2c272c4edf8f71bbd8bf6083666447548776109aa` |
| `images/xfund_ja_04.jpg` | ja | `ja_val_3.jpg` | 2480x3508 | 335154 | `3927737bf6508d25141f4dbee70778a3498e49bcc343fad342952b09941bdfef` |
| `images/xfund_ja_05.jpg` | ja | `ja_val_4.jpg` | 2480x3508 | 740765 | `34bfbc71064f25757f50460b881eee79737308d7c84a1bf59fc55d93132e8f28` |
| `images/xfund_ja_06.jpg` | ja | `ja_val_5.jpg` | 2480x3508 | 413095 | `ac4386cd6099e932c2d316c1e636bbbc31940074137e0fc9d573e27661c85680` |
| `images/xfund_ja_07.jpg` | ja | `ja_val_6.jpg` | 2480x3508 | 365389 | `0a603851134271356aa267b89fc099f563c98bbc96681b7b80cee94fea04f403` |
| `images/xfund_ja_08.jpg` | ja | `ja_val_7.jpg` | 2480x3508 | 700222 | `7e48d940c5fccee17f91157a760681dd79e23df5633b65680b01bb90648e7017` |
| `images/xfund_ja_09.jpg` | ja | `ja_val_8.jpg` | 2480x3508 | 560025 | `6fc4402eb30c3925d7334303e4cd7110a3a00df87ee1f3e79cfc25edddd38fd5` |
| `images/xfund_ja_10.jpg` | ja | `ja_val_9.jpg` | 2480x3508 | 301350 | `fadf9d834c60e415ded71cd595c42cce4bbf3fff00fa2634de307dac7bad0d77` |
| `images/xfund_ja_11.jpg` | ja | `ja_val_10.jpg` | 2480x3508 | 662994 | `cca1b901d87bb376ddbe3df10d16e36e95199d4d70af33ccac38acc4125395b3` |
| `images/xfund_ja_12.jpg` | ja | `ja_val_11.jpg` | 2480x3508 | 393529 | `3259423fbe2e5ede3dc42470716b75b1aedb969df14d7e6ace59e7917f41c8b6` |
| `images/xfund_ja_13.jpg` | ja | `ja_val_12.jpg` | 2480x3508 | 705560 | `4a7d9171cdb98273168dc02aad7785dc5cae0806aca27a758cc96cd1407f2235` |
| `images/xfund_ja_14.jpg` | ja | `ja_val_13.jpg` | 2480x3508 | 392886 | `7003f2f477cf659495852431dd67fb23545d859628c960201f0ba77c55bbb3a4` |
| `images/xfund_ja_15.jpg` | ja | `ja_val_14.jpg` | 2480x3508 | 828086 | `faac18a2311a250abe43c9635ed76a1e079b2014bb9443066e73b36ce419c27b` |
| `images/xfund_ja_16.jpg` | ja | `ja_val_15.jpg` | 2480x3508 | 327158 | `0fac7c1f9d87b4e16a135b41eeec79b89c292c1bc49e1a9f6649aa8e12aa2542` |
| `images/xfund_ja_17.jpg` | ja | `ja_val_16.jpg` | 3507x2550 | 5487333 | `5f15d3fdf1444d48c51a1a334f08598dfb9fe4deec14c49a2220df5650da7c78` |
| `images/xfund_ja_18.jpg` | ja | `ja_val_17.jpg` | 2480x3508 | 820241 | `6edd1475f9418d5f35b3a377f7a60fc7537cc8cbb1d803ef2b362f4f23ce47c3` |
| `images/xfund_ja_19.jpg` | ja | `ja_val_18.jpg` | 2480x3508 | 566824 | `e3769bc71d5fd8be58bb21fe5ed3cac259ac72c122f73261ae15265ef44fc366` |
| `images/xfund_ja_20.jpg` | ja | `ja_val_19.jpg` | 2550x3507 | 598120 | `38a408e21e6867d343edd07d98109f1f6ca5f58628f732988debe49624a1805c` |
| `images/xfund_es_01.jpg` | es | `es_val_0.jpg` | 2480x3508 | 1006701 | `50c1a2bc117d9087c7e9b8bfbbee0dad1362f9bfe44cfd604ad52cfc25bb6496` |
| `images/xfund_es_02.jpg` | es | `es_val_1.jpg` | 2480x3508 | 2240370 | `6391e9616ad6b7535b8710713717492190a7263d6cd80d3254531a58d8804bbb` |
| `images/xfund_es_03.jpg` | es | `es_val_2.jpg` | 2480x3508 | 938365 | `395884d9cbdd4ab3b381b4debd8e7669c19625a4f942821cea267e48d0a79022` |
| `images/xfund_es_04.jpg` | es | `es_val_3.jpg` | 2480x3508 | 1239553 | `299c1e0c73a80ee4a20c041376fab2865ca729c8ec7b6e127dae1c2dc49356dc` |
| `images/xfund_es_05.jpg` | es | `es_val_4.jpg` | 2480x3508 | 663172 | `f88aaa4b3ad7bccf00f17d9e9e2f7c59aee22762c1944784f8d21420ebd331a6` |
| `images/xfund_es_06.jpg` | es | `es_val_5.jpg` | 2480x3508 | 1328972 | `45067c13051d520ab81df9202625ac5d04219e57ff1df5de5d093f9e6504582f` |
| `images/xfund_es_07.jpg` | es | `es_val_6.jpg` | 2480x3508 | 2291802 | `4f269f8c77afa7c608334b821402db781f82dfd8d3f97db906c795f19e98e582` |
| `images/xfund_es_08.jpg` | es | `es_val_7.jpg` | 2480x3508 | 2206963 | `2c3dead9e0226a50fc02f72d53cb78e494d06192d594ed1c1cf6ff2f1b7b355e` |
| `images/xfund_es_09.jpg` | es | `es_val_8.jpg` | 2480x3508 | 2531811 | `ac45598776f7456a010e8e30fd05bcf18797d5279becc84a7f399fa2674bc81e` |
| `images/xfund_es_10.jpg` | es | `es_val_9.jpg` | 2480x3508 | 1625274 | `fde97eea2d987bf3c2371ad16b588d780738eaa76944c2cdbb41a626b0cf0950` |
| `images/xfund_es_11.jpg` | es | `es_val_10.jpg` | 2480x3508 | 1303592 | `31188a05e69dbf39cb09b6c0a7e1305144d6704d00dae81cf8924500cd380d5b` |
| `images/xfund_es_12.jpg` | es | `es_val_11.jpg` | 2480x3508 | 1851215 | `5345c4c417293177b236ec0cdfda89553c1eb1986778e3cb4f45e593dd3954cb` |
| `images/xfund_es_13.jpg` | es | `es_val_12.jpg` | 2480x3508 | 1458951 | `eb4bc66b4fad916c79e64f8455f5b79bdc527234fb20377d79d857b379ca932a` |
| `images/xfund_es_14.jpg` | es | `es_val_13.jpg` | 2480x3508 | 1304602 | `5b5fd1858b608307cd4aca23a3116a09631213f9b60aca1c362778ceb6adf2e9` |
| `images/xfund_es_15.jpg` | es | `es_val_14.jpg` | 2480x3508 | 2102715 | `5059340c7319ab58852b5c2e55f686712f3f822e38604f11c9e8513bb7bb0b44` |
| `images/xfund_es_16.jpg` | es | `es_val_15.jpg` | 2480x3508 | 1183945 | `8b51ef978ae5cd126b1741c17308c213bbe7d3af3c26860f747cf53a9c5c5bc9` |
| `images/xfund_es_17.jpg` | es | `es_val_16.jpg` | 2480x3508 | 1337045 | `37604406f2bc2468d68dbaaebce1c539cf3af0c70e11a42e5ff7948338d4730b` |
| `images/xfund_es_18.jpg` | es | `es_val_17.jpg` | 2480x3508 | 937128 | `08044b7d3e4aab0b425f329e3595668ca3b1406cc3329e86b1b52051c09b9532` |
| `images/xfund_es_19.jpg` | es | `es_val_18.jpg` | 2480x3508 | 1768538 | `be6b428d3482e72eb7d3f9efff80781330a7b258c396d294a2aaf0d23b7aa470` |
| `images/xfund_es_20.jpg` | es | `es_val_19.jpg` | 2480x3508 | 1132519 | `46c03504cb96f4649d7f744234ff9fff26cc0bc9bb6db1611cb85ac4273728d6` |
| `images/xfund_fr_01.jpg` | fr | `fr_val_0.jpg` | 2480x3508 | 546202 | `e58b3254cda870402aad1db663c29da0d7c52d2945d889e661e745c51df786d7` |
| `images/xfund_fr_02.jpg` | fr | `fr_val_1.jpg` | 3508x2480 | 1865916 | `85ddc1fced813ddb2b425cb358c7fe1525078d5ba9468aed46555a293094a0ce` |
| `images/xfund_fr_03.jpg` | fr | `fr_val_2.jpg` | 2480x3508 | 357795 | `f6e369bd93138bf55b06bc662bde9e5f6a90515abddd8289dad9b9a56582d6e2` |
| `images/xfund_fr_04.jpg` | fr | `fr_val_3.jpg` | 2480x3508 | 652778 | `3381c558628ccc6e1b3aaa683c6c74d0cde44011c4601dbcd4817837b0c55338` |
| `images/xfund_fr_05.jpg` | fr | `fr_val_4.jpg` | 2480x3508 | 402891 | `76d9177bf1e175aa6ae506e53aa15a849136225e30675ff3efc210e96bb4523a` |
| `images/xfund_fr_06.jpg` | fr | `fr_val_5.jpg` | 2480x3508 | 409998 | `0b3a00f9f15e970aaf499171ba2362ac0653737d19700714bc103f368b732bcc` |
| `images/xfund_fr_07.jpg` | fr | `fr_val_6.jpg` | 2480x3508 | 395020 | `8fb7048075efebd2db057dbbdffcde2adf6341ef4090425c77995399d62a9773` |
| `images/xfund_fr_08.jpg` | fr | `fr_val_7.jpg` | 2480x3508 | 452204 | `da0e7f5c745ad043863523b3a85d7dad20ae7d919bd985aa1739a5ea7af75c29` |
| `images/xfund_fr_09.jpg` | fr | `fr_val_8.jpg` | 2480x3508 | 579608 | `6b788eaa499a14a4ade5bb41f63ba97de08a6e87b990de89fb62766b0e600d59` |
| `images/xfund_fr_10.jpg` | fr | `fr_val_9.jpg` | 2480x3508 | 363342 | `9a823946ddac361f923d2d43323ab75b41012ce315e8636f41b51e3fee66d6da` |
| `images/xfund_fr_11.jpg` | fr | `fr_val_10.jpg` | 2480x3508 | 479526 | `8e66366d4196b1506d566c79fcc7255bcd95d722c9cb2c6dcb650970c5791641` |
| `images/xfund_fr_12.jpg` | fr | `fr_val_11.jpg` | 2480x3508 | 565863 | `d988e05c7ffffe172ec81e8e92754e7711fa37ab7e9d79453ec10171ec3e3bf3` |
| `images/xfund_fr_13.jpg` | fr | `fr_val_12.jpg` | 2550x3507 | 377755 | `7b93712e6f8705c63f12b74564bfc231a804b081263c6e9a87f3b6062e33bb18` |
| `images/xfund_fr_14.jpg` | fr | `fr_val_13.jpg` | 2480x3508 | 560376 | `7831edd9421051d50432d8b4814843f06653ef7dbb76cbc1e6968a78591d2d5f` |
| `images/xfund_fr_15.jpg` | fr | `fr_val_14.jpg` | 2480x3508 | 561992 | `db1fc047a190744bb6c28877658691ed8df9238678a9afcb59bdcd73293a752a` |
| `images/xfund_fr_16.jpg` | fr | `fr_val_15.jpg` | 2480x3508 | 424088 | `dc9e0ca65007077aa17e837ea943ec005d2d6bb38eb4733acb2c9c5750f9b1e6` |
| `images/xfund_fr_17.jpg` | fr | `fr_val_16.jpg` | 2480x3508 | 688655 | `d22b336b0157a7e589fa8ec0a1a77208fa2a789812be3edd5fee02a576674e61` |
| `images/xfund_fr_18.jpg` | fr | `fr_val_17.jpg` | 2480x3508 | 817636 | `b0a0d9cb5e875ea4d870db55391d7b31af6f6b2fc16831a0867c8fe699d63e05` |
| `images/xfund_fr_19.jpg` | fr | `fr_val_18.jpg` | 2480x3508 | 379067 | `34a8b3ff7012bea147e7021269c11aaaf6599872b3fc8422ae35341fd7a6143c` |
| `images/xfund_fr_20.jpg` | fr | `fr_val_19.jpg` | 2480x3508 | 912125 | `19906cc86ecb45ec184e0da212467ff31c6a28f134016320a8706a208c94e80a` |
| `images/xfund_it_01.jpg` | it | `it_val_0.jpg` | 2480x3508 | 591976 | `e81642ace03cc990075bec5f9d74f5a7e917548710a5a220f71284836e55778a` |
| `images/xfund_it_02.jpg` | it | `it_val_1.jpg` | 2480x3508 | 625438 | `65951727292599ab5a2f259d864e834264a325b55048d0c29c84a52c30e6a1e2` |
| `images/xfund_it_03.jpg` | it | `it_val_2.jpg` | 2480x3508 | 665601 | `f61552a15704ff6d8a8df727aca063de51caff61de196bb3ec0a078d3859971b` |
| `images/xfund_it_04.jpg` | it | `it_val_3.jpg` | 2480x3508 | 707627 | `2a465bfbeb366d4c277e8b6821f94c662e7b49ff81cceac5ebb008d1202b807b` |
| `images/xfund_it_05.jpg` | it | `it_val_4.jpg` | 2480x3508 | 860604 | `7ebb48ae4a895175aa8970c6c86de97c3219dfd1ae1e94b51b857828909d2f18` |
| `images/xfund_it_06.jpg` | it | `it_val_5.jpg` | 2480x3508 | 719329 | `0bdccbb9b338596e4691752e1cca122152bde0235413523356981401d1f6e4f7` |
| `images/xfund_it_07.jpg` | it | `it_val_6.jpg` | 2480x3508 | 731219 | `96d6bd5961b83c337759e3644201e6acad4208c8d152464ab5087a063ac50e14` |
| `images/xfund_it_08.jpg` | it | `it_val_7.jpg` | 2480x3508 | 639399 | `d4800f3b6e063dba39ed9a5a7693bb9b36e109778aa01d5654ace38914e0d9fd` |
| `images/xfund_it_09.jpg` | it | `it_val_8.jpg` | 2480x3508 | 481730 | `6f695d5074292790bb5df40cd35f4b6d2e86cec2e0d4ee2104eecf58cfa86328` |
| `images/xfund_it_10.jpg` | it | `it_val_9.jpg` | 2480x3508 | 539460 | `a15e8b684a380751127bb1cf1b77cb400c32ad0b3b07253e9ff3fcbb1bf2716a` |
| `images/xfund_it_11.jpg` | it | `it_val_10.jpg` | 2480x3508 | 913608 | `96c54c05f1e2972164de97e89ad45312f17dc19e6087847fcd325db299aba7d6` |
| `images/xfund_it_12.jpg` | it | `it_val_11.jpg` | 2480x3508 | 704351 | `d12ff8a6ad49de7fa0e048e1e731ed07412b9a6eb41752edf86c08058b1a748b` |
| `images/xfund_it_13.jpg` | it | `it_val_12.jpg` | 2480x3508 | 682977 | `8294919a326bf36cc6d41b7515cf26d36300879fc60cfd9832801da8d171fefc` |
| `images/xfund_it_14.jpg` | it | `it_val_13.jpg` | 2480x3508 | 381232 | `7f3ee0b2a3bc3a02a48599cea84b4bceab3cc033431b68b7381e35716d615810` |
| `images/xfund_it_15.jpg` | it | `it_val_14.jpg` | 2480x3508 | 564125 | `d4cb5b218defc357926a31309c9293f814b69699ca839d506961354b8f223c41` |
| `images/xfund_it_16.jpg` | it | `it_val_15.jpg` | 2480x3508 | 700079 | `df0286704ea482aad37ed1abc478e0e751cf047e2026f74e29c24aa273635402` |
| `images/xfund_it_17.jpg` | it | `it_val_16.jpg` | 2480x3508 | 813846 | `cecb6cceb81aedb42108403985ed82b9980d29fd034936fc7dd6ebdcf526d275` |
| `images/xfund_it_18.jpg` | it | `it_val_17.jpg` | 2480x3508 | 854086 | `b6cc3138a89afe9b162f4f5a522507d9825c2a2526a5562ae3cdec7e65c2eed0` |
| `images/xfund_it_19.jpg` | it | `it_val_18.jpg` | 2480x3508 | 499577 | `2d58708fdfcfc32f0cf2e4741e415de8e75460a47de247cb305ab967d8105b7c` |
| `images/xfund_it_20.jpg` | it | `it_val_19.jpg` | 2480x3508 | 515693 | `1c2fb193e504b05d493dd73ae14b807ff14527a16ba516d29dd850bf9e727caa` |
| `images/xfund_de_01.jpg` | de | `de_val_0.jpg` | 2480x3508 | 2106284 | `fd1b96cd7c1e9f2af1b8022e75fc06a211742aa16ee9ec97e16665966e0db91e` |
| `images/xfund_de_02.jpg` | de | `de_val_1.jpg` | 2480x3508 | 1438921 | `4a2ee3606bfdf568cab1732ad7cb8a7940c207e4b00b77b927095e63e0565524` |
| `images/xfund_de_03.jpg` | de | `de_val_2.jpg` | 2480x3508 | 1344449 | `dd54e243b1d6f629d216531cd24613459e00c576c3c8ac1b496d453a41e3b26e` |
| `images/xfund_de_04.jpg` | de | `de_val_3.jpg` | 2480x3508 | 734394 | `a05ca0c22cf98690cc1e50d9cdd03706c6df928e1d2c6e9f419e4f1a7dc5ad26` |
| `images/xfund_de_05.jpg` | de | `de_val_4.jpg` | 2480x3508 | 710302 | `bda791eaac3908a1902d275fb11a77967335cac5b11bf982620b1369c771c251` |
| `images/xfund_de_06.jpg` | de | `de_val_5.jpg` | 2480x3508 | 1050057 | `2acf76f4c43be7f52ca7349adb7edb3a1fec8a2fbda274e8c1e42b2b42204963` |
| `images/xfund_de_07.jpg` | de | `de_val_6.jpg` | 2480x3508 | 874293 | `17431d03383a27c193abf22f30fd0ad89a3953ef747b89a16e86bc96a158cb7c` |
| `images/xfund_de_08.jpg` | de | `de_val_7.jpg` | 2480x3508 | 1276006 | `1e56f7243a112fe979a0fd2056085f8ac91ee18acc54647babcdc52d9464050d` |
| `images/xfund_de_09.jpg` | de | `de_val_8.jpg` | 2480x3508 | 1306763 | `30fb1d7745d6f68a2b8896bbcf8d3d84d119a4cf3032472623869d0fb6ca1c42` |
| `images/xfund_de_10.jpg` | de | `de_val_9.jpg` | 2480x3508 | 2460421 | `bd09ad26099ecdc719c504dd43cf14665665c2309216048b2cc85d7c7ec0ea9b` |
| `images/xfund_de_11.jpg` | de | `de_val_10.jpg` | 2480x3508 | 888641 | `ff8623ed9d35631be3d6b6c7d88c0f6243bacdaf3dee9274afef47fa2f894d6e` |
| `images/xfund_de_12.jpg` | de | `de_val_11.jpg` | 2480x3508 | 1794317 | `26a6f813e2f89129b20147a1d27ab4b4a7a04a776a8f3cae6ce5cad60495b272` |
| `images/xfund_de_13.jpg` | de | `de_val_12.jpg` | 2480x3508 | 2124128 | `8a7296aa19265c8c0a8b13823669c1ebf7c0b6944aac13f76410a4191371ee3c` |
| `images/xfund_de_14.jpg` | de | `de_val_13.jpg` | 2480x3508 | 783083 | `6e5abfe6ffc862d664ec27ab5b7429bc6373e5e2b6d43ce6d5e4fe55adac7c0a` |
| `images/xfund_de_15.jpg` | de | `de_val_14.jpg` | 2480x3508 | 1584525 | `f5effaf954715274e569819982701806ad54f4e4d2f7736c926e230b18f47219` |
| `images/xfund_de_16.jpg` | de | `de_val_15.jpg` | 2480x3508 | 1568472 | `001f6039696fc0139830d1f6d867dbd8ff4aa0a38e49901a00ea98885f11abdf` |
| `images/xfund_de_17.jpg` | de | `de_val_16.jpg` | 2480x3508 | 1468244 | `5905baf9c515ce2365ae679ad494fd95f10f2a82da2058b8db03ea23d2ff7e23` |
| `images/xfund_de_18.jpg` | de | `de_val_17.jpg` | 2480x3508 | 1430562 | `bc16177f8ead508c32a5d15bf96ea9732aa43cfebef27be1ae5c72d2ecb64521` |
| `images/xfund_de_19.jpg` | de | `de_val_18.jpg` | 2480x3508 | 2391927 | `4fe7fe1a0084baddd2fc6b96132e19606b2fee3d51216d459011cc587f7155ab` |
| `images/xfund_de_20.jpg` | de | `de_val_19.jpg` | 2480x3508 | 1727592 | `3af7e1cf74d8ab0efd26920e82fa9811ab813ce994eb7bc1bc8416dabe1d8939` |
| `images/xfund_pt_01.jpg` | pt | `pt_val_0.jpg` | 2480x3508 | 720366 | `e549cce7ca4963a15803bd62d701864149e94177ef032277d3434328ea2f37b8` |
| `images/xfund_pt_02.jpg` | pt | `pt_val_1.jpg` | 2480x3508 | 663844 | `628069000aae873264bd3b63f2f001d34095b28ee7defcb1033bdc918e440969` |
| `images/xfund_pt_03.jpg` | pt | `pt_val_2.jpg` | 2480x3508 | 702609 | `fd29c5491dd7044a82443edfe0b7bfe8a485edea301737935cfa367abb6d9d68` |
| `images/xfund_pt_04.jpg` | pt | `pt_val_3.jpg` | 2480x3508 | 564216 | `32225892348cc711df7e90833de8c50ce529c91cea68af1dc9a1c9a65c3399b4` |
| `images/xfund_pt_05.jpg` | pt | `pt_val_4.jpg` | 2480x3508 | 580797 | `6efd66872071244f8c61fc7637a342bf3491b222699ec5455b02ec7e9ce9904a` |
| `images/xfund_pt_06.jpg` | pt | `pt_val_5.jpg` | 2480x3508 | 600373 | `10e79831e0f2d090f1c145db02489a80cc39d5659c58d038563c7fc9e07f89dc` |
| `images/xfund_pt_07.jpg` | pt | `pt_val_6.jpg` | 2480x3508 | 337166 | `86eff7790b5413e1a251467934c744ebb74d6a32f32cf2df68905888c4af6ce0` |
| `images/xfund_pt_08.jpg` | pt | `pt_val_7.jpg` | 2480x3508 | 616662 | `d969e6721dcb098f60faa07303f83ae730277f4175a974f028a5bc875c211ad6` |
| `images/xfund_pt_09.jpg` | pt | `pt_val_8.jpg` | 2480x3508 | 1012256 | `696a34aebdf68045e90fb54b081c8cae8fc3180694053c780fb372848f429d06` |
| `images/xfund_pt_10.jpg` | pt | `pt_val_9.jpg` | 2480x3508 | 728916 | `9610967758fd9fce7aa75b762ab0726c40e4415b554395426c6107698bb67c1d` |
| `images/xfund_pt_11.jpg` | pt | `pt_val_10.jpg` | 2480x3508 | 586617 | `86052b614b153a0ca9646bbe3291c7e47fef20795d297fbbf443c1388e19e7c4` |
| `images/xfund_pt_12.jpg` | pt | `pt_val_11.jpg` | 2480x3508 | 602159 | `d737e40746bb3122d8480d70146470c21aa2f42a9666275c948ace45306a4f7e` |
| `images/xfund_pt_13.jpg` | pt | `pt_val_12.jpg` | 2480x3508 | 523388 | `73f711656389abcaf0108147ddde2113a54e3ba0ebd6ca101d7732afe60c9277` |
| `images/xfund_pt_14.jpg` | pt | `pt_val_13.jpg` | 2480x3508 | 459180 | `6f247c563d48d17164793d64e1f66bf5263ee5657e13c79d5ec9a27f1b8387e7` |
| `images/xfund_pt_15.jpg` | pt | `pt_val_14.jpg` | 2480x3508 | 560940 | `da37cbef687bc59507ca79b87f66218b26d09f2f524a03de7c4a58c35a5ca5df` |
| `images/xfund_pt_16.jpg` | pt | `pt_val_15.jpg` | 2480x3508 | 284552 | `e063626735315df6387b130a58d18c177a19a8c83bc7f035a756da25e8baa567` |
| `images/xfund_pt_17.jpg` | pt | `pt_val_16.jpg` | 2480x3508 | 690259 | `cf5da0082500e82882549d77cfc7fde4f7d08b434f3ded1976f9b9facc1fb858` |
| `images/xfund_pt_18.jpg` | pt | `pt_val_17.jpg` | 2480x3508 | 912887 | `b1b45909d3a798d5494ce2374da33d1876b45d79199c7c3391cdc176ff42ed09` |
| `images/xfund_pt_19.jpg` | pt | `pt_val_18.jpg` | 2480x3508 | 641946 | `32f83c46119562cfef0c960f64ca0c301521e6106252feb6645cf63cccc40ad1` |
| `images/xfund_pt_20.jpg` | pt | `pt_val_19.jpg` | 2480x3508 | 615897 | `21454dc68f82e1d6af3c04433c084810c9adf9ebcde81daf2a5e2df40eb6a908` |

## Considered and not stored

UN Official Document System PDFs were requested and not downloaded beyond licence checking. The UN Terms
and Conditions of Use (<https://www.un.org/en/about-us/terms-of-use>, retrieved 2026-11-27) grant permission
"to download and copy the information, documents and materials ... for the User's personal, non-commercial
use, without any right to resell or redistribute them or to compile or create derivative works therefrom",
and UN Publications' Rights & Permissions page (<https://shop.un.org/rights-permissions>) states "Permission
is required to reuse content from any and all United Nations' online platforms and databases". A rendered,
degraded scan of each page is a derivative work and a shared bucket is redistribution, so the documents need
written permission (<mailto:permissions@un.org>) before they can be used.
