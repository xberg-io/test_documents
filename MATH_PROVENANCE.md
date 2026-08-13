# Math corpus provenance

Documents that carry mathematics, added to exercise formula extraction across every format that can hold it. Each one was fetched from the source below, and its licence read from the source repository, the document itself, or the publisher's stated terms.

## No ground truth, and why

These documents ship without `ground_truth/` files.

The corpus takes ground truth from upstream and normalizes it, then gates each document against an independent oracle. These documents bring none: they are raw published files. Deriving it by running the extractor over them would record today's output as the definition of correct, so a later regression would match the golden file and pass. The corpus is better served by an honest gap than by a golden file that cannot fail.

There is one seam worth noting for later. Four of the documents carry 1,046 LaTeX strings written by their own authors, in MathML `annotation-tex`:

| document | annotations |
|---|---|
| `html/math/mathematics_mathml_pandoc_b65cef.html` | 577 |
| `html/math/2212_09410_f9ff0c.html` | 339 |
| `html/math/2608_12173v1_cf6425.html` | 117 |
| `html/math/2608_11028v2_419bae.html` | 13 |

That is real formula-level ground truth, independent of any extractor. `README.md` places targets of that kind in `ground_truth/structured/`, which the repository does not yet contain, so this change does not invent the format. The material is here when that directory arrives.

## Committed

