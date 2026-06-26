package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.FavoriteFolderCard
import com.example.bookwiseapp.data.repository.FavoriteRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class FavoriteUiState(
    val isLoading: Boolean = false,
    val folders: List<FavoriteFolderCard> = emptyList(),
    val totalCount: Int = 0,
    val message: String? = null,
    val error: String? = null
)

class FavoriteViewModel : ViewModel() {

    private val repo = FavoriteRepository()

    private val _state = MutableStateFlow(FavoriteUiState())
    val state: StateFlow<FavoriteUiState> = _state

    fun loadFolders() {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.getFolders()
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _state.value = FavoriteUiState(
                    folders = data.folders ?: emptyList(),
                    totalCount = data.totalCount ?: 0
                )
            } else {
                _state.value = FavoriteUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun createFolder(name: String) {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.createFolder(name)
            if (result.isSuccess) {
                loadFolders()
                _state.value = _state.value.copy(
                    message = result.getOrNull()?.message ?: "创建成功"
                )
            } else {
                _state.value = _state.value.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun deleteFolder(folderId: Int) {
        viewModelScope.launch {
            _state.value = _state.value.copy(isLoading = true, error = null)
            val result = repo.deleteFolder(folderId)
            if (result.isSuccess) {
                loadFolders()
                _state.value = _state.value.copy(
                    message = result.getOrNull()?.message ?: "已删除"
                )
            } else {
                _state.value = _state.value.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun clearMessage() {
        _state.value = _state.value.copy(message = null)
    }

    fun resetSession() {
        _state.value = FavoriteUiState()
    }
}
