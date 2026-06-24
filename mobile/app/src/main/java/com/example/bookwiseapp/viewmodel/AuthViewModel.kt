package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.CustomerData
import com.example.bookwiseapp.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class AuthUiState(
    val isLoading: Boolean = false,
    val customer: CustomerData? = null,
    val error: String? = null,
    val isLoggedIn: Boolean = false
)

class AuthViewModel : ViewModel() {

    private val repo = AuthRepository()

    private val _state = MutableStateFlow(AuthUiState())
    val state: StateFlow<AuthUiState> = _state

    fun login(username: String, password: String, onSuccess: () -> Unit) {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.login(username, password)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _state.value = _state.value.copy(
                    isLoading = false, customer = data.customer, isLoggedIn = true
                )
                onSuccess()
            } else {
                _state.value = _state.value.copy(
                    isLoading = false, error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun register(
        username: String, password: String, confirmPassword: String,
        name: String, email: String, address: String,
        onSuccess: () -> Unit
    ) {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.register(username, password, confirmPassword, name, email, address)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _state.value = _state.value.copy(
                    isLoading = false, customer = data.customer, isLoggedIn = true
                )
                onSuccess()
            } else {
                _state.value = _state.value.copy(
                    isLoading = false, error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun logout(onSuccess: () -> Unit) {
        viewModelScope.launch {
            repo.logout()
            _state.value = AuthUiState()
            onSuccess()
        }
    }

    fun clearError() {
        _state.value = _state.value.copy(error = null)
    }

    /** 启动时根据本地 Token 恢复登录；无效则清除。*/
    suspend fun tryRestoreSession(): Boolean {
        if (ApiClient.token.isNullOrBlank()) return false
        val result = repo.me()
        return if (result.isSuccess) {
            val customer = result.getOrNull()?.customer
            _state.value = _state.value.copy(customer = customer, isLoggedIn = true)
            true
        } else {
            repo.clearLocalSession()
            _state.value = AuthUiState()
            false
        }
    }
}
