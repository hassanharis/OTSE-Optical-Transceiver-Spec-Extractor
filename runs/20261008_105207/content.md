## Automated Extraction of Parameters from Optical Transceiver Datasheets using Multi-Stage LLM Pipeline 

Haris Hassan _Nokia Carnaxide, Portugal haris.hassan@nokia.com_ 

João Pedro _Nokia, Carnaxide, Portugal Instituto de Telecomunicações, IST joao.pedro@nokia.com_ 

Luís Gonçalo Cancela _Iscte—Instituto Universitario de Lisboa Instituto de Telecomunicações, IST luis.cancela@iscte-iul.pt_ 

_**Abstract**_ **— Optical transceiver datasheets are essential resources for network planning, interoperability assessment, procurement, and optical system design. However, automated extraction of their specifications remains difficult because of vendor-specific layout heterogeneity, mixed parameter scopes, inconsistent terminology and implicit operational modes. The transition from fixed-configuration to flex-rate tunable coherent modules further exacerbates these challenges in inventory modeling and device tracking. Existing rule-based parsers, fixedschema databases, and single-pass large language model (LLM) extraction methods struggle to correctly associate parameters with the operational conditions under which they apply. This paper presents a progressive mode-aware extraction framework that converts optical transceiver PDF datasheets into schemavalidated structured records. Unlike conventional top-down extraction approaches that assume a predefined hierarchy, the proposed framework discovers operational structures and mode relationships before performing scoped parameter extraction and schema synthesis. The system combines layout-aware PDF parsing, schema-grounded prompting, multi-stage LLM orchestration, and operational mode synthesis. The core contribution is a progressive mode discovery pipeline that treats operational modes as first-class entities rather than derived metadata. This enables robust resolution of parameter scope ambiguity across coherent and direct-detect optical modules. The framework supports explicit, fixed, and parametric mode representations while preserving inheritance relationships and conditional constraints. Evaluated on 35 publicly available optical transceiver datasheets, proposed system achieves over 90% mode discovery and Field-level fidelity scores, demonstrating improved field extraction accuracy, mode-association fidelity, and schema consistency compared with baseline zero-shot extraction. The resulting system provides a scalable foundation for capabilitydriven inventory management, interoperability analysis, automated transceiver compliance intelligence, AI-driven optical network planning and machine-readable knowledge bases.** 

## _**Keywords: Optical transceiver, document intelligence, large language models, datasheet extraction, operational modes, schema inference, optical networking automation.**_ 

## I. INTRODUCTION 

The automation of optical network planning and operations increasingly depends on machine-readable representations of transceiver capabilities. Engineers rely on the critical parameters of optical transceivers such as wavelength ranges, modulation formats, FEC, launch power, receiver sensitivity, OSNR, and baud rate to evaluate interoperability, link feasibility, optical budgets, and operational constraints across network deployments. These values are published by vendors in product datasheets. 

Despite describing functionally similar device categories, datasheets vary substantially across vendors in structural 

hierarchy, layout, terminology, and representational convention. Modern coherent and pluggable modules expose hundreds of operational configurations, exhibit mode-dependent performance, and intermix device-level with mode-level specifications. Parameters are frequently conditional—valid only under specific modulation schemes, FEC settings, or wavelength configurations—and these dependencies are rarely stated explicitly. Instead, they are distributed across tables, footnotes, and prose, rendering automated extraction a semantic scope resolution problem. For a value such as "Receiver Sensitivity: −12 dBm", an extraction system must infer whether it applies globally, to a specific mode, a particular wavelength, a host interface or conditional FEC configuration, and whether it is locally scoped, inherited, or overridden. 

Prior work on scientific and technical document parsing has addressed structured table parsing, relation extraction from scientific text, and domain-specific named entity recognition [1] [2] [3]. Applying these methods directly to the transceiver domain fails because the parameters shift with implicit operating mode, footnote-encoded conditions, varying link configuration. Single-pass LLM extraction can interpret heterogeneous technical prose but fails on complex datasheets because it forces unstructured, multi-conditioned data into a fixed schema all at once. This leads to incorrect parameter mapping, duplicate data, and hallucinated relationships [4] [5]. 

