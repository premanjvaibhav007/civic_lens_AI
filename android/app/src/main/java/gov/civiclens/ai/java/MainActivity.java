package gov.civiclens.ai.java;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Standard Java Android Activity for CivicLens AI.
 * Demonstrates the Citizen Complaint submission and live tracking flow in pure Java.
 */
public class MainActivity extends Activity {

    private EditText etTitle;
    private EditText etDescription;
    private TextView tvStatus;
    private Button btnSubmit;
    private Button btnRefresh;

    private final CivicLensApiClient apiClient = new CivicLensApiClient();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Programmatic UI layout so it compiles and runs without XML dependency issues
        android.widget.LinearLayout layout = new android.widget.LinearLayout(this);
        layout.setOrientation(android.widget.LinearLayout.VERTICAL);
        layout.setPadding(40, 60, 40, 40);

        TextView tvHeader = new TextView(this);
        tvHeader.setText("🏛️ CivicLens AI - Java Citizen App");
        tvHeader.setTextSize(20);
        tvHeader.setTypeface(null, android.graphics.Typeface.BOLD);
        layout.addView(tvHeader);

        TextView tvSub = new TextView(this);
        tvSub.setText("Connected to Python FastAPI & Java Spring Boot Backends");
        tvSub.setTextSize(12);
        tvSub.setPadding(0, 8, 0, 30);
        layout.addView(tvSub);

        etTitle = new EditText(this);
        etTitle.setHint("Issue Title (e.g. Hazardous Road Pothole)");
        layout.addView(etTitle);

        etDescription = new EditText(this);
        etDescription.setHint("Description & Landmark Details");
        layout.addView(etDescription);

        btnSubmit = new Button(this);
        btnSubmit.setText("Submit Grievance to Municipal Crew");
        btnSubmit.setPadding(0, 20, 0, 20);
        layout.addView(btnSubmit);

        btnRefresh = new Button(this);
        btnRefresh.setText("Check Live Authority Work Status");
        layout.addView(btnRefresh);

        tvStatus = new TextView(this);
        tvStatus.setText("Ready to report civic grievances.");
        tvStatus.setPadding(0, 30, 0, 0);
        tvStatus.setTextSize(13);
        layout.addView(tvStatus);

        setContentView(layout);

        // Set up click listeners
        btnSubmit.setOnClickListener(v -> submitComplaint());
        btnRefresh.setOnClickListener(v -> checkComplaintStatus());
    }

    private void submitComplaint() {
        String title = etTitle.getText().toString().trim();
        String desc = etDescription.getText().toString().trim();

        if (title.isEmpty()) {
            Toast.makeText(this, "Please enter an issue title", Toast.LENGTH_SHORT).show();
            return;
        }

        tvStatus.setText("Submitting grievance and executing AI triage...");
        btnSubmit.setEnabled(false);

        LocationHelper.getLastKnownLocation(this, new LocationHelper.LocationCallback() {
            @Override
            public void onLocationFound(double lat, double lng) {
                ComplaintModel model = new ComplaintModel(title, desc, "POTHOLE", lat, lng);
                model.setAddress("Reported via Android Java Client");

                apiClient.submitComplaint(model, new CivicLensApiClient.ApiCallback<String>() {
                    @Override
                    public void onSuccess(String result) {
                        mainHandler.post(() -> {
                            btnSubmit.setEnabled(true);
                            tvStatus.setText("✅ Grievance Registered!\n\nAI Status: ROUTED_TO_DEPARTMENT\nResponse: " + result);
                            Toast.makeText(MainActivity.this, "Complaint submitted successfully!", Toast.LENGTH_LONG).show();
                            etTitle.setText("");
                            etDescription.setText("");
                        });
                    }

                    @Override
                    public void onError(Exception error) {
                        mainHandler.post(() -> {
                            btnSubmit.setEnabled(true);
                            tvStatus.setText("❌ Submission failed: " + error.getMessage());
                        });
                    }
                });
            }

            @Override
            public void onError(String message) {
                mainHandler.post(() -> {
                    btnSubmit.setEnabled(true);
                    tvStatus.setText("Location error: " + message);
                });
            }
        });
    }

    private void checkComplaintStatus() {
        tvStatus.setText("Fetching active authority progress from server...");
        apiClient.fetchComplaints("citizen@civiclens.gov", new CivicLensApiClient.ApiCallback<String>() {
            @Override
            public void onSuccess(String result) {
                mainHandler.post(() -> {
                    tvStatus.setText("📋 Live Municipal Grievance Feed:\n" + result);
                });
            }

            @Override
            public void onError(Exception error) {
                mainHandler.post(() -> {
                    tvStatus.setText("Failed to load status: " + error.getMessage());
                });
            }
        });
    }
}
