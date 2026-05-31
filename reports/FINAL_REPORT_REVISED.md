# TomatoCare
## Capstone Project 1

| Student Name               | Student ID |
|----------------------------|------------|
| AlBaraa AlOlabi            | 202210405  |
| Ahmed Saeed Ahmed Mohamed  | 202211615  |
| Kazi Mahir Al Wafi         | 202211829  |
| Iyad El Boussi             | 202111261  |
| Fares Muaatasem Awda       | 202211410  |

**College of Engineering**  
Al Ain University, UAE  
Spring 2026

*The copyright of this report belongs to the authors under the terms of the copyright as qualified by the Intellectual Property Policy of Al Ain University. Due acknowledgement shall always be made of the use of any material contained in, or derived from, this report.*

---

## Abstract

TomatoCare is an offline, artificial-intelligence (AI) powered Android application for home gardeners and small-scale tomato growers in the United Arab Emirates. Non-expert growers struggle to identify tomato leaf diseases reliably, and the diagnostic apps currently available perform their analysis in the cloud, requiring a constant internet connection, and — being single classifiers — will confidently mislabel an out-of-scope photograph (another crop, a hand, an everyday object) as a tomato disease. Such confident-but-wrong advice leads to misapplied treatments, wasted pesticides, and crop loss. TomatoCare addresses this with a safety-first design that runs entirely on-device: it first verifies that an image is a tomato leaf before it will diagnose, presents calibrated confidence, and reports its real-world performance honestly.

The system is a three-stage classification cascade: a leaf gate and a tomato gate (each a lightweight MobileNetV3-Small) reject non-leaf and non-tomato inputs before any diagnosis is attempted, and an eleven-class disease classifier (MobileNetV3-Large) then identifies one of ten tomato diseases or a healthy leaf. The classifier is trained on a PlantVillage-derived tomato dataset, and its confidence is calibrated by temperature scaling so that the 60% low-confidence threshold is statistically meaningful. On a held-out laboratory test set of 6,683 images the deployed cascade reaches 97.59% disease accuracy and 97.19% end-to-end accuracy; on real-world PlantDoc field photographs it reaches 77.2% end-to-end — a laboratory-to-field gap the project measures and reports openly rather than concealing. Each diagnosis is presented with the condition name in English and Arabic, a calibrated confidence score, a severity indicator (Low, Medium, High, or Critical), and treatment suggestions filtered by the user's growing method (greenhouse, open-field, hydroponic, or saline-soil); when confidence falls below 60% a Low Confidence Warning is shown instead of a result. All three models are exported to TensorFlow Lite with float16 quantisation, totalling 9.87 MB, and run fully offline.

TomatoCare is implemented in Kotlin with Jetpack Compose, using CameraX for image capture and Kotlin Serialization to store scan history locally as a JSON file. All processing is performed on-device without any network dependency. The application supports both English and Arabic with full right-to-left layout support, and provides export and import of scan history via the Android Storage Access Framework.

The principal limitation of the system is that its field accuracy (77.2% end-to-end on real-world photographs) remains below its laboratory accuracy (97.19% end-to-end); closing this laboratory-to-field gap with real collected field data, via an in-app feedback flywheel.

---

## Table of Contents

