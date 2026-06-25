package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*
import com.example.bookwiseapp.util.StripeDeepLink

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
        shippingName: String,
        shippingContact: String,
        shippingAddress: String
    ): Result<OrderResponse> = safeCall(
        call = {
            ApiClient.service.createOrder(
                CreateOrderRequest(
                    shippingName = shippingName,
                    shippingContact = shippingContact,
                    shippingAddress = shippingAddress,
                    successUrl = StripeDeepLink.orderSuccessUrl(),
                    cancelUrl = StripeDeepLink.orderCancelUrl()
                )
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

    suspend fun abandonOrder(orderId: Int): Result<SimpleResponse> = safeCall(
        call = { ApiClient.service.abandonOrder(orderId) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun confirmPayment(sessionId: String): Result<PaymentConfirmResponse> = safeCall(
        call = { ApiClient.service.confirmPayment(PaymentConfirmRequest(sessionId)) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun syncOrderPayment(orderId: Int): Result<PaymentConfirmResponse> = safeCall(
        call = { ApiClient.service.syncOrderPayment(orderId) },
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
