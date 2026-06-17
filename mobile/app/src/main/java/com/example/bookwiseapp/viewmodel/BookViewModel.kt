package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.BookData
import com.example.bookwiseapp.data.repository.BookRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val isLoading: Boolean = false,
    val books: List<BookData> = emptyList(),
    val defaultCoverUrl: String = "",
    val error: String? = null
)

data class BookDetailUiState(
    val isLoading: Boolean = false,
    val book: BookData? = null,
    val defaultCoverUrl: String = "",
    val error: String? = null
)

class BookViewModel : ViewModel() {

    private val repo = BookRepository()

    private val _homeState = MutableStateFlow(HomeUiState())
    val homeState: StateFlow<HomeUiState> = _homeState

    // 搜索复用 homeState 的 books 字段
    private val _searchState = MutableStateFlow(HomeUiState())
    val searchState: StateFlow<HomeUiState> = _searchState

    private val _detailState = MutableStateFlow(BookDetailUiState())
    val detailState: StateFlow<BookDetailUiState> = _detailState

    fun loadBooks() {
        viewModelScope.launch {
            _homeState.value = _homeState.value.copy(isLoading = true, error = null)
            val result = repo.listBooks()
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _homeState.value = HomeUiState(
                    books = data.books ?: emptyList(),
                    defaultCoverUrl = data.defaultCoverUrl ?: ""
                )
            } else {
                _homeState.value = HomeUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun searchBooks(query: String) {
        viewModelScope.launch {
            _searchState.value = _searchState.value.copy(isLoading = true, error = null)
            val result = repo.searchBooks(query)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _searchState.value = HomeUiState(books = data.books ?: emptyList())
            } else {
                _searchState.value = HomeUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun loadBookDetail(isbn: String) {
        viewModelScope.launch {
            _detailState.value = BookDetailUiState(isLoading = true)
            val result = repo.getBook(isbn)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _detailState.value = BookDetailUiState(
                    book = data.book,
                    defaultCoverUrl = data.defaultCoverUrl ?: ""
                )
            } else {
                _detailState.value = BookDetailUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }
}
