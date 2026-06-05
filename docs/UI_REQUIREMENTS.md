# UI Requirements

## UI Concept

The planned interface is a single-page guided worksheet optimized for engineering data entry. It should help users enter, review, calculate, and export an auditable analysis without navigating a multi-page wizard.

## Initial Facility Focus

- HCM 7th Edition Chapter 15 Two-Lane Highway motorized vehicle analysis

## Future Facility Support

The worksheet should be designed so additional facility types can be selected in the future, including Multilane Highway LOS, without changing the calculation engine boundary.

## Layout Requirements

- Single-page worksheet, not a multi-page wizard.
- Facility selector near the top of the page.
- Input sections grouped by engineering topic.
- Clear display of assumptions and units.
- Calculation summary visible after inputs are entered.
- Expandable audit details for intermediate values.
- Validation status or warnings clearly separated from final outputs.

## Planned Input Groups For Chapter 15

- Project and scenario metadata
- Facility classification and segment context
- Traffic demand and directional distribution
- Heavy vehicle and grade inputs
- Speed and geometric inputs
- Passing constraints and adjustment factors

These groups are placeholders until the methodology is fully mapped.

## Interaction Requirements

- Keep users on one page.
- Use progressive disclosure for detailed audit values.
- Prefer structured numeric inputs, selectors, and checkboxes over free-form text.
- Show missing or invalid input feedback before calculation.
- Do not hide method assumptions inside UI copy.

## Dependency Requirement

Streamlit may be used as a planned optional local UI dependency. The calculation package must install and run tests without requiring Streamlit.

## Validation Gate

The UI must not be expanded beyond a basic local worksheet until calculation correctness is validated against HCM Chapter 26 example problems.