The proposed progressive, mode-aware framework solves this by breaking the extraction down into a multi-stage pipeline that identifies operational structures and mode relationships, before performing scope-aware extraction and adaptive schema synthesis. Each step is independently prompted, observable, and verifiable [6] [7]. In this work we make the following contributions: 

- **Parameter Decomposition:** Tx and Rx parameters are decomposed into mode-level variables that configures and measure the performance of module's digital signal processor (DSP) and control plane to accommodate highly diverse optical transceiver families. 

- **Progressive Mode Discovery:** structure-first extraction strategy identifies operational modes before parameter synthesis. A mode-synthesis graph discovers atomic parameters, maps co-occurrence relationships, classifies the structural taxonomy of datasheet across three device classes — explicit, fixed, or parametric — and synthesizes validated per-mode records. 

- **Semantic scope-resolution:** A method that explicitly resolves whether parameters are global, mode-specific, conditional, inherited, or redundant during extraction, reducing post-hoc ambiguity and phantom data. 

979-8-3195-4420-9/26/$31.00 ©2026 IEEE 

- **Dynamic Schema-Grounded Prompting:** schema generation mechanism that adapts hierarchy depth and parameter ownership to module family complexity. A central schema registry defined by Pydantic models injects extraction contract into prompt templates, ensuring consistency with downstream validation. [8] 

- **Performance Scope-Resolution:** introduced as a mandatory intermediate stage; experiments demonstrate that attaching parameters to modes without prior scope classification produces systematic errors for footnoteconditioned and multi-mode datasheets. 

A comprehensive evaluation of pipeline is conducted on 35 datasheets spanning the identified complexity classes, demonstrating its superior performance and practical utility in universal extraction of parameters from transceiver datasheets. 

## II. PROBLEM FORMULATION 

## _A. Structural Complexity and Semantic Heterogeneity_ 

Optical transceiver datasheets combine technical values with operational notes, standards reference, marketing material, and conditional constraints. A single datasheet may contain deeply nested tables, multi-column layouts, detached footnotes, operational-mode-dependent parameter blocks, and non-standard symbols or units. Structural inconsistency is further compounded by vendor-specific terminologies: parameters such as “Tx Power,” “Launch Power,” and “Optical Output Power” may refer to the same specification across different documents. 

## _B. Parameter Scope Ambiguity and Multi-Granularity Semantics_ 

With the emergence of configurable, tunable coherent transceivers, datasheets have become semantic bundles of capabilities and constraints. The same parameter name may exist at multiple abstraction levels depending on module architecture, vendor convention, and operational mode. For instance, "Tx Power" is a module-level specification for SFP+, a channel-level specification for CFP2, and a mode-specific specification for coherent modules. [9] This creates a semantic ownership inference problem in which the extraction system must determine whether a value belongs to the module, channel, operational mode, wavelength, FEC configuration, or another conditional entity. 

The challenge becomes more pronounced for parameters such as receiver sensitivity. Across vendors, receiver sensitivity may appear as a single global module value, modedependent value, a value conditioned on modulation format and FEC or vary by wavelength or lane. As a result, ownership hierarchies vary significantly, ranging from: 

- transceiver → rx_sensitivity 

to deeply nested structures such as: 

- transceiver → operational_mode → FEC → wavelength → rx_sensitivity 

Both hierarchies coexist across vendors. Fixed relational schemas cannot adequately represent this variability because a single schema column cannot simultaneously capture global, conditional, and hierarchical semantics. [10] Accurate extraction therefore requires discovery of document-specific mode structures before parameter assignment can occur. 

## _C. Conditional and Mode-Dependent Parameterization_ 

Many optical parameters exist only under specific operational conditions. Chromatic dispersion tolerance, for instance, may be entirely absent in grey-optic SFP+ modules yet appear as multiple conditional values in coherent transceivers depending on modulation mode (e.g., 100GQPSK versus 400G-16QAM). This represents not only a scope variation but also structural heterogeneity: a parameter may be globally absent in one device family while conditionally hierarchical in another. Mode representation itself also varies considerably across coherent transceiver datasheets. Operational behavior may depend on software configuration, modulation format, baud rate, wavelength tuning, or FEC selection. Typical examples include: 

