# AWC Offline for Android

Installable, completely local Android port of the repository's active Streamlit workflows. Android 8.0+ (API 26). No server, API key, sign-in, or INTERNET permission. Assets and JavaScript are served from the APK at an intercepted local HTTPS origin, with remote navigation and network loads blocked.

## Included

- Clinician assessment: the active AWCare Excel filtering pipeline, dynamic indications, primary/secondary product metadata and all product precautions.
- Patient/caregiver guide: five emergency flags, diabetes/chronic-duration escalation, wound/drainage/goal matching.
- Searchable 23-product catalog, full specifications and comparison of up to four products.
- On-device image quality checks, central-region red/yellow/black colour overlay, gallery selection and full-resolution camera capture.
- Reference product and indication images bundled during development; no image downloads at runtime.
- Offline architecture/help content, mobile navigation, Android back handling.

The Streamlit application is unchanged. The mobile code ports the **active** `app.py` views and `core/awc_rules_engine.py`; it does not enable the unused older catalog/rules engine. Product-specific precautions are shown, not converted into patient-specific diagnoses. Full third-party guideline documents are not bundled. The original regulatory-compliance claims are not represented as mobile-app certification. Clinician access is not identity/credential verification.

## Deliberate fixes during porting

- Safety review is required before showing assessment matches, and photo matches require explicit human confirmation.
- A zero-pixel segmentation returns 'no colour classes identified', rather than inventing 100% red tissue.
- Image colour is not used to automatically infer fluid amount or treatment goal. These are selected manually.
- Every matching product is rendered, including entries without a primary/secondary designation.
- Precautions from all product records are aggregated, rather than taking only the first record.
- Broadened matches explicitly disclose all relaxed filters, including healing phase.
- Patient emergency text directs to the nearest emergency department without the source's US-only phone number.

## Build a test APK

Install JDK 17, Python 3, zip and the official Android SDK with platform 35 and build-tools 35.0.0. Set `ANDROID_HOME` to that SDK.

```bash
android/tools/build-apk.sh
```

Output: `android/app/build/manual/AWC-Offline-v1.0.0-test.apk`. The script uses a development signing key at `~/.android/debug.keystore`; it is never committed. Keep that key if you need future APKs to install as updates. Test builds from separate environments may require uninstalling the old APK before installation.

Alternatively open `android/` in Android Studio, or run `cd android && ./gradlew assembleDebug` with a working Android SDK. Gradle configuration and wrapper are supplied; this delivery was built and signature-verified using the standalone SDK script.

The `Build offline Android APK` workflow runs on the feature branch, pull requests, main/master changes and manual dispatch. Download `AWC-Offline-Android-test` from the workflow's artifacts. These are test packages, not Play Store releases. For production distribution, use a private release signing key in Android Studio's Generate Signed Bundle/APK flow and preserve it for future updates. No release signing credentials are bundled.

## Install and verify on a phone

1. Download the APK to an Android 8.0+ device and allow installation from that download source when Android prompts.
2. Install and open AWC Offline. Enable airplane mode and restart the app to verify first-launch offline operation.
3. Review the safety checklist, select clinical filters and check product matches.
4. Check that emergency flags immediately replace matches with referral messaging.
5. Search and compare products. Choose/take a photo, review the quality gate and manually confirm clinical parameters.
6. Clear the photo or leave the tab. Camera capture creates a temporary private file that is deleted after reading; the app keeps no patient history.

Phone installation, camera-provider behavior and device WebView rendering require physical-device testing. Photo quality thresholds are inherited heuristics; resize to a maximum 1600-pixel edge changes sharpness scores on very large photos. Image segmentation is not validated diagnostic AI and cannot establish infection, perfusion, depth or tissue viability. Clinical content must be reviewed by the responsible clinical team before clinical deployment.

## Catalog maintenance

From repository root:

```bash
python android/tools/export_catalog.py
python android/tools/bundle_images.py
python android/tools/check_catalog.py
```

Image bundling is a build-time operation requiring access to the source images. The APK uses a snapshot of `data/AWCare_Merged.xlsx`; update and rebuild to change content. Missing downloads are recorded as empty image references without introducing online runtime fallback.

## Tests

```bash
python android/tools/generate_parity.py /tmp/awc-parity.json
node android/tools/test_engine.cjs /tmp/awc-parity.json
python android/tools/check_catalog.py
```

The parity suite includes 676 reference queries against Python, plus triage/quality/segmentation edge cases. For browser UI verification, install Playwright in your development environment and run `node android/tools/test_ui.cjs`; set `AWC_CHROMIUM` if using an existing Chromium binary. The test covers mobile viewports, emergency stops, catalog search/comparison, photo confirmation, back navigation and zero remote requests.
