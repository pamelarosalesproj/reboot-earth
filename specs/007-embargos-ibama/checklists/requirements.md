# Specification Quality Checklist: Embargos del IBAMA como respaldo cuando MapBiomas no los determina

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-08
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Las tres decisiones que afectan nivel y privacidad (cobertura solo IBAMA, todos vigentes, umbral
  0,1 ha) se confirmaron con la responsable el 2026-11-08 antes de escribir la spec: no quedan
  marcadores de clarificación.
- Se nombran las fuentes (MapBiomas, IBAMA) porque son parte del producto (principio VII: la UI
  indica la base de cada dato), no detalles de implementación. El endpoint, el formato de consulta
  y el cálculo de superposición quedan para `plan.md`/`research.md`.
- "En un único lugar del backend" (FR-702) refleja el principio IV de la constitución, igual que en
  la spec 006.