- FEC-dependent link budgets in 400G/800G modules, 

- tunable wavelengths and dynamic channel spacing, 

- adaptive reach optimization through modulation formats (e.g. QPSK, 8QAM), baud-rate adjustments, or spectrum reallocation. 

These operational modes generally appear in three forms: 

1. **Explicit** - modes are enumerated in tables mapping rates, modulation formats, and performance metrics to named operating points. 

2. **Fixed** - only a single operational configuration. 

3. **Parametric-** tunable parameter ranges, implying a continuous combinatorial operating space rather than discrete modes. 

Each representation requires a different extraction strategy, and the correct interpretation often depends on higher-level analysis of document layout rather than localised parsing alone. 

## _D. Distributed Evidence and Footnote Semantics_ 

Critical constraints are rarely localized within a single section of a datasheet. In coherent transceiver documentation, modulation format may appear in an ordering table, OSNR tolerance in an optical performance table, and FEC requirements within a compliance section. Relationships between these parameters must therefore be inferred through multi-section evidence aggregation. Footnotes introduce an additional layer of semantic complexity. A sensitivity value, for example, may only apply under a specific FEC configuration with a defined overhead percentage. Such footnotes transform otherwise simple scalar values into conditional engineering constraints that modify the interpretation of associated parameters. 

Hence, correct extraction requires conditional constraint resolution, footnote association and interpretation, crosssectional relationship synthesis, and graph-level semantic modeling. These requirements fundamentally undermine naive OCR pipelines, retrieval-augmented generation, and static relational schemas, all of which assume that parameter semantics are localized, explicit, and structurally uniform. 

## III. BACKGROUND AND RELATED WORK 

## _A. Information Extraction from Technical Documents_ 

Automated information extraction from technical documents has been widely studied in scientific and engineering domains. Traditional approaches emphasize named entity recognition, relation extraction, and template-based parsing. Structured 

extraction methods have been successfully applied to technical products including electronic component datasheets, where relatively stable document layouts and vendor conventions allow high-precision extraction. [4] However, their underlying assumptions break down in optical transceiver datasheets. 

Unlike conventional specification sheets, optical datasheets describe hierarchical, mode-conditioned capability spaces in which parameters vary across operational dimensions. As a result, parameter semantics are often distributed across multiple evidence sources—including tables, footnotes, standards reference, and narrative constraints—while their interpretation depends on contextual scope (e.g., module-level, channel-level, or mode-specific). This coupling between specification data and operational context limits the effectiveness of conventional extraction pipelines and requires more context-aware approaches to information extraction. 

## _B. Optical Network Data Modelling_ 

Standardization efforts in optical networking have defined structured representations for optical device capabilities. The IETF working groups have developed YANG models for optical networks, including topology representation (e.g., RFC 9093) and device-level modeling of WDM systems [9]. Similarly, OpenConfig provides vendor-neutral YANG models that distinguish between operational state and configuration state for optical transport devices. Industry specifications such as OpenZR+ define interoperable coherent pluggable modes and associated parameter constraints. 

These frameworks collectively define the target schema space for representing optical devices in a normalized and machine-readable form. However, the datasheets remain inconsistently structured and frequently lacks explicit mapping between specification tables and standard network models. Extracting these standard models from datasheets is therefore a key to automated schema generation. 

## _C. Multi-Stage LLM Pipelines_ 

Large language models (LLMs) provide a flexible mechanism for structured information extraction in constrained explicit schemas from heterogeneous technical text. Prior work has demonstrated that reasoning-oriented prompting strategies such as chain-of-thought improve multistep inference, while structured decoding techniques, including function calling and constrained JSON generation, improve output validity and machine interpretability. Applications in domains such as financial document extraction have shown that LLM-based systems can achieve performance comparable to fine-tuned extraction pipelines. [11] 

