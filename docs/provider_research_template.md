# Provider Research & Capabilities Template (For Member 3)

This checklist standardizes the technical capabilities, pricing facts, and integration parameters for any proposed image generation provider.

---

## 1. Provider Candidate Information
- **Provider Name**: (e.g., OpenAI, Stability AI, Google Cloud Vertex Imagen, AWS Bedrock Titan)
- **Model Name / Version**: (e.g., `dall-e-3`, `stable-diffusion-xl-1024-v1-0`, `imagen-3.0`)
- **Official Documentation URL**:

---

## 2. Supported Configuration Levers
*Note: Only levers that directly reduce billed cost or GPU runtime should be configured as cost-saving.*

| Lever | Supported? (Yes/No) | Allowed Options | Does it reduce billed cost? | Official Pricing Difference |
|---|---|---|---|---|
| **Quality Tier** | Yes / No | e.g. `standard`, `hd` | Yes / No | e.g. $0.040 vs $0.080 |
| **Resolution** | Yes / No | e.g. 512x512, 1024x1024, 1024x1792 | Yes / No | e.g. $0.040 vs $0.080 |
| **Inference Steps** | Yes / No | e.g. 10 to 50 | Yes / No | e.g. $0.018 vs $0.035 |
| **Color Mode Filter** | Yes / No | Prompt-based or parameter? | No (Prompt-based) | Improves output fitness, not cost |

---

## 3. Authentication & Environment Secrets
- **Required Environment Variable(s)**: (e.g. `OPENAI_API_KEY`, `STABILITY_API_KEY`)
- **Rate Limits (RPM / TPM)**:
- **Default Timeout Needed**: (e.g., 30s)

---

## 4. Grounded Pricing Evidence Reference
Link to published pricing table (e.g., OpenAI API pricing page, Stability Platform billing table).
Do not guess or assume discounts.
