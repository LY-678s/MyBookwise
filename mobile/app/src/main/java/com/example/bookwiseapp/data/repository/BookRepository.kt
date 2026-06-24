package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*

class BookRepository : BaseRepository() {

    suspend fun listBooks(page: Int = 1, pageSize: Int = 12, refresh: Boolean = false): Result<BooksResponse> = safeCall(
        call = { ApiClient.service.listBooks(page, pageSize, if (refresh) 1 else null) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun searchBooks(query: String): Result<SearchResponse> = safeCall(
        call = { ApiClient.service.searchBooks(query) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun getBook(isbn: String): Result<BookDetailResponse> = safeCall(
        call = { ApiClient.service.getBook(isbn) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun getCategories(
        category: String? = null,
        sort: String = "title",
        page: Int = 1
    ): Result<CategoriesResponse> = safeCall(
        call = { ApiClient.service.getCategories(category, sort, page) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun getRankings(): Result<RankingsResponse> = safeCall(
        call = { ApiClient.service.getRankings() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun toggleFavorite(isbn: String, folderId: Int? = null): Result<FavoriteToggleResponse> = safeCall(
        call = { ApiClient.service.toggleFavorite(isbn, FavoriteToggleRequest(folderId)) },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
