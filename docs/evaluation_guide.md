# Evaluation & Evidence Guide (For Member 4)

## Scenario Context: 300 Schools District Education Office
- **Scale**: 300 schools generating educational visual aids every month.
- **Monthly Volume**: Estimated 5,000 requests/month across all schools.
- **Distribution**:
  - 60% Coloring worksheets & simple outlines (3,000 images)
  - 25% Classroom flashcards & handouts (1,250 images)
  - 10% Presentation slides (500 images)
  - 5% Official posters & banners (250 images)

---

## Benchmark Comparison: Legacy Baseline vs. Resource-Aware Engine

### 1. The Legacy Baseline (The Cause of the Cloud Bill Surge)
The legacy tool treated every request identically:
- Requested `dall-e-3-hd` at 1024x1792 resolution.
- Cost per image: **$0.080**.
- Total monthly district bill:
  $$\text{Baseline} = 5,000 \times \$0.080 = \mathbf{\$400.00 / \text{month}}$$

### 2. The Resource-Aware Decision Engine
- **Coloring worksheets (3,000 images)**: Standard tier ($0.040) $\rightarrow \$120.00$
- **Flashcards & handouts (1,250 images)**: Standard tier ($0.040) $\rightarrow \$50.00$
- **Slides (500 images)**: Standard tier ($0.040) $\rightarrow \$20.00$
- **Posters & banners (250 images)**: HD tier retained ($0.080) $\rightarrow \$20.00$
- **Total Resource-Aware Bill**:
  $$\text{Optimized} = \$120 + \$50 + \$20 + \$20 = \mathbf{\$210.00 / \text{month}}$$

### 3. Net Quantifiable Savings
- **Monthly Savings**: **$190.00 / month (47.5% bill reduction)**.
- **Annual Savings across 300 schools**: **$2,280.00 / year**.
- **Visual Fitness**: Coloring sheets are crisp black & white line-art (ideal for student photocopiers and crayons) rather than shaded, color-saturated art that wastes printer toner.

---

## Test Verification Checklist for Member 4
1. Run automated pytest suite to ensure all decision thresholds are strictly deterministic.
2. Submit 10 sample prompt combinations covering each `intended_use` category.
3. Compare generated outputs between `mode=baseline` and `mode=optimized`.
4. Validate that cost savings metrics accurately reflect the verified pricing tiers.
