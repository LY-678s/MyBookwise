package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*

class BookRepository : BaseRepository() {

    suspend fun listBooks(): Result<BooksResponse> = safeCall(
        call = { ApiClient.service.listBooks() },
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
}
