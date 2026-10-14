#!/usr/bin/env bash
# Dependency-free APK build using the official Android SDK (alternative to Gradle).
set -euo pipefail
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
android_sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
: "${android_sdk:?Set ANDROID_HOME to an Android SDK with platform 35 and build-tools 35.0.0}"
android_build_tools="${AWC_BUILD_TOOLS:-$android_sdk/build-tools/35.0.0}"
android_platform_jar="${AWC_ANDROID_JAR:-$android_sdk/platforms/android-35/android.jar}"
output_dir="$project_dir/app/build/manual"
mkdir -p "$output_dir/classes" "$output_dir/dex"
rm -f "$output_dir/resources.zip" "$output_dir/unsigned.apk" "$output_dir/aligned.apk"
"$android_build_tools/aapt2" compile --dir "$project_dir/app/src/main/res" -o "$output_dir/resources.zip"
# Gradle injects the package; standalone aapt2 needs it in a generated manifest.
python3 - "$project_dir/app/src/main/AndroidManifest.xml" "$output_dir/AndroidManifest.xml" <<'PYCODE'
import sys
from pathlib import Path
Path(sys.argv[2]).write_text(Path(sys.argv[1]).read_text().replace('<manifest ', '<manifest package="com.awc.offline" ', 1))
PYCODE
"$android_build_tools/aapt2" link -I "$android_platform_jar" --manifest "$output_dir/AndroidManifest.xml" -A "$project_dir/app/src/main/assets" --min-sdk-version 26 --target-sdk-version 35 --version-code 1 --version-name 1.0.0 -o "$output_dir/unsigned.apk" "$output_dir/resources.zip"
find "$project_dir/app/src/main/java" -name '*.java' > "$output_dir/sources.txt"
if [[ -n "${AWC_ECJ:-}" ]]; then
    java -jar "$AWC_ECJ" -8 -classpath "$android_platform_jar" -d "$output_dir/classes" @"$output_dir/sources.txt"
else
    javac -source 8 -target 8 -classpath "$android_platform_jar" -d "$output_dir/classes" @"$output_dir/sources.txt"
fi
find "$output_dir/classes" -name '*.class' > "$output_dir/classes.txt"
"$android_build_tools/d8" --lib "$android_platform_jar" --min-api 26 --output "$output_dir/dex" @"$output_dir/classes.txt"
(cd "$output_dir/dex" && zip -q "$output_dir/unsigned.apk" classes*.dex)
"$android_build_tools/zipalign" -f -p 4 "$output_dir/unsigned.apk" "$output_dir/aligned.apk"
# Development key stays outside the repository. This output is for direct device testing.
awc_debug_key="${AWC_DEBUG_KEY:-$HOME/.android/debug.keystore}"
if [[ ! -f "$awc_debug_key" ]]; then
    mkdir -p "$(dirname "$awc_debug_key")"
    keytool -genkeypair -keystore "$awc_debug_key" -storepass android -keypass android -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -dname 'CN=Android Debug,O=Android,C=US' >/dev/null 2>&1
fi
"$android_build_tools/apksigner" sign --ks "$awc_debug_key" --ks-pass pass:android --key-pass pass:android --out "$output_dir/AWC-Offline-v1.0.0-test.apk" "$output_dir/aligned.apk"
"$android_build_tools/apksigner" verify --verbose "$output_dir/AWC-Offline-v1.0.0-test.apk"
echo "APK: $output_dir/AWC-Offline-v1.0.0-test.apk"