| path | source | licence | notation |
|---|---|---|---|
| `epub/math/IS4E_fbdd3c.epub` | [Introductory Statistics for Economics](https://bookdown.org/bkrauth/IS4E/IS4E.epub) | MIT | MathML (Presentation) with embedded LaTeX anno |
| `epub/math/cnt_mathml_support_a20d9b.epub` | [W3C EPUB 3 test suite](https://w3c.github.io/epub-tests/tests/cnt-mathml-support.epub) | W3C Software and Document License | MathML (Presentation) |
| `epub/math/quadratic_functions_4ebefc.epub` | [Connexions / OpenStax CNX collection col11284 "Quadr](https://archive.org/download/cnx-org-col11284/quadratic-functions.epub) | CC-BY-3.0 | MathML (Presentation, wrapped in <semantics>) |
| `epub/math/statistical_learning_theory_d50966.epub` | [Connexions / OpenStax CNX collection col10532 "Stati](https://archive.org/download/cnx-org-col10532/statistical-learning-theory.epub) | CC-BY-2.0 | MathML (Presentation, wrapped in <semantics>) |
| `html/math/2212_09410_f9ff0c.html` | [ar5iv](https://ar5iv.labs.arxiv.org/html/2212.09410) | CC-BY-4.0 | MathML + TeX in the alttext attribute |
| `html/math/2608_11028v2_419bae.html` | [arXiv native HTML](https://arxiv.org/html/2608.11028v2) | CC-BY-4.0 | MathML + TeX in the alttext attribute |
| `html/math/2608_12173v1_cf6425.html` | [arXiv native HTML](https://arxiv.org/html/2608.12173v1) | CC-BY-4.0 | MathML + TeX in the alttext attribute |
| `html/math/index_6de724.html` | [Stanford CS236 "Deep Generative Models" course notes](https://raw.githubusercontent.com/deepgenerativemodels/notes/master/docs/vae/index.html) | MIT | <script type="math/tex"> / "math/tex; mode=dis |
| `html/math/math_8h_079059.html` | [Motion Primitive Library C++ API documentation](https://raw.githubusercontent.com/sikang/motion_primitive_library/master/docs/math_8h.html) | Apache-2.0 | LaTeX carried only in the alt attribute of a P |
| `html/math/math_d0ba73.html` | [PySurvival documentation, "Mathematics" page](https://raw.githubusercontent.com/square/pysurvival/master/docs/math.html) | Apache-2.0 | <script type="math/tex"> and <script type="mat |
| `html/math/math_experiments_mathml_ttm_3b80f9.html` | [Docutils functional-test expected output](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/expected/math_experiments_mathml_ttm.html) | Public domain | native MathML |
| `html/math/math_output_html_378195.html` | [Docutils functional-test expected output](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/expected/math_output_html.html) | Public domain | HTML/CSS math (no MathML, no TeX) — worst-case |
| `html/math/math_output_mathjax_f0d3c2.html` | [Docutils functional-test expected output](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/expected/math_output_mathjax.html) | Public domain | raw LaTeX carried in span/div class="math" for |
| `html/math/math_output_mathml_64e3ae.html` | [Docutils functional-test expected output](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/expected/math_output_mathml.html) | Public domain | native MathML |
| `html/math/mathematics_mathml_blahtexml_875f65.html` | [Docutils functional-test expected output](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/expected/mathematics_mathml_blahtexml.html) | Public domain | native MathML |
| `html/math/mathematics_mathml_pandoc_b65cef.html` | [Docutils functional-test expected output](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/expected/mathematics_mathml_pandoc.html) | Public domain | MathML with an application/x-tex <annotation>  |
| `html/math/output_data_badc7e.html` | [Aequitas bias-audit toolkit documentation](https://raw.githubusercontent.com/dssg/aequitas/master/docs/output_data.html) | MIT | LaTeX in the alt attribute of Sphinx-rendered  |
| `html/math/reg_783dab.html` | ["Learning Apache Spark with Python" book, regression](https://raw.githubusercontent.com/runawayhorse001/LearningApacheSpark/master/docs/reg.html) | MIT | LaTeX in the alt attribute of Sphinx-rendered  |
| `html/math/rmarkdown_4b0a34.html` | ["Introducción a R" bookdown book](https://raw.githubusercontent.com/rubenfcasal/bookdown_intro/master/docs/rmarkdown.html) | CC0-1.0 | raw LaTeX in \[…\] inside span class="math dis |
| `html/math/sample_5da28a.html` | [MathJax v2 test suite](https://raw.githubusercontent.com/mathjax/MathJax/legacy-v2/test/sample.html) | Apache-2.0 | raw LaTeX with $…$, \(…\), \[…\] and AMS envir |
| `html/math/scipy_stats_norm_60d729.html` | [SciPy reference documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html) | BSD-3-Clause | raw LaTeX in \[…\] / \(…\) inside class="math  |
| `hwp/math/EC_88_98_EC_8B_9D_2acc8f.hwp` | [neolord0/hwplib](https://raw.githubusercontent.com/neolord0/hwplib/main/sample_hwp/basic/%EC%88%98%EC%8B%9D.hwp) | Apache-2.0 | HWP EQEdit script (EQEDIT record, tag 88) insi |
| `hwp/math/SimpleEquation_4e1760.hwpx` | [neolord0/hwpxlib](https://raw.githubusercontent.com/neolord0/hwpxlib/main/testFile/reader_writer/SimpleEquation.hwpx) | Apache-2.0 | HWP EQEdit script inside OWPML <hp:equation><h |
| `hwp/math/doc_8713v3a8b_3D23v9e_3D4av07_3D85v3e_3Dcfafvbb7dv2ad9_v_a3c2e7.hwp` | [Ahnd6474/jakal-hwpx](https://raw.githubusercontent.com/Ahnd6474/jakal-hwpx/main/hwpx_collection/doc_8713v3a8b%3D23v9e%3D4av07%3D85v3e%3Dcfafvbb7dv2ad9_v4607.hwpx) | MIT for the repository | HWP EQEdit script (EQEDIT record, tag 88) insi |
| `hwp/math/eq_01_71f171.hwp` | [postmelee/alhangeul-macos](https://raw.githubusercontent.com/postmelee/alhangeul-macos/main/samples/eq-01.hwp) | MIT for the repository | HWP EQEdit script (EQEDIT record, tag 88) insi |
| `hwp/math/equation_p0_e63f26.hwpx` | [airmang/python-hwpx](https://raw.githubusercontent.com/airmang/python-hwpx/main/tests/fixtures/equation_preview/equation_p0.hwpx) | Apache-2.0 | HWP EQEdit script inside OWPML <hp:equation><h |
| `hwp/math/from_5d05e0.hwpx` | [neolord0/hwp2hwpx](https://raw.githubusercontent.com/neolord0/hwp2hwpx/main/test/equation/from.hwpx) | Apache-2.0 | HWP EQEdit script inside OWPML <hp:equation><h |
| `hwp/math/from_ecaebf.hwp` | [neolord0/hwp2hwpx](https://raw.githubusercontent.com/neolord0/hwp2hwpx/main/test/equation/from.hwp) | Apache-2.0 | HWP EQEdit script (EQEDIT record, tag 88) insi |
| `hwp/math/hard_20example_3d4d15.hwpx` | [Ahnd6474/jakal-hwpx](https://raw.githubusercontent.com/Ahnd6474/jakal-hwpx/main/hwpx_collection/hard%20example.hwpx) | MIT for the repository | HWP EQEdit script inside OWPML <hp:equation><h |
| `iwork/math/geometric_means_qcmc_revised_7d7c7a.key` | [Zenodo record 'Quantum algorithms for matrix geometr](https://zenodo.org/api/records/14309036/files/geometric-means-qcmc-revised.key/content) | CC-BY-4.0 | LaTeX source held in Keynote's native TSWPEqua |
| `jats/math/10_21105_joss_01816_736f75.jats` | [Journal of Open Source Software](https://raw.githubusercontent.com/openjournals/joss-papers/master/joss.01816/10.21105.joss.01816.jats) | CC-BY-4.0 | LaTeX <tex-math> + MathML under <alternatives> |
| `jats/math/10_21105_joss_06105_a7ce1e.jats` | [Journal of Open Source Software](https://raw.githubusercontent.com/openjournals/joss-papers/master/joss.06105/10.21105.joss.06105.jats) | CC-BY-4.0 | LaTeX in <tex-math> CDATA and MathML in <mml:m |
| `jupyter/math/07_sympy_7d5b08.ipynb` | [maths-with-python](https://raw.githubusercontent.com/IanHawke/maths-with-python/master/07-sympy.ipynb) | MIT | LaTeX — both markdown cells and executed outpu |
| `jupyter/math/Handcalcs_julia_cf3b0c.ipynb` | [Handcalcs.jl official examples](https://raw.githubusercontent.com/co1emi11er2/Handcalcs.jl/master/examples/Handcalcs_julia.ipynb) | MIT | LaTeX (`\begin{align}`) in text/latex output b |
| `jupyter/math/StatesOperators_4e6d54.ipynb` | [QuTiP official guide notebooks](https://raw.githubusercontent.com/qutip/qutip-notebooks/master/docs/guide/StatesOperators.ipynb) | BSD-3-Clause | LaTeX — `\begin{equation*}...\end{array}` matr |
| `jupyter/math/SymPy_9b271e.ipynb` | [JetBrains/intellij-ipnb](https://raw.githubusercontent.com/JetBrains/intellij-ipnb/master/testData/SymPy.ipynb) | Apache-2.0 | LaTeX in nbformat v3 `pyout` outputs (legacy ` |
| `jupyter/math/autodiff_cookbook_a09ead.ipynb` | [JAX official documentation](https://raw.githubusercontent.com/jax-ml/jax/main/docs/notebooks/autodiff_cookbook.ipynb) | Apache-2.0 | LaTeX in markdown cells (inline `$...$` and di |
| `jupyter/math/chapter02_definitions_586622.ipynb` | [noBSLAnotebooks](https://raw.githubusercontent.com/minireference/noBSLAnotebooks/master/chapter02_definitions.ipynb) | MIT | LaTeX in text/latex output bundles (newer SymP |
| `jupyter/math/eseries_37d1f4.ipynb` | [QuTiP example notebooks](https://raw.githubusercontent.com/qutip/qutip-notebooks/master/examples/eseries.ipynb) | BSD-3-Clause | LaTeX in text/latex output bundles and inline  |
| `jupyter/math/handcalc_quarto_578f98.ipynb` | [Handcalcs.jl official examples](https://raw.githubusercontent.com/co1emi11er2/Handcalcs.jl/master/examples/handcalc_quarto.ipynb) | MIT | LaTeX (`\begin{aligned}` environments) in text |
| `jupyter/math/latexify_examples_fcaa0e.ipynb` | [latexify_py](https://raw.githubusercontent.com/google/latexify_py/main/examples/latexify_examples.ipynb) | Apache-2.0 | LaTeX in text/latex output bundles |
| `jupyter/math/sympy_expressions_e09585.ipynb` | [Blaze](https://raw.githubusercontent.com/blaze/blaze/master/docs/source/_static/notebooks/sympy-expressions.ipynb) | BSD-3-Clause | LaTeX in nbformat v3 `pyout` outputs (legacy ` |
| `latex/math/36640_t_ab6f06.tex` | [Project Gutenberg / Distributed Proofreaders](https://www.gutenberg.org/files/36640/36640-t/36640-t.tex) | Public domain | LaTeX (amsmath) |
| `latex/math/41568_t_c5dd66.tex` | [Project Gutenberg / Distributed Proofreaders](https://www.gutenberg.org/files/41568/41568-t/41568-t.tex) | Public domain | LaTeX (amsmath, custom \Tag macro) |
| `latex/math/apssamp_456d02.tex` | [REVTeX 4.2](https://mirrors.ctan.org/macros/latex/contrib/revtex/sample/aps/apssamp.tex) | LPPL-1.3c | LaTeX (REVTeX 4.2 + amsmath) |
| `latex/math/mathtools_60dab8.tex` | [brucemiller/LaTeXML](https://raw.githubusercontent.com/brucemiller/LaTeXML/master/t/ams/mathtools.tex) | Public domain / CC0-equivalent | LaTeX (mathtools + amsmath) |
| `latex/math/physics_7344b9.tex` | [brucemiller/LaTeXML](https://raw.githubusercontent.com/brucemiller/LaTeXML/master/t/complex/physics.tex) | Public domain / CC0-equivalent | LaTeX (physics package) |
| `latex/math/sampler_af5d02.tex` | [brucemiller/LaTeXML](https://raw.githubusercontent.com/brucemiller/LaTeXML/master/t/math/sampler.tex) | Public domain / CC0-equivalent | LaTeX (amsmath, amsfonts, mathrsfs, mathtools) |
| `latex/math/testmath_232f5d.tex` | [latex3/latex2e](https://raw.githubusercontent.com/latex3/latex2e/develop/required/amsmath/testmath.tex) | LPPL-1.3c | LaTeX (amsmath) |
| `markdown/math/markdown_features_math_equations_d0952e.mdx` | [Docusaurus documentation site](https://raw.githubusercontent.com/facebook/docusaurus/main/website/docs/guides/markdown-features/markdown-features-math-equations.mdx) | MIT | LaTeX via three MDX notations in one file: `$. |
| `markdown/math/mathjax_49c700.md` | [mdBook user guide](https://raw.githubusercontent.com/rust-lang/mdBook/master/guide/src/format/mathjax.md) | MPL-2.0 | LaTeX in mdBook's doubled-backslash delimiters |
| `markdown/math/neural_networks_case_study_aeb5f4.md` | [Stanford CS231n course notes](https://raw.githubusercontent.com/cs231n/cs231n.github.io/master/neural-networks-case-study.md) | MIT | LaTeX in `$$...$$` display blocks plus `\( ... |
| `markdown/math/spe_67468e.markdown` | [Tapkee](https://raw.githubusercontent.com/lisitsyn/tapkee/main/doc/methods/spe.markdown) | BSD-3-Clause | LaTeX in `$...$` / `$$...$$`, with Markdown-es |
| `markdown/math/supported_b0c613.md` | [KaTeX](https://raw.githubusercontent.com/KaTeX/KaTeX/main/docs/supported.md) | MIT | LaTeX in `$...$` inline math, thousands of ins |
| `markup/math/SimpleFormula_a6349f.odf` | [ODF Toolkit](https://raw.githubusercontent.com/tdf/odftoolkit/master/odfdom/src/test/resources/test-input/SimpleFormula.odf) | Apache-2.0 | MathML, standalone ODF formula document (no dr |
| `markup/math/aGHQ_b16faa.qmd` | [Embrace Uncertainty: Mixed-effects models with Julia](https://raw.githubusercontent.com/JuliaMixedModels/EmbraceUncertainty/main/aGHQ.qmd) | MIT | LaTeX in `$$...$$` with Quarto equation cross- |
| `markup/math/bareboat_math_17fcb0.adoc` | [Bareboat Necessities](https://raw.githubusercontent.com/bareboat-necessities/my-bareboat/master/docs/bareboat-math.adoc) | Apache-2.0 | AsciiMath (via bare `:stem:`) |
| `markup/math/chapter_02_52ac82.rmd` | [esl-solutions](https://raw.githubusercontent.com/AlipayAlgorithms/esl-solutions/master/chapter-02.Rmd) | MIT | LaTeX: `$$` wrapping `\begin{equation}` AMS en |
| `markup/math/component_implementing_streaming_2ffd4c.adoc` | [Talend Component Runtime documentation](https://raw.githubusercontent.com/Talend/component-runtime/master/documentation/src/main/antora/modules/ROOT/pages/component-implementing-streaming.adoc) | Apache-2.0 | AsciiMath |
| `markup/math/formula_0225f1.fodp` | [LibreOffice core, Impress unit-test data](https://raw.githubusercontent.com/LibreOffice/core/master/sd/qa/unit/data/odp/formula.fodp) | MPL-2.0 | MathML inline in a flat ODF presentation (offi |
| `markup/math/from_7b6cac.adoc` | [PartiQL Specification v0.3.0](https://raw.githubusercontent.com/partiql/partiql-lang/main/src/from.adoc) | Custom "PartiQL Specification License" | AsciiMath |
| `markup/math/inline_quoted_5ede1e.adoc` | [asciidoctor-doctest](https://raw.githubusercontent.com/asciidoctor-contrib/asciidoctor-doctest/master/data/examples/asciidoc/inline_quoted.adoc) | MIT | AsciiMath and LaTeXMath (inline macros) |
| `markup/math/licao_6_feba57.qmd` | [stats_modelling](https://raw.githubusercontent.com/maxbiostat/stats_modelling/master/notas/licao_6.qmd) | MIT | LaTeX: raw `\begin{align*}` environments plus  |
| `markup/math/paths_32d458.adoc` | [PartiQL Specification v0.3.0](https://raw.githubusercontent.com/partiql/partiql-lang/main/src/paths.adoc) | Custom "PartiQL Specification License" | AsciiMath |
| `markup/math/sensorlib_spec_f243ef.adoc` | [Sony Semiconductor Solutions](https://raw.githubusercontent.com/SonySemiconductorSolutions/mossfw/main/docs/sensorlib_spec.adoc) | Apache-2.0 | AsciiMath |
| `markup/math/var_982761.qmd` | [dass2024](https://raw.githubusercontent.com/tenomoto/dass2024/main/var.qmd) | BSD-3-Clause | LaTeX in `$$...$$`, `\begin{aligned}`, Quarto  |
| `office/math/03_Inferential_20statistics2024_2025_bd7449.pptx` | [Zenodo](https://zenodo.org/api/records/14361416/files/03_Inferential%20statistics2024_2025.pptx/content) | CC-BY-4.0 | OMML inside <a14:m> |
| `office/math/Fermat_general_7d3de0.pptx` | [Zenodo](https://zenodo.org/api/records/15252111/files/Fermat_general.pptx/content) | CC-BY-4.0 | OMML inside <a14:m> |
| `office/math/MG35_1_MathGuide_7e950e.odt` | [The Document Foundation, LibreOffice 3.5 Math Guide](https://wiki.documentfoundation.org/images/8/8b/MG35_1-MathGuide.odt) | CC-BY-3.0 OR GPL-3.0-or-later | MathML with PREFIXED math: namespace and the O |
| `office/math/MG44_MathGuide_ed525b.odt` | [The Document Foundation, LibreOffice 4.4 Math Guide](https://wiki.documentfoundation.org/images/b/bc/MG44-MathGuide.odt) | CC-BY-4.0 OR GPL-3.0-or-later | MathML (default namespace) with StarMath 5.0 a |
| `office/math/MG7001_CrearEditarFormulas_de2112.odt` | [The Document Foundation, Guia de Math 7.2, Chapter 1](https://wiki.documentfoundation.org/images/4/44/MG7001-CrearEditarFormulas.odt) | CC-BY-4.0 OR GPL-3.0-or-later | MathML with StarMath 5.0 annotation |
| `office/math/MG7003_FormulasCalcDrawImpress_0129ab.odt` | [The Document Foundation, Guia de Math 7.2, Chapter 3](https://wiki.documentfoundation.org/images/9/93/MG7003-FormulasCalcDrawImpress.odt) | CC-BY-4.0 OR GPL-3.0-or-later | MathML with StarMath 5.0 annotation |
| `office/math/Manju_20Ghalyan_2d1798.docx` | [Zenodo record 822996, journal article "MATHEMATICAL ](https://zenodo.org/api/records/822996/files/Manju%20Ghalyan.docx/content) | CC-BY-4.0 | OMML |
| `office/math/OpenDocument_v1_2_os_part1_0fdaaa.odt` | [OASIS OpenDocument v1.2 specification, Part 1](https://raw.githubusercontent.com/tdf/odftoolkit/master/xslt-runner/src/test/resources/odf12/OpenDocument-v1.2-os-part1.odt) | OASIS IPR Policy | MathML 1.01 (default namespace) with StarMath  |
| `office/math/OpenDocument_v1_3_cs01_part3_schema_80057c.odt` | [OASIS OpenDocument v1.3 cs01 Part 3](https://raw.githubusercontent.com/tdf/odftoolkit/master/xslt-runner/src/test/resources/odf13/OpenDocument-v1.3-cs01-part3-schema.odt) | OASIS IPR Policy | MathML with StarMath 5.0 annotation, embedded  |
| `office/math/PSAAP_review_presentation_102022_SAND2022_14495_PE_a5d658.pptx` | [Zenodo](https://zenodo.org/api/records/7232101/files/PSAAP_review_presentation_102022-SAND2022-14495-PE.pptx/content) | CC-BY-4.0 | OMML inside <a14:m> |
| `office/math/PejmanJouzdani_f8d8e3.pptx` | [Zenodo](https://zenodo.org/api/records/10407797/files/PejmanJouzdani.pptx/content) | CC-BY-4.0 | OMML inside <a14:m>, with <m:oMathPara> displa |
| `office/math/Single_THz_photon_detector_JuliangLi_ANL_82bc42.pptx` | [Zenodo](https://zenodo.org/api/records/4641119/files/Single_THz_photon_detector_JuliangLi_ANL.pptx/content) | CC-BY-4.0 | OMML inside <a14:m> |
| `office/math/Supplementry_20Material_1e5dc4.docx` | [Zenodo record 19008259, "SUPPLEMENTARY MATERIALS for](https://zenodo.org/api/records/19008259/files/Supplementry%20Material.docx/content) | CC-BY-4.0 | OMML |
| `office/math/Zucker_EAAT_statistics_16c5f9.pptx` | [Zenodo](https://zenodo.org/api/records/7072775/files/Zucker_EAAT_statistics.pptx/content) | CC-BY-4.0 | OMML inside <a14:m> |
| `office/math/editable_04513a.pptx` | [figedit](https://raw.githubusercontent.com/giszzt/figedit/main/assets/examples/ast-reveal/editable.pptx) | MIT | OMML: <a14:m><m:oMathPara><m:oMath>, inside mc |
| `office/math/editable_0c0c46.pptx` | [figedit](https://raw.githubusercontent.com/giszzt/figedit/main/assets/examples/parallel-loops/editable.pptx) | MIT | OMML: <a14:m><m:oMathPara>, inside mc:Alternat |
| `office/math/equation_16f2f6.docx` | [dotnet Open XML SDK test assets](https://raw.githubusercontent.com/dotnet/Open-XML-SDK/main/test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/wordprocessing/equation/equation.docx) | MIT | OMML |
| `office/math/equation_a59623.doc` | [Apache POI test-data/document](https://raw.githubusercontent.com/apache/poi/trunk/test-data/document/equation.doc) | Apache-2.0 | MathML plus a StarMath 5.0 annotation, inside  |
| `office/math/equations_b6ad03.docx` | [Microsoft MarkItDown test files](https://raw.githubusercontent.com/microsoft/markitdown/main/packages/markitdown/tests/test_files/equations.docx) | MIT | OMML |
| `office/math/equations_d0d980.docx` | [docling](https://raw.githubusercontent.com/docling-project/docling/main/tests/data/docx/sources/equations.docx) | MIT | OMML |
| `office/math/math_OOo311_71135a.odt` | [ODF Toolkit](https://raw.githubusercontent.com/tdf/odftoolkit/master/validator/src/test/resources/math_OOo311.odt) | Apache-2.0 | MathML, prefixed math: namespace + OOo modifie |
| `office/math/pascal_digital_binomial_theorem_Senior_20Seminar_20Thesi_82393b.pptx` | [Zenodo](https://zenodo.org/api/records/20702180/files/pascal_digital_binomial_theorem(Senior%20Seminar%20Thesis,%20%ED%95%99%EC%82%AC%20%EC%84%B8%EB%AF%B8%EB%82%98%20%EB%B0%9C%ED%91%9C%20%EC%9E%90%EB%A3%8C,%20%EC%9B%90%EB%B3%B8).pptx/content) | CC-BY-4.0 | OMML inside <a14:m> |
| `office/math/strict_20math_53ebf7.docx` | [docx4j sample documents](https://raw.githubusercontent.com/plutext/docx4j/VERSION_17_0_3/docx4j-samples-docx4j/sample-docs/strict/strict%20math.docx) | Apache-2.0 | OMML (ISO/IEC 29500 Strict namespace) |
| `office/math/table_with_equations_f14832.docx` | [docling DOCX test corpus](https://raw.githubusercontent.com/docling-project/docling/main/tests/data/docx/sources/table_with_equations.docx) | MIT | OMML |
| `office/math/tdf119223_394ffc.odp` | [LibreOffice core, Impress unit-test data](https://raw.githubusercontent.com/LibreOffice/core/master/sd/qa/unit/data/odp/tdf119223.odp) | MPL-2.0 | MathML with StarMath 5.0 annotation |
| `office/math/tdf130614_9b6224.ods` | [LibreOffice core, Calc UI-test data](https://raw.githubusercontent.com/LibreOffice/core/master/sc/qa/unit/uicalc/data/tdf130614.ods) | MPL-2.0 | MathML with StarMath 5.0 annotation |
| `office/math/tdf159046_e964cb.ods` | [LibreOffice core, Calc UI-test data](https://raw.githubusercontent.com/LibreOffice/core/master/sc/qa/unit/uicalc/data/tdf159046.ods) | MPL-2.0 | MathML with StarMath 5.0 annotation, embedded  |
| `office/math/testMSEquation_govdocs_863534_a6c49e.doc` | [Apache Tika test corpus](https://raw.githubusercontent.com/apache/tika/main/tika-parsers/tika-parsers-standard/tika-parsers-standard-modules/tika-parser-microsoft-module/src/test/resources/test-documents/testMSEquation-govdocs-863534.doc) | Apache-2.0 | MTEF (Microsoft Equation Editor 3.0 / Design S |
| `office/math/testWORD_2006ml_9696cd.docx` | [Apache Tika microsoft-parser test documents](https://raw.githubusercontent.com/apache/tika/main/tika-parsers/tika-parsers-standard/tika-parsers-standard-modules/tika-parser-microsoft-module/src/test/resources/test-documents/testWORD_2006ml.docx) | Apache-2.0 | OMML |
| `office/math/unknown_content_bda4e1.odt` | [ODF Toolkit](https://raw.githubusercontent.com/tdf/odftoolkit/master/odfdom/src/test/resources/test-input/unknown-content.odt) | Apache-2.0 | MathML with StarMath 5.0 annotation |
| `office/math/w11_w11_fore0ww8_8441b1.rtf` | [dotnet/wpf-test](https://raw.githubusercontent.com/dotnet/wpf-test/main/src/Test/Editing/FeatureTests/Data/rtf/rtfcit/w11_w11_fore0ww8.rtf) | MIT | RTF EQ field instructions (\f fraction, \i int |
| `org/math/00_introduccion_02ccfe.org` | [agarbuno/aprendizaje-estadistico](https://raw.githubusercontent.com/agarbuno/aprendizaje-estadistico/latest/notas/00-introduccion.org) | MIT | LaTeX `\begin{align}` and inline `$...$` in Or |
| `org/math/01_montecarlo_c9ecc6.org` | [agarbuno/modelacion-bayesiana](https://raw.githubusercontent.com/agarbuno/modelacion-bayesiana/latest/notas/01-montecarlo.org) | MIT | LaTeX `\begin{align}` and inline `$...$` in Or |
| `org/math/02_mcmc_246b17.org` | [agarbuno/modelacion-bayesiana](https://raw.githubusercontent.com/agarbuno/modelacion-bayesiana/latest/notas/02-mcmc.org) | MIT | LaTeX `\begin{align}` environments and inline  |
| `org/math/Org_Mode_885465.org` | [caiorss/Emacs-Elisp-Programming](https://raw.githubusercontent.com/caiorss/Emacs-Elisp-Programming/master/Org-Mode.org) | Unlicense | LaTeX `\begin{equation}` / `\begin{align}` env |
| `org/math/latex_0d83c6.org` | [orgajs](https://raw.githubusercontent.com/orgapp/orgajs/main/docs/advanced/latex.org) | MIT | Org mode `$$...$$`, `\(...\)`, `\[...\]` and ` |
| `pdf/math/19930091059_e5a481.pdf` | [NACA Report 1135, "Equations, Tables, and Charts for](https://ntrs.nasa.gov/api/citations/19930091059/downloads/19930091059.pdf) | Public domain | SCANNED: 70 pages of 300 dpi bitonal CCITT-G4  |
| `pdf/math/19930093947_a3f534.pdf` | [NACA Technical Memorandum 1278, "General solution of](https://ntrs.nasa.gov/api/citations/19930093947/downloads/19930093947.pdf) | Public domain | SCANNED: 21 pages of 300 dpi bitonal CCITT-G4  |
| `pdf/math/20100014819_ba4d91.pdf` | [NASA Technical Memorandum 20100014819, "Approximate ](https://ntrs.nasa.gov/api/citations/20100014819/downloads/20100014819.pdf) | Public domain | PDF text layer; equations are Word/Equation-Ed |
| `pdf/math/2306_08071_597a81.pdf` | [arXiv](https://arxiv.org/pdf/2306.08071) | CC-BY-4.0 | PDF text layer, LaTeX/Computer-Modern glyph ru |
| `pdf/math/2502_20028_047181.pdf` | [arXiv](https://arxiv.org/pdf/2502.20028) | CC-BY-4.0 | PDF text layer, LaTeX glyph runs; A4 page size |
| `pdf/math/2511_07120_8176dc.pdf` | [arXiv](https://arxiv.org/pdf/2511.07120) | CC-BY-4.0 | PDF text layer, Unicode-mapped math glyph runs |
| `pdf/math/CollegeAlgebra_OP_7d1fcd.pdf` | [OpenStax](https://assets.openstax.org/oscms-prodcms/media/documents/CollegeAlgebra-OP.pdf) | CC-BY-4.0 | PDF text layer, but built-up fractions/radical |
| `pdf/math/amsldoc_642b4e.pdf` | [American Mathematical Society](https://mirrors.ctan.org/macros/latex/required/amsmath/amsldoc.pdf) | LPPL-1.3c | PDF text layer, pdfTeX Type1 math fonts; mixes |
| `pdf/math/journal_pcbi_1012015_type_printable_1eeb41.pdf` | [PLOS Computational Biology 2024, "Modeling single ce](https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1012015&type=printable) | CC-BY-4.0 | PDF text layer, but with a custom symbol-font  |
| `pdf/math/physica_manual_bcb494.pdf` | [typst-physics](https://raw.githubusercontent.com/Leedehai/typst-physics/master/physica-manual.pdf) | MIT | PDF text layer, Typst-generated Unicode math g |
| `pdf/math/testmath_e28157.pdf` | [American Mathematical Society](https://mirrors.ctan.org/macros/latex/required/amsmath/testmath.pdf) | LPPL-1.3c | PDF text layer, pdfTeX Type1 math fonts; the A |
| `rst/math/comprehensive_math_test_276a5e.rst` | [Docutils](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/input/data/comprehensive-math-test.rst) | Public domain | LaTeX inside reST `.. math::` and `:math:` rol |
| `rst/math/fitting_71d4d8.rst` | [lmfit-py](https://raw.githubusercontent.com/lmfit/lmfit-py/master/doc/fitting.rst) | BSD-3-Clause | LaTeX inside reST `.. math::`, including `:now |
| `rst/math/g_functions_7277dd.rst` | [SymPy](https://raw.githubusercontent.com/sympy/sympy/master/doc/src/modules/integrals/g-functions.rst) | BSD-3-Clause | LaTeX (with AMS `cases`) inside reST `.. math: |
| `rst/math/linear_model_1a957c.rst` | [scikit-learn](https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/doc/modules/linear_model.rst) | BSD-3-Clause | LaTeX inside reST `.. math::` directive and `: |
| `rst/math/lombscargle_bedb55.rst` | [Astropy](https://raw.githubusercontent.com/astropy/astropy/main/docs/timeseries/lombscargle.rst) | BSD-3-Clause | LaTeX inside reST `.. math::` |
| `rst/math/math_776aea.rst` | [Docutils functional test suite](https://raw.githubusercontent.com/docutils/docutils/master/docutils/test/functional/input/data/math.rst) | Public domain | LaTeX inside reST `.. math::` (prefix and post |
| `rst/math/math_de2679.rst` | [Sphinx](https://raw.githubusercontent.com/sphinx-doc/sphinx/master/tests/roots/test-ext-math/math.rst) | BSD-2-Clause | LaTeX inside reST `.. math::` with `:label:`,  |
| `rst/math/mixed_linear_524bae.rst` | [statsmodels](https://raw.githubusercontent.com/statsmodels/statsmodels/main/docs/source/mixed_linear.rst) | BSD-3-Clause | LaTeX inside reST `.. math::` and `:math:` |
| `rst/math/neutron_physics_1490f3.rst` | [OpenMC](https://raw.githubusercontent.com/openmc-dev/openmc/develop/docs/source/methods/neutron_physics.rst) | MIT | LaTeX inside reST `.. math::` with `:label:` e |
| `rst/math/physical_models_c61dfa.rst` | [Astropy](https://raw.githubusercontent.com/astropy/astropy/main/docs/modeling/physical_models.rst) | BSD-3-Clause | LaTeX inside reST `.. math::` |
| `typst/math/main_979fe4.typ` | [typst/packages](https://raw.githubusercontent.com/typst/packages/main/packages/preview/ntnu-physics-report-replica/0.1.0/template/main.typ) | MIT | Typst math |
| `typst/math/main_c87a40.typ` | [typst/packages](https://raw.githubusercontent.com/typst/packages/main/packages/preview/clean-math-paper/0.2.8/template/main.typ) | MIT | Typst math |
| `typst/math/manual_4ee3cf.typ` | [typst/packages](https://raw.githubusercontent.com/typst/packages/main/packages/preview/lacy-ubc-math-project/0.2.0/manual.typ) | MIT | Typst math |
| `typst/math/physica_manual_b4d792.typ` | [Leedehai/typst-physics](https://raw.githubusercontent.com/Leedehai/typst-physics/master/physica-manual.typ) | MIT | Typst math |
| `xml/math/7f8rqRq4vSnJ7B738VKMKqF_11b207.xml` | [SciELO](https://raw.githubusercontent.com/scieloorg/packtools/master/tests/fixtures/htmlgenerator/latex/7f8rqRq4vSnJ7B738VKMKqF.xml) | BSD-2-Clause | LaTeX in <tex-math> (with \documentclass/amsma |
| `xml/math/Tutorial_2006_4bafe3.xml` | ["Learning Modern 3D Graphics Programming"](https://raw.githubusercontent.com/paroj/gltut/master/Documents/Positioning/Tutorial%2006.xml) | MIT | DocBook <mathphrase> plain-text math; <equatio |
| `xml/math/elife_41046_v2_622635.xml` | [eLife Sciences](https://raw.githubusercontent.com/elifesciences/elife-article-xml/master/articles/elife-41046-v2.xml) | CC-BY-4.0 | MathML (mml:-prefixed), JATS 1.x disp-formula  |
| `xml/math/equation_004_a5d8f4.xml` | [The DocBook Project](https://raw.githubusercontent.com/docbook/xslTNG/main/src/test/resources/xml/equation.004.xml) | MIT | MathML embedded in DocBook 5 <equation> |
| `xml/math/equation_005_a1808c.xml` | [The DocBook Project](https://raw.githubusercontent.com/docbook/xslTNG/main/src/test/resources/xml/equation.005.xml) | MIT | Verbatim LaTeX in DocBook <mathphrase role="te |
| `xml/math/example_04c981.xml` | [transpect / mml2tex](https://raw.githubusercontent.com/transpect/mml2tex/master/example/example.xml) | BSD-2-Clause | MathML (mml:-prefixed) inside DocBook 5 <equat |
| `xml/math/f_5dcc94.xml` | [SciELO](https://raw.githubusercontent.com/scieloorg/packtools/master/tests/fixtures/htmlgenerator/mmlmath/f.xml) | BSD-2-Clause | MathML, both default-namespace and mml:-prefix |
| `xml/math/journal_pcbi_1005589_type_manuscript_58c02e.xml` | [PLOS Computational Biology](https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1005589&type=manuscript) | CC-BY-4.0 | MathML inside JATS <alternatives>, JATS Journa |
| `xml/math/manuscript_933c4c.xml` | [Texture](https://raw.githubusercontent.com/substance/texture/master/data/kitchen-sink/manuscript.xml) | MIT | LaTeX in <tex-math> CDATA, JATS disp-formula / |

Committed: 136. The binary formats among them live in the bucket and are pinned by `corpus.lock.json`, following the storage split in `README.md`.

## Reference only, not committed

These carry ShareAlike, GFDL or GPL terms, or upstream metadata that disagrees with the project's own stated licence. The redistribution policy in `LICENSES.md` keeps such content out of the repository, so their provenance is recorded without vendoring the bytes.

| document | source | licence |
|---|---|---|
| `2_1_common_math_84f243.adoc` | [Modelica Association](https://raw.githubusercontent.com/modelica/fmi-standard/main/docs/2_1_common_math.adoc) | CC-BY-SA-4.0 |
| `EquationAsScientificNumbering_7e7710.docx` | [LibreOffice core, sw/qa/extras/ooxmlexport/data](https://raw.githubusercontent.com/LibreOffice/core/master/sw/qa/extras/ooxmlexport/data/EquationAsScientificNumbering.docx) | COPYLEFT - FLAGGED |
| `README_38c17d.asciidoc` | [Hilscher / Muhkuh test framework](https://raw.githubusercontent.com/muhkuh-sys/org.muhkuh.tests-ramtest/master/README.asciidoc) | GPL-2.0 |
| `linear_algebra_e4ca4c.epub` | ["A First Course in Linear Algebra" by Robert A. Beez](https://github.com/IDPF/epub3-samples/releases/download/20230704/linear-algebra.epub) | GNU FDL 1.2 or later |
| `lln_clt_5360eb.md` | [QuantEcon](https://raw.githubusercontent.com/QuantEcon/lecture-python-intro/main/lectures/lln_clt.md) | CC-BY-SA-4.0 |
| `math_1a3c42.fb2` | [pandoc](https://raw.githubusercontent.com/jgm/pandoc/main/test/fb2/math.fb2) | GPL-2.0-or-later |
| `math_8f5f31.odp` | [LibreOffice core, Impress unit-test data](https://raw.githubusercontent.com/LibreOffice/core/master/sd/qa/unit/data/odp/math.odp) | MPL-2.0 |
| `math_mso2k7_597eb9.docx` | [LibreOffice core, sw/qa/extras/ooxmlexport/data](https://raw.githubusercontent.com/LibreOffice/core/master/sw/qa/extras/ooxmlexport/data/math-mso2k7.docx) | COPYLEFT - FLAGGED |
| `math_nary_5b4ff9.docx` | [LibreOffice core, sw/qa/extras/ooxmlexport/data](https://raw.githubusercontent.com/LibreOffice/core/master/sw/qa/extras/ooxmlexport/data/math-nary.docx) | COPYLEFT - FLAGGED |
| `mathtype_569f25.docx` | [LibreOffice core, sw/qa/extras/ooxmlexport/data](https://raw.githubusercontent.com/LibreOffice/core/master/sw/qa/extras/ooxmlexport/data/mathtype.docx) | COPYLEFT - FLAGGED |
| `writer_3efc89.org` | [Pandoc test suite](https://raw.githubusercontent.com/jgm/pandoc/main/test/writer.org) | FLAG |
| `writer_db63ab.fb2` | [pandoc](https://raw.githubusercontent.com/jgm/pandoc/main/test/writer.fb2) | GPL-2.0-or-later |

Reference only: 12.
