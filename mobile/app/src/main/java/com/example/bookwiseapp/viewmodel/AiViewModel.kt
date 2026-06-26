package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.AiMessage
import com.example.bookwiseapp.data.repository.AiRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class AiUiState(
    val isLoading: Boolean = false,
    val isSending: Boolean = false,
    val aiConfigured: Boolean = false,
    val messages: List<AiMessage> = emptyList(),
    val error: String? = null
)

class AiViewModel : ViewModel() {

    private val repo = AiRepository()

    private val _state = MutableStateFlow(AiUiState())
    val state: StateFlow<AiUiState> = _state

    fun loadStatus() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.getStatus()
            if (result.isSuccess) {
                val body = result.getOrNull()!!
                _state.value = AiUiState(
                    aiConfigured = body.aiConfigured,
                    messages = body.history
                )
            } else {
                _state.value = AiUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun sendMessage(text: String) {
        val trimmed = text.trim()
        if (trimmed.isEmpty() || _state.value.isSending) return

        viewModelScope.launch {
            val userMsg = AiMessage(role = "user", content = trimmed)
            _state.value = _state.value.copy(
                isSending = true,
                error = null,
                messages = _state.value.messages + userMsg
            )

            val result = repo.sendMessage(trimmed)
            if (result.isSuccess) {
                val reply = result.getOrNull()?.reply.orEmpty()
                _state.value = _state.value.copy(
                    isSending = false,
                    messages = _state.value.messages + AiMessage(role = "assistant", content = reply)
                )
            } else {
                _state.value = _state.value.copy(
                    isSending = false,
                    error = result.exceptionOrNull()?.message,
                    messages = _state.value.messages.dropLast(1)
                )
            }
        }
    }

    fun clearHistory() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.clearHistory()
            if (result.isSuccess) {
                _state.value = _state.value.copy(isLoading = false, messages = emptyList())
            } else {
                _state.value = _state.value.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun clearError() {
        _state.value = _state.value.copy(error = null)
    }

    fun resetSession() {
        _state.value = AiUiState()
    }
}
