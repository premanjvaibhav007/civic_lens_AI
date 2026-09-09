import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import L from "leaflet";
import { ComplaintListItem } from "../types";
import { Sparkles, MapPin, Eye } from "lucide-react";

// Fix default Leaflet marker icons in React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const createCustomIcon = (severity: string) => {
  let color = "#3b82f6";
  if (severity === "CRITICAL") color = "#ef4444";
  else if (severity === "HIGH") color = "#f97316";
  else if (severity === "MEDIUM") color = "#eab308";

  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2.5px solid white; box-shadow: 0 0 8px ${color};"></div>`,
    className: "custom-map-pin",
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

interface MapViewProps {
  complaints: ComplaintListItem[];
  onSelectComplaint: (id: string) => void;
}

export const MapView: React.FC<MapViewProps> = ({ complaints, onSelectComplaint }) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");

  const validComplaints = complaints.filter(
    (c) => c.latitude !== undefined && c.longitude !== undefined && (selectedSeverity ? c.severity === selectedSeverity : true)
  );

  const centerLat = validComplaints.length > 0 && validComplaints[0].latitude ? validComplaints[0].latitude : 28.6328;
  const centerLng = validComplaints.length > 0 && validComplaints[0].longitude ? validComplaints[0].longitude : 77.2197;

  return (
    <div className="space-y-4">
      {/* Map Control Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Geospatial Issue Density & GIS Hotspots</h1>
          <p className="text-xs text-slate-500">Live spatial mapping of {validComplaints.length} localized civic complaints</p>
        </div>

        {/* Severity Legend & Filter */}
        <div className="flex items-center space-x-2 text-xs">
          <button
            onClick={() => setSelectedSeverity("")}
            className={`px-3 py-1.5 rounded-full font-semibold transition-all ${
              !selectedSeverity ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            All
          </button>
          <button
            onClick={() => setSelectedSeverity("CRITICAL")}
            className={`px-3 py-1.5 rounded-full font-semibold transition-all flex items-center space-x-1 ${
              selectedSeverity === "CRITICAL" ? "bg-red-600 text-white" : "bg-red-50 text-red-700 border border-red-200"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            <span>Critical</span>
          </button>
          <button
            onClick={() => setSelectedSeverity("HIGH")}
            className={`px-3 py-1.5 rounded-full font-semibold transition-all flex items-center space-x-1 ${
              selectedSeverity === "HIGH" ? "bg-orange-600 text-white" : "bg-orange-50 text-orange-700 border border-orange-200"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
            <span>High</span>
          </button>
          <button
            onClick={() => setSelectedSeverity("MEDIUM")}
            className={`px-3 py-1.5 rounded-full font-semibold transition-all flex items-center space-x-1 ${
              selectedSeverity === "MEDIUM" ? "bg-yellow-600 text-white" : "bg-yellow-50 text-yellow-700 border border-yellow-200"
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
            <span>Medium</span>
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden h-[620px]">
        <MapContainer
          center={[centerLat, centerLng]}
          zoom={13}
          scrollWheelZoom={true}
          className="w-full h-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {validComplaints.map((c) => (
            <React.Fragment key={c.id}>
              {c.severity === "CRITICAL" && (
                <Circle
                  center={[c.latitude!, c.longitude!]}
                  radius={120}
                  pathOptions={{ color: "#ef4444", fillColor: "#ef4444", fillOpacity: 0.15 }}
                />
              )}
              <Marker
                position={[c.latitude!, c.longitude!]}
                icon={createCustomIcon(c.severity)}
              >
                <Popup className="custom-popup">
                  <div className="p-1 space-y-2 text-xs max-w-xs">
                    <div className="flex items-center justify-between font-mono text-[10px] text-slate-500 font-bold">
                      <span>{c.complaint_number}</span>
                      <span className="text-emerald-600">{c.category_name}</span>
                    </div>
                    <p className="font-bold text-slate-900 text-xs">{c.title}</p>
                    <p className="text-slate-500 text-[11px] truncate">{c.address || c.city}</p>
                    <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                      <span className="font-semibold text-[10px] text-slate-700">Status: {c.status}</span>
                      <button
                        onClick={() => onSelectComplaint(c.id)}
                        className="bg-emerald-600 text-white text-[10px] font-bold px-2 py-1 rounded hover:bg-emerald-500 transition-colors flex items-center space-x-1"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Inspect</span>
                      </button>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};
