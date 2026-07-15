# HCM 7.1 Freeway Weaving Methodology Audit

## Decision

`hcm_7_1` is a known **unqualified** version in Phase 13.2. It is deliberately
registered as unavailable and raises `UnsupportedScopeError`; it has no
numerical fallback, placeholder values, or path into the HCM 7.0 engine.

The source-availability gate is positive: the official National Academies
[HCM Edition 7.1 chapters](https://nap.nationalacademies.org/resource/26432/Highway_Capacity_Manual_Edition_7.1_Chapters.pdf)
contains Chapter 13 and Chapter 27. The qualification gate is not positive yet:
the team has not independently transcribed its observed model domain, completed
the required Chapter 14 input/output capacity checks, or created independently
reviewed example and intermediate-value fixtures. Thus criteria 4, 5, and 8 of
the Phase 13.2 implementation decision remain unmet. No 7.1 production
coefficient is committed.

## Source audit

| Subject | Governing 7.1 location | Audit result |
| --- | --- | --- |
| Geometry and LOS | Ch. 13 pp. 13-3--13-10, Exhibits 13-1--13-7 | New direction-specific `NWRF`, `NWFR`, and `NWRR` geometry terms; do not reuse 7.0 `NWL`. |
| Applicability bounds | Ch. 13 p. 13-11, Exhibit 13-8 | Needs visual transcription before code can enforce the domain. |
| Inputs and flow definitions | Ch. 13 pp. 13-13--13-18, Eqs. 13-1--13-6 | Chapter 12 FFS and HV foundations remain dependencies. |
| Speed/impedance | Ch. 13 pp. 13-18--13-20, Eqs. 13-7--13-14 | A single mean-speed impedance model replaces 7.0's lane-change and separate speed chain. |
| Capacity and LOS | Ch. 13 pp. 13-21--13-22, Eqs. 13-15--13-21 | Uses 35 pc/mi/ln at capacity, a quadratic capacity procedure, and `d/c > 1` termination. |
| Entry/exit checks | Ch. 14 p. 14-18, Exhibits 14-8 and 14-10 | Required for a complete 7.1 operational result; no qualified local implementation exists. |
| Examples | Ch. 27 pp. 27-2--27-16 | Official examples exist but are not yet independently transcribed or validated. |

The NCHRP Report 1038 proposed chapters are useful corroborating history only;
they are not substituted for the finalized official 7.1 chapter.

## Material differences from HCM 7.0

- HCM 7.1 geometry direction counts have different names and semantics from
  HCM 7.0 `NWL`.
- HCM 7.1 has no HCM 7.0 `LCMIN`, `LMAX`, or separate weaving/nonweaving
  lane-change-rate calculation chain.
- The HCM 7.1 capacity density is 35 pc/mi/ln; HCM 7.0's freeway-weaving LOS
  E/F density is 43 pc/mi/ln.
- HCM 7.1 applies SAF/CAF to the comparable basic segment rather than applying
  a second adjustment after its weaving calculation.
- Both core methods terminate speed prediction above capacity, but neither is a
  queue or volume-served model.

## Evidence required to qualify a future implementation

1. Visually transcribe Exhibit 13-8 and every domain/bound without endpoint
   extrapolation.
2. Define and validate a separate 7.1 input model for NWRF/NWFR/NWRR and all
   7.1-only fields.
3. Implement and independently validate the Chapter 14 input/output checks.
4. Independently re-transcribe Examples 1--3 and publish concise fixtures with
   intermediate checks and tolerances.
5. Add equation, boundary, oversaturation, SAF/CAF, and static import-isolation
   tests before changing `hcm_7_1` from unqualified.
