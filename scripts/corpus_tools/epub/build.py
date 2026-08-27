"""Build the synthesized EPUB edge cases.

Each file reproduces one defect that xberg-io/xberg pull request #1498 fixes,
for a case that no public EPUB exhibits. `EPUB_EDGE_CASES.md` records which
cases those are and why. Every other file in that corpus is a published
document fetched by `scripts/fetch_epub_edge_cases.py`.

The output is deterministic: every ZIP member is stored uncompressed with a
fixed timestamp, so the same source always yields the same sha256, and
`scripts/data/epub-edge-cases.json` can pin the bytes. `scripts/tests/test_epub_edge_cases.py`
checks that pin against a fresh build.

    python3 scripts/build_epub_edge_cases.py            # write every file
    python3 scripts/build_epub_edge_cases.py --list     # print path and sha256
"""

import io
import struct
import zipfile
import zlib

from corpus_tools import paths

REPO_ROOT = paths.REPO_ROOT
CORPUS_DIR = "epub/edge-cases"
# ~keep A fixed timestamp keeps the ZIP bytes identical across builds; the sha256 in the
# manifest depends on it.
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

CONTAINER_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
    "  <rootfiles>\n"
    '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
    "  </rootfiles>\n"
    "</container>\n"
)

XHTML11_DOCTYPE = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'

HTML5_DOCTYPE = "<!DOCTYPE html>\n"

XHTML_NS = 'xmlns="http://www.w3.org/1999/xhtml"'


def xhtml(body: str, *, title: str = "Chapter", head_extra: str = "", doctype: str = XHTML11_DOCTYPE) -> str:
    """One XHTML 1.1 content document with the given body markup."""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"{doctype}"
        f"<html {XHTML_NS}>\n<head>\n<title>{title}</title>\n{head_extra}</head>\n"
        f"<body>\n{body}\n</body>\n</html>\n"
    )


