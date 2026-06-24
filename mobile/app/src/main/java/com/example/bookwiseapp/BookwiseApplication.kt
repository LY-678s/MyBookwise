package com.example.bookwiseapp

import android.app.Application
import com.example.bookwiseapp.data.local.TokenStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking

class BookwiseApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        TokenStore.init(this)
        // 同步恢复 Token，避免 MainActivity 启动时尚未读完 DataStore
        runBlocking(Dispatchers.IO) {
            TokenStore.instance.loadToken()
        }
    }
}
