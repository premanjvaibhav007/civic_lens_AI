import React, { useState } from "react";
import { X, Upload, MapPin, AlertCircle, CheckCircle2, Sparkles, Navigation, Camera, Loader2 } from "lucide-react";
import { api } from "../api";

const CIVIC_CATEGORIES = [
  { id: "POTHOLE", label: "Pothole / Road Cavity" },
  { id: "DAMAGED_ROAD", label: "Damaged Road / Broken Asphalt" },
  { id: "STREETLIGHT", label: "Streetlight Malfunction" },
  { id: "GARBAGE", label: "Overflowing Garbage / Dumpster" },
  { id: "OPEN_MANHOLE", label: "Open Manhole / Missing Cover (Critical)" },
  { id: "WATER_LEAKAGE", label: "Drinking Water Pipeline Leak" },
  { id: "DRAINAGE", label: "Clogged Drainage / Waterlogging" },
  { id: "FOOTPATH", label: "Broken Footpath / Pedestrian Path" },
  { id: "DAMAGED_SIGN", label: "Damaged Traffic Sign / Signal" },
  { id: "ILLEGAL_DUMPING", label: "Illegal Waste Dumping" },
  { id: "OTHER", label: "Other Public Infrastructure Issue" }
];

export function ReportIssueModal({ isOpen, onClose, onSuccess, userRole }) {
  if (!isOpen) return null;

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("POTHOLE");
  const [latitude, setLatitude] = useState("28.6328");
  const [longitude, setLongitude] = useState("77.2197");
  const [address, setAddress] = useState("Connaught Place, Central Delhi");
  const [city, setCity] = useState("New Delhi");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const [isLocating, setIsLocating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [submittedData, setSubmittedData] = useState(null);

  const handleDetectLocation = () => {
    if (!navigator.geolocation) {
      setErrorMsg("Geolocation is not supported by your browser.");
      return;
    }
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude.toFixed(6));
        setLongitude(pos.coords.longitude.toFixed(6));
        setIsLocating(false);
      },
      (err) => {
        setIsLocating(false);
        setErrorMsg("Unable to retrieve GPS coordinates: " + err.message);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (loadEvt) => {
        setImagePreview(loadEvt.target?.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");

    if (!title.trim()) {
      setErrorMsg("Please enter an issue title.");
      return;
    }

    try {
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append("title", title);
      formData.append("description", description || `${title} reported by citizen.`);
      formData.append("latitude", latitude);
      formData.append("longitude", longitude);
      formData.append("address", address);
      formData.append("city", city);
      formData.append("submission_channel", "WEB_PORTAL");

      if (imageFile) {
        formData.append("image", imageFile);
      }

      const res = await api.post("/complaints", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      setSubmittedData({
        id: res.data.id || "comp-new",
        complaint_number: res.data.complaint_number || `CIV-${Math.floor(100000 + Math.random() * 900000)}`
      });

      if (onSuccess) onSuccess();
    } catch (err) {
      console.error("Failed to submit grievance:", err);
      // Fallback submission if backend expects JSON (e.g. Spring Boot)
      try {
        const jsonPayload = {
          title,
          description: description || `${title} reported by citizen.`,
          category,
          latitude: parseFloat(latitude),
          longitude: parseFloat(longitude),
          address,
          citizenEmail: localStorage.getItem("civiclens_user") ? JSON.parse(localStorage.getItem("civiclens_user")).email : "citizen@civiclens.gov"
        };
        const resJson = await api.post("/complaints", jsonPayload);
        setSubmittedData({
          id: resJson.data.id || "comp-new",
          complaint_number: resJson.data.complaint_number || `CIV-${Math.floor(100000 + Math.random() * 900000)}`
        });
        if (onSuccess) onSuccess();
      } catch (jsonErr) {
        setErrorMsg(err.response?.data?.detail || "Failed to submit grievance. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/95 backdrop-blur z-10">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">File Public Civic Grievance</h2>
              <p className="text-xs text-slate-500">Citizen Direct Reporting Portal (React + JavaScript)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {submittedData ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-900">Grievance Registered Successfully!</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Your issue has been routed to the respective municipal department.
                </p>
                <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-xl inline-block text-left">
                  <div className="text-[11px] text-slate-400 font-mono">TRACKING REFERENCE ID</div>
                  <div className="text-base font-bold text-blue-600 font-mono">{submittedData.complaint_number}</div>
                </div>
              </div>
              <div className="pt-2">
                <button
                  onClick={onClose}
                  className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold"
                >
                  View in My Complaints
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Title */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Issue Title <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Broken water pipeline flooding street"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full text-xs px-3 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  required
                />
              </div>

              {/* Category */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full text-xs px-3 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
                >
                  {CIVIC_CATEGORIES.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Details / Severity Note</label>
                <textarea
                  placeholder="Describe the defect, location landmarks, or immediate hazard level..."
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                />
              </div>

              {/* Photo Evidence */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Photo Evidence</label>
                {imagePreview ? (
                  <div className="relative aspect-video rounded-xl overflow-hidden border border-slate-200 bg-slate-100">
                    <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                    <button
                      type="button"
                      onClick={() => {
                        setImageFile(null);
                        setImagePreview(null);
                      }}
                      className="absolute top-2 right-2 p-1.5 bg-slate-900/80 text-white rounded-lg text-xs hover:bg-slate-900"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <label className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition bg-slate-50 hover:bg-blue-50/50">
                    <Upload className="w-6 h-6 text-slate-400 mb-1" />
                    <span className="text-xs font-medium text-slate-600">Click or tap to upload photo</span>
                    <span className="text-[10px] text-slate-400 mt-0.5">JPEG, PNG, WebP up to 15MB</span>
                    <input type="file" accept="image/*" onChange={handleImageChange} className="hidden" />
                  </label>
                )}
              </div>

              {/* Location */}
              <div className="border-t border-slate-200 pt-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-700 flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5 text-blue-600" />
                    <span>Location & Coordinates</span>
                  </span>
                  <button
                    type="button"
                    onClick={handleDetectLocation}
                    disabled={isLocating}
                    className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-1 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-lg transition"
                  >
                    <Navigation className={`w-3 h-3 ${isLocating ? "animate-spin" : ""}`} />
                    <span>{isLocating ? "Detecting GPS..." : "Auto-Detect GPS"}</span>
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] text-slate-400 font-mono">LATITUDE</label>
                    <input
                      type="text"
                      value={latitude}
                      onChange={(e) => setLatitude(e.target.value)}
                      className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-400 font-mono">LONGITUDE</label>
                    <input
                      type="text"
                      value={longitude}
                      onChange={(e) => setLongitude(e.target.value)}
                      className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] text-slate-400">STREET / AREA ADDRESS</label>
                  <input
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="w-full text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 active:scale-[0.99] text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/20 transition disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Transmitting & Running AI Triage...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Submit Grievance to Municipal Department</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