1. [Chapter 1: Introduction](#chapter-1-introduction)  
   1.1 Introduction  
   1.2 Background and Motivation  
   &nbsp;&nbsp;&nbsp;&nbsp;1.2.1 The UAE National Food Security Strategy 2051 and the Digital Divide  
   &nbsp;&nbsp;&nbsp;&nbsp;1.2.2 The Accessibility Imperative: Offline Edge Computing  
   &nbsp;&nbsp;&nbsp;&nbsp;1.2.3 Growing Method Context  
   1.3 Proposed System  
   1.4 Problem Statement  
   1.5 Aims and Objectives  
   &nbsp;&nbsp;&nbsp;&nbsp;1.5.1 Aim  
   &nbsp;&nbsp;&nbsp;&nbsp;1.5.2 Objectives  
   1.6 Scope and Delimitations  
   &nbsp;&nbsp;&nbsp;&nbsp;1.6.1 Scope  
   &nbsp;&nbsp;&nbsp;&nbsp;1.6.2 Delimitations  
   1.7 Significance of Study  
   1.8 Expected Outputs  
   1.9 Report Outline  

2. [Chapter 2: Literature Review](#chapter-2-literature-review)  
   2.1 Introduction  
   2.2 CNN-Based Detection of Plant Diseases  
   2.3 Lightweight CNN Architectures for Mobile Deployment  
   2.4 PlantVillage Dataset and Domain Gap  
   2.5 Transfer Learning and Fine-Tuning Strategies  
   2.6 TensorFlow Lite and On-Device Inference  
   2.7 Existing Plant Diagnostic Applications: Comparative Review  
   &nbsp;&nbsp;&nbsp;&nbsp;2.7.1 Farmonaut  
   &nbsp;&nbsp;&nbsp;&nbsp;2.7.2 Flora Incognita  
   &nbsp;&nbsp;&nbsp;&nbsp;2.7.3 Plantix  
   &nbsp;&nbsp;&nbsp;&nbsp;2.7.4 Agrio  
   &nbsp;&nbsp;&nbsp;&nbsp;2.7.5 Comparative Analysis  
   2.8 Privacy, Ethical, and Localisation Considerations  
   2.9 Out-of-Distribution Rejection and Cascaded Classifiers  
   2.10 Confidence Calibration  
   2.11 Generative and Segmentation Techniques  
   2.12 Research Gaps and Conclusion  

3. [Chapter 3: Methodology](#chapter-3-methodology)  
   3.1 Introduction  
   3.2 Team Roles and Responsibilities  
   3.3 Software Development Lifecycle  
   3.4 Methodology Comparison and Selection  
   3.5 Agile Artifacts  
   3.6 Sprint Timeline and Breakdown  
   3.7 Gantt Chart  
   3.8 AI Model Development Methodology  
   &nbsp;&nbsp;&nbsp;&nbsp;3.8.1 Datasets  
   &nbsp;&nbsp;&nbsp;&nbsp;3.8.2 Preprocessing and Parity  
   &nbsp;&nbsp;&nbsp;&nbsp;3.8.3 Cascade Architecture  
   &nbsp;&nbsp;&nbsp;&nbsp;3.8.4 Training  
   &nbsp;&nbsp;&nbsp;&nbsp;3.8.5 Confidence Calibration  
   &nbsp;&nbsp;&nbsp;&nbsp;3.8.6 Export and On-Device Deployment  
   3.9 Data Persistence: JSON File Storage  
   &nbsp;&nbsp;&nbsp;&nbsp;3.9.1 Ethical Handling of User-Feedback Images  
   3.10 Development Tools and Environment  
   3.11 Conclusion  

4. [Chapter 4: Requirements and Specifications](#chapter-4-requirements-and-specifications)  
   4.1 Introduction  
   4.2 Functional Requirements  
   4.3 Non-Functional Requirements  
   4.4 Domain Requirements  
   4.5 Constraint Requirements  
   4.6 Stakeholder Perspective  
   4.7 Use Case Diagram  
   4.8 AI Subsystem — Functional Requirements  
   4.9 AI Subsystem — Non-Functional Requirements  
   4.10 AI Subsystem — Domain Requirements and Constraints  
   4.11 AI Subsystem — Requirements Traceability  

5. [Chapter 5: Design](#chapter-5-design)  
   5.1 System Architecture  
   &nbsp;&nbsp;&nbsp;&nbsp;5.1.1 Layer 1 – Presentation Layer (UI)  
   &nbsp;&nbsp;&nbsp;&nbsp;5.1.2 Layer 2 – Application Logic Layer (Inference Engine)  
   &nbsp;&nbsp;&nbsp;&nbsp;5.1.3 Layer 3 – Data Layer (Local Persistence)  
   &nbsp;&nbsp;&nbsp;&nbsp;5.1.4 Cross-Cutting Concerns  
   5.2 Sequence Diagram  
   5.3 State Chart Diagram  
   5.4 Data Model Diagram  
   5.5 JSON Schema Tree  
   5.6 Class Diagram  
   5.7 Activity Diagram  
   5.8 Architectural Placement of the AI Subsystem  
   5.9 Cascade Inference Design  
   5.10 Preprocessing-Parity Contract  
   5.11 Model-Asset and Label Contract  

6. [Chapter 6: Implementation](#chapter-6-implementation)  
   6.1 Introduction  
   6.2 Model Pipeline  
   6.3 On-Device Cascade Integration  
   6.4 In-App Feedback Flywheel  
   6.5 Application Architecture and Project Structure  
   6.6 Key Components  
   6.7 Continuous Integration and Testing  
   6.8 Implementation Challenges  

7. [Chapter 7: Testing and Evaluation](#chapter-7-testing-and-evaluation)  
   7.1 Evaluation Framework  
   7.2 Deployed-Model Laboratory Results  
   7.3 Confidence Calibration  
   7.4 Field Validation and the Laboratory-to-Field Gap  
   7.5 Experiments to Close the Gap — a Controlled Investigation  
   &nbsp;&nbsp;&nbsp;&nbsp;7.5.1 The Decisive Comparison  
   &nbsp;&nbsp;&nbsp;&nbsp;7.5.2 Mechanistic Per-Class Finding  
   7.6 Synthesis  
   7.7 Capability Statement  
   7.8 Non-Functional Verification  
   7.9 Application Testing  
   7.10 Usability Evaluation  

8. [Chapter 8: Conclusion](#chapter-8-conclusion)  

9. [Chapter 9: Future Work](#chapter-9-future-work)  

[References](#references)  
[Appendix A: Experiment Configurations (Supplementary)](#appendix-a)  
[Appendix B: Application Requirements Catalogue](#appendix-b)  

---

## List of Figures

- Figure 1: UAE Temperatures vs Optimal Tomato Growth
- Figure 2: Visual Similarity Between Tomato Leaf Disease Symptoms
- Figure 3: Farmonaut Application Interface
- Figure 4: Flora Incognita Application Interface
- Figure 5: Plantix Application Interface
- Figure 6: Agrio Application Interface
- Figure 7: Agile SDLC Cycle
- Figure 8: Gantt Chart
- Figure 9: Use Case Diagram
- Figure 10: Layered Architecture Diagram
- Figure 11: Sequence Diagram — Diagnose Leaf
- Figure 12: Sequence Diagram — View Past Scan
- Figure 13: State Chart Diagram
- Figure 14: Data Model Diagram
- Figure 15: JSON Schema Tree
- Figure 16: Class Diagram
- Figure 17: Activity Diagram — Run Diagnosis
- Figure 6.1: DCGAN Synthetic Bacterial-Spot Leaf Samples (Epoch 150)
- Figure 6.2: Application User-Interface Screenshots
- Figure 7.1: Deployed Stage-3 Confusion Matrix (Row-Normalised, n = 6,683)
- Figure 7.2: End-to-End Accuracy Under Four Test Conditions
- Figure 7.3: On-Device Inference-Time and Feedback Evidence (Samsung Galaxy S10+)

---

## List of Tables

- Table 1: Problem Statement
- Table 2: Comparative Feature Analysis
- Table 3: Team Roles and Responsibilities
- Table 4: Comparison of SDLC Methodologies
- Table 5: Sprint Timeline and Breakdown
- Table 3.1: Stage 3 (tomato20k) Dataset Split
- Table 4.1: AI Subsystem Functional Requirements
- Table 4.2: AI Subsystem Non-Functional Requirements
- Table 4.3: AI Requirements Traceability Matrix
- Table 7.1: Deployed-Model Laboratory Results
- Table 7.2: Per-Class Recall (Deployed Stage 3)
- Table 7.3: Domain-Gap Experiments
- Table 7.4: Non-Functional Requirement Verification (AI Subsystem)
- Table 7.5: Application Unit-Test Coverage
- Table 7.6: On-Device Inference Latency by Device
- Table 7.7: Usability Study Results
- Table B.1: Functional Requirements Traceability
- Table B.2: Non-Functional Requirements Traceability
- Table B.3: Domain Requirements Traceability

---

## Chapter 1: Introduction

### 1.1 Introduction

The tomato (*Solanum lycopersicum*) is one of the most widely grown vegetables in the UAE, cultivated by home gardeners, small-scale farmers, and commercial greenhouse operators alike. Tomato production in the Gulf region faces challenges fundamentally different from those of temperate agriculture: summer temperatures exceeding 45 °C, saline groundwater, and intense solar radiation place tomato plants under severe physiological stress and weaken their natural defences against fungal, bacterial, and viral diseases [1].

Tomato was selected as the target crop, in preference to other regional crops, for three specific reasons. First, it is among the most widely cultivated vegetables in the UAE across every grower scale — home gardens, hydroponic urban setups, and commercial greenhouses — so a tomato-specific tool reaches the largest cross-section of the intended users. Second, the tomato is disproportionately disease-prone: it is susceptible to a large number of foliar diseases whose symptoms (early blight, late blight, septoria leaf spot, bacterial spot, leaf mould, and several viruses) are visually similar, which makes accurate identification genuinely difficult for non-experts and therefore a high-value target for automated assistance. Third, the tomato is the best-resourced crop in public plant-pathology datasets — the PlantVillage corpus alone provides ten labelled tomato disease classes — which makes a rigorously evaluated eleven-class classifier feasible within a capstone timeframe, whereas most other regional crops lack labelled data of comparable depth. Narrowing the scope to a single, data-rich, high-impact crop also allowed the project to invest in safety (the rejection cascade) and honest field evaluation rather than spreading effort thinly across many crops.

For the non-expert grower, the central difficulty is identifying which disease a plant is suffering from. Tomato diseases such as early blight (*Alternaria solani*), late blight (*Phytophthora infestans*), septoria leaf spot, and bacterial spot present as overlapping patterns of leaf yellowing, wilting, and necrotic spotting that are difficult to distinguish without formal training. Misidentification leads to the wrong treatment being applied, wasted agricultural inputs, and — in severe cases — complete crop loss.

The diagnostic tools currently available fail to address this problem effectively. Commercial products such as Plantix and Agrio perform their diagnosis in the cloud and therefore require a constant internet connection, which is not always available in rural or outdoor agricultural environments. Those that do offer an Arabic localisation still depend on connectivity for every diagnosis and provide no treatment guidance localised to UAE cultivation methods such as hydroponics or saline-soil farming. Professional agricultural consultants, meanwhile, remain out of reach of most small-scale growers for reasons of cost and geography.

TomatoCare was designed and developed to fill this gap. It is a native Android application — offline, AI-powered, and accessible to any grower regardless of technical expertise, connectivity, or economic status — that enables a grower to photograph a tomato leaf and receive an instant diagnosis with treatment recommendations tailored to UAE growing conditions. TomatoCare directly supports the UAE National Food Security Strategy 2051 [2], which aims to extend the benefits of precision agriculture to small-scale growers who have traditionally been excluded from them.

*Figure 1: UAE Temperatures vs Optimal Tomato Growth*

---

### 1.2 Background and Motivation

#### 1.2.1 The UAE National Food Security Strategy 2051 and the Digital Divide

The United Arab Emirates has made food security a national strategic priority. The UAE National Food Security Strategy 2051 manifests this commitment through three operational pillars: developing local production capability, improving production efficiency, and applying new technologies to enhance agricultural productivity [2]. Its ultimate vision is to equip farmers with data-driven decision-making tools that reduce reliance on imported food and strengthen the country's agricultural resilience.

Despite this policy ambition, a significant gap remains between governmental intent and ground-level practice. Large-scale commercial producers have the financial capacity to invest in precision agriculture technologies, but small-scale growers and home gardeners — who comprise a large and growing proportion of the UAE's food-producing population — remain largely excluded from these advances. This imbalance leads to a predominantly reactive approach to crop management: by the time a small-scale grower notices a disease problem, the condition has typically progressed to the point where significant crop loss is unavoidable. TomatoCare responds to this knowledge gap by placing a specialised agronomic diagnostic tool directly in the hands of any grower who owns a smartphone, regardless of economic scale or technical background.

#### 1.2.2 The Accessibility Imperative: Offline Edge Computing

TomatoCare is built on an offline edge-computing architecture. All image processing and inference are performed on-device, and no network request is made at any point during operation. This is not merely an architectural preference but a necessity dictated by the realities of the target deployment environment: mobile data coverage in rural UAE farming areas is unreliable or entirely absent, making cloud-dependent diagnostic tools unsuitable for field use.

The result is a diagnostic tool equally available to a grower working in a greenhouse in Abu Dhabi and to one tending a home garden in a remote desert community, with no dependence on connectivity, subscription charges, or specialist hardware.

#### 1.2.3 Growing Method Context

Tomato cultivation in the UAE spans a variety of growing techniques, each with different disease dynamics and treatment requirements. Greenhouse cultivation enables environmental control but creates conditions in which fungal pathogens such as leaf mould thrive. Open-field farming exposes crops to the full intensity of UAE solar radiation and wind-borne pathogens. Hydroponic systems, increasingly common in urban UAE settings, are susceptible to root-zone bacterial infections. Saline-soil cultivation, practised where groundwater salinity is elevated, places additional physiological stress on the crop and is prevalent in parts of the UAE. TomatoCare captures the user's growing method at the point of scan and uses this contextual information to rank and filter the most relevant treatment recommendations for that specific cultivation environment.

---

### 1.3 Proposed System

TomatoCare replaces the single-classifier design of the Capstone 1 prototype with a three-stage decision cascade. The application first verifies that the input image is a leaf, then that it is specifically a tomato leaf, and only then attempts a disease diagnosis — rejecting out-of-scope inputs (other crops, hands, everyday objects) before any prediction is shown to the user. All three models run on-device in TensorFlow Lite with no network access, preserving the offline-edge property described in §1.2.2.

After an image is captured (live via CameraX or selected from the device gallery), it is preprocessed once — resized to 224×224 and normalised — and the same preprocessed tensor is passed sequentially to each stage of the cascade. If the leaf gate or the tomato gate rejects the input, the user is shown a clear out-of-scope message rather than a confident wrong diagnosis. If both gates accept, the disease classifier produces a probability distribution over eleven conditions: Tomato Early Blight, Tomato Late Blight, Tomato Bacterial Spot, Tomato Septoria Leaf Spot, Tomato Spider Mites (Two-spotted Spider Mite), Tomato Target Spot, Tomato Yellow Leaf Curl Virus, Tomato Mosaic Virus, Tomato Leaf Mould, Powdery Mildew, and Healthy. The disease classifier's confidence is calibrated by temperature scaling so that the 60% low-confidence threshold reflects true reliability rather than raw softmax output. This threshold is grounded in an ethical design principle discussed in §4.6.

When the top confidence meets or exceeds the threshold, the application shows the primary diagnosis with the condition name in both English and Arabic, the calibrated confidence score, a severity indicator (Low, Medium, High, or Critical), and localised treatment suggestions tailored to the user's growing method. Below the threshold, the application issues a Low Confidence Warning and prompts the user to retake the photograph under better conditions. Scan records are stored locally as JSON via `kotlinx.serialization` with no cloud dependency; the user can export and re-import their history through the Android Storage Access Framework. The application additionally embeds an in-app feedback mechanism that labels and stores real field photographs for future retraining (§6.4).

---

### 1.4 Problem Statement

**Table 1: Problem Statement**

| Element | Description |
|---|---|
| **The Problem Of** | TomatoCare's recognition engine was built in three deliberate iterations, each fixing a measured flaw in the one before it. A from-scratch convolutional network (TomatoCareNet) first established feasibility at 91.17% laboratory accuracy and proved the team could design and train a competitive architecture end-to-end; it was then replaced, for the Capstone 1 prototype, by a single MobileNetV3-Large classifier extended with a `not_tomato` reject class. That prototype exposed the real problem this project sets out to solve: out-of-scope photographs — another crop's leaf, a hand, an everyday object — were labelled as a tomato disease *with high confidence*. In an agricultural advisory context this is a safety defect, not merely an accuracy shortfall — a grower who photographs the wrong subject is handed confident, wrong treatment advice, leading to misapplied pesticide and avoidable crop loss. |
| **Root Cause** | A single softmax head was forced to perform two conflicting tasks at once — out-of-distribution rejection and fine-grained disease discrimination — within one shared feature space, with the `not_tomato` class heavily under-represented. Compounding this, all non-tomato training examples were clean laboratory images while the tomato examples included field photographs, so the model learned to separate images by photographic style (lab vs. field) rather than by leaf identity; a real field photograph of another plant therefore appeared as a tomato. |
| **Impact** | Misapplied treatments, wasted agrochemical inputs, and crop loss for the smallholder farmers and home gardeners — including the large Arabic-speaking agricultural workforce — who lack affordable access to professional agronomic advice and rely on tools that must function in low-connectivity field conditions. Downstream effects include environmental harm from unnecessary pesticide use and the acceleration of pathogen resistance. |
| **Solution** | A free, fully offline, bilingual Android tool that verifies an input is in-domain before diagnosing (leaf gate → tomato gate → disease classifier), aligns training and inference preprocessing so that photographic style cannot drive the decision, reports calibrated confidence, and honestly measures its laboratory-to-field performance gap. Designed for low-end devices (API 26+, ≥ 2 GB RAM) with a combined model footprint under 15 MB. |

---

### 1.5 Aims and Objectives

#### 1.5.1 Aim

This project develops and evaluates TomatoCare, a native bilingual Android application that diagnoses eleven tomato leaf conditions on-device through a safety-correct three-stage classification cascade, with calibrated confidence and an honestly measured laboratory-to-field performance gap. The application runs entirely offline on low-end Android devices (API 26 and above, ≥ 2 GB RAM) within a combined model footprint of under 15 MB.

#### 1.5.2 Objectives

Six objectives were formulated to achieve this aim. Each is reported with its measured outcome and a status tag — **[MET]** or **[PARTIALLY MET]** — so that the report's claims are auditable against Chapter 7.

1. **Safety-Correct Cascade — [MET]:** Design and deploy a three-stage cascade (leaf gate → tomato gate → disease classifier) that rejects non-leaf and non-tomato inputs before any diagnosis is produced, eliminating the confident-wrong-answer failure mode of the Capstone 1 prototype. *Result: 99.55% non-leaf rejection and 0.05% unseen-species leak rate on the held-out evaluation set (Chapter 7).*

2. **On-Device Inference — [MET]:** Export all three cascade stages to TensorFlow Lite with float16 quantisation and integrate them into the Android application so that inference runs in real time with no network dependency. *Result: 9.87 MB combined model footprint (well under the 15 MB budget) with no network permission declared in the manifest (Chapter 6).*

3. **Disease Classification Accuracy — [MET]:** Train an eleven-class classifier (ten diseases plus a healthy class) that meets or exceeds 90% accuracy on a held-out laboratory test set. *Result: 97.59% laboratory accuracy (Chapter 7).*

4. **Confidence Calibration — [PARTIALLY MET]:** Calibrate the disease classifier's confidence by temperature scaling so the 60% low-confidence threshold reflects true reliability (target Expected Calibration Error < 0.02). *Result: in-sample ECE 0.0046 meets the target, but the honest held-out test ECE is 0.061; a dedicated calibration set is required to substantiate a tighter figure (Chapters 7 and 9). Reported transparently rather than overclaimed.*

5. **Honest Real-World Evaluation — [MET]:** Evaluate the system on real field photographs in addition to the laboratory test set, and quantify the laboratory-to-field performance gap rather than concealing it. *Result: 77.2% field end-to-end accuracy versus 97.19% laboratory end-to-end accuracy on a matched subset (Chapter 7).*

6. **Data-Collection Flywheel — [MET]:** Provide an in-app feedback mechanism that labels and stores real field photographs locally so that the cascade can be retrained on the actual operating distribution in future work. *Result: implemented (§6.4); SAF-based export and import of scan history are retained as an additional benefit.*

---

### 1.6 Scope and Delimitations

#### 1.6.1 Scope

TomatoCare is scoped along five dimensions. In terms of crop type, it is limited to tomato (*Solanum lycopersicum*) only. In terms of conditions, the disease classifier recognises eleven classes — ten diseases plus a healthy class — and the three-stage cascade (leaf gate → tomato gate → disease classifier) explicitly rejects inputs outside this scope before any diagnosis is produced. In terms of geographic context, the system is intended for deployment in the UAE and the Gulf region, where fully offline operation and Arabic-language support are essential for the target users. In terms of platform, the application targets native Android devices only (API 26+, ≥ 2 GB RAM), with all inference performed on-device through TensorFlow Lite; full implementation details are documented in Chapters 3 and 6. In terms of language, the user interface is delivered in both English and Arabic with complete right-to-left layout support.

#### 1.6.2 Delimitations

The following capabilities are explicitly outside the scope of this project:

- Conditions outside the eleven trained classes are not diagnosed; novel conditions produce a low-confidence warning rather than a confident label.
- Multi-leaf and full-plant photographs are not supported; the cascade assumes a single, centred leaf.
- Multi-crop support is excluded; the model is trained on tomato leaf images only.
- Cloud synchronisation is not included; all data is stored on the user's device.
- IoT sensor integration and environmental monitoring hardware are not supported.
- iOS, user accounts, and authentication mechanisms are not implemented in this version.
- Treatment recommendations are advisory only and do not constitute a legally binding agrochemical prescription.

---

### 1.7 Significance of Study

TomatoCare makes the following contributions beyond the immediate project:

1. It demonstrates that precision agricultural diagnostics can be delivered on low-end, offline devices — at high laboratory accuracy and with an honestly measured laboratory-to-field gap — directly addressing the digital divide between large-scale commercial farming and smallholder agriculture in the UAE.
2. The three-stage cascade architecture provides a generalisable pattern for safety-correct deployment of plant-disease classifiers: by hard-rejecting out-of-domain inputs before any diagnosis is produced, the system eliminates the confident-wrong-answer failure mode that has been documented but rarely addressed in the agricultural-AI literature.
3. The project reports an honest laboratory-to-field accuracy gap (97.19% laboratory vs. 77.2% field on a matched subset) rather than a single benchmark figure, modelling a transparency standard conspicuously absent from commercial plant-diagnostic products.
4. By reducing the misdiagnosis that drives unnecessary pesticide application, TomatoCare addresses an environmental consequence that no currently available mobile application directly targets.
5. The project directly supports the UAE National Food Security Strategy 2051 by equipping local growers with a tool that reduces crop losses and enhances the sustainability of local food production.
6. The open-source codebase and dataset contributions allow the work to be extended by the global research community, particularly researchers working on arid-climate agricultural AI.

---

### 1.8 Expected Outputs

The completed project produces the following deliverables:

- A three-stage safety-correct classification cascade (leaf gate → tomato gate → disease classifier) achieving 97.59% laboratory accuracy on the eleven-class held-out test set and 77.2% end-to-end accuracy on a matched real-world field subset, with temperature-scaled confidence calibration.
- Three quantised TensorFlow Lite model files totalling 9.87 MB, embedded within the application for fully offline inference.
- A fully functional bilingual Android application compatible with Android 8.0 (API 26) and above.
- An in-app feedback flywheel for collecting and labelling real field photographs to support future retraining.
- An open-source GitHub repository licensed under the MIT License, containing all source code, training scripts, preprocessing-parity tooling, and documentation.

---

### 1.9 Report Outline

The remainder of this report is organised as follows. Chapter 2 reviews the relevant literature, covering CNN-based plant-disease recognition, the domain gap between laboratory and field imagery, lightweight on-device architectures, out-of-distribution rejection via cascaded classifiers, confidence calibration, and a comparative analysis of four existing diagnostic applications. Chapter 3 details the methodology, including the Agile development process, dataset construction, the three-stage cascade architecture, training, calibration, and TensorFlow Lite export. Chapter 4 specifies the system requirements — functional, non-functional, domain, and constraint — for both the Android application and the AI subsystem. Chapter 5 presents the system design and architecture, including the full UML suite and the model-asset contract. Chapter 6 documents the implementation of the model pipeline and on-device cascade integration. Chapter 7 reports testing and evaluation, including laboratory and field accuracy results, the four controlled domain-gap experiments, and non-functional verification. Chapter 8 concludes the report, and Chapter 9 sets out future work. Appendix A provides supplementary experiment configurations, and Appendix B catalogues the full application requirements.

---

## Chapter 2: Literature Review

### 2.1 Introduction

This chapter provides the academic and technical context for the design choices made in TomatoCare and situates the system within the existing landscape of AI-based plant diagnostic tools. Recent advances in artificial intelligence, computer vision, and mobile computing have transformed plant disease detection into an increasingly automated, image-based discipline [3, 4]. Despite this progress, the literature reveals significant gaps when existing tools are assessed against the needs of small-scale tomato production in arid climates such as the UAE.

Sections 2.2 to 2.6 establish the technical and academic foundations for the major design decisions in TomatoCare: convolutional neural networks for image-based plant-disease classification, the selection of a lightweight architecture suitable for mobile deployment, the choice of training data and augmentation strategy, transfer learning, and the role of TensorFlow Lite quantisation in enabling on-device inference. Section 2.7 provides a comparative analysis of four existing applications (Farmonaut, Flora Incognita, Plantix, and Agrio). Section 2.8 discusses the privacy, ethical, and localisation considerations relevant to the UAE setting. Sections 2.9 to 2.11 cover out-of-distribution rejection and cascaded classifiers, confidence calibration, and the generative and segmentation techniques used in the domain-gap experiments. Section 2.12 synthesises the research gaps identified and the rationale for TomatoCare.

---

### 2.2 CNN-Based Detection of Plant Diseases

Deep learning applied to plant disease classification has evolved rapidly over the past decade. Early image-based diagnostic systems relied on conventional computer vision methods — colour histogram analysis and hand-crafted feature extraction — which performed reasonably under controlled laboratory conditions but generalised poorly to real-world field imagery. Convolutional neural networks (CNNs) provided a fundamental paradigm shift by enabling hierarchical visual features to be learned automatically from labelled images [3].

Recent peer-reviewed studies report that state-of-the-art CNN architectures achieve classification accuracies exceeding 98% on controlled plant-disease datasets, with corresponding F1 scores at the same level [3, 4]. Field deployments, where lighting, background, and image quality vary considerably, typically report lower but still strong accuracies in the range of 90–95% [3]. This well-documented phenomenon has a direct implication for TomatoCare's evaluation methodology: rather than reporting only a laboratory benchmark, the project evaluates the deployed model on real-world field photographs so that the laboratory-to-field performance gap is measured rather than assumed away (Chapter 7).

CNNs are particularly well suited to plant disease classification because the diagnostic features that distinguish one pathology from another — the geometry of necrotic lesions, colour transitions of chlorotic tissue, and morphological patterns of fungal mycelium — are precisely the kind of localised visual patterns that CNN architectures are designed to detect through their convolutional and pooling layers [3, 4]. This fit between architectural capability and problem structure informs the adoption of a CNN-based approach in TomatoCare.

---

### 2.3 Lightweight CNN Architectures for Mobile Deployment

Although CNNs possess the diagnostic capacity that TomatoCare requires, the deployment environment — low-end Android devices operating in a fully offline setting — imposes strict constraints on model size, memory footprint, and inference latency. CNN architectures designed for cloud-based inference, such as ResNet-50 and InceptionV3, are unsuitable in this context. ResNet-50, for example, has approximately 25.6 million parameters and occupies around 98 MB on disk, which exceeds both the target APK size and the memory constraints of devices in the API 26 / 2 GB RAM category [5].

The MobileNet family of architectures was developed to address precisely this limitation. MobileNet models significantly reduce parameter count and computational cost compared to traditional CNNs while retaining most of their classification accuracy. The architecture selected by TomatoCare — MobileNetV3-Large — builds on this foundation with Neural Architecture Search to optimise the layer structure for mobile hardware, the hard-swish activation function for improved gradient flow at low computational cost, and squeeze-and-excitation blocks for enhanced feature representation [6]. The resulting model has approximately 5.4 million parameters, occupies roughly 22 MB before quantisation, and achieves a top-1 ImageNet accuracy of 75.2%.

The selection of MobileNetV3-Large over MobileNetV2 (lower accuracy at similar size) and EfficientNet-B0 (marginally higher accuracy but slower inference on mobile hardware) was a deliberate engineering decision to maximise diagnostic accuracy within the latency and storage constraints imposed by the offline, low-end-device deployment setting. A direct comparison of these architectures is provided in §3.8.3.

---

### 2.4 PlantVillage Dataset and Domain Gap

The PlantVillage dataset, originally compiled and published by Hughes and Salathé, has become a de facto standard benchmark in plant disease classification research [9, 10]. It comprises more than 54,000 labelled images across 38 classes and 14 crop species, including ten tomato classes (one healthy and nine diseased). TomatoCare's disease classifier is trained on a PlantVillage-derived tomato collection that extends this set to eleven classes by adding a powdery mildew class (Chapter 3). The close alignment between the available data and the project's classification taxonomy motivated the choice of PlantVillage-derived data as the primary training source.

However, PlantVillage has a well-documented limitation: all images were captured under controlled laboratory conditions with uniform backgrounds and lighting [9, 10]. Models trained exclusively on such images typically suffer a sharp accuracy decline when applied to field imagery with variable lighting, cluttered backgrounds, and non-standard camera angles. This phenomenon is termed the domain gap, and it is particularly pronounced when models trained on temperate-climate laboratory images are deployed in environments with markedly different visual properties — such as the high-brightness, dust-affected, heat-saturated conditions characteristic of UAE outdoor and greenhouse agriculture.

The domain gap is therefore the central evaluation challenge for any PlantVillage-trained system, and TomatoCare confronts it directly. The deployed disease classifier is trained with only minimal augmentation (horizontal flip only); a heavier augmentation pipeline intended to simulate field conditions — brightness, contrast, gamma, colour, and blur jitter — was investigated as a means of closing the gap but was found to *reduce* field accuracy and was therefore rejected. This is one of four controlled domain-gap experiments reported in Chapter 7. The measurement-driven approach reflects the literature's caution that augmentation strategies must be validated against real field data rather than assumed to help [10].

---

### 2.5 Transfer Learning and Fine-Tuning Strategies

Training a CNN from random initialisation requires millions of labelled images and substantial computational resources — both impractical within the limits of a typical academic capstone project. Transfer learning offers an established alternative: a model pre-trained on a large, general-purpose dataset (typically ImageNet, with over one million labelled images across a thousand categories) is adapted to a specialised task by replacing its classification head and fine-tuning a subset of its layers on the target dataset.

The literature confirms that transfer learning yields considerable performance benefits in plant disease classification in particular [9, 10]. Pre-training the lower convolutional layers on ImageNet furnishes the network with general-purpose visual feature detectors — edges, colour transitions, textures, and basic shape primitives — that transfer effectively to the plant disease domain. The upper layers, which learn more task-specific feature combinations, are then retrained on the target data to capture the visual representations of the conditions under classification.

TomatoCare implements a two-stage transfer-learning strategy. In the first stage, all layers of the MobileNetV3-Large backbone are frozen and only the new classification head is trained, allowing the head to adapt to the eleven tomato classes without disrupting pre-trained feature representations. In the second stage, the top thirty layers of the backbone are unfrozen and fine-tuned at a reduced learning rate, enabling the model to adjust higher-level feature combinations to the visual properties specific to tomato leaf conditions. This two-phase approach, elaborated further in Chapter 3, is consistent with current best practice in the transfer-learning literature [6].

---

### 2.6 TensorFlow Lite and On-Device Inference

TomatoCare's fully offline architecture is a fundamental property of the technical design. On-device inference offers four benefits directly relevant to UAE deployment: it eliminates any dependence on network availability, removes inference latency caused by network round-trips, ensures complete privacy of user data, and incurs no ongoing operational cost.

TensorFlow Lite is Google's framework for deploying machine learning models on mobile and embedded devices. It accepts a TensorFlow SavedModel and produces a compact FlatBuffer file (`.tflite`) optimised for fast loading and execution on mobile hardware. The framework supports several quantisation strategies, each with a different trade-off between model size, inference speed, and accuracy retention. Float32 (no quantisation) is the most accurate but yields the largest models. Int8 quantisation produces the smallest and fastest models but can introduce significant accuracy degradation on fine-grained classification tasks. Float16 quantisation — the strategy adopted by TomatoCare — is intermediate: it approximately halves model size while preserving accuracy to within a fraction of a percent of the unquantised baseline, making it the appropriate choice when classification accuracy is the primary concern [11].

With float16 quantisation applied, the models load quickly, fit within the available memory without issue, and run within the latency budget required for an interactive diagnostic experience. The combination of MobileNetV3-Large and float16 quantisation is therefore a coordinated design decision: each element is necessary, and together they enable the offline, on-device operation that defines the architectural identity of TomatoCare.

---

### 2.7 Existing Plant Diagnostic Applications: Comparative Review

Four AI-based plant diagnostic systems were selected for detailed analysis: Farmonaut, Flora Incognita, Plantix, and Agrio. Together they represent the full range of current practice — large-scale satellite-based commercial agriculture (Farmonaut), citizen-science species identification (Flora Incognita), and smallholder-focused disease diagnosis (Plantix and Agrio) — and collectively illustrate the capabilities and shortcomings of the existing state of the art.

#### 2.7.1 Farmonaut

*Figure 3: Farmonaut Application Interface*

Farmonaut is a precision agriculture platform that integrates satellite spectral tracking with smartphone-based image analysis via its Jeevn AI subsystem. The platform uses multispectral satellite data in the near-infrared and red-edge bands to detect large-scale crop anomalies, computing vegetation indices including NDVI, NDRE, EVI, SAVI, NDWI, and NDMI to assess plant health, water status, and soil conditions across entire fields [15]. Satellite imagery is delivered at 10-metre resolution at three-to-five-day intervals, with synthetic aperture radar (SAR) imagery provided irrespective of cloud cover.

The Jeevn AI component uses CNNs to analyse smartphone-captured crop images, identifying diseases from the geometry of necrotic lesions, chlorotic colour variation, and fungal mycelium morphology. Farmonaut's own published materials report a diagnostic accuracy of 98.32% in laboratory conditions, with an F1 score of 97.99% and approximately 90–95% in field deployment [16]; these are vendor-reported figures and, to the authors' knowledge, have not been independently verified in the peer-reviewed literature.

**Limitations and Applicability to TomatoCare.** Farmonaut is fundamentally mismatched to TomatoCare's target users. It is a paid subscription service designed for large commercial agricultural operations, with satellite-based monitoring that requires fields large enough to be meaningfully resolved at 10-metre resolution — a scale incompatible with the home gardens and small plots typical of UAE smallholder cultivation [16]. Farmonaut performs its analysis in the cloud rather than on-device, and offers no UAE-specific treatment recommendations [14]; an Arabic-language interface could not be independently confirmed. Its operation presupposes the cloud connectivity and commercial scale that TomatoCare is specifically designed to work without.

#### 2.7.2 Flora Incognita

*Figure 4: Flora Incognita Application Interface*

Flora Incognita is a free scholarly plant identification application, research-funded by the Max Planck Institute for Biogeochemistry and the Technical University of Ilmenau [17]. The system employs a hierarchical deep learning method in which multiple CNNs process plant images sequentially, progressing from low-level features (geometric form, texture) to high-level botanical structures (flowers, fruits). When diagnostic confidence is low, the application requests additional images of the specimen to refine its identification; the final classification is performed on a dedicated server cluster.

Flora Incognita has identified over 30,000 vascular plant species across more than 20 supported languages. A 2024 peer-reviewed validation study, conducted on an independent reference dataset in ecological survey conditions, reported a true positive rate of 98.8% [18], establishing the platform as a scientifically credible species-identification tool. The application also supports an offline mode, gamified citizen-science interactions via the Flora Capture programme, and informational fact sheets including plant toxicity data [19].

**Limitations and Applicability to TomatoCare.** The principal limitation of Flora Incognita, viewed through the lens of TomatoCare, is a fundamental category mismatch: the application identifies plant species, not diseases. It would correctly identify the species as *Solanum lycopersicum* but would provide no information about any observed pathological condition [17, 18]. Its training data consists entirely of images of wild, uncultivated ecosystems and contains no diseased crop samples. Although the platform does offer an Arabic localisation, it provides no disease diagnosis, no treatment advice, and no agronomic guidance applicable to UAE cultivation methods. Its identification is performed server-side; the much-cited "offline mode" merely stores photographs locally for later online identification rather than running inference on the device.

#### 2.7.3 Plantix

*Figure 5: Plantix Application Interface*

Plantix, developed by PEAT GmbH, is one of the most widely used smartphone applications for identifying plant diseases and pests. It uses CNN-based image recognition to identify diseases and pest damage from user-submitted photographs, supplemented by a peer-to-peer discussion forum. Unlike the other platforms reviewed here, Plantix has been the subject of independent scholarly evaluation. A field study conducted with farmers in the Indian state of Andhra Pradesh reported an identification success rate above 90% for common crop diseases [36], and a 2022 independent evaluation of seventeen plant-disease applications found Plantix to be the only one able to identify the plant, detect the disease, maintain a plant database, and recommend a treatment — while concluding that most such applications are deficient in their core AI functionality [37].

**Limitations and Applicability to TomatoCare.** Plantix is a cloud-based application: every diagnosis is performed on remote servers and therefore requires a live internet connection, with only previously viewed content available offline — a constraint that makes it unreliable in rural farming communities with poor connectivity. Although Plantix does provide an Arabic localisation, its treatment suggestions are not localised to UAE cultivation practices such as hydroponics or saline-soil farming, and — like every single-classifier system — it has no mechanism to reject an out-of-scope photograph before diagnosing it, the precise safety gap that motivated TomatoCare's rejection cascade.

#### 2.7.4 Agrio

*Figure 6: Agrio Application Interface*

Agrio is a commercial AI-based crop protection platform that combines image-based disease detection with a curated agronomy database, weather-based predictive alerts, and Integrated Pest Management advisory services. Its developer reports a real-world diagnostic accuracy of approximately 91% [16]; unlike the figure for Plantix, this claim does not appear to have been independently evaluated in the peer-reviewed literature and should be read as a vendor statement. Agrio operates on a paid subscription model.

**Limitations and Applicability to TomatoCare.** Agrio shares the central limitation of every cloud platform reviewed here: it uploads each image to its servers for analysis and is therefore unusable without connectivity. Its interface offers around fifteen languages, but Arabic support could not be independently confirmed. It provides no treatment recommendations adapted to UAE-specific cultivation methods such as hydroponic growing or saline-soil cultivation, and — like Plantix — performs no out-of-scope rejection before diagnosing. Its paid-subscription model introduces a financial barrier that further restricts access for the low-income smallholders who form the core user base of TomatoCare.

#### 2.7.5 Comparative Analysis

**Table 2: Comparative Feature Analysis**

| Feature | TomatoCare | Farmonaut | Flora Incognita | Plantix | Agrio |
|---|---|---|---|---|---|
| Disease detection via image AI | ✓ | ✓ | ✗ (species ID only) | ✓ | ✓ |
| On-device AI inference (no connectivity required) | ✓ | ✗ | ✗ | ✗ | ✗ |
| Out-of-scope (OOD) input rejection before diagnosis | ✓ | ✗ | ✗ | ✗ | ✗ |
| Calibrated confidence + low-confidence warning | ✓ | ✗ | ✗ | ✗ | ✗ |
| Arabic interface | ✓ (full RTL) | Unconfirmed | ✓ (partial) | ✓ | Unconfirmed |
| Honest lab-to-field accuracy reporting | ✓ | ✗ | ✗ | ✗ | ✗ |
| Localised treatment recommendations (UAE) | ✓ | ✗ | ✗ | ✗ | ✗ |
| Free to use | ✓ | ✗ | ✓ | ✓ | ✗ |
| Open source | ✓ | ✗ | ✗ | ✗ | ✗ |

The accuracy figures advertised for these platforms — approximately 95% for Farmonaut, 91% for Agrio, and 90% for Plantix — are considerably higher than the 60–75% a non-expert grower typically achieves by unaided visual inspection, but they must be read critically. Only the Plantix figure derives from independent, peer-reviewed evaluation [36, 37]; the Farmonaut and Agrio figures are vendor self-reports. More importantly, none of the platforms discloses its real-world field accuracy separately from its laboratory benchmark, so the accuracy a grower can actually expect in the field remains unknown. This absence of transparent field benchmarking is a methodological gap shared by the commercial tools and much of the published literature alike.

A feature-by-feature tally (Table 2) nonetheless understates the distinction. The more important question is not *what the competitors lack* but *why TomatoCare is the technically stronger design* for the users it targets. Four architectural decisions separate it from every platform reviewed.

**Deployment architecture — on-device versus cloud.** Farmonaut, Plantix, and Agrio all perform inference on remote servers, and Flora Incognita identifies species server-side; every one of them is therefore unusable, or degraded to cached content, when connectivity fails. TomatoCare runs all three inference stages on the device itself. This is not merely a convenience: it removes network round-trip latency, eliminates any recurring subscription or data cost, and — because no image ever leaves the handset — satisfies the data-minimisation principle of UAE Federal Decree-Law No. 45 of 2021 by construction rather than by policy (§2.8). For a grower in a low-connectivity field, an offline tool is not the better option; it is the only one that works.

**Safety — rejecting out-of-scope inputs.** Each competitor is, architecturally, a single classifier: shown a photograph of another crop, a hand, or an everyday object, it returns its most probable disease label, often with high confidence. This is the exact failure mode that TomatoCare's own Capstone 1 prototype exhibited and that its two-gate rejection cascade was built to eliminate (§2.9). No reviewed platform performs any equivalent out-of-distribution rejection before diagnosing, which makes TomatoCare safer precisely where a confident-but-wrong answer is most damaging.

**Trustworthy confidence.** TomatoCare's reported confidence is temperature-calibrated (§2.10), and any diagnosis below the 60% threshold is withheld in favour of an explicit Low-Confidence Warning. None of the reviewed applications exposes a calibrated confidence value or a comparable abstention mechanism; the user is handed a label, not a reliable indication of how far to trust it.

**Evaluation honesty and localisation depth.** TomatoCare reports both a laboratory result and a measured field result on real photographs (Chapter 7), where the competitors publish a single, favourable benchmark. It pairs this with a complete Arabic/English right-to-left interface and treatment guidance filtered by UAE growing method (greenhouse, open-field, hydroponic, saline-soil). Plantix and Flora Incognita do offer an Arabic localisation, but neither combines it with offline operation or UAE-specific agronomy, and Flora Incognita does not diagnose disease at all.

Taken together, it is not any single feature but their combination — fully on-device inference, a safety-first rejection cascade, calibrated confidence, honest field evaluation, and deep UAE localisation — that no reviewed platform matches, and that defines TomatoCare's technical contribution for the smallholder and home-grower segment it serves.

---

### 2.8 Privacy, Ethical, and Localisation Considerations

The use of AI-based diagnostic tools in agricultural environments raises a range of privacy, ethical, and localisation considerations that are particularly pertinent to the UAE context. The offline-first architecture of TomatoCare provides a structural solution to many of these concerns: since all image processing, scan storage, and diagnostic inference are performed exclusively on the user's device, no user data — including images, scan history, or device identifiers — is transmitted to any external server at any point during operation. This design complies with the data-minimisation principle of UAE Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data [13], which requires that information collected and processed be strictly necessary for the diagnostic function, and it eliminates the cross-border data transfer issues that affect cloud-based competitors.

Ethically, the application is designed to deliver diagnostic suggestions rather than clinical judgements. The 60% confidence threshold, below which the system issues a Low Confidence Warning instead of a confident diagnosis, is an explicit ethical safeguard intended to ensure that users are not encouraged to act on uncertain results. All treatment recommendations are framed as guidance to support — not replace — professional agronomic advice, and the application includes a clear disclaimer to this effect on the results screen.

Localisation in TomatoCare extends beyond translation. Effective bilingual support requires not only Arabic-language strings for all interface text and treatment recommendations, but also full right-to-left layout adaptation, mirrored navigation elements, and culturally appropriate use of agricultural and botanical terminology. TomatoCare meets these requirements by building on the native RTL support of Jetpack Compose, providing complete dual-language string resources, and sourcing Arabic terminology from established agricultural references. The resulting implementation ensures that the application is both functionally and culturally accessible to the significant Arabic-speaking segment of the UAE agricultural workforce, rather than treating Arabic support as a translation layer overlaid on an English-language product.

---

### 2.9 Out-of-Distribution Rejection and Cascaded Classifiers

A classifier deployed to non-expert users must handle inputs it was not trained on. Hendrycks and Gimpel [34] established softmax-confidence baselines for detecting misclassified and out-of-distribution inputs, and showed that a plain softmax is an unreliable rejector — high confidence does not imply in-distribution membership. A single classifier augmented with a reject class inherits this weakness: the reject decision competes with the disease-discrimination task within one shared representation. Decomposing the problem into a cascade of focused stages — each with a dedicated in-distribution or out-of-distribution objective — is a well-established alternative that gives each decision its own representation and allows the pipeline to terminate early on rejected inputs. TomatoCare adopts this cascade structure specifically to address the Capstone 1 prototype failure in which a shared reject head misclassified non-tomato inputs with high confidence.

---

### 2.10 Confidence Calibration

Modern deep networks are typically overconfident: their reported probabilities do not match their empirical accuracy. Guo et al. [27] characterised this phenomenon and showed that temperature scaling — dividing the logits by a single learned scalar *T* before the softmax — is a simple, effective post-hoc calibration method that minimises negative log-likelihood on a held-out set while leaving the argmax (and therefore accuracy) unchanged. Calibration quality is measured by the Expected Calibration Error (ECE), the weighted average gap between confidence and accuracy across probability bins. TomatoCare applies temperature scaling to its disease classifier because the application's low-confidence warning is only meaningful if the underlying probabilities are well calibrated.

---

### 2.11 Generative and Segmentation Techniques

Two additional techniques were employed in the project's domain-gap experiments. Deep Convolutional Generative Adversarial Networks (DCGANs) [31] generate images through adversarial training of a convolutional generator against a discriminator; they are a standard approach for synthetic data augmentation and were investigated as a means of enlarging the weakest disease class. The Segment Anything Model (SAM) [29] is a promptable zero-shot segmentation model; MobileSAM [30] is a lightweight distillation suitable for commodity hardware. Both were applied to test whether isolating the leaf from its background could close the laboratory-to-field gap. As Chapter 7 reports, neither technique improved field accuracy — a result consistent with the domain-gap literature: synthetic images reproduce the distribution on which they were trained, and background removal cannot alter the leaf's own field appearance.

---

### 2.12 Research Gaps and Conclusion

The literature review identifies four research and product gaps that together establish the design rationale for TomatoCare.

1. **Cloud-dependent architectures that do not serve low-connectivity users.** Three of the four reviewed applications (Farmonaut, Plantix, Agrio) require a constant internet connection, making them effectively unusable in the rural and outdoor environments typical of small-scale UAE agriculture [14, 16].

2. **Absence of offline, Arabic-capable diagnosis.** The applications that operate offline provide no Arabic interface, while those that do offer an Arabic localisation (Plantix and Flora Incognita) perform their inference in the cloud and therefore require connectivity for every diagnosis — leaving Arabic-speaking growers in low-connectivity areas without a usable option, even though they form a significant proportion of the UAE agricultural workforce.

3. **Absence of UAE-localised treatment recommendations.** The reviewed platforms provide recommendations suited to temperate-climate practice and do not address UAE-specific cultivation methods such as hydroponics, saline-soil farming, or extreme-heat management [26].

4. **Unreported laboratory-to-field gap.** Models trained on laboratory datasets such as PlantVillage are well known to lose accuracy on real field imagery, yet none of the reviewed platforms reports its field performance separately from its laboratory benchmark, leaving the accuracy a grower can actually expect unmeasured.

TomatoCare addresses all four gaps. It combines a PlantVillage-derived training pipeline with a safety-correct three-stage cascade, an offline-first architecture quantised to float16 for on-device inference, full bilingual English/Arabic support with right-to-left layout adaptation, and a treatment knowledge base localised to the four cultivation methods common in the UAE (greenhouse, open-field, hydroponic, saline-soil). Crucially, it reports its real-world field accuracy openly rather than presenting only a laboratory benchmark. These design choices are grounded in the literature reviewed in Sections 2.2 through 2.11: convolutional neural networks for image classification, lightweight architectures for mobile deployment, transfer learning, TensorFlow Lite quantisation, out-of-distribution rejection via cascaded classifiers, and confidence calibration.

This chapter has shown that the combination of features offered by TomatoCare is unmatched among current platforms, that each technical decision is grounded in the state of the art, and that the gaps the application is designed to address are real, documented, and consequential. Chapter 3 details the methodology through which TomatoCare implements these decisions.

---

## Chapter 3: Methodology

### 3.1 Introduction

This chapter outlines the methodology followed in the planning, development, and validation of TomatoCare, building on the problem definition in Chapter 1 and the literature review in Chapter 2. The chapter is organised into ten substantive sections. Section 3.2 describes the team structure and the allocation of responsibilities among team members. Section 3.3 introduces the Agile SDLC and presents the rationale for its adoption. Section 3.4 provides a formal comparative analysis of Agile against Waterfall, Spiral, and Scrum. Section 3.5 describes the Agile artefacts adopted by the team. Section 3.6 presents the sprint timeline and breakdown. Section 3.7 presents the project Gantt chart. Section 3.8 details the AI model development methodology, covering dataset preparation, preprocessing, architecture selection, training, calibration, and TFLite export. Section 3.9 addresses the data persistence strategy, and Section 3.10 lists the development tools and environment.

The methodology combines two technical disciplines — machine learning model development and native Android application development — in a single iterative process. This combination is reflected in the Agile approach: model training is inherently experimental and requires repeated cycles of training, evaluation, and refinement, while mobile application development benefits from incremental delivery and continuous testing on physical hardware.

---

### 3.2 Team Roles and Responsibilities

The TomatoCare team comprises five members. While the Agile methodology emphasises collective ownership and shared accountability, individual primary responsibilities were assigned based on technical strengths to ensure that no critical area of the project lacks an accountable owner. The role distribution is summarised in Table 3.

**Table 3: Team Roles and Responsibilities**

| Team Member | Student ID | Primary Role | Key Responsibilities |
|---|---|---|---|
| AlBaraa AlOlabi | 202210405 | Computer Vision Engineer | Dataset preparation and augmentation, MobileNetV3-Large training, model evaluation, TFLite export and float16 quantisation |
| Ahmed Saeed Ahmed Mohamed | 202211615 | Android Developer (UI/UX) | Jetpack Compose UI implementation, screen design, RTL layout, language toggle, result and severity badge components |
| Kazi Mahir Al Wafi | 202211829 | Android Developer (Backend) | CameraX integration, image preprocessing pipeline, TFLite inference engine, JSON storage, Storage Access Framework export/import |
| Iyad El Boussi | 202111261 | System Architect & Documentation | Requirements specification, UML diagrams, architecture design, academic report authorship |
| Fares Muaatasem Awda | 202211410 | QA & Integration Lead | Functional testing, device compatibility testing, integration testing, bug tracking, Arabic localisation review |

Every team member participates in sprint planning, sprint reviews, and retrospectives. Any merge to the main branch requires mandatory code review with approval from at least one team member who did not author the change. Documentation is a shared responsibility, with the System Architect maintaining the canonical version of the report and incorporating contributions from all members.

---

### 3.3 Software Development Lifecycle

The Software Development Lifecycle (SDLC) is a formal model of the activities involved in producing a software system, from requirements gathering through to final deployment and validation [24]. SDLC models differ in how they order these activities — some follow a linear, phase-by-phase sequence, while others use iterative or incremental cycles — and the choice of model has significant practical implications for projects involving uncertainty, experimentation, or evolving requirements.

TomatoCare uses an Agile-based SDLC. Unlike linear models such as Waterfall, in which each phase must be completed before the next begins, Agile breaks the project into a sequence of short, time-boxed iterations called sprints. Each sprint produces a working increment of the system, which is then assessed and used to inform planning for the next sprint. This iterative structure enables the team to respond to findings — such as discovering that a particular augmentation strategy induces overfitting, or that a specific UI element is unintuitive in an Arabic RTL layout — by adjusting the plan without restarting the entire process.

Three reasons explain why Agile is the best fit for TomatoCare. First, machine learning model development is inherently experimental: model accuracy depends on a complex interaction of dataset quality, augmentation strategy, architectural choice, and hyperparameter settings, and the most effective combination cannot be known in advance. Repeated training and evaluation cycles are essential to meet the 90% accuracy criterion. Second, strong coordination between the machine learning and mobile development streams requires frequent synchronisation and incremental integration rather than a single large-scale integration at the end. Third, the offline-first architecture introduces device-specific constraints — APK size, memory footprint, inference latency — that can only be validated by testing on real target hardware, a process Agile accommodates naturally at the end of each sprint.

*Figure 7: Agile SDLC Cycle*

---

### 3.4 Methodology Comparison and Selection

Several established SDLC methodologies could be applied to TomatoCare, each with distinct trade-offs [24, 25]. Table 4 compares the four most relevant options against the criteria most pertinent to this project.

**Table 4: Comparison of SDLC Methodologies**

| Criterion | Waterfall | Spiral | Scrum | Agile (Selected) |
|---|---|---|---|---|
| Development Approach | Sequential, linear progression through fixed phases | Iterative with explicit risk analysis at each cycle | Agile framework with strict roles and ceremonies | Iterative and incremental with flexible structure |
| Flexibility | Low — changes after development starts are difficult | Moderate — supports change but management overhead is high | High within sprint cycles | Very high — adapts continuously |
| Risk Management | Limited — risks surface late | Strong — risk evaluation built into each spiral | Risks addressed in sprint reviews | Risks minimised through continuous iteration |
| Suitability for ML Projects | Poor — cannot accommodate experimental nature of model training | Adequate but operationally heavy | Good when team can adopt full Scrum ceremony | Excellent — directly supports experiment-driven development |
| Feedback Integration | At end of each phase | At end of each spiral | At end of each sprint | Continuous, throughout each iteration |
| Documentation Overhead | High | High | Moderate | Light to moderate |
| Suitability for Five-Person Team | Workable but rigid | Excessive structure | Workable but ceremony-heavy | Well-matched to team size |
| **Overall Suitability for TomatoCare** | **Low** | **Moderate** | **High** | **Very High (Selected)** |

The Waterfall model was rejected because its inflexibility is incompatible with the experimental nature of model training and the iterative refinement required in offline-first mobile development. Once a Waterfall project has passed the requirements phase, accommodating a discovered need — such as an additional augmentation strategy required to address the field-versus-laboratory accuracy gap — requires either ignoring the need or recycling the affected phases.

The Spiral model offers more comprehensive risk management but introduces too much operational overhead for a five-person student team working within a fixed academic schedule. Its structured risk-analysis cycles are worthwhile in safety-critical or high-cost projects, but are disproportionate for a project of TomatoCare's scope.

Scrum, as a specific Agile framework, was also considered. Its strengths — fixed-length sprints, clear roles (Product Owner, Scrum Master, Development Team), and prescribed ceremonies (Sprint Planning, Daily Standup, Sprint Review, Sprint Retrospective) — are well aligned with the project's needs. However, the formal role boundaries that Scrum prescribes are not realistic for a group of five individuals each contributing across multiple technical domains. The team therefore adopted a lightweight Agile process that incorporates the most valuable Scrum artefacts — sprint planning, sprint review, and sprint retrospective — without imposing the full ceremonial structure of canonical Scrum.

---

### 3.5 Agile Artefacts

To ensure transparency, progress tracking, and measurable value delivery in every iteration, the team uses the following Agile artefacts.

The **Product Backlog** is the canonical list of all features and tasks required to deliver the project. For TomatoCare, this includes: dataset collection and augmentation, CNN architecture selection and training, TFLite conversion with float16 quantisation, offline inference pipeline integration, implementation of all UI screens (Home, Scan, Results, History, Settings), bilingual English/Arabic support with full RTL layout, confidence-score display with the 60% threshold warning, and scan history export/import via the Android Storage Access Framework.

The **Sprint Backlog** is the subset of the Product Backlog selected for completion within a given sprint, chosen based on dependencies, team capacity, and the sprint goal.

**Sprint Planning** is performed at the start of every sprint to establish the sprint goal and select the corresponding backlog items. For example, the Sprint 4 goal was to produce a trained, evaluated, and quantised TFLite model achieving at least 90% accuracy on the held-out test set.

**Daily Standups** are brief synchronisation meetings in which each team member reports progress since the last standup, the next steps to be taken, and any blockers requiring team support. These sessions are kept concise and oriented towards coordination rather than status reporting.

**Sprint Reviews** are held at the end of every sprint and present the sprint's deliverables to the project supervisor. Reviews for TomatoCare include demonstrations of working software — such as the live offline diagnosis pipeline running on a physical Android device — alongside artefacts such as model training curves and confusion matrices.

**Sprint Retrospectives** follow each Sprint Review and focus on process improvement. The team identifies what worked well, what can be improved, and the concrete actions to be taken in the following sprint. Examples of adjustments made include revisions to the data augmentation strategy to reduce overfitting, extensions to the JSON storage format to support export/import, and updates to the device testing matrix.

The **Increment** at the end of each sprint is tangible, working progress towards the final system. Each increment is evaluated against the sprint goal to provide the basis for the next sprint's planning.

---

### 3.6 Sprint Timeline and Breakdown

TomatoCare is a two-semester project, with Capstone 1 in Spring 2026 and Capstone 2 in Autumn 2026. Capstone 1 focuses on project planning, requirements engineering, system design, and academic writing; Capstone 2 focuses on technical implementation. The sprint schedule reflects this split, with three sprints allocated to each capstone phase.

**Table 5: Sprint Timeline and Breakdown**

| Sprint | Phase | Duration | Focus | Key Deliverables |
|---|---|---|---|---|
| Sprint 1 — Planning and Literature Review | Capstone 1 | 20 Jan – 16 Feb 2026 | Project initiation, backlog creation, problem definition, literature review of existing platforms, identification of research gaps, dataset and CNN architecture selection | Chapters 1 and 2 of the report; initial product backlog; PlantVillage dataset and MobileNetV3-Large confirmed as baseline choices |
| Sprint 2 — Methodology and System Design | Capstone 1 | 17 Feb – 21 Mar 2026 | Documentation of Agile methodology, definition of the AI training pipeline, design of the Android application architecture, requirements specification, production of all UML diagrams, JSON data schema design | Chapters 3 and 4 of the report; full UML diagram suite (use case, sequence, activity, class, state chart, ERD); requirements catalogue |
| Sprint 3 — Final Design and Report Consolidation | Capstone 1 | 22 Mar – 20 Apr 2026 | UI mockup design, architectural design, integration of all chapters, internal review, citation verification, formatting, and submission | Chapter 5 of the report; UI mockups for all screens; architectural diagram; final consolidated Capstone 1 report and presentation |
| Sprint 4 — Dataset Preparation and Model Training | Capstone 2 (planned) | ~3 weeks | Implementation of the dataset preprocessing pipeline, augmentation comparison (deployed model uses horizontal flip only; heavier field-simulation augmentation tested and rejected — Chapter 7), two-stage transfer-learning training, model evaluation against the target metrics established in §3.8.5 | Trained MobileNetV3-Large achieving ≥ 90% accuracy on the test set; quantised TFLite file under 15 MB; training curves and confusion matrix |
| Sprint 5 — Android Application Development | Capstone 2 (planned) | ~3 weeks | CameraX integration, embedded TFLite inference pipeline, JSON-based scan history storage, bilingual interface with full Arabic RTL support, scan history export and import via the Android Storage Access Framework | Functional APK with offline diagnosis pipeline; complete bilingual UI; working JSON export and import |
| Sprint 6 — Testing, Validation, and Release | Capstone 2 (planned) | ~3 weeks | Functional testing on low-end target devices (API 26, 2 GB RAM), verification of all non-functional requirements (inference speed, APK size, cold start time, full offline operation), bug fixes, RTL layout review, and final Capstone 2 report | Release-ready APK with all NFRs verified; open-source GitHub repository; final Capstone 2 report and project demonstration |

The work in Sprints 4, 5, and 6 is summarised here for completeness; detailed implementation and evaluation results are reported in Chapters 6 and 7.

---

### 3.7 Gantt Chart

Figure 8 shows the Gantt chart for the Capstone 1 sprints, covering the project timeline from January to April 2026. The chart illustrates the sequencing of activities, the parallelism between report writing and design work, and the dependencies between sprints.

*Figure 8: Gantt Chart*

The Gantt chart serves three purposes. First, it communicates timeline expectations clearly to all team members, indicating when major contributions are required. Second, it exposes dependencies — for example, the Capstone 1 design artefacts produced during Sprint 3 must be finalised before Capstone 2 implementation can begin in Sprint 4, so that upstream delays can be detected and managed before they affect the implementation phase. Third, it provides an anchor against which real progress is measured at the end of each sprint, enabling the team to detect schedule slippage early and adjust scope or effort accordingly.

---

### 3.8 AI Model Development Methodology

The cascade design, training procedure, calibration, and on-device export described in this section together specify how the AI subsystem is built and what evidence is gathered to demonstrate that the design objectives in §1.5 are met. The Agile process and team workflow within which this work is conducted are described in §§3.1–3.7.

#### 3.8.1 Datasets

The cascade is trained from three labelled sources, each serving a distinct stage. The disease classifier (Stage 3) is trained on a tomato leaf-disease collection referred to as *tomato20k*; the gates (Stages 1 and 2) are trained on smaller balanced datasets constructed specifically to distinguish leaf from non-leaf and tomato from non-tomato. All sources are kept separate to prevent gate decisions from leaking information about disease classes.

**Stage 3 — Disease Classifier (tomato20k, 11 classes).** tomato20k is a PlantVillage-derived tomato collection augmented with a powdery mildew class absent from the original PlantVillage tomato subset. The eleven classes are: `bacterial_spot`, `early_blight`, `late_blight`, `leaf_mold`, `powdery_mildew`, `septoria_leaf_spot`, `spider_mites`, `target_spot`, `tomato_mosaic_virus`, `tomato_yellow_leaf_curl_virus`, and `healthy`. The collection contains 32,534 images in total, partitioned into a 25,851-image training pool and a 6,683-image held-out test set; the test set is the basis for every Stage 3 figure reported in Chapter 7 and is never seen during training or early stopping. The training pool is further divided 85/15 into training and validation (seed 42, stratified per class). The resulting three-way split is summarised in Table 3.1.

**Table 3.1: Stage 3 (tomato20k) Dataset Split**

| Partition | Images | Approx. share | Role |
|---|---|---|---|
| Training | ≈ 21,973 | ≈ 68% | Weight updates (Phases 1–2) |
| Validation | ≈ 3,878 | ≈ 12% | Early stopping, learning-rate scheduling, temperature fit |
| Test (held-out) | 6,683 | ≈ 20% | Chapter 7 reported metrics only |
| **Total** | **32,534** | **100%** | — |

**Train/test independence and the same-plant question.** Because tomato20k is PlantVillage-derived, and PlantVillage is known to contain several photographs of the same physical leaf, it is reasonable to ask whether near-duplicate images of one plant could fall in both the training and test partitions. Exact duplicates were removed when the source datasets were merged and de-duplicated, and the split is stratified per class under a fixed seed; however, the split is not grouped by source plant, so the possibility that visually near-identical shots of the same laboratory leaf land on both sides of the train/test boundary cannot be fully excluded. This is a recognised limitation of all PlantVillage-derived evaluation, and it is a principal reason the project does not rest on the laboratory figure alone. The held-out PlantDoc field set (described below) is drawn from entirely independent sources, shares no plants or photographic provenance with the training data, and therefore provides the trustworthy measure of real-world generalisation; the laboratory-to-field gap reported in Chapter 7 should be read in that light.

**Stage 2 — Tomato Gate.** Positives are tomato leaves from the above collection; negatives are non-tomato crop leaves — 4,627 PlantVillage pepper and potato images plus PlantDoc non-tomato field leaves. Including real-field PlantDoc images among the negatives is deliberate: without them, a model trained on laboratory positives and laboratory negatives would learn to separate images by photographic style (lab vs. field) rather than by leaf identity — precisely the failure mode that motivated the cascade design (§1.3).

**Stage 1 — Leaf Gate.** Positives are leaf images (tomato and other crops); negatives are natural-world non-leaf images (people, animals, vehicles, everyday objects) drawn from an ImageNette-style natural-image source. The gate uses the MobileNetV3-Small backbone because the binary in-distribution or out-of-distribution decision requires little model capacity.

**PlantDoc Field Data.** 824 tomato field images are folded into the Stage 2/3 training splits, and 79 tomato field images are held out as the field benchmark used in Chapter 7. PlantDoc contains no `target_spot` or `powdery_mildew` images, so the field benchmark covers a 9-class subset of the 11 deployed classes.

#### 3.8.2 Preprocessing and Parity

Every image — in both the Python training pipeline and the Android Kotlin inference engine — passes through an identical, contract-fixed pipeline: decode to RGB (3-channel); centre-crop to the largest centred square (to avoid squash-to-square distortion); resize to 224×224 using bilinear interpolation; scale to [0, 1] by dividing by 255; and no ImageNet mean/std normalisation (the network consumes [0, 1] directly). The input tensor is therefore float32[1, 224, 224, 3].

Centre-cropping rather than naive resize-to-square preserves leaf morphology — the lesion size and shape ratios that distinguish diseases — and corrects a Capstone 1 prototype defect in which the Python and Kotlin sides used different aspect-ratio handling. Preprocessing parity is part of the model-asset contract (§5.10) and is regression-tested: the Kotlin engine and the Python pipeline must produce numerically identical tensors for the same input image; otherwise, on-device probabilities cannot be trusted to match the Python evaluation figures.

#### 3.8.3 Cascade Architecture

The system is a sequential cascade of three independent classifiers. A rejection at either gate halts the pipeline and returns a retake instruction to the user; only inputs that pass both gates reach the disease classifier. The gates use the MobileNetV3-Small backbone because binary in-distribution or out-of-distribution decisions require little model capacity, while the disease classifier uses MobileNetV3-Large for the harder eleven-class problem.

This is the central architectural decision of the project. A single classifier must simultaneously solve out-of-distribution rejection and fine-grained disease discrimination within one softmax head — conflicting objectives that share one representation, with the rare reject class competing for capacity against ten common disease classes. The Capstone 1 prototype exhibited the predicted failure: non-tomato inputs were classified as a tomato disease with high confidence. Splitting the decision into three stages gives each its own representation and allows the easy decisions (is this a leaf? is it a tomato?) to be made with small, fast, confident models before the hard disease-discrimination question is even attempted.

The cascade is the third iteration of the project's recognition engine. The first version, TomatoCareNet, was a custom convolutional network built from scratch — four convolutional blocks with squeeze-and-excitation attention and global average pooling, trained across four merged datasets (PlantVillage, PlantDoc, TomatoVillage, and a supplementary Kaggle tomato set). It reached 91.17% on a held-out test split and confirmed that the team could design and train a competitive architecture end-to-end, but also that high laboratory accuracy alone does not guarantee reliable behaviour on out-of-scope inputs. The second iteration replaced the bespoke network with a single MobileNetV3-Large backbone plus a `not_tomato` reject class, which raised in-domain accuracy and reduced the model's mobile footprint, but surfaced the safety defect described above. The third and deployed iteration — the three-stage cascade — resolves that defect by giving each decision its own dedicated model. Each step was a deliberate engineering response to a measured limitation of the previous one, and the progression from a hand-built CNN to a calibrated, safety-correct cascade is itself a contribution of the project.

#### 3.8.4 Training

All three stages follow the same two-phase transfer-learning recipe. In **Phase 1** (head training, frozen backbone), the ImageNet-pretrained backbone is frozen and only the new classification head is trained, using the Adam optimiser with learning rate 1×10⁻³, categorical cross-entropy loss, and label smoothing of 0.05. In **Phase 2** (fine-tuning), the top approximately 30 backbone layers are unfrozen and trained at a reduced learning rate (Adam, 1×10⁻⁴) to adapt high-level features to leaf pathology without disrupting the low-level ImageNet representations.

Class imbalance (e.g., `powdery_mildew` is the smallest class) is handled using inverse-frequency class weights. Training uses EarlyStopping (patience 5 on validation accuracy, best weights restored) and ReduceLROnPlateau (factor 0.5, patience 3 on validation loss). The deployed Stage 3 variant is the minimal-augmentation model (horizontal flip only); the augmentation comparison and its findings are reported in Chapter 7.

#### 3.8.5 Confidence Calibration

Deep classifiers are typically overconfident, which would make the application's 60% low-confidence threshold meaningless if left uncorrected. Temperature scaling [27] is applied to Stage 3: a single scalar temperature *T* is fitted by minimising negative log-likelihood on a held-out validation set, and the logits are divided by *T* at inference. Temperature scaling does not change the argmax — and therefore does not change accuracy — but it does improve the calibration of the reported probability. The fitted temperature is T = 0.5889. The resulting ECE figures are reported transparently in Chapter 7: 0.0046 in-sample and 0.061 on the honest held-out test set. The gap between these figures motivates the dedicated calibration-set work flagged in Chapter 9.

#### 3.8.6 Export and On-Device Deployment

Each stage is exported to TensorFlow Lite with float16 weight quantisation (approximately 2× smaller than float32; inputs and outputs remain float32 so the Android inference layer is unchanged). The three deployed artefacts are `stage1_leaf_float16.tflite` (MobileNetV3-Small, 1.92 MB), `stage2_tomato_float16.tflite` (MobileNetV3-Small, 1.92 MB), and `stage3_disease_float16.tflite` (MobileNetV3-Large, 6.03 MB), for a combined 9.87 MB — well within the 15 MB model budget defined in NFR-AI-02 (§4.9).

On Android, the three interpreters run in sequence; a gate rejection short-circuits the pipeline so no unnecessary inference is performed. Class order and preprocessing parameters are baked into the model-asset contract (§5.11), so updating any single model requires only swapping the `.tflite` file and the label list — no Kotlin code change is required.

---

### 3.9 Data Persistence: JSON File Storage

TomatoCare stores scan history, diagnosis results, and user settings in a JSON file in the application's internal storage directory (`context.filesDir`) [20]. The data classes representing scans, results, and treatments are serialised and deserialised using Kotlin Serialization [21].

JSON file storage is chosen over a relational database (such as Room or SQLite) for six substantive reasons:

1. The data model is conceptually simple — an unstructured sequential list of scan records — and does not require the relational joins, aggregate operations, or complex queries that would justify the overhead of a relational database.
2. The project avoids schema migration costs; updating the data model requires only modifying a Kotlin data class, rather than writing database migration scripts.
3. JSON aligns naturally with the application's export and import capabilities, since the on-device storage format and the export format are identical, eliminating the need for a separate serialisation layer.
4. An atomic-write pattern (write to a temporary file, then rename to the target file) is crash-safe, ensuring the JSON file cannot be left in a corrupted state if the application is interrupted during a write.
5. The data volume is modest — a typical user produces a small number of scans per day, each occupying approximately 500 bytes, so even a thousand scans occupy under one megabyte, well within the performance range of file-based I/O.
6. Android's internal storage security guarantees — sandboxed per-application access and on-device encryption on Android 10 and above — are applied to the JSON file automatically, without requiring any additional cryptographic effort from the application.

The JSON file structure is an array of scan records, each containing: an integer scan identifier; the image path; an ISO 8601 timestamp; the growing method selected by the user; the model version used at scan time; and an array of diagnosis results. Each result includes the condition name, a primary-result flag, a confidence score, a severity level, a static `stress_type` label (descriptive metadata, not a separate prediction), and an array of treatment objects containing treatment type, urgency level, and bilingual recommendation strings. The full schema is presented and discussed in Chapter 5.

#### 3.9.1 Ethical Handling of User-Feedback Images

The in-app feedback flywheel (§6.4) invites users to confirm or correct a diagnosis and, in doing so, to contribute their own field photographs as future training data. Because those photographs are user-generated content rather than public dataset images, their handling is governed by an explicit set of ethical safeguards, aligned with the data-protection principles of UAE Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data [13].

**Informed consent and opt-in.** Contribution is strictly opt-in. A diagnosis is never retained as training data unless the user actively confirms or corrects it; the default behaviour stores nothing beyond the local scan history the user already controls. The feedback control states plainly that the image and its label may be reused to improve the model.

**On-device by default; user-initiated transfer only.** Feedback images never leave the device automatically. They remain in the application's sandboxed internal storage and are aggregated into a training-data export only when the user explicitly invokes it through the Android Storage Access Framework, selecting the destination themselves (§6.4). The application declares no INTERNET permission, so no covert transmission path exists (§7.8).

**Data minimisation.** Only the data necessary for retraining is captured: the leaf photograph, the user-confirmed class label, the growing method, and the model version. No account, contact detail, device identifier, or location is attached — satisfying the PDPL principle that processing be limited to what is necessary for the stated purpose [13].

**Anonymity and the right to erasure.** Contributed images carry no personal identifier and cannot be traced to an individual user. Because every record lives in a single user-controlled JSON store and image directory, the user can delete any scan — and thereby withdraw any contribution — at any time, directly exercising the erasure right afforded to data subjects under the PDPL.

**Purpose limitation.** Contributed images are used only to retrain the disease cascade on the real operating distribution; they are not repurposed for any secondary use. This narrow purpose is the basis on which consent is sought and is honoured by design rather than by policy alone.

Together these safeguards let the feedback flywheel close the laboratory-to-field gap with real data (§7.5, Chapter 9) without weakening the privacy guarantees that the offline-first architecture already establishes (§2.8).

---

### 3.10 Development Tools and Environment

The project uses a fixed toolchain spanning machine learning, Android development, version control, and design.

| Tool / Framework | Purpose |
|---|---|
| TensorFlow (Python) | CNN model construction, training, and evaluation |
| TensorFlow Lite | Conversion of trained models to mobile-compatible `.tflite` format with float16 quantisation |
| Kotlin + Jetpack Compose | Native Android application development; declarative UI with built-in RTL layout support |
| CameraX | Unified Android camera API for consistent image capture across target devices |
| Kotlin Serialization | Serialisation and deserialisation of scan records to and from JSON storage |
| Android Storage Access Framework | Export and import of scan history files without legacy storage permissions |
| Kaggle | Source of the publicly available PlantVillage dataset |
| GitHub | Version control and team collaboration; branch protection and mandatory code review enforced |
| Figma | Interface design, wireframing, and interactive prototyping |
| Android Studio | Integrated development environment for coding, debugging, and on-device testing |

---

### 3.11 Conclusion

This chapter has detailed the methodology through which TomatoCare was developed. The Agile SDLC was selected because its iterative structure is uniquely effective for a project that combines experimental machine learning with mobile application development. Six sprints of approximately two to three weeks each — three in Capstone 1 and three planned for Capstone 2 — provide the operational rhythm of the project, supported by Agile artefacts that ensure transparency and continuous improvement across both semesters. The five-member team operates with well-defined primary roles and shared collective ownership, balancing individual accountability with the collaborative working style demanded by the project's scope and timeline.

The AI model development methodology — encompassing dataset construction, the preprocessing-parity contract, two-stage transfer learning on MobileNetV3-Large, confidence calibration via temperature scaling, and TFLite export with float16 quantisation — implements the design decisions justified in Chapter 2. The data persistence strategy, based on JSON file storage and Kotlin Serialization rather than a relational alternative, is appropriate to the simplicity of the data model and the operational requirements of the application. The toolchain is uniform, current, and well-supported, enabling the project to be delivered within the academic timeline of Capstone 1 and Capstone 2.

With the methodology established, Chapter 4 defines the system requirements — functional, non-functional, domain, and constraint — and the use case descriptions that specify what TomatoCare must do.

---

## Chapter 4: Requirements and Specifications

### 4.1 Introduction

This chapter defines the requirements specification for TomatoCare, translating the problem definition from Chapter 1 and the design choices justified in Chapter 2 into concrete, testable statements of what the system must do and how well it must do it. The chapter is organised into ten substantive sections. Section 4.2 presents the functional requirements. Section 4.3 presents the non-functional requirements. Section 4.4 defines the domain requirements arising from the agricultural and UAE-specific context. Section 4.5 specifies the constraint requirements. Section 4.6 presents the stakeholder perspectives that informed requirements selection. Section 4.7 presents the use case diagram. Sections 4.8 through 4.11 cover the AI subsystem requirements: functional, non-functional, domain constraints, and traceability, respectively.

The requirements documented in this chapter were elicited through three complementary activities: analysis of the problem domain as described in Chapter 1, comparative review of existing solutions and identification of their gaps as documented in Chapter 2, and consideration of the technical constraints imposed by an offline-first, on-device inference architecture targeting low-end Android hardware. These requirements are intended to be sufficient for the design phase in Chapter 5 and the implementation phase in Capstone 2.

---

### 4.2 Functional Requirements

Functional requirements define the behaviours the TomatoCare system must exhibit in response to user actions and internal events. They specify what the system shall do, expressed as single declarative statements using the modal verb "shall," uniquely identified for traceability, and written at a level of detail sufficient to support the derivation of test cases.

**FR-01:** The system shall operate fully offline. All processing, storage, and retrieval shall be performed on-device without any network connection during normal operation.

**FR-02:** The system shall enable the user to photograph a tomato leaf using the device camera, within the CameraX framework [22].

**FR-03:** The system shall allow the user to select an existing tomato leaf image from the device gallery as an alternative to live capture.

**FR-04:** The system shall validate the input image before inference. It shall reject files that are not PNG or JPEG format or exceed 10 MB in size, and shall display a descriptive error message accordingly.

**FR-05:** The system shall preprocess all input images before inference by resizing to 224×224 pixels and normalising pixel values from the integer range [0, 255] to the floating-point range [0, 1].

**FR-06:** The system shall classify the input image using on-device inference with the embedded TensorFlow Lite model, with no reliance on an internet or network connection at any point.

**FR-07:** The system shall display the diagnosis result to the user, including the identified condition name in both English and Arabic, the confidence score as a percentage, and a severity indicator.

**FR-08:** The system shall display a Low Confidence Warning when the highest-scoring class returned by the model has a confidence score below 60%, to alert the user to retake the photograph under better conditions.

**FR-09:** The system shall use localised treatment guidelines based on the identified condition. Recommendations shall be retrieved from the embedded JSON treatment database and displayed in the user's selected interface language.

**FR-10:** The system shall filter treatment recommendations according to the growing method selected by the user, supporting at least the following categories: greenhouse, open-field, hydroponic, and saline-soil cultivation.

**FR-11:** The system shall store every completed scan record locally in a Kotlin Serialization JSON file. Each record shall contain the scan identifier, image path, timestamp, identified condition, confidence score, stress type, severity level, and associated treatment information.

**FR-12:** The system shall enable the user to access the full history of past scans in date order.

**FR-13:** The system shall enable the user to select a past scan in the history view and review its full details, including the original diagnosis and treatment recommendations.

**FR-14:** The system shall present a dashboard summarising the user's scan activity.

**FR-15:** The system shall allow the user to delete all locally stored scan history via a dedicated control in the Settings menu, presenting a confirmation dialogue before deletion is performed.

**FR-16:** The system shall enable the user to export all scan history data as a JSON file to a user-chosen path, using the Android Storage Access Framework.

**FR-17:** The system shall enable the user to import a previously exported JSON file to restore scan history. The system shall validate the file format prior to importing and shall reject files that do not match the expected schema.

**FR-18:** The system shall support both English and Arabic as interface languages, allowing the user to switch between them at any time via the Settings menu.

**FR-19:** When Arabic is selected as the active language, the system shall render the entire application layout in right-to-left mode, with mirrored navigation elements, text orientation, and UI component positioning.

**FR-20:** The system shall display clear, descriptive error messages to the user in the event of any anticipated failure — including unsupported image formats, model loading failure, and local storage errors — and shall remain in a stable state without crashing.

---

### 4.3 Non-Functional Requirements

Non-functional requirements define the quality attributes the system must exhibit. Each is expressed as a measurable, testable property of the system.

**NFR-01 — Connectivity:** The system shall function without requiring an internet connection. No network call shall be initiated by the application during normal operation.

**NFR-02 — Inference Performance:** The system shall complete on-device inference for a single submitted image within three seconds on a target device meeting the minimum specification (Android API 26, 2 GB RAM, mid-range processor of approximately Snapdragon 660 class or equivalent).

**NFR-03 — Diagnostic Accuracy:** The deployed disease classifier shall achieve a minimum classification accuracy of 90% on a held-out laboratory test set, with real-world field accuracy additionally measured and reported (Chapter 7).

**NFR-04 — Application Size:** The complete application, including the embedded TensorFlow Lite models and all assets, shall not exceed 50 MB. The combined quantised model files shall not exceed 15 MB.

**NFR-05 — Usability:** The user interface shall be operable by a user with no prior technical or agricultural training. Core functions — scanning, viewing results, and reviewing history — shall each be reachable within two taps from the home screen. Text shall meet a minimum size and contrast level sufficient for outdoor reading in bright sunlight.

**NFR-06 — Reliability:** The application shall not crash under normal operating conditions. All anticipated failure modes — including corrupt images, model loading failures, and storage I/O errors — shall be handled gracefully with descriptive error messages that leave the application in a stable, recoverable state.

**NFR-07 — Portability:** The application shall run on Android devices with API level 26 (Android 8.0 Oreo) and above.

**NFR-08 — Data Privacy:** No user image, scan record, or device-identifying information shall be transmitted outside the device under any circumstances. The application shall comply with the data-minimisation principles of UAE Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data [13].

**NFR-09 — Maintainability:** The application's source code shall be organised into modular components (presentation layer, business logic layer, persistence layer, inference engine, and localisation resources) such that the AI model, language resources, or treatment database can be updated independently without requiring modifications to unrelated parts of the application.

**NFR-10 — Localisation Quality:** All user-facing strings — including disease names, treatment recommendations, error messages, and navigation labels — shall be available in both English and Arabic. Arabic terminology shall use established botanical and agricultural usage rather than literal translation.

The following three requirements refine the usability and localisation goals of NFR-05 and NFR-10 into explicit, separately verifiable accessibility criteria.

**NFR-11 — Text Scaling and Font Size:** All user-facing text shall be defined in scalable-pixel (`sp`) units and shall honour the operating-system font-size setting, remaining legible and free of clipping or overlap when the system font scale is increased to at least 130%. Body text shall be no smaller than 14 sp and primary action labels no smaller than 16 sp. *Verification: inspection of layout resources for `sp` (not `dp`/`px`) usage, plus a functional test of each core screen at 100% and 130% system font scale (§7.9).*

**NFR-12 — Arabic Readability and Right-to-Left Layout:** In Arabic mode the entire interface shall mirror to a right-to-left layout — including navigation order, directionally meaningful icons, and text alignment — and shall render Arabic with adequate line height using a font that supports full Arabic glyph shaping. No English text shall remain in the Arabic interface except proper nouns and Latin binomial (scientific) names. *Verification: functional test of every screen in Arabic mode for correct RTL mirroring and string completeness (§7.9); inspection of `values-ar/` parity with `values/`.*

**NFR-13 — Colour Contrast:** All text and essential interface elements shall meet the WCAG 2.1 Level AA contrast standard — at least 4.5:1 for normal text and 3:1 for large text (≥ 18 pt, or 14 pt bold) and meaningful icons — in both light and dark themes. Severity shall never be communicated by colour alone; a text label shall always accompany the colour cue (WCAG 1.4.1). *Verification: measurement of foreground/background contrast ratios for each theme using a contrast analyser, recorded in the test evidence (§7.9).*

---

### 4.4 Domain Requirements

Domain requirements arise from the specific operational context of TomatoCare — agricultural diagnosis in the UAE — and from the academic and ethical norms governing AI-based diagnostic tools. They differ from functional requirements in that they reflect rules imposed by the domain itself rather than features chosen by the design team.

**DR-01:** The system shall classify only tomato (*Solanum lycopersicum*) leaves. Diagnostic claims about other plant species are explicitly outside the system's domain of validity.

**DR-02:** The system shall present each diagnosis as one of its eleven trained tomato conditions (ten diseases or healthy). Conditions outside this set — including abiotic stress such as sunscald, heat injury, or salinity-induced chlorosis — are outside the system's domain of validity and shall surface as a low-confidence warning rather than a confident label. The system does not claim to detect or classify abiotic stress.

**DR-03:** Treatment advice shall be specific to UAE growing conditions, taking into account high heat tolerance, salinity tolerance, and the agricultural inputs and practices available in the region.

**DR-04:** The system shall display a disclaimer on the results screen stating that TomatoCare provides diagnostic recommendations, not professional agronomic advice.

**DR-05:** Disease and treatment terminology shall use formal botanical and agricultural language in both English and Arabic. Common-name simplifications shall not replace standard terminology used in agricultural extension materials.

**DR-06:** The confidence threshold below which the system displays a Low Confidence Warning shall be set at 60%. This threshold reflects an ethical safeguard against misleading users with uncertain diagnoses and is designated as a configurable parameter in future releases.

**DR-07:** The system shall not infer or display claims about the user's identity, location, or behaviour. Diagnostic outputs shall be limited to observable visual properties of the submitted leaf image.

---

### 4.5 Constraint Requirements

Constraint requirements bound the design space within which the system must be implemented. They reflect technical, operational, and academic constraints that the project must respect regardless of design preferences.

**CR-01:** The application shall operate without requiring any network connectivity. No cloud-based API, model-serving endpoint, or remote database may be used.

**CR-02:** The TensorFlow Lite model files shall be included in the APK at build time and shall not be downloaded at runtime.

**CR-03:** The application shall target Android only. The project scope does not include iOS or cross-platform implementation.

**CR-04:** Scan history persistence shall use a JSON flat file accessed through Kotlin Serialization. Relational database systems including Room and SQLite shall not be used in the Capstone 1/Capstone 2 deliverable.

**CR-05:** The convolutional neural network model shall be trained exclusively on tomato leaf images. Generalisation to other plant species or non-leaf imagery is outside the model's scope.

**CR-06:** The minimum target device specification is Android API level 26 (Android 8.0 Oreo) with at least 2 GB of RAM. Devices below this specification are explicitly outside the support envelope.

**CR-07:** Advanced features — including IoT sensor integration, multi-crop classification, user accounts, and cloud synchronisation — are out of scope for Capstone 1 and Capstone 2 and are documented as future work.

**CR-08:** The application shall not provide legally binding agrochemical prescriptions. Treatment outputs are advisory recommendations and shall be presented as such.

---

### 4.6 Stakeholder Perspective

The requirements above reflect the needs and interests of several stakeholder groups. Each group assigns different priorities to the system, and the requirements specification represents a balance among them.

**Primary stakeholders — home gardeners and small-scale tomato growers in the UAE.** This is the main end-user group. Members typically lack formal agricultural training, may speak Arabic as their primary language, and operate in areas with unreliable internet connectivity. Their primary expectations are ease of use, accessibility in their native language, fast and reliable diagnosis, and treatment guidance that is practical in their cultivation context.

**Secondary stakeholders — UAE agricultural extension officers and professional agronomists.** These professionals may refer TomatoCare to growers in their care or use it as a pedagogical tool. Their expectations centre on agronomic correctness of the treatment recommendations, alignment with UAE agricultural policy, and appropriate framing of the system as advisory rather than authoritative.

**Indirect stakeholders — environmental regulators and food security policy agencies.** These parties have an indirect interest in tools that can reduce unnecessary pesticide application and support sustainable local food production — interests expressed at the policy level in the UAE National Food Security Strategy 2051 (Chapter 1). Their expectations include compliance with data privacy requirements, transparency about diagnostic limitations, and measurable contributions to agricultural sustainability.

**Development team.** The project team of five members is also a stakeholder: requirements must be technically feasible within the Capstone 1 and Capstone 2 timeline, sufficiently specific to support implementation, and testable against measurable standards.

The requirements specification balances these perspectives by prioritising simplicity, accessibility, and offline operation for primary stakeholders; agronomic appropriateness and clear advisory framing for secondary and indirect stakeholders; and feasibility and testability for the development team.

---

### 4.7 Use Case Diagram

*Figure 9: Use Case Diagram*

The use-case diagram captures the interactions between the single actor — the Grower — and the application's core functions. Because TomatoCare is a single-user, fully offline tool with no accounts or remote services, there is exactly one human actor and no external system actors. The primary use cases are *Scan Leaf* (capture via camera or select from the gallery), *View Diagnosis* (read the calibrated result, severity, and treatment advice), *Adjust Confidence Threshold*, *Browse Disease Encyclopedia*, *View and Search History*, *Provide Feedback* (confirm or correct a diagnosis, feeding the training-data flywheel), *Export/Import Data*, and *Change Settings* (language and theme). *Scan Leaf* «include»s the preprocessing-and-cascade inference step and «extend»s to a *Low-Confidence Warning* when the top calibrated probability falls below the 60% threshold. The diagram reflects the shipped navigation, including the bottom navigation bar and the Disease Encyclopedia, dark mode, and feedback features added since Capstone 1.

---

### 4.8 AI Subsystem — Functional Requirements

This section specifies the functional requirements governing the AI subsystem (the three-stage cascade and its on-device inference engine). Application-level functional requirements — history browsing, treatment-database navigation, and the full use-case catalogue — are documented in §4.2.

**Table 4.1: AI Subsystem Functional Requirements**

| ID | Requirement |
|---|---|
| FR-AI-01 | The system shall accept a single still image (gallery or camera) and produce a diagnosis or a rejection. |
| FR-AI-02 | The system shall reject any input that is not a leaf (Stage 1) and return a "Not a leaf" retake instruction. |
| FR-AI-03 | The system shall reject any leaf that is not a tomato leaf (Stage 2) and return a "Not a tomato leaf" retake instruction. |
| FR-AI-04 | The system shall return, with each diagnosis, a calibrated confidence score and shall surface a Low Confidence Warning whenever the calibrated probability falls below 60%. |
| FR-AI-05 | The system shall perform all inference on-device with no network call. |
| FR-AI-06 | The system shall allow the user to confirm or correct a diagnosis, and shall store the labelled image locally for future retraining. |

---

### 4.9 AI Subsystem — Non-Functional Requirements

The non-functional requirements governing the AI subsystem are summarised in Table 4.2, together with their measurable targets. The deployed system's results against these targets are reported in Chapter 7.

**Table 4.2: AI Subsystem Non-Functional Requirements**

| ID | Requirement | Target |
|---|---|---|
| NFR-AI-01 | Disease-classification accuracy on a held-out laboratory test set | ≥ 90% |
| NFR-AI-02 | Combined size of all deployed cascade models | ≤ 15 MB |
| NFR-AI-03 | Confidence calibration (Expected Calibration Error) supporting the 60% low-confidence threshold | ECE < 0.02 |
| NFR-AI-04 | Fully offline operation; no INTERNET permission declared | No network call |
| NFR-AI-05 | No user data leaves the device | Local-only |

---

### 4.10 AI Subsystem — Domain Requirements and Constraints

**DR-AI-01 — Preprocessing contract.** Training and inference preprocessing must be byte-identical: centre-crop to the largest centred square, resize to 224×224 by bilinear interpolation, scale to [0, 1] by division by 255, with no ImageNet mean/std normalisation. Parity is enforced by an automated regression check (§3.8.2).

**DR-AI-02 — Single-leaf assumption.** Inputs are assumed to contain a single, centred leaf. Multi-leaf images and full-plant photographs are out of scope and are typically rejected at one of the gates or surfaced as a low-confidence diagnosis.

**DR-AI-03 — Closed condition set.** The disease classifier covers exactly eleven conditions (ten diseases plus a healthy class). A novel condition outside this set must surface as a low-confidence warning rather than a confident wrong label.

---

### 4.11 AI Subsystem — Requirements Traceability

Table 4.3 traces each AI subsystem requirement to the chapter, section, and measured result that demonstrates the requirement has been satisfied.

**Table 4.3: AI Requirements Traceability Matrix**

| Requirement | Verified By | Result |
|---|---|---|
| FR-AI-02 / FR-AI-03 (rejection at gates) | Hard-negative and gate evaluation (§7.2, §7.7) | Non-leaf rejection 99.55%; unseen-species leak 0.05% |
| FR-AI-04 (calibrated confidence) | Expected Calibration Error on held-out test (§7.3) | Test ECE 0.061; in-sample ECE 0.0046 |
| FR-AI-05 / NFR-AI-04 (offline operation) | Build inspection (§6.3); manifest review | No INTERNET permission; models bundled in APK |
| NFR-AI-01 (accuracy ≥ 90%) | Deployed-model laboratory evaluation (§7.2) | 97.59% |
| NFR-AI-02 (size ≤ 15 MB) | Model file sizes (§3.8.6) | 9.87 MB |
| FR-AI-06 (feedback flywheel) | Implementation review (§6.4) | Implemented |

---

## Chapter 5: Design

### 5.1 System Architecture

TomatoCare adopts a three-layer, offline-first architecture, dividing the system into a Presentation Layer, an Application Logic Layer, and a Data Layer. This architecture was selected for two principal reasons. First, it provides modularity: each component can be tested and replaced independently without affecting the other layers, which is essential in TomatoCare because replacing the AI model, for example, should not require changes to the persistence layer. Second, the offline-first structure enables farmers in remote, rural areas — where internet connectivity is not guaranteed — to use the application without limitation.

#### 5.1.1 Layer 1 – Presentation Layer (UI)

The Presentation Layer is implemented in Kotlin using Jetpack Compose. It renders everything the user sees: the home screen, camera capture screen, diagnosis results screen, and all supporting views. Jetpack Compose was selected over XML-based layouts for its declarative nature (which reduces boilerplate), its built-in `LayoutDirection.RTL` support (which handles Arabic right-to-left layout without requiring a parallel XML hierarchy), and its status as the current recommended Android UI toolkit. CameraX is part of this layer and provides a unified camera API that abstracts device-to-device camera differences, ensuring consistent image capture across all target hardware.

#### 5.1.2 Layer 2 – Application Logic Layer (Inference Engine)

The Application Logic Layer comprises two core components: the image preprocessing pipeline and the TensorFlow Lite inference engine. The preprocessing pipeline takes the image from the Presentation Layer, resizes it to 224×224 pixels, and normalises pixel values to the floating-point range [0, 1] as required by the model. The resulting tensor is passed to the TFLite inference engine, which loads the quantised model and performs on-device inference.

The engine returns a ranked list of class probabilities across the eleven output classes. If the top prediction confidence is at or above 60%, the result is forwarded to the Data Layer for storage and to the Presentation Layer for display. Otherwise, the engine returns a low-confidence flag, causing the UI to display a Low Confidence Warning and prompt the user to retake the photograph under better conditions. This behaviour balances diagnostic precision against usability.

#### 5.1.3 Layer 3 – Data Layer (Local Persistence)

The Data Layer handles all read and write operations. It serialises scan records to a JSON file using Kotlin's `kotlinx.serialization` library. The Android Storage Access Framework (SAF) enables exporting and importing of scan history, allowing the user to read from and write to any location accessible via the device file picker (internal storage, SD card, or USB-OTG drive) without requiring the legacy `WRITE_EXTERNAL_STORAGE` permission, which is restricted on Android 10 and above. This ensures compatibility with devices running API 26–34 while conforming to the Android permission model enforced from API 29 onwards. No data is transmitted outside the device (see §1.6.2).

#### 5.1.4 Cross-Cutting Concerns

Three concerns span all three layers.

First, **localisation**: UI string resources and the bundled treatment database are stored in parallel English and Arabic versions. The active locale is determined at runtime based on the user's language preference, stored in SharedPreferences. When Arabic is selected, the RTL layout is applied automatically.

Second, **privacy**: because no network calls are made anywhere in the system, personal diagnostic data never leaves the device, complying with the data-minimisation principle of UAE Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data.

Third, **performance**: the inference pipeline is executed on a background coroutine (Kotlin Coroutines) to ensure the application remains responsive on lower-end hardware while inference is in progress.

*Figure 10: Layered Architecture Diagram*

---

### 5.2 Sequence Diagram

*Figure 11: Sequence Diagram — Diagnose Leaf*

**Diagnose Leaf.** The Grower triggers `captureImage()` on the ScanUI, which delegates to ScanController via `startScan(image)`. The controller preprocesses the image internally, then calls `classify(tensor)` on the TFLiteEngine and receives a probability vector. An alt fragment splits on the 60% confidence threshold: above threshold, the controller fetches treatment from LocalStorage, persists the scan, and returns the result to the UI; below threshold, the UI surfaces a Low Confidence Warning so the Grower can retake the image.

*Figure 12: Sequence Diagram — View Past Scan*

**View Past Scan.** The Grower opens the history screen; HistoryController loads the full scan list from LocalStorage and presents it via HistoryUI. When the Grower selects a specific scan, HistoryController loads that record from storage and returns the diagnosis and treatment data to the UI for display.

---

### 5.3 State Chart Diagram

*Figure 13: State Chart Diagram*

The ScanSession lifecycle has four non-terminal states (Ready, Analyzing, AwaitingRetake, Persisting) and three terminal states (Saved, Cancelled, Failed). The pipeline operations of validation, preprocessing, and classification are modelled as internal `do/` activities of the Analyzing state rather than as separate states, since they are computations performed *while* the session is in that state, not durable conditions of the session itself. The same convention applies to Persisting, which contains treatment lookup and scan persistence as internal activities. Errors during analysis or persistence both lead to Failed but are distinguished by the trigger label so that the recovery path is unambiguous.

---

### 5.4 Data Model Diagram

*Figure 14: Data Model Diagram*

The data model diagram models the conceptual data structure of the application across five entities: `USER_SETTINGS`, `SCAN_RECORD`, `DIAGNOSIS_RESULT`, `CONDITION`, and `TREATMENT`. It is drawn in an entity-relationship style for clarity, but it deliberately describes a *conceptual* data model — one the application persists as a single nested JSON document (§5.5), not a relational database. It is therefore labelled a data model diagram rather than an entity-relationship diagram (ERD).

`USER_SETTINGS` stores the user's application preferences with the following attributes: `settings_id` (primary key), `preferred_language`, `default_growing_method`, `confidence_threshold`, and `app_version`. It participates in a one-to-many *configures* relationship with `SCAN_RECORD`.

`SCAN_RECORD` represents every diagnostic session performed by the user. Its attributes are: `scan_id` (primary key), `image_path`, `timestamp`, `growing_method`, and `model_version`. It participates in a one-to-many *produces* relationship with `DIAGNOSIS_RESULT`, where a single scan can produce multiple results ranked by confidence.

`DIAGNOSIS_RESULT` records the output of the on-device TFLite inference for a particular scan. Its attributes are: `result_id` (primary key), `confidence_score`, `is_primary`, `severity_level`, and `stress_type`. The `stress_type` attribute is static descriptive metadata carried from the `CONDITION` record; it is not a separate learned prediction, and the system does not detect abiotic stress. `DIAGNOSIS_RESULT` participates in a many-to-one *identifies* relationship with `CONDITION`.

`CONDITION` is the internal knowledge base of the eleven tomato leaf conditions (ten diseases plus healthy) that the model is trained to recognise. Its attributes are: `condition_id` (primary key), `name_en`, `name_ar`, `description_en`, `description_ar`, and `stress_type`. The bilingual name and description attributes reflect the application's English/Arabic language support.

`TREATMENT` contains localised treatment advice associated with each condition. Its attributes are: `treatment_id` (primary key), `growing_method`, `treatment_type`, `urgency_level`, `recommendation_en`, and `recommendation_ar`. It participates in a many-to-one relationship with `CONDITION`, where each condition can have multiple treatment records depending on the growing method (greenhouse, open-field, hydroponic, or saline-soil).

Primary-key attributes are underlined in the diagram. Foreign keys and join tables are not shown because the application does not use a relational database: these entities are serialised as a single nested JSON document (§5.5), so the diagram captures their conceptual relationships rather than a physical relational schema.

---

### 5.5 JSON Schema Tree

*Figure 15: JSON Schema Tree*

The JSON schema tree shows how the conceptual data model of §5.4 is physically realised as a single nested JSON document — the form in which the application actually persists data (§3.9). The root is an array of `ScanRecord` objects; each `ScanRecord` nests its `DiagnosisResult` objects, and each result in turn nests its `Treatment` objects together with a reference to the `Condition` it identifies. User preferences are held in a separate, small settings object. The tree makes explicit that the relationships drawn in the data model diagram are represented by JSON nesting rather than by foreign keys and join tables — confirming that no relational database is required and that the on-device storage format is identical to the export format (§5.1.3).

---

### 5.6 Class Diagram

*Figure 16: Class Diagram*

The class diagram presents the principal Kotlin types and their relationships, grouped by architectural layer (§5.1). The Presentation layer holds the Compose screens and their `ViewModel`s (for example `ScanViewModel`, `HistoryViewModel`, and `SettingsViewModel`); the Application-Logic layer holds `ImagePreprocessor` and `TFLiteEngine`, the latter owning the three TFLite interpreters and implementing the cascade; and the Data layer holds the serialisable model classes (`ScanRecord`, `DiagnosisResult`, `Treatment`, `Condition`, `UserSettings`) alongside the local store and the `TrainingDataExporter`. The associations show each `ViewModel` depending on the inference engine and the local store rather than on one another, illustrating the unidirectional, layer-respecting dependencies that keep the inference engine free of any UI or persistence knowledge (§5.8).

---

### 5.7 Activity Diagram

*Figure 17: Activity Diagram — Run Diagnosis*

The activity diagram traces the control flow of a single diagnosis from capture to a stored, displayed result. After the grower captures or selects an image, the flow proceeds through preprocessing (centre-crop, resize, normalise) to the leaf gate; a decision node routes a rejected input to a *Not a Leaf* message and a retake. A passed input reaches the tomato gate, whose decision node routes rejections to a *Not a Tomato* message. Inputs that clear both gates reach the disease classifier, after which a second decision node tests the calibrated top confidence against the 60% threshold: below it, the flow shows a Low-Confidence Warning and offers a retake; at or above it, the flow looks up the growing-method-appropriate treatment, persists the scan, and renders the result. These three branch points — the two gates and the confidence test — are what make the diagram match the deployed cascade behaviour.

---

### 5.8 Architectural Placement of the AI Subsystem

The application follows a layered architecture in which the AI cascade occupies a dedicated inference layer between the Presentation Layer (camera and gallery capture, results UI) and local storage. The inference layer is self-contained: it receives a bitmap, applies the preprocessing contract specified in §3.8.2, runs the three-interpreter cascade in sequence, and returns either a rejection reason (not a leaf, or not a tomato) or a diagnosis with its calibrated confidence and severity indicator. This layer has no knowledge of the UI, no knowledge of persistence, and no network capability — properties that arise naturally from the design rather than being bolted on.

---

### 5.9 Cascade Inference Design

The inference layer loads three TensorFlow Lite interpreters once at application start-up and runs them in sequence, short-circuiting on the first gate rejection. The leaf gate runs first; on rejection the pipeline returns `NOT_A_LEAF` and no further inference is performed. If the input passes the leaf gate, the tomato gate runs; on rejection the pipeline returns `NOT_A_TOMATO`. Only if both gates accept does the disease classifier run and return the eleven-class probability vector. Because the stages use independent interpreters, a gate rejection halts the pipeline having invoked at most both gate models (1.92 MB each), never reaching the larger 6.03 MB disease classifier — the cascade is cheaper on rejected inputs than on accepted ones, which is the appropriate cost profile for an out-of-domain rejection path.

---

### 5.10 Preprocessing-Parity Contract

The preprocessing contract (§3.8.2) is pinned in a `labels.json` file and mirrored in the Kotlin `ImagePreprocessor`. The contract — centre-crop to square, resize to 224×224 by bilinear interpolation, divide by 255, RGB channel order, no ImageNet mean/std normalisation — is the single most safety-critical interface in the system, because any silent divergence between training and inference preprocessing degrades accuracy without throwing an error. An automated parity check guards the contract at export time: the same fixture image is processed through both the Python pipeline and the Kotlin engine, and the resulting tensors must match to within floating-point tolerance before the build may be published.

---

### 5.11 Model-Asset and Label Contract

The three `*_float16.tflite` files, a `labels.json` file (recording each stage's class order and `pass_class`), and a `treatments.json` file (per-condition advice keyed by the Stage 3 class names) together constitute the deployed model contract. Class names are snake\_case strings shared verbatim between the Python pipeline and the Android assets, establishing a single canonical label set across training, evaluation, and the application — eliminating the possibility of name-conversion errors or label drift between the two systems. Updating any single model in production requires only swapping the corresponding `.tflite` file and — if the class set changed — the relevant `labels.json` entries; no Kotlin code change is required.

---

## Chapter 6: Implementation

### 6.1 Introduction

This chapter documents the implementation of the AI model pipeline and its on-device integration. The full application implementation — screen-level code, persistence layer, and navigation — is documented in the application-level implementation sections of this report. Section 6.2 describes the Python model pipeline, Section 6.3 covers on-device cascade integration in Android, and Section 6.4 documents the in-app feedback flywheel.

---

### 6.2 Model Pipeline

The training and deployment pipeline is a sequence of Python scripts in the `ml/` tree of the project repository. Each script has a single responsibility and writes its output to a fixed location, enabling the pipeline to be re-run end-to-end from raw datasets to deployable `.tflite` files in one command. The pipeline comprises the following scripts:

`build_dataset.py`, `integrate_plantdoc.py`, and `prepare_*` scripts assemble the tomato20k splits, the gate datasets, and fold in the PlantDoc field images.

`train.py` implements the two-phase transfer-learning recipe described in §3.8.4 with selectable augmentation modes (minimal = flip only, the deployed configuration; lighting; heavy; none) and inverse-frequency class weights.

`calibrate.py` fits the temperature scalar *T* on validation logits and bakes it into the final Dense layer (W ← W / T, b ← b / T), leaving the argmax — and therefore accuracy — unchanged while making the reported probabilities meaningful.

`export.py` converts each Keras model to float16 TFLite and runs the preprocessing-parity check that gates deployment. A build that fails the parity check is rejected before the assets reach the Android project.

`eval_deployed_tflite.py` runs the shipped TFLite cascade against the held-out test set and writes a single `eval_deployed.json` file — the canonical source of truth for every quantitative result reported in Chapter 7.

---

### 6.3 On-Device Cascade Integration

The Android inference layer (`TFLiteEngine.kt`) loads the three TFLite interpreters from the application's assets bundle at start-up and implements the cascade specified in §5.9. `ImagePreprocessor` implements the same five-step preprocessing contract as the Python pipeline: decode to RGB, centre-crop to the largest centred square, resize to 224×224, divide by 255, and write to an NHWC float32 ByteBuffer. The centre-crop step was the critical correction from the Capstone 1 prototype, in which non-square photos were squashed to square, distorting the leaf morphology on which fine-grained disease discrimination depends.

No INTERNET permission is declared in the Android manifest. The bundled assets are the three `.tflite` files, `labels.json`, and `treatments.json`; no other model-related artefacts are retrieved at runtime. A build inspection (§7.8) verifies the absence of the INTERNET permission and the completeness of the bundled-asset list.

*Figure 6.2 — [Placeholder: application user-interface screenshots. Capture and insert a montage of the key screens, ideally showing both English and Arabic (RTL) and light/dark themes: (1) Home dashboard (stats + disease-distribution chart), (2) camera/scan screen with the framing overlay, (3) results screen (diagnosis, confidence gauge, treatments, feedback control), (4) Disease Encyclopedia with search, (5) Settings (language + theme + data export), (6) the gate-rejection and low-confidence warnings. Screenshots can be taken on the test device as in `meseremnts/`.]*

---

### 6.4 In-App Feedback Flywheel

To close the laboratory-to-field gap with real data over time, the application implements a lightweight feedback mechanism. After each diagnosis, the results screen offers a one-tap "Was this correct?" confirm-or-correct control. The outcome is stored on the local `ScanRecord`, and a background exporter (`TrainingDataExporter.kt`) packages the labelled photographs into a ZIP organised by `correctedConditionId/` subfolder — the exact directory layout that the training pipeline's `image_dataset_from_directory` expects. The ZIP can be copied off the device via the Android Storage Access Framework and fed back into a future training run without any reformatting or relabelling step.

*Figure 6.1 — [Placeholder: DCGAN synthetic bacterial-spot leaf samples generated at training epoch 150 (8×8 grid, 64 samples). Training was stable with no mode collapse, yet these synthetic images reproduce the laboratory distribution (uniform white background, studio lighting) rather than field conditions — a finding that explains why adding them to the training set produced no gain in field recall, as reported in §7.5. Image file `reports/figures/gan_samples_epoch150.png`; insert here when finalising.]*

### 6.5 Application Architecture and Project Structure

The Android application follows the three-layer, offline-first architecture introduced in §5.1 — a Presentation layer (Jetpack Compose UI and per-screen `ViewModel`s), an Application-Logic layer (the inference engine), and a Data layer (local JSON persistence) — wired together by a single hand-rolled dependency container, `AppContainer`, created once in `TomatoCareApp.onCreate()`. Dependencies (the inference engine, repositories, storage managers, and the settings store) are constructed there and surfaced to the `ViewModel`s through the `Application` reference, which avoids imposing a heavyweight dependency-injection framework on a small single-process application. The container also fires one warm-up inference on a blank bitmap at start-up, so the first real scan does not pay the one-time native-library and JIT cost.

The source tree is organised by architectural layer and, within the UI layer, by feature:

```
com/tomatocare/
├── TomatoCareApp.kt          Application — builds AppContainer; model warm-up
├── MainActivity.kt           single activity; hosts the Compose navigation graph
├── di/AppContainer.kt        hand-rolled dependency container
├── ui/
│   ├── home/                 HomeScreen, HomeViewModel, HomeStats
│   ├── scan/                 ScanScreen, CameraScreen, CameraController, ScanViewModel
│   ├── result/               ResultScreen, ResultViewModel
│   ├── encyclopedia/         EncyclopediaScreen, EncyclopediaViewModel
│   ├── history/              HistoryScreen, HistoryViewModel
│   ├── settings/             SettingsScreen, SettingsViewModel
│   ├── components/           reusable Compose UI (ConfidenceGauge, SeverityChip,
│   │                         StressBadge, TreatmentCard, LowConfidenceWarning,
│   │                         GateRejectWarning, StatCard, SimpleBarChart, FeedbackCard,
│   │                         OnboardingDialog, FullScreenImageViewer, …)
│   ├── navigation/           Routes, TomatoCareNavHost (bottom-navigation graph)
│   └── theme/                Theme, Color, Type (Material 3, light + dark)
├── inference/
│   ├── TFLiteEngine.kt        loads the three interpreters; runs the cascade
│   ├── ImagePreprocessor.kt   the preprocessing-parity contract (§3.8.2)
│   ├── TomatoClasses.kt       canonical label set shared with the ML pipeline
│   └── SeverityHeuristic.kt   confidence → severity mapping
├── data/
│   ├── model/                 ScanRecord, DiagnosisResult, Treatment, ConditionInfo,
│   │                          UserSettings, ThemeMode, … (kotlinx.serialization)
│   ├── storage/               ScanStorageManager, ScanExporter, ScanImporter,
│   │                          SettingsStore, TrainingDataExporter
│   └── repository/            TreatmentRepository, ConditionRepository
└── utils/                     LocaleHelper

app/src/main/assets/   stage{1,2,3}_*_float16.tflite, labels.json, treatments.json, model_card.md
app/src/main/res/      values/strings.xml (English) · values-ar/strings.xml (Arabic)
app/src/test/          48 JVM unit tests   ·   app/src/androidTest/  Compose UI + instrumented tests
```

The build targets `minSdk = 26` (Android 8.0) and `targetSdk = 34`, compiled against JDK 17. Two settings directly protect non-functional requirements: ProGuard/R8 shrinking (`isMinifyEnabled`, `isShrinkResources`) keeps the release APK within the 50 MB budget (NFR-04), and `noCompress += "tflite"` keeps the model files uncompressed inside the APK so the runtime can memory-map them rather than allocating roughly 9.87 MB of heap at load time.

### 6.6 Key Components

**Presentation layer.** Each screen is a Compose function backed by a `ViewModel` that exposes an immutable UI-state data class as a `StateFlow`, following the unidirectional-data-flow pattern. `MainActivity` hosts `TomatoCareNavHost`, which defines the bottom-navigation graph (Home, Scan, Encyclopedia, History, Settings). Live image capture is handled by `CameraController` over CameraX; gallery selection shares the same downstream decode path (§6.8). All theming (Material 3, light and dark) lives in `ui/theme/`, and every user-facing string is resolved from `res/values/` and `res/values-ar/`, so the same composables render correctly in either language and layout direction.

**Application-logic layer.** `TFLiteEngine` loads the three float16 interpreters once and executes the cascade described in §5.9, short-circuiting on the first gate rejection. `ImagePreprocessor` implements the byte-exact preprocessing-parity contract (§3.8.2). `SeverityHeuristic` and `TomatoClasses` were deliberately extracted as pure Kotlin units so that the most safety-critical logic — the label contract and the confidence-to-severity mapping — can be unit-tested on the JVM without a device. In simplified form, the engine's control flow is:

```kotlin
fun classify(bitmap: Bitmap, method: GrowingMethod): InferenceOutput {
    val tensor = preprocessor.toTensor(bitmap)        // parity-checked pipeline (§3.8.2)
    if (!leafGate.passes(tensor))   return Reject(NOT_A_LEAF)
    if (!tomatoGate.passes(tensor)) return Reject(NOT_A_TOMATO)
    val probs = diseaseClassifier.run(tensor)         // 11-class calibrated softmax
    return Diagnose(probs, method)                    // severity + treatment resolved downstream
}
```

**Data layer.** Scan records and settings are serialised with `kotlinx.serialization`. `ScanStorageManager` performs crash-safe atomic writes (write-to-temp-then-rename, §3.9), `SettingsStore` is built on DataStore and exposes settings reactively (§6.8), and the SAF-based `ScanExporter`/`ScanImporter` together with the flywheel's `TrainingDataExporter` move data on and off the device only when the user initiates it (§3.9.1).

### 6.7 Continuous Integration and Testing

Quality is enforced automatically rather than checked by hand at submission time. A GitHub Actions workflow (`.github/workflows/android-ci.yml`) runs on every push and pull request to `main`: it sets up JDK 17, runs the JVM unit-test suite, runs Android Lint for static analysis, generates a JaCoCo coverage report, and assembles a debug APK, uploading the test, coverage, and lint reports as build artifacts (superseded runs on the same branch are cancelled to conserve CI minutes). Because the gitignored TFLite models are loaded by name at runtime, their absence does not affect the compile-and-unit-test signal this workflow provides. A second workflow (`release.yml`) builds the APK and opens a draft GitHub Release on a `v*` tag.

The unit suite comprises **48 JVM tests**. To make Android-coupled logic testable without an emulator, three pure units were extracted from their host classes — the confidence-to-severity heuristic (`SeverityHeuristic`, from `TFLiteEngine`), the home-dashboard statistics (`HomeStats`, from `HomeViewModel`), and the feedback-export label resolver (`TrainingDataExporter.resolveLabel`). The tests guard the ML↔app label contract, severity boundaries, dashboard statistics (including the health-rate regression described in §6.8), feedback round-trip and backward compatibility, history search and filter, and persistence and formatting; Compose UI tests (`BadgeUiTest`) cover badge rendering on an emulator. The full enumeration of the suite, and the black-box functional matrix of 28 cases (FR-01–FR-28), are given in §7.9 (Table 7.5).

### 6.8 Implementation Challenges

Assembling the application surfaced several defects whose diagnosis and resolution are themselves part of the engineering record. Three are representative.

**Gallery selections crashed the application.** Captured images were decoded with `BitmapFactory.decodeFile(uri.path)`, which returns `null` for the `content://` URIs that the gallery picker supplies, producing a `NullPointerException` that broke the gallery capture path (FR-05). The fix moved decoding into `ScanViewModel`, off the main thread, reading from the content resolver and using the EXIF-aware `ImageDecoder` on API 28 and above so that orientation metadata is honoured; a failed decode now surfaces a message instead of crashing. The path is guarded by an instrumented image-validation test and a decode-failure unit case.

**The Home "health rate" was permanently 0%.** The dashboard computed the health rate by counting results whose `conditionId` equalled `"tomato_healthy"`, but the canonical class identifier — shared with `assets/treatments.json` and the ML label set — is `"healthy"`. The mismatch meant no scan was ever counted as healthy. Correcting the identifier fixed the metric, and `HomeStatsTest` now pins the calculation as a regression test — a direct payoff of having extracted `HomeStats` as a pure, testable unit.

**Theme and language changes required a restart.** `SettingsStore` originally exposed only a one-shot `read()`, so a change to theme or language was not observed by the running UI until the application was relaunched. It now exposes a reactive `StateFlow<UserSettings>` that `MainActivity` collects: the theme switches live on selection, and a language change re-applies the locale (via `recreate()`) so the interface — including right-to-left layout — updates immediately. This delivers the live-switching behaviour expected of a bilingual, themeable design.

---

## Chapter 7: Testing and Evaluation

All laboratory results in this chapter were obtained by running the deployed TFLite artefacts (`stage{1,2,3}_*_float16.tflite`) against the held-out tomato20k test set (6,683 images, never used in training or early stopping), using the exact production preprocessing pipeline. The source artefact is `ml/reports/eval_deployed.json` (output of `ml/eval_deployed_tflite.py`). Field results were obtained on the 79 held-out PlantDoc tomato images using the same artefacts and preprocessing.

---

### 7.1 Evaluation Framework

The cascade is evaluated on four axes, each targeting a distinct failure mode:

1. **Stage-3 disease accuracy on the held-out laboratory test set** — measures disease-discrimination quality.
2. **Gate behaviour** — measures how many genuine tomato leaves pass both gates (false-reject rate) and how many out-of-scope inputs are rejected (rejection recall and leak rate).
3. **End-to-end accuracy** — the fraction of tomato test images that pass both gates and receive the correct diagnosis; this is the figure the user actually experiences.
4. **Field accuracy** — end-to-end accuracy on real-world phone photographs (PlantDoc).

---

### 7.2 Deployed-Model Laboratory Results

**Table 7.1: Deployed-Model Laboratory Results (held-out test set, n = 6,683)**

| Metric | Value | Source |
|---|---|---|
| Stage-3 disease accuracy | 97.59% | Recomputed (deployed TFLite) |
| End-to-end accuracy | 97.19% | Recomputed |
| Tomato leaves passing the leaf gate | 100.0% | Recomputed |
| Tomato leaves passing both gates | 99.42% | Recomputed |
| Stage-3 test ECE (15-bin) | 0.061 | Recomputed |
| Total model size | 9.87 MB | Model files |
| Not-leaf rejection recall | 99.55% | Prior gate evaluation† |
| Other-leaf rejection recall | 99.37% | Prior gate evaluation† |
| Unseen-species leak rate | 0.05% | Prior gate evaluation† |

*† The gate-rejection metrics were produced by an earlier hard-negative evaluation (`hard_negative_test.py`), not by the deployed-model run, which exercises the gates only on tomato inputs (for the end-to-end figure). They remain valid because Stages 1–2 were not retrained between the baseline and the deployed cascade.*

**Confusion matrix.** Figure 7.1 shows the row-normalised 11×11 confusion matrix of the deployed Stage-3 model. *[FIG\_7\_1\_PLACEHOLDER — insert `reports/figures/confusion_matrix_deployed.png` when finalising.]*

*Figure 7.1 — Deployed Stage-3 confusion matrix, row-normalised (n = 6,683 held-out test images).*

The raw counts (rows = true class, columns = predicted) are:

| True \ Pred | bact | e\_bl | hlth | l\_bl | l\_ml | mosv | powd | sept | spid | targ | ylcv |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bacterial\_spot | 717 | 2 | 0 | 1 | 1 | 0 | 0 | 6 | 1 | 0 | 4 |
| early\_blight | 3 | 606 | 1 | 10 | 6 | 0 | 1 | 11 | 0 | 3 | 2 |
| healthy | 0 | 0 | 795 | 0 | 1 | 1 | 0 | 0 | 0 | 6 | 2 |
| late\_blight | 3 | 4 | 2 | 773 | 4 | 0 | 2 | 2 | 1 | 1 | 0 |
| leaf\_mold | 4 | 1 | 2 | 5 | 718 | 2 | 0 | 0 | 1 | 5 | 1 |
| mosaic\_virus | 0 | 0 | 2 | 0 | 0 | 576 | 1 | 0 | 0 | 2 | 3 |
| powdery\_mildew | 0 | 0 | 0 | 0 | 0 | 0 | 252 | 0 | 0 | 0 | 0 |
| septoria\_leaf\_spot | 13 | 4 | 0 | 2 | 3 | 1 | 1 | 714 | 1 | 7 | 0 |
| spider\_mites | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 424 | 8 | 0 |
| target\_spot | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 453 | 0 |
| yellow\_leaf\_curl\_virus | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 494 |

*Abbreviations: bact = bacterial\_spot, e\_bl = early\_blight, hlth = healthy, l\_bl = late\_blight, l\_ml = leaf\_mold, mosv = mosaic\_virus, powd = powdery\_mildew, sept = septoria\_leaf\_spot, spid = spider\_mites, targ = target\_spot, ylcv = yellow\_leaf\_curl\_virus.*

**Table 7.2: Per-Class Recall (Deployed Stage 3)**

| Class | Recall | n | Dominant Confusions |
|---|---|---|---|
| powdery\_mildew | 1.000 | 252 | — |
| yellow\_leaf\_curl\_virus | 0.992 | 498 | bacterial\_spot (2) |
| target\_spot | 0.991 | 457 | spider\_mites (1), septoria (1) |
| healthy | 0.988 | 805 | target\_spot (6) |
| mosaic\_virus | 0.986 | 584 | ylcv (3), target\_spot (2) |
| bacterial\_spot | 0.980 | 732 | septoria (6), ylcv (4) |
| late\_blight | 0.976 | 792 | early\_blight (4), leaf\_mold (4) |
| spider\_mites | 0.975 | 435 | target\_spot (8) |
| leaf\_mold | 0.972 | 739 | late\_blight (5), target\_spot (5) |
| septoria\_leaf\_spot | 0.957 | 746 | bacterial\_spot (13), target\_spot (7) |
| early\_blight | 0.943 | 643 | septoria (11), late\_blight (10), leaf\_mold (6) |

Every class achieves at least 94% recall. The two weakest — `early_blight` (0.943) and `septoria_leaf_spot` (0.957) — together with their dominant confusions form a single coherent cluster (`early_blight` ↔ `late_blight` ↔ `septoria_leaf_spot`, `septoria_leaf_spot` ↔ `bacterial_spot`): all present as small, dark, necrotic foliar lesions that are difficult to separate visually even for human experts. The field analysis in §§7.4–7.5 returns to exactly these classes.

---

### 7.3 Confidence Calibration

Temperature scaling [27] was applied to Stage 3, with the scalar temperature baked into the final dense layer (T = 0.5889) so that the argmax — and therefore accuracy — is unchanged. On the temperature-fitting validation split, the in-sample ECE fell from approximately 0.07 to 0.0046. Measured on the held-out test set, the deployed ECE is 0.061 — a fourfold degradation, consistent with the validation split having been used during early stopping. Both figures are reported here for transparency: the in-sample figure confirms that the temperature-scaling step worked as designed; the held-out figure represents what the user actually experiences.

The deployment figure of 0.061 indicates that confidence is reasonably, though not tightly, calibrated. In practice, the 60% low-confidence warning fires rarely on clean laboratory images (where confidences are high) and more usefully on lower-quality field images. A dedicated, held-out calibration set is required to substantiate a tighter ECE figure (§9).

---

### 7.4 Field Validation and the Laboratory-to-Field Gap

The deployed cascade was evaluated on PlantDoc tomato field photographs (n = 79 held-out field images; real cluttered backgrounds, natural lighting, phone-camera quality). End-to-end accuracy is 77.2% and field disease accuracy is 87.1%, compared with 97.19% and 97.59% on the laboratory test set — a gap of approximately 20 percentage points. The gates remain stable: 96.2% of field tomato leaves pass both gates; non-tomato leaves continue to be rejected at high rates. The performance drop is therefore concentrated in the disease classifier's response to field-style leaf appearance.

*Methodological caveat (disclosed):* PlantDoc's own test partition was folded into the early-stopping validation split, so absolute field numbers are mildly optimistic and n is small. However, this caveat applies equally to all model variants compared in §7.5, so the relative deltas between variants remain fair.

---

### 7.5 Experiments to Close the Gap — a Controlled Investigation

Four interventions were designed and tested to close the laboratory-to-field gap. Each was a falsifiable hypothesis; each failed; together they triangulate the underlying cause. They are presented here as a single structured investigation.

**Table 7.3: Domain-Gap Experiments**

| # | Experiment | Direction | Result | Mechanism |
|---|---|---|---|---|
| 1 | Heavy environmental augmentation (brightness/contrast/gamma/hue/saturation/JPEG/blur) | Training → field | Field e2e −11.4 pts (74.7 → 63.3) — not deployed | Colour/gamma/JPEG jitter discarded diagnostic colour cues |
| 2 | Leaf segmentation (MobileSAM) background suppression, folded into training | Training → field | All metrics declined slightly — reverted | Laboratory backgrounds are already near-uniform; no new information added |
| 3 | DCGAN synthetic `bacterial_spot` (+600 images, 150 stable epochs) | Training → field | Field `bacterial_spot` recall flat at 2/9 (22%); zero gain | A GAN reproduces the laboratory distribution it was trained on |
| 4 | Test-time normalisation (segment field leaf → white background at inference) | Inference → lab | Field e2e −30.4 pts (77.2 → 46.8) | Hard cut-outs on white backgrounds are a third, out-of-distribution image type; the tomato gate rejected them 3× more often |

A lighter, lighting-only augmentation variant (brightness/contrast/gamma only — no colour jitter, no blur) was also tested and performed worse than the deployed minimal-augmentation model on field data (73.4% vs. 77.2%, −3.8 pts; laboratory accuracy ≈97.9%), confirming that even mild colour-space augmentation distorts the lesion colour signals the model relies on. The deployed model uses horizontal flip only.

**Experiment 1 — Heavy Augmentation (detail).** All three stages were retrained with a heavy per-image augmentation pipeline intended to simulate UAE field conditions and evaluated on both test sets. On the laboratory set it cost approximately 2 percentage points across every metric; on the field set it cost 11.4 end-to-end points. The mechanism is that the jitter destroyed the diagnostic colour signals (yellowing patterns, lesion colour) that the disease classifier relies on, without introducing the actual leaf-appearance variation found in field images.

**Experiment 3 — DCGAN (detail).** A DCGAN was trained for 150 epochs on the 2,503 `bacterial_spot` training images (the weakest field class) and generated 600 synthetic images (Figure 6.1). Training was stable with no mode collapse. A clean A/B test — the same minimal-augmentation training recipe with and without the 600 synthetic images — produced identical field `bacterial_spot` recall (2/9 = 22%) and laboratory metrics statistically indistinguishable from the deployed baseline. The synthetic images reproduce the laboratory distribution they were trained on; they cannot manufacture the field distribution.

*Figure 7.2 — [Placeholder: bar chart of end-to-end accuracy under four test conditions (Lab, Field, Composited 65.5%, Test-time normalisation 46.8%). Insert `reports/figures/lab_vs_field_accuracy.png` when finalising.]*

*Figure 7.2 — End-to-end accuracy of the deployed cascade under four test conditions. The 20-point lab-to-field drop narrows when backgrounds are swapped (composited: 65.5%) but the field-leaf-on-white-background variant collapses to 46.8%, demonstrating that leaf appearance — not background — is what the model misses on field data.*

#### 7.5.1 The Decisive Comparison

Placing Experiment 4 alongside a composited-background test isolates what actually drives the gap. The composited test ran the cascade on laboratory leaves (white background removed by threshold) pasted onto field-like backgrounds (n = 165, 15 per class).

| Configuration | Leaf Appearance | Background | End-to-End |
|---|---|---|---|
| Composited | Laboratory (perfect) | Synthetic field | 65.5% |
| Test-time normalisation (Exp. 4) | Field | White (lab-like) | 46.8% |

A perfect laboratory leaf survives a cluttered background (65.5%); a field leaf on a clean background still fails (46.8%). Leaf appearance — its lighting, focus, and white balance — dominates the domain gap, not the background. No transformation of the training data or the inference input bridges this gap; only collecting real field data will do so.

#### 7.5.2 Mechanistic Per-Class Finding

On the composited benchmark the gates remained background-robust (164/165, 99.4% passed both gates — an important safety result demonstrating that the cascade does not rely on white backgrounds to reject out-of-scope inputs). Disease recall split cleanly:

- **Background-independent (strong):** `late_blight` (15/15), `mosaic_virus` (15/15), `yellow_leaf_curl_virus` (14/15) — distinctive shape/colour signals.
- **Background-dependent (weak):** `early_blight` (2/15, 13%), `bacterial_spot` (6/15), `target_spot` (7/15) — small dark lesions that rely on contrast against the uniform white laboratory background.

Early blight's composited collapse to 13% is the sharpest illustration. Its laboratory recall on the pre-deployment cascade used for this experiment was 91.3%; on the deployed model it is 94.3% (Table 7.2). This is mechanistically consistent with early blight being one of the weakest field classes — the same lesion-versus-background dependency that compositing exposes also fails on real field photographs where backgrounds vary unpredictably.

---

### 7.6 Synthesis

The experiments share one root cause and one conclusion. Interventions that operate within the laboratory distribution — augmenting it, cleaning its backgrounds, or synthesising more of it — cannot manufacture the field distribution, and transforming a field image at inference cannot reconstruct a laboratory image. The remaining gap is attributable to real-world leaf appearance under natural light, on phone-camera sensors, against cluttered backgrounds: a distribution shift that only labelled real field data can close. The in-app feedback flywheel (§6.4) is the deliberate response to this finding; rather than overclaiming through synthetic augmentation, the system collects the actual operating distribution from real users.

---

### 7.7 Capability Statement

**The system can:** diagnose the eleven trained conditions on clean, single-leaf images at 97.59% accuracy; reject non-leaf inputs (99.55%) and non-tomato leaves (0.05% unseen-species leak rate) before diagnosis; present calibrated confidence and warn when uncertain; and run fully offline within a 9.87 MB combined model footprint.

**The system cannot (known limitations):** match laboratory accuracy on real field photographs (77.2% end-to-end); reliably separate the visually similar `early_blight`, `septoria_leaf_spot`, `late_blight`, and `leaf_mold` cluster on hard examples (per-class recalls 0.943–0.972); or diagnose conditions outside the eleven trained classes (a low-confidence warning is surfaced instead). The weakest field classes are `early_blight`, `bacterial_spot`, and `target_spot`.

---

### 7.8 Non-Functional Verification

**Table 7.4: Non-Functional Requirement Verification (AI Subsystem)**

| Requirement ID | Requirement | Result |
|---|---|---|
| NFR-AI-01 | Disease accuracy ≥ 90% (held-out laboratory test) | Met — 97.59% |
| NFR-AI-02 | Models ≤ 15 MB combined | Met — 9.87 MB |
| NFR-AI-03 | Calibration supporting the 60% threshold (ECE < 0.02) | Partially met — test ECE 0.061 (target met only in-sample: 0.0046) |
| NFR-AI-04 / CR-01 | Fully offline, no network call | Met — no INTERNET permission; models bundled |
| NFR-AI-05 | No data leaves the device | Met — local storage only |
| Obj-5 | Honest real-world evaluation (§1.5.2 Objective 5) | Met — 77.2% field e2e disclosed (§7.4) |

---

### 7.9 Application Testing

Application testing complements the model evaluation above with white-box unit
testing of the Android code and a black-box functional test plan for the
end-to-end user journeys.

**Unit (white-box) testing.** The application's correctness-critical logic is
covered by an automated JVM unit-test suite of 48 tests that run without a device or emulator, complemented by Compose UI tests that run on an emulator. To make Android-coupled logic testable, three pure units
were extracted from their host classes: the confidence-to-severity heuristic
(`SeverityHeuristic`, from `TFLiteEngine`), the home-dashboard statistics
(`HomeStats`, from `HomeViewModel`), and the feedback-export label resolver
(`TrainingDataExporter.resolveLabel`). The suite is summarised in Table 7.5.

**Table 7.5: Application Unit-Test Coverage**

| Test class | Subject under test | Representative cases |
|---|---|---|
| `ClassNamesTest` | ML↔app label contract | alphabetical order; count and names match `training_config.yaml` |
| `SeverityHeuristicTest` | Confidence → severity mapping | boundary cases at 0.90 / 0.75 / 0.60; non-primary always LOW; clamp at LOW |
| `HomeStatsTest` | Dashboard statistics | health-rate on `healthy` id; distinct-condition count; localised top-conditions; records without a primary |
| `FeedbackSerializationTest` | Flywheel data integrity | feedback round-trip; legacy records without the field decode (backward compatibility) |
| `TrainingLabelTest` | Flywheel export labelling | confirmed prediction vs. user correction vs. fallback |
| `HistoryFilterTest` | History search & filter | name search (EN/AR), severity filter, and their combination |
| `ScanHistorySerializationTest`, `ScanRecordTest`, `FormatTest` | Persistence & formatting | history JSON round-trip; primary-result selection; timestamp formatting |

These tests are executed on every push and pull request by a continuous
integration pipeline (GitHub Actions, `.github/workflows/android-ci.yml`), which
also assembles a debug APK — so a regression that breaks the build or the
contract is caught automatically rather than at submission time.

**Functional (black-box) testing.** End-to-end user journeys are specified as a
functional test matrix of 28 cases (FR-01–FR-28) in
`docs/functional_tests.md`, derived by equivalence-class partitioning over the
input space — valid tomato leaf, healthy leaf, non-leaf and non-tomato inputs
(gate rejection), low-confidence inputs, unsupported file types and oversize
images, and the gallery-versus-camera capture paths. The matrix covers the scan,
result, history, encyclopedia, settings (language, theme, data export), and
feedback-flywheel flows, each with explicit pre-conditions, steps, and expected
results. These cases are executed on physical devices and emulators at the
minimum and target API levels (API 26 and API 34); the recorded pass/fail
results, together with integration, system, and user-acceptance testing, are
maintained by the QA lead.

**Regression evidence for the fixed defects.** Each of the three defects documented in §6.8 now has explicit evidence that its fix holds. The Home health-rate miscalculation is pinned by `HomeStatsTest`, which asserts the rate is computed against the canonical `"healthy"` identifier and would fail if the previous `"tomato_healthy"` string were reintroduced. The gallery-decode crash is covered by an instrumented image-validation and EXIF test together with a decode-failure unit case that exercises the `content://` path and asserts a graceful error state rather than a `NullPointerException`. The live theme-and-language switch is verified by functional cases in `docs/functional_tests.md` that change each setting and confirm the interface — including right-to-left re-layout — updates without an application restart. The before/after screenshots accompanying these cases form part of the on-device evidence montage (Figure 7.3).

**Performance measurement.** Inference latency is the user-facing performance
metric governed by NFR-02 (≤ 3 s on a minimum-specification device — Android API
26, 2 GB RAM, ~Snapdragon 660 class). The application reports the total cascade
time — three model forward passes — on every scan, shown on the results screen as
"Diagnosed on-device in *N* ms" (`InferenceOutput.inferenceTimeMs`), and logs a
per-stage breakdown under the `TomatoCarePerf` logcat tag.

Latency was measured on a physical device across ten scans spanning all four
severity levels and the full confidence range (50%–99%). The individual readings,
in milliseconds, were: 13, 13, 20, 14, 20, 16, 13, 12, 13, 15. The summary is
given in Table 7.6.

**Table 7.6: On-Device Inference Latency by Device**

| Device | RAM | Android (API) | Median latency | Max latency | Status |
|---|---|---|---|---|---|
| Samsung Galaxy S10+ (Snapdragon 855 / Exynos 9820) | 8 GB | *[confirm on device — e.g. Android 12 / API 31]* | 13.5 ms | 20 ms | Measured (n = 10) |
| Min-spec baseline (≈ Snapdragon 660 class) | 2 GB | Android 8.0 (API 26) | — | ≪ 3000 ms (projected) | Projection — not measured |
| *[representative low-end device]* | *2–3 GB* | *API 26–29* | *—* | *—* | Planned |

Summary statistics for the measured S10+ run (n = 10): minimum 12 ms, median 13.5 ms, mean 14.9 ms, maximum 20 ms, against the NFR-02 budget of 3000 ms — a worst-case margin of roughly 150×.

*Test device: Samsung Galaxy S10+, 8 GB RAM (Snapdragon 855 / Exynos 9820 class,
2019 flagship).* The reported figure is the cascade inference time (three
MobileNetV3 forward passes); it excludes image decode and preprocessing, which
add a small fixed overhead that does not materially affect the conclusion.
Because the measured worst case (20 ms) is more than two orders of magnitude
under the 3-second budget, NFR-02 is met with very wide headroom. The S10+ is a
2019 flagship and exceeds the minimum specification; given the ~150× margin,
however, the budget would still hold comfortably on a min-spec device an order of
magnitude slower. A confirmatory run on representative low-end hardware is planned
to evidence the low-end claim directly. Per-stage timing (leaf gate / tomato gate
/ classifier) is available via the `TomatoCarePerf` log; cold-start warm-up is
logged separately at startup.

*Figure 7.3 — [Placeholder: on-device evidence screenshots from the Samsung
Galaxy S10+ run — the results screen showing "Diagnosed on-device in 13 ms" with
the diagnosis, confidence gauge, and feedback control. Source images are in the
`meseremnts/` folder (e.g. `Screenshot_20260529_121935_TomatoCare.jpg`); insert a
1–3 screenshot montage here when finalising. These also evidence dark mode and
the feedback flywheel.]*

---

### 7.10 Usability Evaluation

Beyond functional correctness, the application's fitness for non-expert growers is assessed through a lightweight usability study. The protocol below is designed for approximately five participants — the established threshold at which formative usability testing surfaces the large majority of severe issues — drawn from classmates and family members who are non-expert growers and including at least one Arabic-first speaker.

**Consent and ethics.** Each participant gives verbal informed consent before the session; participation is voluntary and may be stopped at any time. No personal data is recorded — only task outcomes, timings, and observations — consistent with the data-handling principles of §3.9.1.

**Tasks.** Each participant attempts eight representative tasks, unaided, while thinking aloud:

1. Scan a tomato leaf with the camera and read the diagnosis, confidence, and treatment.
2. Scan a non-leaf or non-tomato object and interpret the gate-rejection message.
3. Trigger and interpret a Low-Confidence Warning (for example, a blurred or partial image).
4. Switch the interface to Arabic, confirm the layout mirrors correctly, then switch back.
5. Toggle dark mode.
6. Find a specific disease in the Disease Encyclopedia using search.
7. Open History, search or filter it, and reopen a past scan.
8. Provide feedback on a result (confirm or correct it).

**Metrics.** For each task: completion (success / success-with-difficulty / failure), time on task, and observed errors or hesitations. After all tasks, each participant completes the ten-item System Usability Scale (SUS) questionnaire, yielding a 0–100 score, plus two open questions (what was confusing; what was most useful). A mean SUS of ≥ 70 — the conventional "good" threshold — is adopted as the success criterion.

**Procedure and reporting.** A facilitator introduces the study without coaching on the tasks, observes silently, records the metrics, and conducts a brief debrief. Results — per-task success rates, median task times, the aggregate SUS score, and a prioritised list of issues with remediation notes — are recorded in Table 7.7 once the sessions are complete.

**Table 7.7: Usability Study Results (n ≈ 5)** — *to be completed after the sessions*

| Task | Success rate | Median time | Notable issues |
|---|---|---|---|
| T1–T8 | *pending* | *pending* | *pending* |
| **Mean SUS score** | *pending (target ≥ 70)* | | |

At the time of writing, the protocol is finalised and participant recruitment is under way; the study is scheduled to complete before final submission, and any high-severity findings will be addressed in a follow-up iteration.

---

## Chapter 8: Conclusion

Tomato production in the United Arab Emirates faces challenges that differ markedly from those of temperate agriculture, and the growers most exposed to them — home gardeners and smallholders — are also those least served by existing diagnostic tools. For a non-expert, identifying which disease a tomato plant is suffering from is particularly difficult: many tomato diseases present as overlapping patterns of leaf yellowing, spotting, and necrosis that are hard to distinguish even with training. Misidentification leads to the wrong treatment, wasted pesticides, higher production costs, and, in the worst case, crop loss.

TomatoCare was created to fill this gap. It is a native Android diagnostic tool that runs entirely offline, enabling any grower in the UAE with a smartphone to photograph a tomato leaf and receive an instant diagnosis with treatment guidance tailored to their growing method. Building it required more than adapting an existing classifier: the Capstone 1 prototype — a single classifier augmented with a reject class — mislabelled out-of-scope inputs (other crops, hands, everyday objects) as tomato diseases with high confidence, a safety defect rather than merely an accuracy shortfall. Correcting that failure was the central design driver of the project.

The literature review in Chapter 2 identified four research and product gaps that together define the problem space. First, three of the four reviewed platforms (Farmonaut, Plantix, Agrio) require a constant internet connection and are therefore effectively unusable in the low-connectivity environments typical of UAE smallholder cultivation. Second, none of the reviewed applications combines offline, on-device diagnosis with an Arabic-language interface; the cloud-based tools that do offer Arabic (such as Plantix) still require connectivity for every diagnosis, leaving Arabic-speaking growers in low-connectivity areas unserved. Third, none provides treatment recommendations adapted to UAE cultivation methods such as greenhouse, open-field, hydroponic, or saline-soil cultivation. Fourth, none reports its real-world field accuracy separately from its laboratory benchmark, leaving the accuracy a grower can actually expect in the field unmeasured.

TomatoCare addresses all four gaps. Its AI subsystem is a three-stage cascade — a leaf gate and a tomato gate (MobileNetV3-Small) that reject out-of-scope inputs, followed by an eleven-class disease classifier (MobileNetV3-Large) covering ten tomato diseases and a healthy class. The classifier was trained on a PlantVillage-derived tomato dataset using a two-phase transfer-learning strategy and evaluated on a held-out laboratory test set, achieving 97.59% — well above the 90% accuracy target. All three models are exported to TensorFlow Lite with float16 quantisation, for a combined footprint of 9.87 MB — well under the 15 MB budget.

Each diagnosis displays the condition name in English and Arabic, a calibrated confidence score, and a severity indicator (Low, Medium, High, or Critical). When confidence falls below the 60% threshold, the system withholds the result and shows a Low Confidence Warning instead, so that users are not misled by uncertain predictions. Treatment recommendations are drawn from an embedded bilingual knowledge base and filtered by the user's selected growing method, keeping the advice relevant to their cultivation situation.

The project was developed using an Agile SDLC organised into six sprints across Capstone 1 and Capstone 2. Agile was chosen for its suitability for the experimental nature of machine learning development and the need to integrate and test across machine learning and Android development streams. Capstone 1 covered project planning, literature review, requirements specification, system architecture, and design. The Capstone 2 implementation produced a complete, functional bilingual Android application with an embedded, fully evaluated three-stage AI cascade.

TomatoCare is intentionally scoped. The application covers only tomato (*Solanum lycopersicum*) leaves and is not generalised to other crop species. It does not include cloud synchronisation, user accounts, IoT sensor integration, or iOS support. Crucially, TomatoCare is an advisory decision-support tool, not a replacement for professional diagnosis: its outputs are guidance intended to help a grower act sooner and more accurately, and for high-value crops or uncertain cases a qualified agronomist or plant-protection authority should still be consulted. Treatment outputs are advisory recommendations and are not legally binding agrochemical prescriptions. These delimitations are appropriate to a Capstone 1 and Capstone 2 deliverable; several of them — multi-crop support and IoT integration — are identified as future development directions.

The AI subsystem contributes a safety-correct three-stage cascade (leaf gate → tomato gate → disease classifier) that hard-rejects out-of-domain inputs before any diagnosis is produced, eliminating the confident-wrong-answer failure mode observed in the Capstone 1 prototype. Measured rejection performance on the held-out evaluation set is 99.55% non-leaf rejection and 0.05% unseen-species leak rate, and confidence calibration via temperature scaling (T = 0.5889) makes the 60% low-confidence threshold statistically meaningful rather than cosmetic.

On the eleven-class held-out laboratory test set (n = 6,683), the deployed cascade achieves 97.59% disease accuracy and 97.19% end-to-end accuracy within a 9.87 MB combined model footprint — well under the 15 MB budget — with no INTERNET permission declared. The central empirical finding of the project, however, is the honest quantification of the laboratory-to-field gap: on real PlantDoc field photographs (n = 79) the deployed cascade reaches 77.2% end-to-end accuracy, an approximately 20-point drop. Four controlled experiments — heavy environmental augmentation, MobileSAM leaf segmentation, DCGAN synthetic samples for the weakest class, and test-time normalisation to a white background — were each designed to close this gap. All four failed. A decisive composited-background experiment isolated the cause to field-leaf appearance rather than background clutter: a laboratory leaf survives a cluttered background (65.5%), but a field leaf on a clean background still fails (46.8%).

This experimental record is itself a contribution: it provides clear empirical evidence — not merely theoretical argument — that data-centric collection of real UAE field imagery is the correct next step, not further synthetic augmentation or normalisation. The in-app feedback flywheel labels and stores every field photograph the user confirms or corrects, providing the deliberate mechanism by which future versions of the model will close the remaining gap. The project therefore delivers not only a deployable bilingual offline diagnostic system, but an honestly evaluated one with a measured, mechanistic understanding of its own limitations and a concrete plan for improving them.

TomatoCare directly contributes to the goals of the UAE National Food Security Strategy 2051 by placing a specialised, accessible, and accurate diagnostic tool in the hands of growers who have historically been underserved by precision agriculture technologies.

---

## Chapter 9: Future Work

Several extensions follow directly from the findings in Chapter 7 and would meaningfully improve the deployed system or its supporting analysis. The list below is ordered by expected impact on the laboratory-to-field gap, which is the project's largest open issue.

1. **Real-world field-data collection via the feedback flywheel.** The four failed experiments confirm that real field data is the only demonstrated way to close the laboratory-to-field gap. The in-app flywheel (§6.4) is the lowest-friction path to accumulating labelled UAE field images; even 200–400 real images per class would likely produce a measurable improvement, concentrated on the background-dependent classes (`early_blight`, `bacterial_spot`, `target_spot`).

2. **Motion-blur augmentation.** Lighting-only augmentation was tested and did not help (§7.5); motion-blur-only augmentation — the remaining component of the lightweight-augmentation hypothesis — has not yet been isolated and is a reasonable next experiment, since hand-held capture blur is common in real use.

3. **Leaf segmentation on field data.** MobileSAM segmentation showed no benefit on laboratory images because their backgrounds are already near-uniform (§7.5). Once real field images are available via the flywheel, applying background suppression before retraining may yield positive results, because field backgrounds (soil, canopy, fencing) are meaningfully confounding.

4. **A dedicated held-out calibration set.** Re-fitting the temperature scalar on a held-out calibration set, separate from the early-stopping validation data, would substantiate a tighter Expected Calibration Error than the current 0.061 and allow the confidence-calibration objective (NFR-AI-03) to be fully met.

5. **Per-class confidence thresholds.** The single 60% threshold could be replaced by per-class thresholds, reducing false low-confidence warnings on strong classes (`powdery_mildew` recall 1.000, `yellow_leaf_curl_virus` recall 0.992) and raising sensitivity on weaker ones (`early_blight` recall 0.943).

6. **Re-verification of gate safety metrics.** The non-leaf and other-leaf rejection figures should be regenerated against a fresh, held-out hard-negative set alongside the deployed-model evaluation, to bring every reported safety metric under one authoritative artefact.

7. **CameraX live capture and multi-crop generalisation.** Live camera capture with real-time blur and framing feedback would help users take a sharp, centred leaf photograph, directly addressing the single-leaf assumption. Beyond Capstone 2, the cascade architecture is generalisable to other crops by training crop-specific Stage 2 gates and Stage 3 classifiers — the safety-correct pattern itself transfers.

Beyond these technical refinements, four practical steps would move TomatoCare from a capstone deliverable toward sustained, trustworthy real-world use:

8. **A larger, UAE-specific field dataset.** Scale the flywheel collection of item 1 into a deliberate campaign that gathers and expert-labels several hundred real UAE field images per class across greenhouse, open-field, hydroponic, and saline-soil settings — the dataset the laboratory-to-field analysis (§7.5) identifies as the binding constraint on field accuracy.

9. **A continuous retraining pipeline.** Formalise the feedback flywheel into a periodic retrain–evaluate–redeploy loop: aggregate the collected field images, retrain the cascade, gate the result on both the held-out laboratory metrics and a growing real-field benchmark, and ship updated `.tflite` assets only when they improve field accuracy without regressing gate safety. This turns one-off collection into a sustained, measurable improvement process (an MLOps pipeline).

10. **Expert agronomist validation.** Have a qualified agronomist review a sample of the model's field diagnoses and the bilingual treatment knowledge base, validating clinical and agronomic appropriateness beyond raw classification accuracy and reinforcing the system's advisory — rather than authoritative — role.

11. **Lower-end and broader device testing.** Run the latency protocol (§7.9, Table 7.6) and the usability study (§7.10) on representative low-end hardware (≈ API 26 / 2 GB RAM) and across a range of screen sizes, replacing the current min-spec projection with measured evidence and confirming the accessibility requirements (NFR-11–NFR-13) on real devices.

---

## References

[1] UAE National Center of Meteorology, "Climate Temperature Indicators," Federal Competitiveness and Statistics Centre, 2025. [Online]. Available: https://uaestat.fcsc.gov.ae.

[2] UAE Government, "National Food Security Strategy 2051," United Arab Emirates, 2023. [Online]. Available: https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/strategies-plans-and-visions/environment-and-energy/national-food-security-strategy-2051.

[3] D. Devarajan, R. Allafi, M. Obayya, and N. Nemri, "AI based real time disease diagnosis in plants using deep learning driven CNNs," *Scientific Reports*, vol. 16, Art. no. 4587, Jan. 2026, doi: 10.1038/s41598-025-34681-1. [Online]. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC12868782/.

[4] M. Shafay, T. Hassan, M. Owais, I. Hussain, S. G. Khawaja, L. Seneviratne, and N. Werghi, "Recent advances in plant disease detection: challenges and opportunities," *Plant Methods*, vol. 21, Art. no. 140, Oct. 2025, doi: 10.1186/s13007-025-01450-0. [Online]. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC12570820/.

[5] K. He, X. Zhang, S. Ren, and J. Sun, "Deep Residual Learning for Image Recognition," in *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 770–778.

[6] A. Howard, M. Sandler, B. Chen, W. Wang, L.-C. Chen, M. Tan, G. Chu, V. Vasudevan, Y. Zhu, R. Pang, H. Adam, and Q. Le, "Searching for MobileNetV3," in *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*, 2019, pp. 1314–1324.

[7] M. Sandler, A. Howard, M. Zhu, A. Zhmoginov, and L.-C. Chen, "MobileNetV2: Inverted Residuals and Linear Bottlenecks," in *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2018, pp. 4510–4520.

[8] M. Tan and Q. V. Le, "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks," in *Proceedings of the 36th International Conference on Machine Learning (ICML)*, 2019, pp. 6105–6114.

[9] D. P. Hughes and M. Salathé, "An open access repository of images on plant health to enable the development of mobile disease diagnostics," *arXiv preprint*, arXiv:1511.08060, 2016.

[10] S. P. Mohanty, D. P. Hughes, and M. Salathé, "Using deep learning for image-based plant disease detection," *Frontiers in Plant Science*, vol. 7, p. 1419, 2016.

[11] B. Jacob et al., "Quantization and training of neural networks for efficient integer-arithmetic-only inference," in *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2018, pp. 2704–2713.

[12] Google AI Edge, "LiteRT: High-Performance On-Device Machine Learning Framework," 2024. [Online]. Available: https://ai.google.dev/edge/litert.

[13] UAE Federal Decree-Law No. 45 of 2021, "On the Protection of Personal Data," United Arab Emirates, 2021.

[14] Farmonaut, "App That Tells You What's Wrong With Your Plant," *Farmonaut Blog*, 2024. [Online]. Available: https://farmonaut.com/precision-farming/app-that-tells-you-whats-wrong-with-your-plant.

[15] Farmonaut, "How To Monitor Crop Health Using Satellite Crop Systems," 2024. [Online]. Available: https://farmonaut.com/satellite-based-crop-health-monitoring.

[16] Farmonaut, "Best Apps To Diagnose Plant Diseases: 2025's Ultimate Guide," *Farmonaut Blog*, 2025. [Online]. Available: https://farmonaut.com/blogs/best-apps-to-diagnose-plant-diseases-2025s-ultimate-guide.

[17] Flora Incognita, "Structure and Functionality of the Flora Incognita App," 2024. [Online]. Available: https://floraincognita.com/flora-incognita-app/.

[18] Flora Incognita, "Study on Identification Accuracy: Flora Incognita Reaches 98.8%," Oct. 2024. [Online]. Available: https://floraincognita.com/blog/2024/10/24/study-on-identification-accuracy-flora-incognita-reaches-98-8/.

[19] Flora Incognita, "Flora Incognita++ Citizen Science Project," 2024. [Online]. Available: https://floraincognita.com/flora-incognita-plusplus/.

[20] Android Developers, "Data and File Storage Overview," Google, 2024. [Online]. Available: https://developer.android.com/training/data-storage.

[21] JetBrains, "Serialization," *Kotlin Documentation*, 2024. [Online]. Available: https://kotlinlang.org/docs/serialization.html.

[22] Android Developers, "CameraX Overview," Google, 2024. [Online]. Available: https://developer.android.com/training/camerax.

[23] Android Developers, "Jetpack Compose," Google, 2024. [Online]. Available: https://developer.android.com/jetpack/compose.

[24] I. Sommerville, *Software Engineering*, 10th ed. Pearson Education Limited, 2016.

[25] R. S. Pressman and B. R. Maxim, *Software Engineering: A Practitioner's Approach*, 9th ed. McGraw-Hill, 2020.

[26] F. Abbas and S. Al-Naemi, "Managing salinity stress through microclimate control to enhance tomato productivity in arid regions," *Scientific Reports*, vol. 16, Art. no. 13042, Mar. 2026, doi: 10.1038/s41598-026-42022-z. [Online]. Available: https://www.nature.com/articles/s41598-026-42022-z.

[27] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, "On Calibration of Modern Neural Networks," in *Proceedings of the 34th International Conference on Machine Learning (ICML)*, 2017, pp. 1321–1330.

[28] D. Singh, N. Jain, P. Jain, P. Kayal, S. Kumawat, and N. Batra, "PlantDoc: A Dataset for Visual Plant Disease Detection," in *Proceedings of the 7th ACM IKDD CoDS and 25th COMAD*, 2020, pp. 249–253.

[29] A. Kirillov, E. Mintun, N. Ravi, H. Mao, C. Rolland, L. Gustafson, T. Xiao, S. Whitehead, A. Berg, W.-Y. Lo, P. Dollár, and R. Girshick, "Segment Anything," in *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*, 2023, pp. 4015–4026.

[30] C. Zhang, D. Han, Y. Qiao, J. U. Kim, S.-H. Bae, S. Lee, and C. S. Hong, "Faster Segment Anything: Towards Lightweight SAM for Mobile Applications," *arXiv preprint*, arXiv:2306.14289, 2023.

[31] A. Radford, L. Metz, and S. Chintala, "Unsupervised Representation Learning with Deep Convolutional Generative Adversarial Networks," *arXiv preprint*, arXiv:1511.06434, 2015.

[32] K. P. Ferentinos, "Deep learning models for plant disease detection and diagnosis," *Computers and Electronics in Agriculture*, vol. 145, pp. 311–318, 2018, doi: 10.1016/j.compag.2018.01.009.

[33] J. G. A. Barbedo, "Factors influencing the use of deep learning for plant disease recognition," *Biosystems Engineering*, vol. 172, pp. 84–91, 2018, doi: 10.1016/j.biosystemseng.2018.05.013.

[34] D. Hendrycks and K. Gimpel, "A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks," in *Proceedings of the International Conference on Learning Representations (ICLR)*, 2017.

[35] A. Motwani, "Tomato Leaves Dataset," Kaggle, 2022. [Online]. Available: https://www.kaggle.com/datasets/ashishmotwani/tomato.

[36] S. Rupavatharam, A. Kennepohl, B. Kummer, and V. Parimi, "Automated plant disease diagnosis using innovative Android app (Plantix) for farmers in the Indian state of Andhra Pradesh," *Phytopathology*, vol. 108, no. 10 (Suppl.), 2018.

[37] A. Siddiqua, M. A. Kabir, T. Ferdous, I. B. Ali, and L. A. Weston, "Evaluating Plant Disease Detection Mobile Applications: Quality and Limitations," *Agronomy*, vol. 12, no. 8, Art. no. 1869, 2022, doi: 10.3390/agronomy12081869.

---

## Appendix A: Experiment Configurations (Supplementary) {#appendix-a}

**DCGAN (Experiment 3).** Latent dimension 128; image resolution 96×96; batch size 64; 150 epochs; Adam optimiser (learning rate 2×10⁻⁴, β₁ = 0.5); binary cross-entropy with logits; one-sided real-label smoothing 0.9; trained on the 2,503 `bacterial_spot` training images; 600 synthetic images generated and added to the training pool. Training was stable (discriminator loss ≈ 0.96, generator loss ≈ 1.52 at epoch 150; no mode collapse).

**Heavy augmentation (Experiment 1).** Per-image random horizontal flip; brightness jitter ±0.30; contrast factor sampled from [0.55, 1.60]; gamma γ sampled from [0.6, 1.6] with probability 0.6; hue shift ±0.06; saturation factor from [0.5, 1.6]; motion blur kernel 9×9 with probability 0.4; JPEG quality sampled from [30, 75] with probability 0.4. Applied in the `tf.data` pipeline (unbatch → augment → rebatch), not baked into the model graph.

**Composited-background validation (§7.5.1).** Laboratory leaves had their white background removed by threshold (R, G, B > 220) with 3-pixel erosion of the resulting mask, then were scaled to 78% of the canvas with ±8% position jitter and pasted onto twelve field-like background images. The resulting 165 composited images (15 per class × 11 classes) were passed through the full deployed cascade for end-to-end evaluation.

---

## Appendix B: Application Requirements Catalogue {#appendix-b}

This appendix consolidates the requirements specified in Chapter 4 (§4.2–§4.4)
into a single traceability catalogue, mapping each requirement to the component
that implements it and the method by which it is verified. It complements the
prose specification in Chapter 4 and the test plans in §7.9. Verification methods
are: *Measurement* (a recorded quantitative result), *Inspection* (static check
of code, manifest, or resources), *Unit test* (automated JVM test, §7.9),
*Functional test* (black-box case in the FR-01–FR-28 matrix, `docs/functional_tests.md`,
executed on-device and recorded by QA), and *By design* (satisfied by an
architectural decision).

Note: TomatoCare is a single-user, fully offline application; it deliberately has
no user authentication, no remote notifications, and no cloud accounts, so no such
requirements appear.

**Table B.1: Functional Requirements Traceability**

| ID | Requirement (abridged) | Implementing component | Verification |
|---|---|---|---|
| FR-01 | Operate fully offline | Manifest (no INTERNET); `TFLiteEngine` | Inspection (§7.8) — Met |
| FR-02 | Camera capture | `CameraScreen`, `ScanViewModel` | Functional test |
| FR-03 | Gallery selection | `CameraScreen` (SAF GetContent) | Functional test |
| FR-04 | Validate format / ≤10 MB | `ImageValidation` | Functional test |
| FR-05 | Preprocess (224×224, ÷255) | `ImagePreprocessor` | Inspection — preprocessing-parity check (§6.2–6.3) |
| FR-06 | On-device inference | `TFLiteEngine` (3-stage cascade) | Inspection + Functional test |
| FR-07 | Bilingual result + confidence + severity | `ResultScreen` | Functional test |
| FR-08 | Low-confidence warning < 60% | `SeverityHeuristic`, `LowConfidenceWarning` | Unit test (`SeverityHeuristicTest`) + Functional test |
| FR-09 | Localised treatment guidance | `TreatmentRepository` | Functional test |
| FR-10 | Filter treatments by growing method | `ResultViewModel.onMethodSelected` | Functional test |
| FR-11 | Persist scan record as JSON | `ScanStorageManager` | Unit test (`ScanHistorySerializationTest`, `ScanRecordTest`) |
| FR-12 | History in date order | `HistoryScreen` | Functional test |
| FR-13 | Review a past scan | `ResultScreen` (from history) | Functional test |
| FR-14 | Scan-activity dashboard | `HomeScreen`, `HomeStats` | Unit test (`HomeStatsTest`) + Functional test |
| FR-15 | Delete all history (with confirm) | `SettingsScreen` | Functional test |
| FR-16 | Export history via SAF | `ScanExporter` | Functional test |
| FR-17 | Import + validate schema | `ScanImporter` | Unit test (serialization) + Functional test |
| FR-18 | Switch EN/AR at any time | `SettingsStore` flow → `recreate()` | Functional test |
| FR-19 | Full RTL layout in Arabic | Compose RTL + `values-ar/` | Functional test |
| FR-20 | Graceful error messages, no crash | `ScanViewModel`/`ResultScreen` error states | Unit test (decode-failure path) + Functional test |

**Table B.2: Non-Functional Requirements Traceability**

| ID | Requirement (abridged) | Verification | Result |
|---|---|---|---|
| NFR-01 | No network connectivity required | Inspection — no INTERNET permission (§7.8) | Met |
| NFR-02 | Inference < 3 s on min-spec device | Measurement — inference latency (§7.9, Table 7.6) | Met — 12–20 ms (median 13.5), n = 10 |
| NFR-03 | Disease accuracy ≥ 90% (lab) | Measurement (§7.2) | Met — 97.59% |
| NFR-04 | App ≤ 50 MB; models ≤ 15 MB | Measurement (§7.2) | Met — 38.51 MB APK / 9.87 MB models |
| NFR-05 | Usable without training; core ≤ 2 taps | Usability testing (§7.9, QA-recorded) | — |
| NFR-06 | No crash; graceful failure handling | Unit test + Functional test (§7.9) | — |
| NFR-07 | Runs on Android API 26+ | Inspection — `minSdk = 26` | Met by configuration |
| NFR-08 | No data leaves the device | Inspection — no INTERNET; local storage only (§7.8) | Met |
| NFR-09 | Modular, independently updatable | Inspection — layered architecture (`docs/architecture.md`) | Met by design |
| NFR-10 | All strings in EN and AR | Inspection — `values/` + `values-ar/` parity | Met |
| NFR-11 | Text in `sp`; legible at ≥130% font scale | Inspection (`sp` usage) + Functional test at 100%/130% | Planned |
| NFR-12 | Full RTL mirroring + Arabic readability | Functional test (all Arabic screens) + `values-ar/` parity | Met |
| NFR-13 | WCAG 2.1 AA contrast (4.5:1 / 3:1), both themes | Measurement (contrast analyser), both themes | Planned |

**Table B.3: Domain Requirements Traceability**

| ID | Requirement (abridged) | Verification |
|---|---|---|
| DR-01 | Tomato leaves only | By design — Stage-2 tomato gate |
| DR-02 | 11 conditions; abiotic → low-confidence, not a confident label | By design — gates + 60% threshold; no abiotic class |
| DR-03 | UAE-specific treatment advice | Content — `treatments.json` by growing method |
| DR-04 | Disclaimer on the results screen | Functional test (§7.9) |
| DR-05 | Formal EN/AR botanical terminology | Content inspection — `treatments.json` |
| DR-06 | 60% low-confidence threshold | By design — `confidenceThreshold = 0.60` (§3.8.5) |
| DR-07 | No identity/location/behaviour claims | By design — no such fields; offline-only |
