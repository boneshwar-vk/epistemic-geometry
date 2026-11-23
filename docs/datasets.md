# Datasets

Reconciled from three independent reviews (facts/sizes, interpretability suitability, adversarial-reviewer).
Numbers are tagged **[C]** confirmed from a primary source this pass, **[~]** approximate, **[U]** unverified
(a host was unreachable or the figure is version-dependent) — the **[U]** items are listed in *Verify before the
paper* and must be checked against the primary source. Sizes count **rows/measurements**; what matters for this
project is **non-redundant clusters** after leakage-aware splitting (see *Minimum-N principle*).

**Guiding principle.** Interpretability does not have a data-scale problem; it has a data-*cleanliness* problem.
Each quantity needs a few hundred clean, non-redundant, properly-split clusters with trustworthy ground truth and
matched nulls — not millions of rows. Scale invites leakage and buys nothing here.

## Role per quantity (cleanliness-ranked, lowest leakage/bias risk first)

| # | Quantity | Role |
|---|---|---|
| 1 | Backbone dihedrals (φ/ψ/ω/χ), secondary structure, SASA, contacts | **LOAD-BEARING** (spine) |
| 2 | PPI interface identity / buried surface area | **LOAD-BEARING** (probe-only posture) |
| 3 | Fold stability ΔG / ΔΔG | **LOAD-BEARING** — the thermodynamics **anchor** |
| 4 | Dynamics / flexibility | **PROBE-ONLY** — localization only; drop the identity claim |
| 5 | PPI binding affinity + interface ΔΔG / hot-spots | **DEFERRED** — demote continuous ΔΔG → hot-spot classification |
| 6 | Protein–ligand binding Kd / ΔG | **PROBE-ONLY + GATED** (G-B1); appendix-negative if it fails |
| 7 | On/off-target specificity | **PROBE-ONLY + APPENDIX** — control-gated; most dual-use |

## Per-quantity datasets, sizes, splits

### 1. Dihedrals / secondary structure / SASA / contacts — ESM3, single-chain  [LOAD-BEARING]
Labels are **computed by code** (DSSP / FreeSASA / mdtraj) from experimental structures, so "size" is the number
of non-redundant chains you choose to cache.
| Dataset | Size | License | Use |
|---|---|---|---|
| PDB chains via **PISCES** / **CATH S40** cull | CATH S40 ~31k reps **[U]** | PDB public domain; CATH academic | pool → cache ~200–300 non-redundant chains/split |
| **CB513** / TS115 | 513 / 115 **[~]** | academic | appendix SS benchmark |
| **CAMEO** / **CASP15–16** | hundreds **[~]** | academic | post-cutoff strict held-out |
- **Split:** MMseqs2 ≤30% identity ∩ deposition-date (and CATH-superfamily). **Structure track OFF** (else dihedral
  decode is trivial — an auto-reject). SASA = the non-periodic **double-dissociation control**.

### 2. Dynamics / flexibility  [PROBE-ONLY]
| Dataset | Size | License | Use |
|---|---|---|---|
| **ATLAS** (all-atom MD) | 1,390 proteins (orig) / 1,938 (Nov-2024) **[C]** | CC BY-NC-4.0 | localization; converged RMSF as GT |
| **mdCATH** | 5,398 domains **[C]** | CC BY-4.0 | larger MD alternative |
| B-factors / pLDDT | — | — | appendix/control only |
- No clean ground truth (force-field / crystal-packing nuisance) → **keep per-layer localization, drop the
  identity claim** unless MD↔B-factor consensus. Fold/topology split.

### 3. Fold stability ΔG / ΔΔG  [LOAD-BEARING — thermodynamics anchor]
| Dataset | Size | License | Use |
|---|---|---|---|
| **Tsuboyama / Rocklin mega-scale (2023)** | **776,298 ΔG** measurements; 479 domains (331 natural + 148 designed); 210,118 double mutants **[C]** (ML-ready single-mutant count varies ~272k–851k by filter **[U]** — pin the Zenodo version) | CC BY 4.0 (Zenodo) | **the anchor** |
| FireProtDB v1 | ~16,000 **[~]** (v2 is millions incl. DMS — not comparable) | academic **[U]** | OOD appendix |
| ThermoMutDB / ProThermDB | 14,669 / 31,580 **[C/~]** | academic **[U]** | cross-study → appendix |
| Meltome Atlas (Tm) | ~48,000 proteins / 13 species **[~]** | CC BY **[U]** | coarse → dropped from identity |
| **S669 / Ssym** | small leakage-filtered ΔΔG test sets **[~]** | academic | OOD generalization test |
- **Why Tsuboyama is the anchor:** one assay (cDNA-display proteolysis → no cross-assay batch confound unlike
  Meltome/FireProt), dense within-domain saturation gives a true **monotone ΔG axis** and a dose-response
  substrate, uniquely **powers the confidently-wrong slice** (point mutants that wreck ΔG while sequence barely
  moves), clean CATH **domain-split**, cheap 40–72-aa activations, and 148 de-novo designs as a built-in
  anti-memorization OOD stratum.
- **Split:** WT-domain cluster (CATH) — **never per-mutant** (per-mutant is pseudo-replication = auto-reject).

