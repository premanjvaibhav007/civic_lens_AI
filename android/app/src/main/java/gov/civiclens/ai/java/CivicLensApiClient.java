package gov.civiclens.ai.java;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Pure Java HTTP client for CivicLens AI Android App.
 * Connects to either:
 * - Python FastAPI backend: http://10.0.2.2:8000/api/v1
 * - Java Spring Boot backend: http://10.0.2.2:8080/api/v1
 */
public class CivicLensApiClient {

    // 10.0.2.2 is Android Emulator localhost alias
    public static final String FASTAPI_BASE_URL = "http://10.0.2.2:8000/api/v1";
    public static final String SPRINGBOOT_BASE_URL = "http://10.0.2.2:8080/api/v1";

    private String activeBaseUrl = FASTAPI_BASE_URL;
    private final ExecutorService executor = Executors.newFixedThreadPool(4);

    public interface ApiCallback<T> {
        void onSuccess(T result);
        void onError(Exception error);
    }

    public CivicLensApiClient() {}

    public void setUseSpringBoot(boolean useSpringBoot) {
        this.activeBaseUrl = useSpringBoot ? SPRINGBOOT_BASE_URL : FASTAPI_BASE_URL;
    }

    /**
     * Submit a civic complaint asynchronously in Java.
     */
    public void submitComplaint(ComplaintModel complaint, ApiCallback<String> callback) {
        executor.execute(() -> {
            try {
                URL url = new URL(activeBaseUrl + "/complaints");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json; utf-8");
                conn.setRequestProperty("Accept", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(8000);
                conn.setReadTimeout(8000);

                String jsonPayload = String.format(
                    "{\"title\":\"%s\",\"description\":\"%s\",\"category\":\"%s\",\"latitude\":%f,\"longitude\":%f,\"address\":\"%s\"}",
                    escapeJson(complaint.getTitle()),
                    escapeJson(complaint.getDescription()),
                    escapeJson(complaint.getCategory()),
                    complaint.getLatitude(),
                    complaint.getLongitude(),
                    escapeJson(complaint.getAddress())
                );

                try (OutputStream os = conn.getOutputStream()) {
                    byte[] input = jsonPayload.getBytes(StandardCharsets.UTF_8);
                    os.write(input, 0, input.length);
                }

                int code = conn.getResponseCode();
                if (code >= 200 && code < 300) {
                    String response = readStream(conn.getInputStream());
                    callback.onSuccess(response);
                } else {
                    String errResponse = readStream(conn.getErrorStream());
                    callback.onError(new IOException("HTTP " + code + ": " + errResponse));
                }
            } catch (Exception e) {
                callback.onError(e);
            }
        });
    }

    /**
     * Fetch citizen complaints.
     */
    public void fetchComplaints(String citizenEmail, ApiCallback<String> callback) {
        executor.execute(() -> {
            try {
                String endpoint = activeBaseUrl + "/complaints";
                if (citizenEmail != null && !citizenEmail.isEmpty()) {
                    endpoint += "?citizen_email=" + citizenEmail;
                }
                URL url = new URL(endpoint);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setRequestProperty("Accept", "application/json");
                conn.setConnectTimeout(8000);

                int code = conn.getResponseCode();
                if (code >= 200 && code < 300) {
                    callback.onSuccess(readStream(conn.getInputStream()));
                } else {
                    callback.onError(new IOException("HTTP " + code + ": " + readStream(conn.getErrorStream())));
                }
            } catch (Exception e) {
                callback.onError(e);
            }
        });
    }

    private String readStream(InputStream is) throws IOException {
        if (is == null) return "";
        BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }
        return sb.toString();
    }

    private String escapeJson(String s) {
        if (s == null) return "";
        return s.replace("\"", "\\\"").replace("\n", "\\n");
    }
}
