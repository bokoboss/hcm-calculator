# Phase 3 non-example case register

| Case | Classification | Purpose / independent basis | Expected checks |
| --- | --- | --- | --- |
| PL-C1-HV5 | method_conformance_case | Class 1, 5% HV; Exhibit 15-5 and Eq. 15-24--34 hand-derived inputs | 1,500 veh/h capacity; flow and HV conservation; positive midpoint density |
| PL-C3-UP | method_conformance_case | Class 3 upgrade; Chapter 15 coefficient-table path | applicable class, Step 7 lane values and Eq. 15-34 density finite |
| PL-C5-HV8 | method_conformance_case | Class 5, 8% HV; Exhibit 15-5 row | 1,400 veh/h capacity |
| PL-DS-NEAR | method_conformance_case | ordered constrained/lane/constrained sequence | Step 9 applies at 1.0 mi from lane start |
| PL-RESET | regression_case | two explicit lanes in ordered sequence | downstream context identifies the second lane |
| PL-BAD-CONTEXT | regression_case | downstream role without preceding lane | explicit HCMCalcError |

Expected values are asserted from the cited equations and Exhibit 15-5 rather
than generated from the production functions under test. Published Examples 3
and 4 are tracked independently as `published_reference_case` regressions.
