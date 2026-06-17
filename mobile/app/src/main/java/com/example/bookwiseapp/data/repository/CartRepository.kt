package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*

class CartRepository : BaseRepository() {

    suspend fun getCart(): Result<CartResponse> = safeCall(
        call = { ApiClient.service.getCart() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun addToCart(isbn: String, quantity: Int): Result<CartResponse> = safeCall(
        call = { ApiClient.service.addToCart(AddToCartRequest(isbn, quantity)) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun updateItem(isbn: String, quantity: Int): Result<CartResponse> = safeCall(
        call = { ApiClient.service.updateCartItem(isbn, UpdateCartRequest(quantity)) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun removeItem(isbn: String): Result<CartResponse> = safeCall(
        call = { ApiClient.service.removeFromCart(isbn) },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
