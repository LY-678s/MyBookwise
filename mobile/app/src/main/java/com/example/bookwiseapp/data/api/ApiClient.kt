package com.example.bookwiseapp.data.api

import com.example.bookwiseapp.BuildConfig
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {

    /**
     * 服务器根地址，来自 [mobile/settings.properties] 的 `server_base`。
     * 首次克隆请：`copy settings.properties.example settings.properties` 后修改。
     */
    val SERVER_BASE: String = BuildConfig.SERVER_BASE
    val BASE_URL: String = "$SERVER_BASE/api/"

    var token: String? = null

    /** 将相对路径拼成完整 URL；封面请走 bookCoverUrl()。 */
    fun fullImageUrl(relativePath: String?): String? {
        if (relativePath.isNullOrEmpty()) return null
        return if (relativePath.startsWith("http")) relativePath
        else "$SERVER_BASE$relativePath"
    }

    /** 图书封面代理地址（优先 API 返回的 cover_image_url，否则按 ISBN 拼接）。 */
    fun bookCoverUrl(isbn: String, coverImageUrl: String? = null): String? {        if (isbn.isBlank()) return null
        val path = if (!coverImageUrl.isNullOrBlank() && coverImageUrl.contains("/cover/")) {
            coverImageUrl
        } else {
            "/api/books/$isbn/cover/"
        }
        return fullImageUrl(path)
    }

    private val authInterceptor = Interceptor { chain ->
        val req = chain.request().newBuilder().apply {
            token?.let { addHeader("Authorization", "Token $it") }
        }.build()
        chain.proceed(req)
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .build()

    val service: ApiService = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(ApiService::class.java)
}
