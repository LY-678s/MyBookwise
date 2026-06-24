package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.BookData
import com.example.bookwiseapp.data.api.model.CustomerData
import com.example.bookwiseapp.data.repository.AccountRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class AccountUiState(
    val isLoading: Boolean = false,
    val account: CustomerData? = null,
    val message: String? = null,
    val error: String? = null
)

data class BrowseHistoryUiState(
    val isLoading: Boolean = false,
    val books: List<BookData> = emptyList(),
    val defaultCoverUrl: String = "",
    val error: String? = null
)

class AccountViewModel : ViewModel() {

    private val repo = AccountRepository()

    private val _state = MutableStateFlow(AccountUiState())
    val state: StateFlow<AccountUiState> = _state

    private val _browseHistoryState = MutableStateFlow(BrowseHistoryUiState())
    val browseHistoryState: StateFlow<BrowseHistoryUiState> = _browseHistoryState

    fun loadAccount() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null, message = null)
            val result = repo.getAccount()
            if (result.isSuccess) {
                _state.value = AccountUiState(account = result.getOrNull()?.account)
            } else {
                _state.value = AccountUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun updateAccount(
        name: String, email: String, address: String,
        currentPassword: String? = null, newPassword: String? = null, confirmPassword: String? = null,
        onSuccess: () -> Unit
    ) {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.updateAccount(name, email, address, currentPassword, newPassword, confirmPassword)
            if (result.isSuccess) {
                _state.value = AccountUiState(
                    account = result.getOrNull()?.account,
                    message = result.getOrNull()?.message
                )
                onSuccess()
            } else {
                _state.value = _state.value.copy(isLoading = false, error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun recharge(amount: String, onSuccess: () -> Unit) {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.recharge(amount)
            if (result.isSuccess) {
                _state.value = AccountUiState(
                    account = result.getOrNull()?.account,
                    message = result.getOrNull()?.message
                )
                onSuccess()
            } else {
                _state.value = _state.value.copy(isLoading = false, error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun repay(onSuccess: () -> Unit) {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.repay()
            if (result.isSuccess) {
                _state.value = AccountUiState(
                    account = result.getOrNull()?.account,
                    message = result.getOrNull()?.message
                )
                onSuccess()
            } else {
                _state.value = _state.value.copy(isLoading = false, error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun clearMessage() {
        _state.value = _state.value.copy(message = null, error = null)
    }

    fun loadBrowseHistory() {
        viewModelScope.launch {
            _browseHistoryState.value = _browseHistoryState.value.copy(isLoading = true, error = null)
            val result = repo.getBrowseHistory()
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _browseHistoryState.value = BrowseHistoryUiState(
                    books = data.books ?: emptyList(),
                    defaultCoverUrl = data.defaultCoverUrl ?: ""
                )
            } else {
                _browseHistoryState.value = BrowseHistoryUiState(
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }
}
