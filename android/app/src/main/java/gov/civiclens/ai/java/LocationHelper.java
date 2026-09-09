package gov.civiclens.ai.java;

import android.content.Context;
import android.location.Location;
import android.location.LocationManager;

/**
 * Pure Java helper for retrieving GPS coordinates on Android.
 */
public class LocationHelper {

    public interface LocationCallback {
        void onLocationFound(double latitude, double longitude);
        void onError(String message);
    }

    public static void getLastKnownLocation(Context context, LocationCallback callback) {
        try {
            LocationManager locationManager = (LocationManager) context.getSystemService(Context.LOCATION_SERVICE);
            if (locationManager == null) {
                callback.onError("LocationManager unavailable");
                return;
            }

            // Fallback default coordinates (New Delhi) if emulator has no GPS lock
            Location gpsLocation = null;
            try {
                gpsLocation = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            } catch (SecurityException ignored) {}

            if (gpsLocation != null) {
                callback.onLocationFound(gpsLocation.getLatitude(), gpsLocation.getLongitude());
            } else {
                callback.onLocationFound(28.6139, 77.2090);
            }
        } catch (Exception e) {
            callback.onError(e.getMessage());
        }
    }
}