However, in engineering-grade specifications such as optical datasheets, the primary challenge is not syntactic correctness of extracted JSON, but semantic fidelity and schema consistency under conditional parameterization. In particular, LLMs are prone to conflating operational modes, misattributing parameter scopes, or hallucinating values when confronted with incomplete or ambiguously structured tables (e.g., confusing typical vs. maximum launch power or mixing client-side and line-side constraints). 

To address these limitations, multi-stage LLM frameworks have been explored in code synthesis, scientific reasoning, and complex QA systems, where tasks are decomposed into sequential subtasks with intermediate validation. [12] This decomposition principle is directly applicable to optical transceiver extraction, where classification of operational 

modes, parameter normalization and scope resolution require distinct reasoning contexts and error controls. 

## IV. SYSTEM DESIGN 

## _A. Data Collection_ 

A corpus of 35 optical transceiver datasheets was assembled by downloading publicly available PDFs from the product portals of 6 vendors. Datasheets were selected to represent diversity in product tier and document production quality. Table 1 shows distribution of datasheets orpus across vendors and form factors. 

_Table 1. Datasheet Corpus distribution by form factor_ 

|**Form Factor**|**Datasheets**|**Vendors**|**Avg. Pages**|
|---|---|---|---|
|SFP / SFP+|8|3|6.2|
|QSFP28|9|4|8.1|
|QSFP-DD|7|3|9.7|
|CFP2|6|3|11.3|
|OSFP|5|3|10.5|
|**Total**|**35**|**6**|**8.9**|



## _B. Annotation Schema_ 

Optical transceiver specifications are categorised into performance (what module achieves) and configuration (what you can choose) that are combined to represent operational modes. Furthermore, the module identity, physical specs and claimed standards are also collected. The operational modes can be explicit, fixed, and parametric. Numerical values are canonicalized to SI units and ranges were expressed as (min, max) tuples where applicable. 

## _C. Schema Registry and Prompt Grounding:_ 

Pydantic models serve as the single source of truth for the extraction contract. Prompt templates reference schemas through a registry that serialises model field names, types, and documentation strings into the prompt at assembly time. This ensures that if the schema is updated, all prompts that reference it are automatically updated, eliminating the drift between prompts and validation code that is common in ad hoc extraction systems. [13] 

## V. MULTI-STAGE PIPELINE 

Figure 1 provides a high-level view of pipeline along with the evaluation framework of its different parts. 

## _A. PDF Ingestion and Pre-processing_ 

We tested 7 different layout-aware parsers to ensure optimal extraction quality, ultimately selecting the bestperforming solution for our pipeline. Prior to stage execution, the input PDF is processed by the selected layout-aware parser (using Docling) to yield markdown representation of pdf. 

Docling was chosen for its superior performance across three key metrics: **Table Cell Accuracy (TCA)** , **Footnote Linkage Score (FLS)** , and **Structure Score (SS)** . The tierweighted scores for all reviewed parsers are shown in Table 2 

_Table 2. Performance comparison of different parsers_ 

|**Parser**|**TCA**|**FLS**|**SS**|**Speed**|
|---|---|---|---|---|
|docling|0.8521|0.7284|0.8983|0.6977|
|unstructured_hires|0.8485|0.7284|0.8499|0.6751|
|marker|0.8080|0.5972|0.8336|0.5691|
|pymupdf4llm|0.6681|0.4486|0.8200|0.8455|
|unstructured_fast|0.0000|0.2539|0.4000|0.9535|



_Figure 1. High level architecture diagram of Proposed multi-stage LLM pipeline along with Key performance indicators (KPIs), inputs and stages_ 

**==> picture [431 x 100] intentionally omitted <==**

**==> picture [431 x 100] intentionally omitted <==**

More results are available in Github repository [14]. 

## _B. Atomic Parameter Extraction_ 

