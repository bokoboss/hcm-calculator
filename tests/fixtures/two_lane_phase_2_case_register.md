# Two-Lane Highway Phase 2 case register

All records below are `method_conformance_case`, not published HCM examples.
They are transparent non-example inputs exercised in
`tests/unit/test_two_lane_phase_2_envelope.py`.

| ID | Purpose | Inputs / independent checks | Sources | Status |
| --- | --- | --- | --- | --- |
| P2-PC-C2..C5 | Passing Constrained nonlevel Classes 2--5 | 0.5 mi, 3/5/6/7% upgrade; Exhibit 15-11 produces Classes 2/3/4/5; 800/0.95 demand; capacity 1,700; opposing flow 1,500. | Exhibits 15-10, 15-11; Eq. 15-1; Ch. 15 capacity text | active |
| P2-PZ-D4 | Passing Zone downgrade | 0.5 mi, -7%, 475 veh/h opposing at PHF .95; independent opposing demand = 500 veh/h and Exhibit 15-11 Class 4. | Exhibits 15-10, 15-11; Eq. 15-1 | active |
| P2-HC-3 | arbitrary horizontal structure | Three subsegments 1,000/800/840 ft total 2,640 ft = 0.5 mi; 800 ft, 2% curve is Exhibit 15-22 Class 2. | Eq. 15-12--15-16; Exhibit 15-22 | active |
| P2-CAP | capacity boundaries | volume 0, 1,615, 1,615.1 with PHF .95 gives d/c 0, 1.0, >1.0; no demand clamping. | Eq. 15-1; Ch. 15 capacity text | active |
