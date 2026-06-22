package com.example.bookwiseapp.data.api

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {

    /**
     * 服务器地址（改这一处即可）。
     *
     * | 场景           | 示例 |
     * |----------------|------|
     * | 模拟器         | http://10.0.2.2:8000 |
     * | 真机同 Wi-Fi   | http://192.168.x.x:8000 |
     * | 跨网（cloudflared） | https://xxxx.trycloudflare.com |
     *
     * 跨网步骤见项目根 README「跨网访问」。
     */
    // const val SERVER_BASE = "https://xxxx.trycloudflare.com"  // 跨网穿透时用 https
    const val SERVER_BASE = "http://10.16.206.195:8000"
    const val BASE_URL = "$SERVER_BASE/api/"

    /** 当前登录 Token（内存中），由 TokenStore 在 App 启动时恢复。*/
    var token: String? = null

    /** 将图书封面等相对路径拼成完整 URL，如 /static/images/xxx.jpg */
    fun fullImageUrl(relativePath: String?): String? {
        if (relativePath.isNullOrEmpty()) return null
        return if (relativePath.startsWith("http")) relativePath
        else "$SERVER_BASE$relativePath"
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