Stage B extracts the structured evidence required for downstream operational reasoning. The objective is not to immediately construct the final schema, but to recover the primitive technical entities and relationships embedded within heterogeneous datasheet layouts. The extraction targets include operational parameters such as data rate, modulation format, FEC type, baud rate, channel spacing, optical power, and dispersion limits, together with physical device attributes including form factor, connector type, management interface, and power consumption. The prompt constrains the model to return only schema-valid structured output and explicitly suppresses explanatory or marketing-oriented text [15]. 

In addition to scalar parameter extraction, the stage identifies repeated parameter tuples and co-varying value groups. Repeated combinations of data rate, modulation format, FEC, baud rate, and channel spacing are treated as evidence that the document describes multiple operational modes rather than a single static configuration. 

## _C. Mode Discovery and Context Classification_ 

Stage C discovers the operational structure of the device and synthesizes stable mode entities prior to parameter attachment. This ordering is necessary because direct extraction into a fixed schema frequently produces incorrect associations between parameters and operational configurations. The system classifies the datasheet into one of following operational structure categories: 

- **Fixed** - a single operating configuration; 

- **Explicit** - operational modes enumerated through tables, rows, or bullet structures; 

- **Parametric** - tunable operating spaces defined by ranges and option sets; 

For explicit structures, each discovered mode receives a stable mode_id anchor derived using following priority order: 

- CMIS application code, 

- MSA identifier combined with data rate, 

- Sequential row index. 

CMIS application codes are preferred because they provide vendor-independent operational identifiers defined by open standards. For parametric devices, the system constructs a mode_envelope representation instead of enumerating all possible operating combinations. The envelope stores supported parameter ranges and discrete option sets defining the valid operating space. 

The operational context classifies the signal-processing unit as coherent or direct-detect. Classification is performed through evidence aggregation rather than keyword matching. For example, the simultaneous presence of DP-16QAM modulation, soft-decision FEC, OSNR specs, and high chromatic dispersion tolerance strongly indicates a coherent interface even if the term coherent does not explicitly appear in the datasheet. The device class classifies the hardware entity as pluggable, transponder, amplifier, or unknown using formfactor mentions, MSA compliance declarations, clientinterface structure, and architectural terminology. The resulting classification determines the schema template used during final entity synthesis and prevents structural mismatches between incompatible device families. 

## _D. Scope-Aware Parameter Extraction_ 

Stage D performs semantic scope resolution before attaching parameters to operational modes. This stage constitutes the central methodological contribution of the framework. This approach eliminates the systematic errors native to conventional extract-then-attach systems that fails on conditional, mode-dependent, or footnotes-qualified values. Table 3 provides an overview of scopes and assignment criteria 

_Table 3. Scope Taxonomy and Assignment Criteria_ 

|**Scope Class**|**Assignment Criterion**|**Representation**|
|---|---|---|
|global|Single occurrence without mode<br>variation or footnote|Attached directly<br>to device entity|
|mode_specific|Appears within mode-indexed<br>structures or co-varies with<br>operationalprimitives|Attached to<br>corresponding<br>mode_id|
|conditional|Qualified by footnotes or<br>operational constraints|Stored with<br>conditions<br>metadata|
|mode_envelope|Defines a parametric range rather<br>than a discrete instance|Attached to<br>mode_envelope|



Conditional parameters are preserved as structured records containing the value, parsed condition text, footnote reference, and provenance metadata. Multiple conditional variants of the same parameter are retained independently rather than merged into a single scalar value. This preserves the full engineering semantics of datasheet, avoiding lossy disambiguation during extraction. 

## _E. Schema Synthesis and Validation_ 

Stage E synthesizes the final machine-readable transceiver entity by combining the outputs of the previous stages into a schema-validated representation. Mode-specific parameters are attached to their corresponding mode_id entries, while globally scoped parameters are propagated as shared defaults subject to override by mode-level values. Conditional parameters are preserved as independent condition-bearing records, and parametric devices retain their envelope representation rather than being expanded into combinatorial mode enumerations. The resulting entity includes: 

- operational modes, 

- physical device attributes, 

- performance specifications, 

- provenance metadata, 

- schema validation flags, 

- operational context classification, 

- and device-class annotations. 