### 4. Protein–ligand binding Kd / ΔG — co-folding model  [PROBE-ONLY + GATED]
| Dataset | Size | License | Use |
|---|---|---|---|
| **PLINDER** | 449,383 PLI systems **[C]**; license Apache-2.0 + CC-BY-4.0 parts **[~]** | — | **leakage-aware splits** (PL50 / TIME / ECOD) |
| **PDBbind v2020** | general 14,108 / refined 5,050 / core 285 **[C]** | free academic | complexes + experimental Kd |
| **LP-PDBBind** | split only | — | alternative leakage-aware split |
| Binding MOAD | 41,409 structures; 15,223 with affinity **[C]** | academic | breadth |
| **CASF-2016** | 285 **[C]** | academic | report-on benchmark |
| BindingDB | ~2.9M measurements **[C]** (no structures; pooled Ki/IC50/Kd) | CC BY-4.0 | **CUT as primary** (assay heterogeneity) |
- Use ~**800–1,500** non-redundant complexes under **PLINDER PL50 + time + scaffold**; **experimental Kd only,
  single assay type**; never the model's own predicted affinity (PairSAE circularity). Highest-leakage quantity →
  gate G-B1; if it fails, report the leakage-negative in the appendix.

### 5. PPI affinity + interface ΔΔG / hot-spots  [DEFERRED]
| Dataset | Size | License | Use |
|---|---|---|---|
| **SKEMPI 2.0** | 7,085 mutations / 345 complexes (~237 interactions) **[C]** | academic **[U]** | hot-spot classification; complex-cluster split |
| PPI affinity benchmark (Kastritis 2011) | 144 complexes **[C]** | academic | tiny gold standard |
| PDBbind protein–protein subset | ~2.5k **[~]** | academic | breadth |
- No large clean dataset; small + assay-heterogeneous + redundant on a few complexes → **demote continuous ΔΔG to
  hot-spot classification**; continuous/causal version deferred. Split by **complex cluster**, never per-mutation;
  de-bias antibody–antigen.

### 6. PPI interface identity / BSA  [LOAD-BEARING]
| Dataset | Size | License | Use |
|---|---|---|---|
| **PINDER** | 2,319,564 dimeric systems; 1,955 leakage-free test **[C]**; license **[U]** | — | **interface-structural splits** |
| **PPIRef** | PPIRef300K 322,454 / PPIRef50K 45,553 **[C]** | academic **[U]** | dedup pool |
| DIPS | 42,826 **[C]** | academic | **CUT** (DB5 leak + crystal contacts as interface) |
- Structure-defined label (not model-defined) → one of the cleaner quantities. Use ~**150–250** non-redundant
  complexes; **interface-similarity split** (not sequence); biological-assembly filter; surface/conservation baseline.

### 7. On/off-target specificity  [PROBE-ONLY + APPENDIX; most dual-use]
| Dataset | Size | License | Use |
|---|---|---|---|
| **LIT-PCBA** | 15 targets / 7,761 actives / ~407,839 inactives **[C]** (2025 duplicate-leakage critique → AVE-dedup) | academic | ligand specificity (real inactives) |
| DUD-E | 102 targets / 22,886 actives / ~1.14M decoys **[C]** | academic | **appendix only** (analogue/decoy bias) |
| DEKOIS 2.0 | 81 targets **[~]** | academic | alternative |
| **Bernett et al. (2024)** PPI gold standard | de-leaked splits 163,192 / 59,260 / 52,048 **[C]** | academic **[U]** | PPI specificity |
| Negatome 2.0 | PDB 4,397 + Manual 2,171 **[C]** | academic | PPI negatives |
- Only ~15 ligand targets → per-target AUROC; **cannot be load-bearing**. Requires a **protein-dependence /
  pocket-ablation control** (does "specificity" need the protein, or is it decoy artifact?) or the claim is
  dropped. Probe-only, benign complexes, **no steering** — the most dual-use-sensitive quantity.

## Cross-cutting additions (flagged by the facts review)
- **ProteinGym** — ~2.7M DMS measurements with standardized splits **[~]**: fitness/variant-effect, useful as an
  OOD variant-effect probe and a second mutational substrate alongside Tsuboyama.
- **FLIP** — standardized fitness/generalization splits.
- **MISATO** — MD-refined PDBbind (dynamics for complexes).
- **S669 / Ssym** — leakage-filtered ΔΔG test sets (listed under stability).

## Minimum-N principle
The binding constraint is **non-redundant clusters after leakage-aware splitting, not rows**. For per-layer
localization + identity: ~**150–300 clusters** per split suffice. For the **truth-vs-confidence** AUROC the gate is
~**45–55 cases inside the confidently-wrong slice** (DeLong, AUROC 0.70 vs 0.50 at 80% power) — this slice is the
§14.1 limitation made concrete, so power must be checked up front per quantity.

## Auto-reject traps (any one can sink a quantity)
1. Track-A **structure track left ON** (trivial dihedral decode).
2. **Random / legacy splits on a pretraining corpus** — random PISCES/CB513, PDBBind random split / CASF core,
   **mutation-level** Tsuboyama or SKEMPI, FireProt/ThermoMut random.
3. **DIPS → DB5 interface leak**, or crystal contacts treated as interface.
4. **DUD-E specificity AUROC with no protein-dependence control** (analogue bias is learnable).
5. **BindingDB with Ki/IC50/Kd pooled** (incommensurable; no structures).
6. **Target = the model's own predicted affinity** (PairSAE circularity).
7. **B-factors as the sole dynamics label.**
8. Any number **not reported as trained − random-init** and **not beating the explicit leakage probe**.

## Verify before the paper (human / primary-source pass)
- CATH S40 exact domain count; **PINDER license**; **Tsuboyama** ML-ready single-mutant count + the exact Zenodo
  version to pin; PDBBind/CASF/FireProtDB/Negatome/Bernett exact counts + licenses; BindingDB usable-Kd subset;
  and — governing the Track-A confidence object — **ESM3 `d_model`, whether it uses RoPE, and whether a per-residue
  pLDDT is emitted on sequence-only input** (else use structure-token predictive entropy as the confidence signal).

_Reconciled 2026-11-23 from three independent agent reviews; figures to be re-confirmed against primary sources
before publication. Benign/defensive framing; the specificity quantity is probe-only with no steering._
