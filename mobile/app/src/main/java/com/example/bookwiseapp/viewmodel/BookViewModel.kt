package com.example.bookwiseapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.bookwiseapp.data.api.model.BookData
import com.example.bookwiseapp.data.api.model.CategoryItem
import com.example.bookwiseapp.data.api.model.FavoriteFolderData
import com.example.bookwiseapp.data.api.model.RankingSection
import com.example.bookwiseapp.data.repository.BookRepository
import com.example.bookwiseapp.data.repository.FavoriteRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val isLoading: Boolean = false,
    val isLoadingMore: Boolean = false,
    val isRefreshing: Boolean = false,
    val books: List<BookData> = emptyList(),
    val defaultCoverUrl: String = "",
    val hasMore: Boolean = false,
    val error: String? = null
)

data class BookDetailUiState(
    val isLoading: Boolean = false,
    val book: BookData? = null,
    val defaultCoverUrl: String = "",
    val isFavorited: Boolean = false,
    val favoriteCount: Int = 0,
    val favoriteFolderId: Int? = null,
    val favoriteFolders: List<FavoriteFolderData> = emptyList(),
    val favoriteMessage: String? = null,
    val favoriteLoading: Boolean = false,
    val error: String? = null
)

data class CategoriesUiState(
    val isLoading: Boolean = false,
    val categories: List<CategoryItem> = emptyList(),
    val books: List<BookData> = emptyList(),
    val selectedCategory: String = "",
    val sort: String = "title",
    val currentPage: Int = 1,
    val totalPages: Int = 1,
    val error: String? = null
)

data class RankingsUiState(
    val isLoading: Boolean = false,
    val sections: List<RankingSection> = emptyList(),
    val error: String? = null
)

data class SearchUiState(
    val isLoading: Boolean = false,
    val inputQuery: String = "",
    val activeQuery: String = "",
    val books: List<BookData> = emptyList(),
    val recentSearches: List<String> = emptyList(),
    val error: String? = null
)

class BookViewModel : ViewModel() {

    private val repo = BookRepository()
    private val favoriteRepo = FavoriteRepository()
    private val pageSize = 12
    private var nextPage = 1

    private val _homeState = MutableStateFlow(HomeUiState())
    val homeState: StateFlow<HomeUiState> = _homeState

    private val _searchState = MutableStateFlow(SearchUiState())
    val searchState: StateFlow<SearchUiState> = _searchState

    private val _detailState = MutableStateFlow(BookDetailUiState())
    val detailState: StateFlow<BookDetailUiState> = _detailState

    private val _categoriesState = MutableStateFlow(CategoriesUiState())
    val categoriesState: StateFlow<CategoriesUiState> = _categoriesState

    private val _rankingsState = MutableStateFlow(RankingsUiState())
    val rankingsState: StateFlow<RankingsUiState> = _rankingsState

    fun ensureHomeFeedLoaded() {
        val state = _homeState.value
        if (state.books.isNotEmpty() || state.isLoading || state.isRefreshing) return
        loadBooks()
    }