Final validation enforces schema consistency, removes duplicate field assignments, normalizes units and terminology, and verifies mode-to-parameter relationships before export into the structured knowledge representation. 

## VI. RESULTS DISCUSSION 

Experiments were run on zero-shot LLM (No stages), ablated pipeline (no Stage D), and proposed pipeline using Qwen2.5-32B-Instruct-Q4_K_M LLM model running locally on GPU. Three systems were evaluated against following key performance indicators (KPIs): 

- **Field-level fidelity** (FE): % of all annotatable fields extracted with correct value and correct schema location. 

- **Scope accuracy** (SE): % of mode-specific or conditional fields that are attached to the correct mode. 

- **Mode discovery** (Mdisc): Modes correctly identified 

- **Mode population completeness** (Mpop): Params per mode complete 

- **Condition fidelity** (CF): Footnote constraints preserved 

- Figure 2 presents the mean key performance indicators 

- (KPI) scores for all three systems across the 35-PDFs corpus. 

_Figure 2. KPI comparison based on mean score values of FE, SE, Mdisc, Mpop, and CF for three systems on 35-document corpus._ 

**==> picture [232 x 122] intentionally omitted <==**

**----- Start of picture text -----**<br>
Zero-shot LLM Ablated pipeline Proposed pipeline<br>10090 91.3 87.6 86.2 91 82.7<br>75.6<br>80 69.3 67.4<br>70 57.4 61.4 55.3<br>60<br>50<br>40 31.8<br>30 22.1<br>20<br>10 3.7 4.2<br>0<br>FE (%) SE (%) Mdisc % Mpop (%) CF %<br>**----- End of picture text -----**<br>


The proposed pipeline achieves a mean field-level fidelity (FE) of 91.3%, compared to 75.6% for the ablated variant (pipeline without Stage D) and 57.4% for the zero-shot LLM baseline. These results confirm the general hypothesis that staged, structure-aware extraction substantially outperforms single-pass instruction-following approaches on heterogeneous technical documents. 

Exploratory benchmarking across different local LLM running on NVIDIA RTX A4500 GPU revealed that extraction quality does not scale linearly with parameter count. Models below approximately 7B parameters exhibited unstable schema adherence, frequent mode-collapsing behavior, and poor preservation of conditional scope relationships. [10] Midscale reasoning-oriented models (14B–32B) provided the best trade-off between semantic fidelity and throughput, while larger 70B models improved semantic consistency only marginally relative to their substantially higher latency and memory cost. Table 4 compares the 5 LLM models with varying parameters size on following KPIs: 

- **SAR** = Schema Adherence Rate 

- **HR** = Hallucination rate 

- **TTFT** = time to first token 

- **TPS** = tokens per second 

_Table 4. KPI comparison across LLM Models of different sizes_ 

|**Model**|**SAR**|**HR**|**TTFT**|**TPS(tok/s) **|**Latency**|
|---|---|---|---|---|---|
|Nemotron Nano<br>4B|45–65%|20–35%|0.3–0.8 s|90–160|6–14 s|
|Qwen3-14B|74–88%|8–18%|1.0–2.5 s|35–75|15–35 s|
|Qwen2.5-32B|88–96%|3–9%|2–6 s|16–38|28–60 s|
|Nemotron 70B|91–98%|2–7%|5–14 s|6–18|60–180 s|
|Gemma 3 27B|80–92%|5–14%|2–5 s|16–40|22–50 s|



The results demonstrate that accurate extraction from optical transceiver datasheets depends not only on language understanding, but also on explicit operational-mode discovery and scope-aware reasoning. The significant improvement in scope accuracy using proposed pipeline confirms that singlepass extraction is insufficient for resolving mode-dependent and conditional specifications. The zero-shot baseline frequently merged parameters from different operational modes into globally scoped fields, producing syntactically valid but semantically incorrect outputs. This was particularly problematic for coherent transceivers, where parameters such as OSNR, receiver sensitivity, and chromatic dispersion tolerance vary across modulation and FEC configurations. 

