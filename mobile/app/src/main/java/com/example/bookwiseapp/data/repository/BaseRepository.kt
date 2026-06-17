package com.example.bookwiseapp.data.repository

import retrofit2.Response

/** 统一解析 Retrofit 响应，处理 HTTP 错误和业务错误。*/
abstract class BaseRepository {

    protected suspend fun <T> safeCall(
        call: suspend () -> Response<T>,
        errorField: (T) -> String?,
        successCheck: (T) -> Boolean = { true }
    ): Result<T> {
        return try {
            val response = call()
            if (response.isSuccessful) {
                val body = response.body()
                    ?: return Result.failure(Exception("响应体为空"))
                if (successCheck(body)) {
                    Result.success(body)
                } else {
                    Result.failure(Exception(errorField(body) ?: "操作失败"))
                }
            } else {
                Result.failure(Exception("服务器错误 ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(Exception("网络错误：${e.message}"))
        }
    }
}
