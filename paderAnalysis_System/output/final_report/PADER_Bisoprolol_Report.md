# Periodic Adverse Drug Experience Report (PADER)
## Bisoprolol (Application Number: B-1)

**Report Type:** PADER (simplified exercise version)
**Reporting Period:** 2024-12-27 to 2025-12-26
**Date of This Report:** 2026-08-16
**Data Source:** Bisoprolol_icsr_sample_1068rows.xlsx (1,068 rows / 1,024 unique cases after deduplication)

---

## 1. Reporting Period

| Field | Value |
|---|---|
| Product | Bisoprolol |
| Application Number | B-1 |
| Report Type | PADER (simplified, exercise version) |
| Reporting Period | 2024-12-27 to 2025-12-26 |
| Data Cut-off | 2025-12-26 (latest `receivedate` in source data) |
| Report Generated | 2026-08-16 |

## 2. Data Processing Notes

- Source file contained 1068 rows representing 1024 unique cases (`safetyreportid`). 44 rows were superseded follow-up versions of the same case and were excluded, keeping only the latest version per case.
- Kept max(safetyreportversion) row per safetyreportid; reaction/outcome fields split on comma with positional alignment.
- 83 cases have no recorded patient age; 28 cases have no recorded sex.
- No System Organ Class (SOC) field is present in the source data; reaction analysis is reported at the MedDRA Preferred Term level only.
- No product label/CCDS reference was supplied for this exercise; expectedness (labeled vs. unlabeled) is out of scope.
- No history-of-actions data was supplied for this exercise (see Section 8).

## 3. Narrative Summary and Analysis

During the reporting period of 2024-12-27 to 2025-12-26, 1,024 cases of adverse events associated with Bisoprolol were received. Of these, 1,023 cases (99.9%) were classified as serious, and 1 case (0.1%) was classified as non-serious.

The most frequently reported reactions overall were Acute kidney injury (80 cases), Drug ineffective (54 cases), and Hypotension (46 cases). Among serious cases specifically, the most frequently reported reactions were Acute kidney injury (80 cases), Drug ineffective (53 cases), and Hypotension (46 cases).

Cases originated most frequently from the EU region (344 cases), the United Kingdom (281 cases), and France (185 cases). By patient sex, 503 cases involved female patients, 493 involved male patients, and 28 cases had no recorded sex.

Of the 1,024 cases, 1,023 (99.9%) met 15-day Alert reporting criteria. Data completeness varied across fields: 83 of 1,024 cases had no recorded patient age, and 28 cases had no recorded sex.

## 4. Summary Analysis of Cases

A total of 1,024 cases were received during the reporting period, of which 1,023 (99.9%) were serious and 1 (0.1%) was non-serious.

By age group, the majority of cases involved elderly patients (65+ years): 674 cases. Adult patients (18-64 years) accounted for 248 cases. Smaller numbers were recorded across other age groups: Adolescent (12-17 years), 6 cases; Infant (28 days-2 years), 5 cases; Child (2-11 years), 4 cases; and Neonate (under 28 days), 1 case. Age was not recorded for 86 cases.

By sex, 503 cases involved female patients and 493 involved male patients; sex was not recorded for 28 cases.

The five countries with the highest case counts were the EU region (344), United Kingdom (281), France (185), Canada (56), and Italy (51).

By reported outcome across the individual reaction records in the dataset: recovered/resolved (1,280 records), unknown (1,039 records), not recovered/not resolved/ongoing (536 records), recovering/resolving (406 records), fatal (134 records), and recovered/resolved with sequelae (34 records).

## 5. Reaction / Adverse Event Analysis

A total of 3,429 individual reaction mentions were recorded during the reporting period, representing 1,122 distinct MedDRA Preferred Terms. No System Organ Class field is available in the source data; the analysis below is presented at the Preferred Term level only.

The most frequently reported reactions overall were: Acute kidney injury (80), Drug ineffective (54), Hypotension (46), Drug interaction (43), Dyspnoea (38), Bradycardia (37), Dizziness (36), Fatigue (33), Off label use (31), and Fall (30).

Among reactions reported in serious cases, the ranking was largely consistent with the overall pattern: Acute kidney injury (80), Drug ineffective (53), and Hypotension (46) were the most frequently reported.

These figures reflect observed reporting frequency only. Expectedness (whether a reaction is already listed in the approved product label) and causal relationship to Bisoprolol were not assessed as part of this analysis, as label/CCDS reference data was not supplied for this exercise.

## 6. Serious Cases / 15-Day Alerts

