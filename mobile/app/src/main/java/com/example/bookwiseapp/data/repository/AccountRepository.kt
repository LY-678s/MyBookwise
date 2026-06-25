package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*
import com.example.bookwiseapp.util.StripeDeepLink

class AccountRepository : BaseRepository() {

    suspend fun getAccount(): Result<AccountResponse> = safeCall(
        call = { ApiClient.service.getAccount() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun updateAccount(
        name: String, email: String, address: String,
        currentPassword: String? = null,
        newPassword: String? = null,
        confirmPassword: String? = null
    ): Result<AccountResponse> = safeCall(
        call = {
            ApiClient.service.updateAccount(
                UpdateAccountRequest(name, email, address, currentPassword, newPassword, confirmPassword)
            )
        },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun createMembershipCheckout(): Result<MembershipCheckoutResponse> = safeCall(
        call = {
            ApiClient.service.createMembershipCheckout(
                MembershipCheckoutRequest(
                    successUrl = StripeDeepLink.membershipSuccessUrl(),
                    cancelUrl = StripeDeepLink.membershipCancelUrl()
                )
            )
        },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun activateMembership(): Result<AccountResponse> = safeCall(
        call = { ApiClient.service.activateMembership() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun confirmPayment(sessionId: String): Result<PaymentConfirmResponse> = safeCall(
        call = { ApiClient.service.confirmPayment(PaymentConfirmRequest(sessionId)) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun getBrowseHistory(): Result<BrowseHistoryResponse> = safeCall(
        call = { ApiClient.service.getBrowseHistory() },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
