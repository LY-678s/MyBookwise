package com.example.bookwiseapp

import android.app.Application
import coil.Coil
import coil.ImageLoader
import coil.disk.DiskCache
import coil.memory.MemoryCache
import coil.request.CachePolicy
import com.example.bookwiseapp.data.local.TokenStore
import com.example.bookwiseapp.data.local.PendingPaymentStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

class BookwiseApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        TokenStore.init(this)
        PendingPaymentStore.init(this)
        runBlocking(Dispatchers.IO) {
            TokenStore.instance.loadToken()
        }

        val imageClient = OkHttpClient.Builder()
            .followRedirects(true)
            .followSslRedirects(true)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .build()

        Coil.setImageLoader(
            ImageLoader.Builder(this)
                .okHttpClient(imageClient)
                .crossfade(true)
                .diskCachePolicy(CachePolicy.ENABLED)
                .memoryCachePolicy(CachePolicy.ENABLED)
                .diskCache {
                    DiskCache.Builder()
                        .directory(cacheDir.resolve("image_cache"))
                        .maxSizePercent(0.05)
                        .build()
                }
                .memoryCache {
                    MemoryCache.Builder(this)
                        .maxSizePercent(0.25)
                        .build()
                }
                .build()
        )
    }
}
