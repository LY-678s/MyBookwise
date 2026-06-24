package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*

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

    suspend fun recharge(amount: String): Result<AccountResponse> = safeCall(
        call = { ApiClient.service.recharge(RechargeRequest(amount)) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun repay(): Result<AccountResponse> = safeCall(
        call = { ApiClient.service.repay() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun getBrowseHistory(): Result<BrowseHistoryResponse> = safeCall(
        call = { ApiClient.service.getBrowseHistory() },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
