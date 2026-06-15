package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*
import com.example.bookwiseapp.data.local.TokenStore

class AuthRepository : BaseRepository() {

    suspend fun login(username: String, password: String): Result<AuthResponse> {
        val result = safeCall(
            call = { ApiClient.service.login(LoginRequest(username, password)) },
            errorField = { it.error },
            successCheck = { it.success }
        )
        if (result.isSuccess) {
            result.getOrNull()?.token?.let { TokenStore.instance.saveToken(it) }
        }
        return result
    }

    suspend fun register(
        username: String, password: String, confirmPassword: String,
        name: String, email: String, address: String
    ): Result<AuthResponse> {
        val result = safeCall(
            call = {
                ApiClient.service.register(
                    RegisterRequest(username, password, confirmPassword, name, email, address)
                )
            },
            errorField = { it.error },
            successCheck = { it.success }
        )
        if (result.isSuccess) {
            result.getOrNull()?.token?.let { TokenStore.instance.saveToken(it) }
        }
        return result
    }

    suspend fun logout(): Result<SimpleResponse> {
        val result = safeCall(
            call = { ApiClient.service.logout() },
            errorField = { it.error },
            successCheck = { it.success }
        )
        TokenStore.instance.clearToken()
        return result
    }

    suspend fun me(): Result<MeResponse> = safeCall(
        call = { ApiClient.service.me() },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