def pack(members: list[tuple[str, bytes]]) -> bytes:
    """Write an EPUB container: `mimetype` first and stored, every member uncompressed."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        mimetype = zipfile.ZipInfo("mimetype", date_time=ZIP_TIMESTAMP)
        mimetype.compress_type = zipfile.ZIP_STORED
        archive.writestr(mimetype, b"application/epub+zip")
        for name, data in members:
            info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)
    return buffer.getvalue()


def png_1x1() -> bytes:
    """A valid 1x1 opaque white PNG, so a cover item carries real image bytes."""

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b"\x00\xff\xff\xff"
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def package(
    *,
    version: str,
    metadata: str,
    items: list[tuple[str, str, str, str]],
    spine: list[str],
    guide: str = "",
    manifest_extra: str = "",
) -> str:
    """The package document. `items` are (id, href, media-type, extra attributes)."""
    # Every package carries a table of contents, so epubcheck reads the fixture as a
    # conforming EPUB and the defect under test is the only thing wrong with it.
    if version == "2.0":
        items = [*items, ("ncx", "toc.ncx", "application/x-dtbncx+xml", "")]
        toc_attr = ' toc="ncx"'
    else:
        items = [*items, ("nav", "nav.xhtml", "application/xhtml+xml", ' properties="nav"')]
        metadata += '    <meta property="dcterms:modified">2026-08-25T00:00:00Z</meta>\n'
        toc_attr = ""
    manifest = "".join(
        f'    <item id="{item_id}" href="{href}" media-type="{media_type}"{extra}/>\n'
        for item_id, href, media_type, extra in items
    )
    itemrefs = "".join(f'    <itemref idref="{item_id}"/>\n' for item_id in spine)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<package xmlns="http://www.idpf.org/2007/opf" version="{version}" unique-identifier="uid">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">\n'
        f"{metadata}"
        "  </metadata>\n"
        f"  <manifest>\n{manifest}{manifest_extra}  </manifest>\n"
        f"  <spine{toc_attr}>\n{itemrefs}  </spine>\n"
        f"{guide}"
        "</package>\n"
    )


def basic_metadata(title: str, identifier: str) -> str:
    return (
        f'    <dc:identifier id="uid">urn:xberg-test-documents:{identifier}</dc:identifier>\n'
        f"    <dc:title>{title}</dc:title>\n"
        "    <dc:language>en</dc:language>\n"
    )


def toc_member(version: str, first_href: str, identifier: str, title: str = "Start") -> tuple[str, bytes]:
    """The table-of-contents member that `package` declared: an NCX for EPUB 2, a nav document for EPUB 3."""
    if version == "2.0":
        ncx = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
            f'<head><meta name="dtb:uid" content="urn:xberg-test-documents:{identifier}"/><meta name="dtb:depth" content="1"/>'
            '<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>\n'
            "<docTitle><text>Test</text></docTitle>\n"
            f'<navMap><navPoint id="n1" playOrder="1"><navLabel><text>{title}</text></navLabel><content src="{first_href}"/></navPoint></navMap>\n'
            "</ncx>\n"
        )
        return "OEBPS/toc.ncx", ncx.encode("utf-8")
    nav = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
        "<head><title>Contents</title></head>\n"
        f'<body><nav epub:type="toc"><ol><li><a href="{first_href}">{title}</a></li></ol></nav></body>\n'
        "</html>\n"
    )
    return "OEBPS/nav.xhtml", nav.encode("utf-8")


def simple_epub(
    slug: str,
    title: str,
    chapters: list[tuple[str, bytes]],
    *,
    version: str = "2.0",
    media_type: str = "application/xhtml+xml",
    metadata: str | None = None,
    extra_items: list[tuple[str, str, str, str]] | None = None,
    extra_members: list[tuple[str, bytes]] | None = None,
    guide: str = "",
    opf_bytes: bytes | None = None,
) -> bytes:
    """An EPUB whose spine is the given chapters, in order."""
    items = [(f"c{index}", href, media_type, "") for index, (href, _) in enumerate(chapters, start=1)]
    items += extra_items or []
    opf = opf_bytes or package(
        version=version,
        metadata=metadata if metadata is not None else basic_metadata(title, slug),
        items=items,
        spine=[f"c{index}" for index in range(1, len(chapters) + 1)],
        guide=guide,
    ).encode("utf-8")
    members = [("META-INF/container.xml", CONTAINER_XML.encode("utf-8")), ("OEBPS/content.opf", opf)]
    members += [(f"OEBPS/{href}", data) for href, data in chapters]
    members += extra_members or []
    members.append(toc_member(version, chapters[0][0], slug))
    return pack(members)


# Issue #1488: an HTML named entity plus a tag whose name or attributes contain
# "style" or "script" before the first text node. The first chapter is the
# reproduction from the issue verbatim; the second uses the other trigger tags.
def entity_style() -> bytes:
    chapter_one = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"{XHTML11_DOCTYPE}"
        f"<html {XHTML_NS}>\n"
        '<head><link rel="stylesheet" href="style.css"/><title></title></head>\n'
        "<body><p>First&nbsp;para ENTITY-CHAPTER-ONE</p><p>Second para</p></body>\n"
        "</html>\n"
    )
    chapter_two = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"{XHTML11_DOCTYPE}"
        f"<html {XHTML_NS}>\n<head><title>Two</title></head>\n"
        '<body style="margin: 0">\n'
        '<p style="text-indent: 0">&Eacute;lan ENTITY-CHAPTER-TWO &mdash; the second chapter.</p>\n'
        '<p>H<span class="subscript">2</span>O and a<sup>2</sup>&nbsp;+&nbsp;b<sup>2</sup>.</p>\n'
        "</body>\n</html>\n"
    )
    return simple_epub(
        "entity-style",
        "Entities and style attributes",
        [("chapter1.xhtml", chapter_one.encode("utf-8")), ("chapter2.xhtml", chapter_two.encode("utf-8"))],
        extra_items=[("css", "style.css", "text/css", "")],
        extra_members=[("OEBPS/style.css", b"p { margin: 0 }\n")],
    )


# Issue #1488: a UTF-8 byte order mark before the XML declaration.
def bom_prelude() -> bytes:
    chapter = b"\xef\xbb\xbf" + xhtml("<p>BOM-CHAPTER text after a byte order mark.</p>", title="BOM").encode("utf-8")
    return simple_epub("bom-prelude", "Byte order mark before the XML declaration", [("chapter1.xhtml", chapter)])


# Issue #1488: a chapter that does not parse as XML at all. The fix warns and
# names the file instead of dropping it silently.
def unparseable_chapter() -> bytes:
    good = xhtml("<p>GOOD-CHAPTER parses.</p>", title="Good").encode()
    broken = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"<html {XHTML_NS}><head><title>Broken</title></head>\n"
        "<body><p>BROKEN-CHAPTER has an <b>unclosed element</p><div></body></html>\n"
    ).encode()
    return simple_epub(
        "unparseable-chapter",
        "A chapter that fails to parse",
        [("good.xhtml", good), ("broken.xhtml", broken)],
    )


# Issue #1490: element nesting about 30,000 levels deep. The issue measured
# that 20,000 passes and 30,000 ends the process.
def nested_30000(depth: int = 30_000) -> bytes:
    body = (
        "<p>DEPTH-LEAD paragraph.</p>\n<div>"
        + "<span>" * depth
        + "DEPTH-CORE"
        + "</span>" * depth
        + "</div>\n<p>DEPTH-TAIL paragraph.</p>"
    )
    chapter = xhtml(body, title="Deep").encode("utf-8")
    return simple_epub("nested-30000", "Thirty thousand nested elements", [("deep.xhtml", chapter)])


# Issue #1491: a spine item whose manifest href is a URL. The path-traversal
# and absolute-path forms come from the epubcheck test suite.
def remote_url_spine_item() -> bytes:
    chapter = xhtml("<p>LOCAL-CHAPTER next to a remote spine item.</p>", title="Local", doctype=HTML5_DOCTYPE).encode(
        "utf-8"
    )
    items = [
        ("c1", "chapter1.xhtml", "application/xhtml+xml", ""),
        ("remote", "https://example.org/remote.xhtml", "application/xhtml+xml", ""),
    ]
    opf = package(
        version="3.0",
        metadata=basic_metadata("A remote spine item", "remote-url-spine-item"),
        items=items,
        spine=["c1", "remote"],
    ).encode("utf-8")
    return simple_epub("remote-url-spine-item", "", [("chapter1.xhtml", chapter)], version="3.0", opf_bytes=opf)


# Issue #1492: every Dublin Core element that the last-wins parser got wrong,
# in the EPUB 2 form with `opf:role` and `opf:event`.
def dublin_core_epub2() -> bytes:
    metadata = (
        '    <dc:identifier id="uid">urn:xberg-test-documents:dublin-core-epub2</dc:identifier>\n'
        "    <dc:title>Main Title</dc:title>\n"
        "    <dc:title>Subtitle</dc:title>\n"
        '    <dc:creator opf:role="aut" opf:file-as="Author, Alice">Alice Author</dc:creator>\n'
        '    <dc:creator opf:role="ill" opf:file-as="Illustrator, Ivan">Ivan Illustrator</dc:creator>\n'
        "    <dc:subject>Fiction</dc:subject>\n"
        "    <dc:subject>Illustrated books</dc:subject>\n"
        "    <dc:subject>Test fixtures</dc:subject>\n"
        '    <dc:date opf:event="publication">1999-01-01</dc:date>\n'
        '    <dc:date opf:event="modification">2020-02-02</dc:date>\n'
        "    <dc:language>en</dc:language>\n"
    )
    chapter = xhtml("<p>DUBLIN-CORE chapter.</p>").encode("utf-8")
    return simple_epub("dublin-core-epub2", "", [("chapter1.xhtml", chapter)], metadata=metadata)


# Issue #1492: `<meta name="cover">` that points at the cover XHTML page
# instead of the cover image.
def cover_meta_points_at_xhtml() -> bytes:
    metadata = (
        basic_metadata("Cover reference to an XHTML page", "cover-meta-xhtml")
        + '    <meta name="cover" content="cover-page"/>\n'
    )
    cover_page = xhtml('<div><img src="cover.png" alt="COVER-ALT front cover"/></div>', title="Cover").encode("utf-8")
    chapter = xhtml("<p>COVER-XHTML body chapter.</p>").encode("utf-8")
    items = [
        ("cover-page", "cover.xhtml", "application/xhtml+xml", ""),
        ("c1", "chapter1.xhtml", "application/xhtml+xml", ""),
        ("cover-image", "cover.png", "image/png", ""),
    ]
    opf = package(version="2.0", metadata=metadata, items=items, spine=["cover-page", "c1"]).encode("utf-8")
    members = [
        ("META-INF/container.xml", CONTAINER_XML.encode("utf-8")),
        ("OEBPS/content.opf", opf),
        ("OEBPS/cover.xhtml", cover_page),
        ("OEBPS/chapter1.xhtml", chapter),
        ("OEBPS/cover.png", png_1x1()),
        toc_member("2.0", "cover.xhtml", "cover-meta-xhtml"),
    ]
    return pack(members)


# Issue #1494: chapters declared in a single-byte or multi-byte legacy
# encoding, with real non-ASCII bytes in that encoding.
def declared_encoding(slug: str, encoding: str, declared: str, text: str) -> bytes:
    chapter = (
        f'<?xml version="1.0" encoding="{declared}"?>\n'
        f"<html {XHTML_NS}><head><title>{slug}</title></head>\n"
        f"<body><p>{text}</p></body></html>\n"
    ).encode(encoding)
    return simple_epub(slug, f"A chapter declared {declared}", [("chapter1.xhtml", chapter)])


LATIN1_TEXT = "LATIN1-CHAPTER Café crème à la française, naïve façade, Ærø, señor."
CP1252_TEXT = "CP1252-CHAPTER Price €12 for a “quoted” œuvre, Œdipe, ‰, †."
SHIFT_JIS_TEXT = "SHIFT-JIS-CHAPTER 吾輩は猫である。名前はまだ無い。"
UTF16_TEXT = "UTF16-CHAPTER Café crème, 吾輩は猫である, Ærø."


def utf16_chapter(slug: str, encoding: str, declared: str) -> bytes:
    source = (
        f'<?xml version="1.0" encoding="{declared}"?>\n'
        f"<html {XHTML_NS}><head><title>{slug}</title></head>\n"
        f"<body><p>{UTF16_TEXT}</p></body></html>\n"
    )
    # `utf-16-le`/`utf-16-be` write no BOM; prepend the one the declaration promises.
    bom = b"\xff\xfe" if encoding == "utf-16-le" else b"\xfe\xff"
    chapter = bom + source.encode(encoding)
    return simple_epub(slug, f"A chapter written in {declared}", [("chapter1.xhtml", chapter)])


# Issue #1494: the package document itself in Latin-1.
def opf_latin1() -> bytes:
    metadata = (
        '    <dc:identifier id="uid">urn:xberg-test-documents:opf-latin1</dc:identifier>\n'
        "    <dc:title>Éléments d'un livre</dc:title>\n"
        "    <dc:creator>Zoë Ångström</dc:creator>\n"
        "    <dc:language>fr</dc:language>\n"
    )
    opf = (
        package(
            version="2.0",
            metadata=metadata,
            items=[("c1", "chapter1.xhtml", "application/xhtml+xml", "")],
            spine=["c1"],
        )
        .replace('encoding="utf-8"', 'encoding="iso-8859-1"')
        .encode("iso-8859-1")
    )
    chapter = xhtml("<p>OPF-LATIN1 chapter.</p>").encode("utf-8")
    return simple_epub("opf-latin1", "", [("chapter1.xhtml", chapter)], opf_bytes=opf)


# Issues #1486 and #1487: media-type labels that are not the two core types.
MEDIA_TYPE_LABELS = [
    ("text-html", "text/html"),
    ("text-xml", "text/xml"),
    ("application-xml", "application/xml"),
    ("parameters", "application/xhtml+xml; charset=utf-8"),
    ("uppercase", "APPLICATION/XHTML+XML"),
    ("empty", ""),
]


def media_type_labels() -> bytes:
    items = []
    chapters = []
    for slug, label in MEDIA_TYPE_LABELS:
        href = f"{slug}.xhtml"
        marker = f"MEDIA-TYPE-{slug.upper()}"
        chapters.append(
            (
                f"OEBPS/{href}",
                xhtml(
                    f"<p>{marker} chapter declared as {label or 'an empty attribute'}.</p>", doctype=HTML5_DOCTYPE
                ).encode("utf-8"),
            )
        )
        items.append((slug, href, label, ""))
    opf = package(
        version="3.0",
        metadata=basic_metadata("Media type labels", "media-type-labels"),
        items=items,
        spine=[slug for slug, _ in MEDIA_TYPE_LABELS],
    ).encode("utf-8")
    members = [("META-INF/container.xml", CONTAINER_XML.encode("utf-8")), ("OEBPS/content.opf", opf), *chapters]
    members.append(toc_member("3.0", MEDIA_TYPE_LABELS[0][0] + ".xhtml", "media-type-labels"))
    return pack(members)


BUILDERS = {
    f"{CORPUS_DIR}/entities/synthetic_entity_style.epub": entity_style,
    f"{CORPUS_DIR}/entities/synthetic_bom_prelude.epub": bom_prelude,
    f"{CORPUS_DIR}/entities/synthetic_unparseable_chapter.epub": unparseable_chapter,
    f"{CORPUS_DIR}/depth/synthetic_nested_30000.epub": nested_30000,
    f"{CORPUS_DIR}/unsafe-href/synthetic_remote_url_spine_item.epub": remote_url_spine_item,
    f"{CORPUS_DIR}/metadata/synthetic_dublin_core_epub2.epub": dublin_core_epub2,
    f"{CORPUS_DIR}/metadata/synthetic_cover_meta_xhtml.epub": cover_meta_points_at_xhtml,
    f"{CORPUS_DIR}/encoding/synthetic_latin1.epub": lambda: declared_encoding(
        "latin1", "iso-8859-1", "iso-8859-1", LATIN1_TEXT
    ),
    f"{CORPUS_DIR}/encoding/synthetic_cp1252.epub": lambda: declared_encoding(
        "cp1252", "cp1252", "windows-1252", CP1252_TEXT
    ),
    f"{CORPUS_DIR}/encoding/synthetic_shift_jis.epub": lambda: declared_encoding(
        "shift-jis", "shift_jis", "Shift_JIS", SHIFT_JIS_TEXT
    ),
    f"{CORPUS_DIR}/encoding/synthetic_utf16le.epub": lambda: utf16_chapter("utf16le", "utf-16-le", "UTF-16"),
    f"{CORPUS_DIR}/encoding/synthetic_utf16be.epub": lambda: utf16_chapter("utf16be", "utf-16-be", "UTF-16"),
    f"{CORPUS_DIR}/encoding/synthetic_opf_latin1.epub": opf_latin1,
    f"{CORPUS_DIR}/media-types/synthetic_media_type_labels.epub": media_type_labels,
}


def build_all() -> dict[str, bytes]:
    return {path: builder() for path, builder in BUILDERS.items()}
