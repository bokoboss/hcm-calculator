# Localization acceptance matrix

| Area | Evidence |
| --- | --- |
| Catalogs | `test_localization.py` checks `en`/`th` key, placeholder, and blank-value parity. |
| Locale state | Session `ui_locale` defaults to English; selector is before calculator forms. |
| Canonical calculations | Locale is absent from normalized inputs and fingerprints; protected method suite remains unchanged. |
| Projects | Optional schema-1.2 `presentation.locale`; saved locale restores; legacy omission retains UI locale. |
| JSON | Canonical keys, enum values, numbers, nulls, method/version fields retained; presentation locale added. |
| CSV / Excel / Markdown | Same-as-UI, English, and Thai selection; Thai Excel/Markdown covered by targeted tests. |
| Thai terminology | Reviewed glossary in `engineering_terminology_glossary.md`; abbreviations and units preserved. |
| Constraints | No method engines, equations, exhibit data, thresholds, or supported domains changed. |
