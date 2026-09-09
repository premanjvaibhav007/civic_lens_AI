package gov.civiclens.ai.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import gov.civiclens.ai.data.repository.CivicRepository
import gov.civiclens.ai.domain.model.UserSummary
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    data class Authenticated(val user: UserSummary) : AuthState()
    data class Error(val message: String) : AuthState()
}

class AuthViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = CivicRepository(application)

    private val _authState = MutableStateFlow<AuthState>(AuthState.Idle)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()

    fun login(email: String, pass: String) {
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            val result = repository.login(email, pass)
            result.onSuccess { user ->
                _authState.value = AuthState.Authenticated(user)
            }.onFailure { err ->
                _authState.value = AuthState.Error(err.message ?: "Authentication failed")
            }
        }
    }

    fun register(name: String, email: String, pass: String, phone: String?, city: String?) {
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            val result = repository.register(name, email, pass, phone, city)
            result.onSuccess { user ->
                _authState.value = AuthState.Authenticated(user)
            }.onFailure { err ->
                _authState.value = AuthState.Error(err.message ?: "Registration failed")
            }
        }
    }

    fun resetState() {
        _authState.value = AuthState.Idle
    }
}
