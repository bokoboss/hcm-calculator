# v0.6.1 - Weaving configuration reference images

This maintenance release adds configuration reference images to the qualified HCM
7.0 Freeway Weaving Segment worksheet. Calculation logic, numerical outputs,
project schema, exports, and calculation fingerprints are unchanged.

## Authorized asset source

The repository owner authorized project reuse of the image assets from
[`bokoboss/hcm7-weaving-segments`](https://github.com/bokoboss/hcm7-weaving-segments),
source commit `8bcdf89038329fbdc46dac286733d6d18f9f3504`.

| Legacy asset | Meaning | Current UI state | Reuse decision |
| --- | --- | --- | --- |
| `one-side.png` | General one-sided weaving configuration, including ramp and major coding context | Displayed for both deterministic one-sided subtypes | Reused unchanged as `src/hcmcalc/ui/assets/weaving/one_sided_weave.png` |
| `two-side.png` | General two-sided weaving configuration | Displayed for the qualified two-sided subtype | Reused unchanged as `src/hcmcalc/ui/assets/weaving/two_sided_weave.png` |
| No distinct major/ramp, option-lane, or entry/exit-side variants | Not present in the legacy repository | No unsupported image variants shown | Not created or inferred from imagery |
| Design/Sensitivity controls and examples | Legacy application concepts, not image assets needed by the qualified worksheet | Not exposed | Not reused |

The legacy assets are repository PNG files, not embedded content. No legacy
JavaScript, formulas, or numerical logic was copied.

## UI behavior and mapping

The reference appears below primary configuration geometry and updates as those
controls change. It is visible before calculation and remains visible after a
calculation or while a result is stale.

| Qualified coded geometry | Presentation subtype | Asset |
| --- | --- | --- |
| `one_sided`, `NWL=3` | One-sided major weave | `one_sided_weave.png` |
| `one_sided`, `NWL=2` | One-sided ramp weave | `one_sided_weave.png` |
| `two_sided`, `NWL=0` | Two-sided weave | `two_sided_weave.png` |
| Other/incomplete values | Neutral prompt | none |

The `NWL` mapping is presentation-only and is derived from the existing qualified
geometry; it is not a new engine input or a duplicate source of truth. The former
inline SVG schematic is replaced in the worksheet by the owner-authorized legacy
PNG reference because the PNGs provide the useful engineering configuration
context users need.

## Accessibility and limits

Each diagram has a bilingual title, visible bilingual conceptual-reference
caption, text-only interpretation, movement legend (FF/FR/RF/RR), and current
coded geometry summary including `N`, `NWL`, entry/exit sides, and lane-change
values. The image is a coding aid, not scaled geometry or CAD; entered values
remain authoritative. The legacy repository has no distinct option-lane or
entry/exit-side image variants, so those conditions remain visible in the coded
summary rather than being represented by a misleading image.

The assets are packaged with the UI package and resolved locally with package
resources. No runtime checkout, legacy repository, or internet dependency exists.
