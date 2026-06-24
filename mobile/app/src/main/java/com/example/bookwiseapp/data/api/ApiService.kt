package com.example.bookwiseapp.data.api

import com.example.bookwiseapp.data.api.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ── 认证 ──────────────────────────────────────────────────────
    @POST("auth/login/")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>

    @POST("auth/register/")
    suspend fun register(@Body request: RegisterRequest): Response<AuthResponse>

    @POST("auth/logout/")
    suspend fun logout(): Response<SimpleResponse>

    @GET("auth/me/")
    suspend fun me(): Response<MeResponse>

    // ── 图书 ──────────────────────────────────────────────────────
    @GET("books/")
    suspend fun listBooks(
        @Query("page") page: Int? = null,
        @Query("page_size") pageSize: Int? = null,
        @Query("refresh") refresh: Int? = null
    ): Response<BooksResponse>

    @GET("books/search/")
    suspend fun searchBooks(@Query("q") query: String): Response<SearchResponse>

    @GET("books/{isbn}/")
    suspend fun getBook(@Path("isbn") isbn: String): Response<BookDetailResponse>

    @POST("books/{isbn}/favorite/")
    suspend fun toggleFavorite(
        @Path("isbn") isbn: String,
        @Body request: FavoriteToggleRequest
    ): Response<FavoriteToggleResponse>

    @GET("categories/")
    suspend fun getCategories(
        @Query("category") category: String? = null,
        @Query("sort") sort: String? = null,
        @Query("page") page: Int? = null
    ): Response<CategoriesResponse>

    @GET("rankings/")
    suspend fun getRankings(): Response<RankingsResponse>

    @GET("favorites/folders/")
    suspend fun getFavoriteFolders(): Response<FavoriteFoldersResponse>

    @POST("favorites/folders/")
    suspend fun createFavoriteFolder(@Body request: CreateFavoriteFolderRequest): Response<FavoriteFoldersResponse>

    @DELETE("favorites/folders/{id}/")
    suspend fun deleteFavoriteFolder(@Path("id") folderId: Int): Response<SimpleResponse>

    // ── 购物车 ──────────────────────────────────────────────────────
    @GET("cart/")
    suspend fun getCart(): Response<CartResponse>

    @POST("cart/items/")
    suspend fun addToCart(@Body request: AddToCartRequest): Response<CartResponse>

    @PUT("cart/items/{isbn}/")
    suspend fun updateCartItem(
        @Path("isbn") isbn: String,
        @Body request: UpdateCartRequest
    ): Response<CartResponse>

    @DELETE("cart/items/{isbn}/")
    suspend fun removeFromCart(@Path("isbn") isbn: String): Response<CartResponse>

    // ── 订单 ──────────────────────────────────────────────────────
    @GET("orders/preview/")
    suspend fun orderPreview(): Response<PreviewResponse>

    @GET("orders/")
    suspend fun listOrders(): Response<OrdersResponse>

    @POST("orders/")
    suspend fun createOrder(@Body request: CreateOrderRequest): Response<OrderResponse>

    @GET("orders/{id}/")
    suspend fun getOrder(@Path("id") orderId: Int): Response<OrderResponse>

    @POST("orders/{id}/pay/")
    suspend fun payOrder(@Path("id") orderId: Int): Response<OrderResponse>

    @POST("orders/{id}/cancel/")
    suspend fun cancelOrder(@Path("id") orderId: Int): Response<OrderResponse>

    @POST("orders/{id}/confirm-receipt/")
    suspend fun confirmReceipt(@Path("id") orderId: Int): Response<OrderResponse>

    // ── 账户 ──────────────────────────────────────────────────────
    @GET("account/")
    suspend fun getAccount(): Response<AccountResponse>

    @PATCH("account/")
    suspend fun updateAccount(@Body request: UpdateAccountRequest): Response<AccountResponse>

    @POST("account/recharge/")
    suspend fun recharge(@Body request: RechargeRequest): Response<AccountResponse>

    @POST("account/repay/")
    suspend fun repay(): Response<AccountResponse>

    // ── AI 助手 ──────────────────────────────────────────────────────
    @GET("ai/")
    suspend fun getAiStatus(): Response<AiStatusResponse>

    @POST("ai/chat/")
    suspend fun sendAiMessage(@Body request: AiChatRequest): Response<AiChatResponse>

    @POST("ai/clear/")
    suspend fun clearAiChat(): Response<SimpleResponse>
}
