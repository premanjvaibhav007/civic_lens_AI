package gov.civiclens.ai.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import gov.civiclens.ai.data.local.ComplaintDraft
import gov.civiclens.ai.data.repository.CivicRepository
import gov.civiclens.ai.domain.model.ComplaintDetail
import gov.civiclens.ai.domain.model.ComplaintItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File

class ComplaintViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = CivicRepository(application)

    // My complaints
    private val _myComplaints = MutableStateFlow<List<ComplaintItem>>(emptyList())
    val myComplaints: StateFlow<List<ComplaintItem>> = _myComplaints.asStateFlow()

    // Nearby complaints
    private val _nearbyComplaints = MutableStateFlow<List<ComplaintItem>>(emptyList())
    val nearbyComplaints: StateFlow<List<ComplaintItem>> = _nearbyComplaints.asStateFlow()

    // Active detail
    private val _selectedComplaint = MutableStateFlow<ComplaintDetail?>(null)
    val selectedComplaint: StateFlow<ComplaintDetail?> = _selectedComplaint.asStateFlow()

    // Loading & error
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _statusMessage = MutableStateFlow<String?>(null)
    val statusMessage: StateFlow<String?> = _statusMessage.asStateFlow()

    // Report Flow Form State
    var draftImageFile: File? = null
    var draftTitle: String = ""
    var draftDescription: String = ""
    var draftLatitude: Double = 28.6328
    var draftLongitude: Double = 77.2197
    var draftAddress: String = "Connaught Place, New Delhi"
    var draftCity: String = "New Delhi"
    var draftCategoryId: String? = null

    init {
        loadMyComplaints()
        loadNearbyComplaints(draftLatitude, draftLongitude)
    }

    fun loadMyComplaints() {
        viewModelScope.launch {
            _isLoading.value = true
            val res = repository.getMyComplaints()
            res.onSuccess {
                _myComplaints.value = it
            }
            _isLoading.value = false
        }
    }

    fun loadNearbyComplaints(lat: Double, lng: Double) {
        viewModelScope.launch {
            val res = repository.getNearbyComplaints(lat, lng)
            res.onSuccess {
                _nearbyComplaints.value = it
            }
        }
    }

    fun loadComplaintDetail(id: String) {
        viewModelScope.launch {
            _isLoading.value = true
            val res = repository.getComplaintDetail(id)
            res.onSuccess {
                _selectedComplaint.value = it
            }
            _isLoading.value = false
        }
    }

    fun submitCurrentDraft(onComplete: (Boolean) -> Unit) {
        viewModelScope.launch {
            _isLoading.value = true
            val res = repository.submitComplaint(
                title = draftTitle,
                description = draftDescription,
                categoryId = draftCategoryId,
                latitude = draftLatitude,
                longitude = draftLongitude,
                address = draftAddress,
                city = draftCity,
                imageFile = draftImageFile
            )

            _isLoading.value = false
            res.onSuccess {
                _statusMessage.value = "Complaint submitted! AI Triage scheduled."
                loadMyComplaints()
                onComplete(true)
            }.onFailure { err ->
                _statusMessage.value = err.message
                onComplete(false)
            }
        }
    }

    fun verifyResolution(complaintId: String, isResolved: Boolean, rating: Int?, feedback: String?, reopenReason: String?, onComplete: () -> Unit) {
        viewModelScope.launch {
            _isLoading.value = true
            val res = repository.verifyResolution(complaintId, isResolved, rating, feedback, reopenReason)
            _isLoading.value = false
            res.onSuccess {
                loadComplaintDetail(complaintId)
                loadMyComplaints()
                onComplete()
            }
        }
    }

    fun clearStatusMessage() {
        _statusMessage.value = null
    }
}