The ablated pipeline improved general extraction accuracy through explicit mode discovery but still failed to preserve conditional semantics encoded in footnotes and cross-table relationships. In contrast, the proposed framework achieved substantially higher condition fidelity, demonstrating that intermediate scope classification is essential for preserving engineering meaning in heterogeneous technical documents. 

Another important insight is that scope cannot be resolved reliably before operational-mode discovery. By synthesizing operational structures before final parameter association, the proposed pipeline provides the contextual constraints required for accurate scope-aware extraction and significantly reduces phantom data generation. 

Conventional top-down pipelines classify and apply a fixed schema before assigning parameters to modes in post- 

processing. This ordering fails because the schema determines what parameters are extracted, and parameters extracted without mode context cannot be correctly scoped. The modesynthesis stage, by constructing mode objects before modulelevel field extraction is finalised, provides a structural context that guides scope tagging and reduces the phantom data created when a per-mode value is assigned a module-level field. 

The pipeline is vendor-agnostic by design as the extraction contract is defined entirely by Pydantic models and prompt templates. Experiments across heterogeneous datasheet formats demonstrated robust generalization using a single extraction workflow. As the system architecture is domainadaptable, it is extensible to other products documents characterized by conditional specifications, hierarchical parameters, and heterogeneous document structures, including optical amplifiers, RF systems, and power electronics. 

## VII. LIMITATION AND FUTURE CHALLENGES 

The current pipeline does not extract information from figures or graphs. Evaluation is currently limited to 35 datasheets; broader evaluation across more vendors and form factors is planned. The footnote resolution mechanism assumes that superscripts are reliably detected by the PDF parser; for documents with custom glyph encodings, superscript detection may fail. As AI-assisted procurement increasingly replaces the manual datasheet review, vendors must optimize technical documentation for machine interpretability. Complex layouts, implicit parameter relationships, and inconsistent operational semantics reduce extraction reliability, increasing procurement cost and evaluation latency. Another challenge is operationalmode standardization. Although standards such as CMIS and OpenConfig define operational-mode mechanisms, vendors still use proprietary mode identifiers and semantics. Hence, equivalent coherent configurations are represented differently across vendors, preventing interoperable machine reasoning and cross-vendor automation. While fixed-configuration interoperability for 400ZR and emerging 800ZR systems has largely matured, software-defined and flex-rate operational provisioning remains fragmented. [16] [9] This configurationfocused extraction also underscores the benefits of capabilitybased inventory, where devices are described by operational attributes such as modulation, baud rate, reach, and FEC rather than fixed hardware Stock Keeping Unit-identifier. Enabling this transition requires standardized operational semantics, machine-readable specifications, and vendor-independent mode vocabularies. 

## VIII. CONCLUSION 

This paper presented a multi-stage LLM pipeline for universal extraction of structured transceiver parameters from datasheets. Unlike conventional extraction approaches, the proposed framework explicitly models operational modes, parameter scope, and conditional constraints during extraction, enabling reliable synthesis of machine-readable transceiver specifications. Evaluation on a diverse corpus demonstrated substantial improvements in field extraction fidelity and scope resolution accuracy compared with baseline approaches. The results show that progressive operational-mode discovery and scope-aware extraction are critical for preserving conditional engineering semantics and preventing incorrect parameter associations. 

## IX. ACKNOWLEDGEMENTS 

Funded by the European Union’s Horizon Europe research and innovation programme under project NESTOR G.A. No. 101119983 

## X. REFERENCES 

- [1]  J. Dagdelen, A. Dunn, S. Lee, N. Walker, A. S. Rosen, G. Ceder, K. A. Persson and A. Jain, “Structured information extraction from scientific text with large language models,” _Nature Communications,_ vol. 15, 2024. 

- [2]  M. Schilling-Wilhelmi, M. Ríos-García, S. Shabih, M. V. Gil, S. Miret, C. T. Koch, J. A. Márquez and K. M. Jablonka, “From text to insight: large language models for chemical data extraction,” _Chemical Society Reviews,_ vol. 54, pp. 1125-1150, 2025. 

