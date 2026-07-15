# Engineering terminology glossary

Arabic numerals, decimal points, US customary engineering units, equation
symbols, and established abbreviations (LOS, FFS, PHF, PCE, SAF, CAF) are
retained in both locales. Thai uses the abbreviation on prominent use.

| Concept | Canonical English | Approved Thai | Abbreviation / unit | Note |
| --- | --- | --- | --- | --- |
| HCM | Highway Capacity Manual | คู่มือความจุทางหลวง | HCM | Official publication title remains English in citations. |
| Method / analysis | Method / Analysis | วิธีการ / การวิเคราะห์ | — | Do not treat a method ID as display text. |
| Segment / facility | Segment / Facility | ช่วงถนน / สิ่งอำนวยความสะดวก | — | Never conflate segment with facility. |
| Direction | Direction | ทิศทาง | — | Directional inputs are not facility outputs. |
| Traffic volume | Traffic volume | ปริมาณจราจร | veh/h | Distinct from demand flow rate. |
| Demand flow rate | Demand flow rate | อัตราการไหลความต้องการ | pc/h/ln | Adjusted engineering flow. |
| Capacity | Capacity | ความจุ | pc/h/ln | Keep base and adjusted capacity separate. |
| Demand-to-capacity ratio | Demand-to-capacity ratio | อัตราส่วนความต้องการต่อความจุ | v/c | Not a capacity status. |
| Free-flow speed | Free-flow speed | ความเร็วการไหลอิสระ | FFS, mi/h | Measured, estimated, base, and adjusted are distinct. |
| Mean / average travel speed | Mean speed / Average travel speed | ความเร็วเฉลี่ย / ความเร็วเดินทางเฉลี่ย | mi/h | Method-specific output names are retained. |
| Density | Density | ความหนาแน่น | pc/mi/ln | Never use for follower density. |
| Follower density | Follower density | ความหนาแน่นของรถตาม | fol/mi/ln | Two-Lane measure only. |
| LOS | Level of service | ระดับการให้บริการ | LOS | Keep letter grade unchanged. |
| PHF | Peak-hour factor | ตัวคูณชั่วโมงเร่งด่วน | PHF | Unitless. |
| PCE | Passenger-car equivalent | ค่าเทียบเท่ารถยนต์นั่ง | PCE | Separate internal and external sources. |
| Heavy-vehicle factor | Heavy-vehicle factor | ตัวคูณปรับยานพาหนะหนัก | — | Not PCE itself. |
| Grade / length | Grade / Segment length | ความชัน / ความยาวช่วงถนน | %, mi | Preserve US units in this release. |
| Lane / clearance | Lane width / Lateral clearance | ความกว้างช่องจราจร / ระยะเคลียร์ด้านข้าง | ft | Left and right remain distinct. |
| Median / access | Median / Access-point density | เกาะกลาง / ความหนาแน่นจุดเข้าออก | access points/mi | TWLTL is not a divided median. |
| Passing terms | Passing lane / zone / no-passing zone | ช่องแซง / เขตแซง / เขตห้ามแซง | — | Passing restrictions affect Two-Lane analysis. |
| Alignment | Vertical alignment / Horizontal curve | แนวทางดิ่ง / โค้งราบ | — | Do not conflate curve and grade. |
| Multilane | Divided / undivided highway | ทางหลวงแบ่งทิศทาง / ไม่แบ่งทิศทาง | — | TWLTL remains explicitly named. |
| Freeway factors | Speed / capacity adjustment factor | ตัวคูณปรับความเร็ว / ความจุ | SAF / CAF | Preserve SAF and CAF abbreviations. |
| Specific grade | Specific grade / upgrade / downgrade | ความชันเฉพาะ / ทางขึ้น / ทางลง | % | Grade domain is method-limited. |
| Audit context | Assumption / warning / limitation / provenance | ข้อสมมติ / คำเตือน / ข้อจำกัด / ที่มา | — | Provenance text is not machine-translated. |
| Lookup | Lookup path / interpolation | เส้นทางการค้นตาราง / การแทรกค่า | — | Retain source/exhibit identifiers. |
| Status | Result is stale / recalculation required | ผลลัพธ์ไม่เป็นปัจจุบัน / ต้องคำนวณใหม่ | — | Locale switching alone never creates this status. |
| Prediction | Not predicted / demand exceeds capacity | ไม่มีการพยากรณ์ค่า / ความต้องการเกินความจุ | — | Absent prediction is never zero. |
| Export | Export blocked | การส่งออกถูกระงับ | — | Current result is required. |
