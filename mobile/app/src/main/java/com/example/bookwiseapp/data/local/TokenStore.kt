package com.example.bookwiseapp.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.example.bookwiseapp.data.api.ApiClient
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "bookwise_prefs")

/** Token 持久化存储，并同步到 ApiClient.token（供拦截器使用）。*/
class TokenStore(private val context: Context) {

    companion object {
        private val KEY_TOKEN = stringPreferencesKey("auth_token")

        lateinit var instance: TokenStore
            private set

        fun init(context: Context) {
            instance = TokenStore(context)
        }
    }

    /** App 启动时调用：从 DataStore 恢复 Token 到内存。*/
    suspend fun loadToken() {
        val saved = context.dataStore.data.map { it[KEY_TOKEN] }.first()
        ApiClient.token = saved
    }

    suspend fun saveToken(token: String) {
        ApiClient.token = token
        context.dataStore.edit { it[KEY_TOKEN] = token }
    }

    suspend fun clearToken() {
        ApiClient.token = null
        context.dataStore.edit { it.remove(KEY_TOKEN) }
    }

    suspend fun getToken(): String? =
        context.dataStore.data.map { it[KEY_TOKEN] }.first()
}