    fun loadBooks() {
        viewModelScope.launch {
            _homeState.value = _homeState.value.copy(isLoading = true, error = null)
            nextPage = 1
            val result = repo.listBooks(page = 1, pageSize = pageSize)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                nextPage = 2
                _homeState.value = HomeUiState(
                    books = data.books ?: emptyList(),
                    defaultCoverUrl = data.defaultCoverUrl ?: "",
                    hasMore = data.hasMore ?: false
                )
            } else {
                _homeState.value = HomeUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun refreshBooks() {
        val state = _homeState.value
        if (state.isRefreshing || state.isLoading) return
        viewModelScope.launch {
            _homeState.value = state.copy(isRefreshing = true, error = null)
            nextPage = 1
            val result = repo.listBooks(page = 1, pageSize = pageSize, refresh = true)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                nextPage = 2
                _homeState.value = HomeUiState(
                    books = data.books ?: emptyList(),
                    defaultCoverUrl = data.defaultCoverUrl ?: "",
                    hasMore = data.hasMore ?: false
                )
            } else {
                _homeState.value = state.copy(
                    isRefreshing = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun loadMoreBooks() {
        val state = _homeState.value
        if (state.isLoading || state.isLoadingMore || state.isRefreshing || !state.hasMore) return
        viewModelScope.launch {
            _homeState.value = state.copy(isLoadingMore = true, error = null)
            val result = repo.listBooks(page = nextPage, pageSize = pageSize)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                nextPage += 1
                _homeState.value = state.copy(
                    isLoadingMore = false,
                    books = state.books + (data.books ?: emptyList()),
                    hasMore = data.hasMore ?: false
                )
            } else {
                _homeState.value = state.copy(
                    isLoadingMore = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun loadSearchLanding() {
        val state = _searchState.value
        if (state.isLoading || state.activeQuery.isNotBlank()) return
        viewModelScope.launch {
            _searchState.value = state.copy(isLoading = true, error = null)
            val result = repo.searchBooks("")
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _searchState.value = state.copy(
                    isLoading = false,
                    recentSearches = data.recentSearches ?: emptyList()
                )
            } else {
                _searchState.value = state.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun updateSearchInput(query: String) {
        _searchState.value = _searchState.value.copy(inputQuery = query)
    }

    fun searchBooks(query: String) {
        val trimmed = query.trim()
        if (trimmed.isBlank()) return
        viewModelScope.launch {
            _searchState.value = _searchState.value.copy(
                isLoading = true,
                error = null,
                inputQuery = trimmed,
                activeQuery = trimmed
            )
            val result = repo.searchBooks(trimmed)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _searchState.value = SearchUiState(
                    inputQuery = trimmed,
                    activeQuery = trimmed,
                    books = data.books ?: emptyList(),
                    recentSearches = data.recentSearches ?: emptyList()
                )
            } else {
                _searchState.value = _searchState.value.copy(
                    isLoading = false,
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun clearSearchInput() {
        val state = _searchState.value
        if (state.activeQuery.isNotBlank()) {
            _searchState.value = SearchUiState(
                inputQuery = "",
                recentSearches = state.recentSearches
            )
            loadSearchLanding()
            return
        }
        _searchState.value = state.copy(inputQuery = "")
    }

    fun clearSearchHistory() {
        viewModelScope.launch {
            val result = repo.clearSearchHistory()
            if (result.isSuccess) {
                _searchState.value = _searchState.value.copy(recentSearches = emptyList())
            } else {
                _searchState.value = _searchState.value.copy(
                    error = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun loadBookDetail(isbn: String) {
        viewModelScope.launch {
            _detailState.value = _detailState.value.copy(isLoading = true, error = null)
            val result = repo.getBook(isbn)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _detailState.value = BookDetailUiState(
                    book = data.book,
                    defaultCoverUrl = data.defaultCoverUrl ?: "",
                    isFavorited = data.isFavorited ?: false,
                    favoriteCount = data.favoriteCount ?: 0,
                    favoriteFolderId = data.favoriteFolderId,
                    favoriteFolders = data.favoriteFolders ?: emptyList()
                )
            } else {
                _detailState.value = BookDetailUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun toggleFavorite(isbn: String, folderId: Int? = null) {
        viewModelScope.launch {
            val state = _detailState.value
            _detailState.value = state.copy(favoriteLoading = true, favoriteMessage = null)
            val result = repo.toggleFavorite(isbn, folderId)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _detailState.value = state.copy(
                    favoriteLoading = false,
                    isFavorited = data.isFavorited ?: false,
                    favoriteCount = data.favoriteCount ?: state.favoriteCount,
                    favoriteFolderId = data.folderId,
                    favoriteMessage = data.message
                )
            } else {
                _detailState.value = state.copy(
                    favoriteLoading = false,
                    favoriteMessage = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun createFavoriteFolder(name: String, onCreated: (FavoriteFolderData) -> Unit) {
        viewModelScope.launch {
            val state = _detailState.value
            _detailState.value = state.copy(favoriteLoading = true, favoriteMessage = null)
            val result = favoriteRepo.createFolder(name)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                val folder = data.folder
                if (folder != null) {
                    val updatedFolders = state.favoriteFolders + folder
                    _detailState.value = state.copy(
                        favoriteLoading = false,
                        favoriteFolders = updatedFolders,
                        favoriteMessage = data.message
                    )
                    onCreated(folder)
                } else {
                    _detailState.value = state.copy(favoriteLoading = false)
                }
            } else {
                _detailState.value = state.copy(
                    favoriteLoading = false,
                    favoriteMessage = result.exceptionOrNull()?.message
                )
            }
        }
    }

    fun ensureCategoriesLoaded() {
        val state = _categoriesState.value
        if (state.categories.isNotEmpty() || state.isLoading) return
        loadCategories()
    }

    fun loadCategories(category: String? = null, sort: String = "title", page: Int = 1) {
        viewModelScope.launch {
            _categoriesState.value = _categoriesState.value.copy(isLoading = true, error = null)
            val result = repo.getCategories(category, sort, page)
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _categoriesState.value = CategoriesUiState(
                    categories = data.categories ?: emptyList(),
                    books = data.books ?: emptyList(),
                    selectedCategory = data.selectedCategory ?: "",
                    sort = data.sort ?: sort,
                    currentPage = data.currentPage ?: page,
                    totalPages = data.totalPages ?: 1
                )
            } else {
                _categoriesState.value = CategoriesUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun loadRankings() {
        viewModelScope.launch {
            _rankingsState.value = _rankingsState.value.copy(isLoading = true, error = null)
            val result = repo.getRankings()
            if (result.isSuccess) {
                val data = result.getOrNull()!!
                _rankingsState.value = RankingsUiState(sections = data.sections ?: emptyList())
            } else {
                _rankingsState.value = RankingsUiState(error = result.exceptionOrNull()?.message)
            }
        }
    }

    fun resetSession() {
        nextPage = 1
        _homeState.value = HomeUiState()
        _searchState.value = SearchUiState()
        _detailState.value = BookDetailUiState()
        _categoriesState.value = CategoriesUiState()
        _rankingsState.value = RankingsUiState()
    }
}