A total of 1,023 cases (99.9% of total case volume) met 15-day Alert (expedited) reporting criteria during the reporting period. Of these alert cases, 68 involved a fatal outcome.

The most frequently reported reactions among 15-day Alert cases were Acute kidney injury (80), Drug ineffective (53), Hypotension (46), Drug interaction (43), and Dyspnoea (38).

Seriousness criteria are recorded as independent yes/no flags and are not mutually exclusive; a single case may meet more than one criterion, so the figures below do not sum to the total case count. Across all serious cases, the criteria breakdown was: Other medically important (905 cases), Hospitalization (482 cases), Life-threatening (105 cases), Death (68 cases), Disabling (44 cases), and Congenital anomaly (7 cases).

Individual alert case identifiers are available in the accompanying Case Index for reviewer traceability.

## 7. Trends and Important Observations

Monthly case volume during the reporting period ranged from a low of 21 cases (December 2024, a partial month at the start of the reporting window) to a high of 109 cases (July 2025). Monthly counts across the full period were: Dec 2024: 21, Jan 2025: 75, Feb 2025: 94, Mar 2025: 83, Apr 2025: 78, May 2025: 80, Jun 2025: 84, Jul 2025: 109, Aug 2025: 64, Sep 2025: 76, Oct 2025: 102, Nov 2025: 75, Dec 2025: 83.

Comparing the first half of the reporting period to the second half (split at 2025-06-27), reporting counts for the three most frequent reactions shifted as follows: Acute kidney injury was reported in 48 cases in the first half versus 32 in the second half; Drug ineffective in 25 cases versus 29; and Hypotension in 21 cases versus 25.

These are observed numerical patterns only. No causal or safety-signal conclusion is drawn from this data; month-to-month and half-period variation of this kind is presented for qualified human reviewer assessment.

## 8. History of Actions

No history-of-actions data (e.g. labeling changes, regulatory communications, or safety-related studies) was supplied for this reporting period. No actions are reported in this section.

## 9. Case Index / Listing

The table below lists the first 50 of 1024 total cases for illustration. The complete case-level listing, to which every aggregate figure above is traceable, is provided in the companion file `case_index_full.csv`.