- [3]  S. Sadruddin, E. Poupaki, J. D'Souza, S. Auer, A. Watkins, B. Karasulu, A. J. M. Mackus and E. Kessels, “Designing an agentic AI workflow for structured information extraction from scientific text: A case study on atomic layer deposition of ZnO and IGZO,” _Journal of Vacuum Science and Technology A,_ vol. 44, p. 032413, 2026. 

- [4]  H. C. Chen, Y. P. Xu and Y. Zhang, “D2S-FLOW: Automated Parameter Extraction from Datasheets for SPICE Model Generation Using Large Language Models,” arxiv, 2025. [Online]. Available: https://arxiv.org/abs/2502.16540. 

- [5]  D. Kong, N. Funabiki, H. H. S. Kyaw, I. N. D. Kotama, Z. Zhu and A. A. Rahmadani, “A Generative AI-Based Technical Data Extraction Tool for IoT Application Systems,” _Sensors,_ vol. 26, no. 4, p. 1081, 2026. 

- [6]  X. Wang, A. Raj, M. Luebbe, H. Wen, S. Xu and K. Lu, “Reliable Endto-End Material Information Extraction from the Literature with SourceTracked Multi-Stage Large Language Models,” Arxiv, 2025. [Online]. Available: https://arxiv.org/abs/2510.05142. 

- [7]  M. Mahbub, G. M. Dams, J. Arnold, C. Rizy, S. Srinivasan, E. M. Fielstein, M. A. Aghevli, K. L. Craig, E. M. Oliva, J. Erdos, J. Trafton and I. Danciu, “A Multi-Stage Validation Framework for Trustworthy Largescale Clinical Information Extraction using Large Language Models,” arxiv, 2026. [Online]. Available: https://arxiv.org/abs/2604.06028. 

- [8]  “Pydantic,” [Online]. Available: 

https://pydantic.dev/docs/validation/latest/get-started/. 

- [9]  R. Rokui, A. Guo, P. Bedard, B. Swamynathan and G. Grammel, “Modelling of Optical Pluggables in Packet Over Optical Network,” June 2024. [Online]. Available: https://www.ietf.org/archive/id/draft-rokuiccamp-actn-wdm-pluggable-modelling-00.html. 

- [10]  U. Barzelay, O. Azulai, I. Shapira, I. Friedman, F. Abo Dahood, M. Lee and A. Daniels, “VAREX: A Benchmark for Multi-Modal Structured Extraction from Documents,” arxiv, 2026. 

- [11]  Y. K. Siddhant Kulkarni, “Benchmarking Multi-Agent LLM Architectures for Financial Document Processing: A Comparative Study of Orchestration Patterns, Cost-Accuracy Tradeoffs and Production Scaling Strategies,” arxiv, 24 Mar 2026. [Online]. Available: https://arxiv.org/html/2603.22651v1. 

- [12]  A. Almorsi, M. Ahmed and W. Gomaa, “Guided Code Generation with LLMs: A Multi-Agent Framework for Complex Code Tasks,” arxiv, January 2025. [Online]. Available: https://arxiv.org/abs/2501.06625. 

- [13]  J. Villota, “Structured Data with LLMs Done Right: A Practical Guide to Classification, Retrieval and Generation with LLMs,” CEMFI, Madrid, Spain, 2025. 

- [14]  H. Hassan, “Optical Transceiver Datasheets Parser Benchmark,” 2026. [Online]. Available: https://github.com/hassanharis/optical-transceiverdatasheets-Parser-Benchmark. 

- [15]  L. Pommeret, T. Gerald, P. Paroubek, S. Ghannay, C. Servan and S. Rosset, “LLM-based Atomic Propositions Help Weak Extractors: Evaluation of a Propositioner for Triplet Extraction,” in _Proceedings of Conference on Computational Linguistics_ , 2025. 

- [16]  . OpenConfig, “openconfig-platform-transceiver.yang,” 2025. [Online]. Available: https://github.com/openconfig/public/blob/ master/release/models/platform/openconfig-platform-transceiver.yang. [Accessed 21 May 2026]. 

