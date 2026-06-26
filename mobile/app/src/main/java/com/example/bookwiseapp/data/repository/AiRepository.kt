package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*

class AiRepository : BaseRepository() {

    suspend fun getStatus(): Result<AiStatusResponse> = safeCall(
        call = { ApiClient.service.getAiStatus() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun sendMessage(message: String): Result<AiChatResponse> = safeCall(
        call = { ApiClient.aiService.sendAiMessage(AiChatRequest(message)) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun clearHistory(): Result<SimpleResponse> = safeCall(
        call = { ApiClient.service.clearAiChat() },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
