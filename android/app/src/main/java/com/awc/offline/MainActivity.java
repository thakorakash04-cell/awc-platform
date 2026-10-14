package com.awc.offline;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.*;
import android.widget.Toast;
import java.io.*;

/** Entire application is bundled locally. No INTERNET permission or remote fallback. */
public class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final int PICK_IMAGE = 10, CAMERA = 11;
    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private final Uri cameraUri = Uri.parse("content://com.awc.offline.photos/capture.jpg");
    private static final int MAX_IMAGE_BYTES = 20 * 1024 * 1024;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(244,246,248));
        setContentView(web);
        web.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                    insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets.consumeSystemWindowInsets();
        });
        web.requestApplyInsets();
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setBlockNetworkLoads(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !isLocal(request.getUrl());
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (!isLocal(uri)) return response("text/plain", new ByteArrayInputStream(new byte[0]), 403);
                String path = uri.getPath().substring("/assets/".length());
                if (path.contains("..") || path.contains("\\")) return response("text/plain", new ByteArrayInputStream(new byte[0]),403);
                try {
                    String mime = path.endsWith(".html") ? "text/html" : path.endsWith(".js") ? "application/javascript" : path.endsWith(".css") ? "text/css" : path.endsWith(".png") ? "image/png" : "application/octet-stream";
                    return response(mime,getAssets().open(path),200);
                } catch (IOException e) { return response("text/plain",new ByteArrayInputStream(new byte[0]),404); }
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);
                try { startActivityForResult(intent, PICK_IMAGE); }
                catch (Exception e) { callback.onReceiveValue(null); fileCallback = null; Toast.makeText(MainActivity.this,"No photo picker available",Toast.LENGTH_LONG).show(); }
                return true;
            }
        });
        web.addJavascriptInterface(new CameraBridge(), "AWCNative");
        web.loadUrl("https://" + HOST + "/assets/index.html");
    }
    private boolean isLocal(Uri uri) {
        return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost()) && uri.getPath() != null && uri.getPath().startsWith("/assets/");
    }
    private WebResourceResponse response(String mime, InputStream stream, int status) {
        java.util.Map<String,String> headers = new java.util.HashMap<>();
        headers.put("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'none'; object-src 'none'; base-uri 'none'");
        return new WebResourceResponse(mime,"UTF-8",status,status == 200 ? "OK" : "Blocked",headers,stream);
    }
    public final class CameraBridge {
        @JavascriptInterface public void takePhoto() {
            runOnUiThread(() -> {
                Intent intent = new Intent("android.media.action.IMAGE_CAPTURE");
                intent.putExtra("output", cameraUri);
                intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                intent.setClipData(ClipData.newRawUri("Wound photo", cameraUri));
                try { startActivityForResult(intent, CAMERA); }
                catch (Exception e) { Toast.makeText(MainActivity.this,"Camera unavailable. Use Choose photo instead.",Toast.LENGTH_LONG).show(); }
            });
        }
    }
    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request,result,data);
        if (request == PICK_IMAGE) {
            if (fileCallback != null) { fileCallback.onReceiveValue(result == RESULT_OK && data != null && data.getData() != null ? new Uri[]{data.getData()} : null); fileCallback = null; }
        }
        if (request == CAMERA && result == RESULT_OK) {
            // Decode on a worker thread, limit payload, and delete the temporary camera file.
            new Thread(() -> {
                File capture = new File(getCacheDir(),"capture.jpg");
                try {
                    if (capture.length() > MAX_IMAGE_BYTES) throw new IOException("Photo exceeds 20 MB. Choose a smaller photo.");
                    byte[] bytes = java.nio.file.Files.readAllBytes(capture.toPath());
                    String encoded = android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP);
                    runOnUiThread(() -> web.evaluateJavascript("window.receiveCameraPhoto('data:image/jpeg;base64," + encoded + "')",null));
                } catch (Exception e) { runOnUiThread(() -> Toast.makeText(this,"Could not read camera photo; use Choose photo.",Toast.LENGTH_LONG).show()); }
                finally { capture.delete(); }
            }).start();
        }
        if (request == CAMERA && result != RESULT_OK) new File(getCacheDir(),"capture.jpg").delete();
    }
    @Override public void onBackPressed() { web.evaluateJavascript("window.handleAndroidBack()", value -> { if (!"true".equals(value)) finish(); }); }
    @Override protected void onDestroy() {
        if (fileCallback != null) fileCallback.onReceiveValue(null);
        web.removeJavascriptInterface("AWCNative"); web.destroy();
        new File(getCacheDir(),"capture.jpg").delete();
        super.onDestroy();
    }
}