| Case ID | Reactions | Serious | Received Date | Country | Sex | Age Group |
|---|---|---|---|---|---|---|
| 24780403 | Rectal haemorrhage; Deficiency anaemia | Yes | 2024-12-27 | Italy | Female | Elderly (65+yr) |
| 24780599 | Coma | Yes | 2024-12-27 | France | Female | Elderly (65+yr) |
| 24780680 | Acute kidney injury | Yes | 2024-12-27 | France | Male | Elderly (65+yr) |
| 24784771 | Muscle spasms | Yes | 2024-12-28 | United Kingdom | Female | Elderly (65+yr) |
| 24784845 | Chest pain; Anxiety; Panic attack | Yes | 2024-12-28 | United Kingdom | Male | Adult (18-64yr) |
| 24784920 | Genital burning sensation | Yes | 2024-12-28 | United Kingdom | Female | Adult (18-64yr) |
| 24784985 | Pemphigoid | Yes | 2024-12-28 | United Kingdom | Male | Elderly (65+yr) |
| 24784989 | Drug interaction; Hypersensitivity | Yes | 2024-12-28 | United Kingdom | Male | Adult (18-64yr) |
| 24787006 | Bradycardia; Medication error | Yes | 2024-12-30 | United Kingdom | Male | Adult (18-64yr) |
| 24787240 | Muscle twitching; Muscle spasms | Yes | 2024-12-30 | United Kingdom | Male | Adult (18-64yr) |
| 24787307 | Cardiac arrest | Yes | 2024-12-30 | United Kingdom | Female | Adult (18-64yr) |
| 24787627 | Hypoglycaemia; Acidosis | Yes | 2024-12-30 | Italy | Female | Elderly (65+yr) |
| 24788122 | Erectile dysfunction; Condition aggravated; Drug ineffective | Yes | 2024-12-30 | Italy | Male | Adult (18-64yr) |
| 24791327 | Cardiac failure | Yes | 2024-12-31 | France | Female | Elderly (65+yr) |
| 24791598 | Hepatic cytolysis | Yes | 2024-12-31 | France | Female | Elderly (65+yr) |
| 24791831 | Cardiogenic shock | Yes | 2024-12-31 | United Kingdom | Unknown | Unknown |
| 24792345 | Atrioventricular block | Yes | 2024-12-31 | United Kingdom | Unknown | Unknown |
| 24792691 | Pseudoporphyria | Yes | 2024-12-31 | France | Male | Elderly (65+yr) |
| 24792889 | Hyponatraemia; Hypervolaemia; Cardiac failure | Yes | 2024-12-31 | Spain | Male | Elderly (65+yr) |
| 24793431 | Dyskinesia | Yes | 2024-12-31 | France | Female | Elderly (65+yr) |
| 24795574 | Oxygen saturation decreased; Cardiac failure congestive; ... | Yes | 2024-12-31 | United Kingdom | Female | Adult (18-64yr) |
| 24795755 | Acute kidney injury | Yes | 2025-01-01 | United Kingdom | Male | Elderly (65+yr) |
| 24796067 | Leg amputation | Yes | 2025-01-01 | United Kingdom | Male | Elderly (65+yr) |
| 24796224 | Dyskinesia | Yes | 2025-01-01 | France | Male | Elderly (65+yr) |
| 24798336 | Inappropriate antidiuretic hormone secretion; Hyponatraem... | Yes | 2025-01-02 | Spain | Male | Elderly (65+yr) |
| 24802877 | Acute kidney injury | Yes | 2025-01-03 | France | Male | Adult (18-64yr) |
| 24803041 | Hyponatraemia | Yes | 2025-01-03 | Spain | Female | Unknown |
| 24803117 | Hepatic enzyme increased | Yes | 2025-01-03 | United Kingdom | Female | Elderly (65+yr) |
| 24803128 | Haematemesis | Yes | 2025-01-03 | Spain | Female | Unknown |
| 24803463 | Hepatic cytolysis | Yes | 2025-01-03 | France | Male | Adult (18-64yr) |
| 24806665 | Foetal growth restriction; Medically induced preterm birt... | Yes | 2025-01-04 | France | Male | Unknown |
| 24806776 | Sinus bradycardia; Drug ineffective | Yes | 2025-01-04 | Eu | Female | Elderly (65+yr) |
| 24806812 | Sudden onset of sleep; Sleep disorder; Somnolence; Distur... | Yes | 2025-01-04 | Germany | Female | Unknown |
| 24806832 | Cardio-respiratory arrest | Yes | 2025-01-04 | Portugal | Female | Elderly (65+yr) |
| 24807274 | BRASH syndrome | Yes | 2025-01-05 | Portugal | Female | Elderly (65+yr) |
| 24809124 | Cough; Chest discomfort; Dyspnoea | Yes | 2025-01-06 | Italy | Male | Adult (18-64yr) |
| 24812900 | Dilated cardiomyopathy | Yes | 2025-01-07 | France | Female | Elderly (65+yr) |
| 24812977 | Suicide attempt; Intentional overdose | Yes | 2025-01-07 | Germany | Female | Adult (18-64yr) |
| 24813208 | Urostomy complication | Yes | 2025-01-07 | Germany | Female | Elderly (65+yr) |
| 24813219 | Pancytopenia | Yes | 2025-01-07 | France | Male | Elderly (65+yr) |
| 24813415 | Cutaneous vasculitis; Vascular purpura | Yes | 2025-01-07 | France | Male | Elderly (65+yr) |
| 24815412 | Bradycardia foetal; Neonatal respiratory distress; Microe... | Yes | 2025-01-07 | France | Female | Unknown |
| 24816890 | Hepatic cytolysis | Yes | 2025-01-07 | France | Male | Elderly (65+yr) |
| 24822547 | Symptom masked | Yes | 2025-01-09 | United Kingdom | Male | Elderly (65+yr) |
| 24823024 | Gastric ulcer | Yes | 2025-01-09 | Germany | Female | Elderly (65+yr) |
| 24828530 | Altered state of consciousness; Cognitive disorder; Asthe... | Yes | 2025-01-10 | France | Female | Adult (18-64yr) |
| 24828871 | Syncope; Hyponatraemia; Asthenia; Dizziness; Fall | Yes | 2025-01-10 | Spain | Female | Elderly (65+yr) |
| 24833163 | Hypoglycaemia | Yes | 2025-01-11 | France | Male | Elderly (65+yr) |
| 24833191 | Mobility decreased; Hypertonia; Parkinsonism; Cognitive d... | Yes | 2025-01-11 | United Kingdom | Female | Elderly (65+yr) |
| 24833204 | Chest pain; Dizziness; Blood pressure systolic decreased;... | Yes | 2025-01-11 | Germany | Female | Adult (18-64yr) |

---

*This report was generated by an AI-assisted pipeline for a technical exercise. All figures are derived deterministically from the source dataset via Python analysis; narrative text was generated per-section from scoped, pre-computed evidence packets, subject to automated grounding checks and human review before inclusion. See README.md for full methodology.*
