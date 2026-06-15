package com.example.bookwiseapp

import android.app.Application
import com.example.bookwiseapp.data.local.TokenStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class BookwiseApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        // 初始化 TokenStore，并从 DataStore 恢复 Token 到内存
        TokenStore.init(this)
        CoroutineScope(Dispatchers.IO).launch {
            TokenStore.instance.loadToken()
        }
    }
}
