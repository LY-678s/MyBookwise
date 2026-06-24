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
     * | 公网固定域名   | https://mybookwise.xyz |
     * | 模拟器         | http://10.0.2.2:8000 |
     * | 真机同 Wi-Fi   | http://192.168.x.x:8000 |
     *
     * 公网域名需本机 cloudflared 命名隧道运行，见 README。
     */
    const val SERVER_BASE = "https://mybookwise.xyz"
    // const val SERVER_BASE = "http://10.0.2.2:8000"       // 模拟器本地
    // const val SERVER_BASE = "http://192.168.x.x:8000"  // 同 Wi-Fi 真机
    const val BASE_URL = "$SERVER_BASE/api/"

    /** 当前登录 Token（内存中），由 TokenStore 在 App 启动时恢复。*/
    var token: String? = null

    /** 将图书封面等相对路径拼成完整 URL，如 /static/images/xxx.jpg */
    fun fullImageUrl(relativePath: String?): String? {
        if (relativePath.isNullOrEmpty()) return null
        var url = if (relativePath.startsWith("http")) relativePath
        else "$SERVER_BASE$relativePath"
        // 数据库封面多为 http:// 外链；Android 9+ 默认禁止明文 HTTP 拉图
        if (url.startsWith("http://")) {
            url = "https://${url.removePrefix("http://")}"
        }
        return url
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
