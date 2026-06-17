package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*

class OrderRepository : BaseRepository() {

    suspend fun preview(): Result<PreviewResponse> = safeCall(
        call = { ApiClient.service.orderPreview() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun listOrders(): Result<OrdersResponse> = safeCall(
        call = { ApiClient.service.listOrders() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun createOrder(
        paymentChoice: String,
        shippingName: String,
        shippingContact: String,
        shippingAddress: String
    ): Result<OrderResponse> = safeCall(
        call = {
            ApiClient.service.createOrder(
                CreateOrderRequest(paymentChoice, shippingName, shippingContact, shippingAddress)
            )
        },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun getOrder(orderId: Int): Result<OrderResponse> = safeCall(
        call = { ApiClient.service.getOrder(orderId) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun payOrder(orderId: Int): Result<OrderResponse> = safeCall(
        call = { ApiClient.service.payOrder(orderId) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun cancelOrder(orderId: Int): Result<OrderResponse> = safeCall(
        call = { ApiClient.service.cancelOrder(orderId) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun confirmReceipt(orderId: Int): Result<OrderResponse> = safeCall(
        call = { ApiClient.service.confirmReceipt(orderId) },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
