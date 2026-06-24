package com.example.bookwiseapp.data.repository

import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.*

class FavoriteRepository : BaseRepository() {

    suspend fun getFolders(): Result<FavoriteFoldersResponse> = safeCall(
        call = { ApiClient.service.getFavoriteFolders() },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun createFolder(name: String): Result<FavoriteFoldersResponse> = safeCall(
        call = { ApiClient.service.createFavoriteFolder(CreateFavoriteFolderRequest(name)) },
        errorField = { it.error },
        successCheck = { it.success }
    )

    suspend fun deleteFolder(folderId: Int): Result<SimpleResponse> = safeCall(
        call = { ApiClient.service.deleteFavoriteFolder(folderId) },
        errorField = { it.error },
        successCheck = { it.success }
    )
}
