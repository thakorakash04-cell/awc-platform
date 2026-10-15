# Photo assessment and product matching

The third (camera) workspace now supports up to three dated images of one wound, from JPEG/PNG uploads or camera capture. A single photo also works. Replace rejected low-quality images; select and confirm each wound-bed crop. Multiple captures must be different photos of the same wound with distinct dates in chronological order. Colours are local pixel observations and include unclassified pixels; neither colours nor a general-purpose AI description establish wound type, infection, depth, exudate volume, tissue viability or healing.

Photo comparisons show clinically entered cm² values only. No area is derived from pixels, no depth is inferred from a photograph, and the system does not label changes as healing. The displayed percentage is the arithmetic change between the first and last entered measurements. Image orientation is corrected and EXIF metadata removed; visible identifying details must still be excluded by the user.

## Clinical confirmation and matching

Location, wound type, exudate level, clinical goal, depth, vascular/infection status, allergies and product precautions require clinical assessment. A confirmation checkbox resets when images, dates, measurements or clinical fields change. Emergency flags stop matching. Cavity/tunnelling, uncertain depth and infection/vascular concerns require specialist assessment through the clinical pathway; the image workflow withholds candidates in these cases. Product candidates come from the existing local AWCare formulary using exact confirmed criteria. This path never silently relaxes the selected goal if no match exists. Photos and AI descriptions never directly prescribe products.

The formerly failing cavity-packing rule now assigns a self-contained composite as the filler’s secondary cover, rather than leaving the cover absent or adding a duplicate primary layer. Other clinical rules and contraindication filtering remain in place.

## Optional Gemini description

Local analysis works without an API key. To enable the optional description, add `GEMINI_API_KEY` in Streamlit Secrets, or enter a key in the password field for that session. `WOUND_VISION_MODEL` selects the model (default `gemini-2.5-flash`). Use a compatible Gemini image-understanding model with generateContent and structured JSON output support. API availability, access and quota depend on the provider account.

Nothing is sent automatically. A user with assessment-tool permission must explicitly authorise the provider upload and press Describe latest crop with AI. Only a resized, re-encoded JPEG of the latest confirmed crop is sent to Google. Case reference, clinical fields, earlier photos and database credentials are not sent. The model is asked only for visible appearance/colours and limitations; extra diagnosis/product fields, blocked/incomplete responses and invalid schemas are rejected. A general-purpose model is not a trained or clinically validated wound diagnostic model. Provider privacy/data-use terms apply; the user must be authorised to share the cropped image. Real provider access was not tested with a live API key; API tests use mocked responses.

## Private follow-up records

Save confirmed assessment to my history is explicit. Use a de-identified wound reference, not a patient name or hospital ID. Saved records contain capture dates, entered areas, colour fractions and confirmed clinical selections. Raw images, original filenames, API keys and AI text are excluded. Records are owner-scoped in `awc_wound_assessments` in the existing PostgreSQL database, persist across restarts and cannot be read through another account, including the administrator account. Access requires the existing use_tools permission. Normal account logs record a generic tool event, not assessment contents. Re-upload photos when you want another visual comparison; saved history does not retain photographs.

## Reference and implementation boundary

Smith+Nephew WOUND COMPASS is used as a workflow reference for guided assessment by location/type/appearance/exudate/depth, specialist escalation and customer-formulary matching. Its public description does not establish a photo-only diagnostic model. This repository does not contain, decompile or reproduce its APK, proprietary model, images or recommendation content. No affiliation, equivalent validation or clinical accuracy is claimed.

- Official WOUND COMPASS overview: https://www.smith-nephew.com/en/health-care-professionals/products/advanced-wound-management/clinical-support-app
- Official launch/workflow description: https://www.smith-nephew.com/en/news/2022/07/12/20220712-sn-launches-clinical-support-app-to-help-reduce-practice-variation-in-wound-care
- Google image understanding: https://ai.google.dev/gemini-api/docs/image-understanding
- Google generateContent API: https://ai.google.dev/api/generate-content
- Google structured output: https://ai.google.dev/gemini-api/docs/structured-output

Validation: `python -m pytest tests -q`. Synthetic images and mocked API responses test the software behavior; they do not validate performance on clinical wound images.
