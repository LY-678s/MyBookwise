package com.example.bookwiseapp.data.api.model

import com.google.gson.annotations.SerializedName

// ────────────────── 通用 ──────────────────

data class SimpleResponse(
    val success: Boolean,
    val message: String? = null,
    val error: String? = null
)

// ────────────────── 顾客 ──────────────────

data class CustomerData(
    @SerializedName("customerid") val customerId: Int,
    val username: String,
    val name: String,
    val email: String?,
    val address: String?,
    @SerializedName("levelid") val levelId: Int? = null,
    @SerializedName("member_level") val memberLevel: Int? = null,
    @SerializedName("discount_rate") val discountRate: String,
    @SerializedName("discount_percent") val discountPercent: String,
    @SerializedName("registerdate") val registerDate: String?,
    val points: Int? = null,
    @SerializedName("is_member") val isMember: Boolean? = null,
    @SerializedName("has_reading_pass") val hasReadingPass: Boolean? = null,
    @SerializedName("reading_pass_expires_at") val readingPassExpiresAt: String? = null,
    @SerializedName("next_level_points") val nextLevelPoints: String? = null,
    @SerializedName("effective_discount_percent") val effectiveDiscountPercent: String? = null
)

// ────────────────── 认证 ──────────────────

data class LoginRequest(
    val username: String,
    val password: String
)

data class RegisterRequest(
    val username: String,
    val password: String,
    @SerializedName("confirm_password") val confirmPassword: String,
    val name: String,
    val email: String,
    val address: String
)

data class AuthResponse(
    val success: Boolean,
    val message: String? = null,
    val token: String? = null,
    val customer: CustomerData? = null,
    val error: String? = null
)

// ────────────────── 图书 ──────────────────

data class BookData(
    val isbn: String,
    val title: String,
    val publisher: String?,
    val price: String,
    val keywords: String?,
    @SerializedName("stockqty") val stockQty: Int,
    val location: String?,
    @SerializedName("minstocklimit") val minStockLimit: Int,
    @SerializedName("cover_image_url") val coverImageUrl: String?,
    val coverimage: String?,
    val authors: List<String>? = null,
    @SerializedName("metric_label") val metricLabel: String? = null,
    @SerializedName("metric_value") val metricValue: Int? = null
)

data class BooksResponse(
    val success: Boolean,
    val books: List<BookData>? = null,
    @SerializedName("default_cover_url") val defaultCoverUrl: String? = null,
    @SerializedName("has_more") val hasMore: Boolean? = null,
    @SerializedName("current_page") val currentPage: Int? = null,
    @SerializedName("total_pages") val totalPages: Int? = null,
    @SerializedName("total_count") val totalCount: Int? = null,
    val error: String? = null
)

data class BookDetailResponse(
    val success: Boolean,
    val book: BookData? = null,
    @SerializedName("default_cover_url") val defaultCoverUrl: String? = null,
    @SerializedName("is_favorited") val isFavorited: Boolean? = null,
    @SerializedName("favorite_count") val favoriteCount: Int? = null,
    @SerializedName("favorite_folder_id") val favoriteFolderId: Int? = null,
    @SerializedName("favorite_folders") val favoriteFolders: List<FavoriteFolderData>? = null,
    val error: String? = null
)

data class SearchResponse(
    val success: Boolean,
    val query: String? = null,
    val books: List<BookData>? = null,
    @SerializedName("recent_searches") val recentSearches: List<String>? = null,
    val message: String? = null,
    val error: String? = null
)

data class SearchHistoryClearResponse(
    val success: Boolean,
    val message: String? = null,
    @SerializedName("recent_searches") val recentSearches: List<String>? = null,
    val error: String? = null
)

// ────────────────── 分区 / 榜单 / 收藏 ──────────────────

data class CategoryItem(
    val name: String,
    val count: Int,
    val active: Boolean = false
)

data class CategoriesResponse(
    val success: Boolean,
    val categories: List<CategoryItem>? = null,
    val books: List<BookData>? = null,
    @SerializedName("selected_category") val selectedCategory: String? = null,
    val sort: String? = null,
    @SerializedName("default_cover_url") val defaultCoverUrl: String? = null,
    @SerializedName("current_page") val currentPage: Int? = null,
    @SerializedName("total_pages") val totalPages: Int? = null,
    @SerializedName("total_count") val totalCount: Int? = null,
    val error: String? = null
)

data class RankingSection(
    val title: String,
    val subtitle: String,
    val icon: String? = null,
    val books: List<BookData>? = null
)

data class RankingsResponse(
    val success: Boolean,
    val sections: List<RankingSection>? = null,
    @SerializedName("default_cover_url") val defaultCoverUrl: String? = null,
    val error: String? = null
)

data class FavoriteFolderData(
    val id: Int,
    val name: String,
    @SerializedName("is_default") val isDefault: Boolean = false
)

data class FavoriteFolderCard(
    val folder: FavoriteFolderData,
    val books: List<BookData>? = null,
    val count: Int = 0
)

data class FavoriteFoldersResponse(
    val success: Boolean,
    val folders: List<FavoriteFolderCard>? = null,
    @SerializedName("total_count") val totalCount: Int? = null,
    val message: String? = null,
    val folder: FavoriteFolderData? = null,
    val error: String? = null
)

data class CreateFavoriteFolderRequest(
    val name: String
)

data class FavoriteToggleRequest(
    @SerializedName("folder_id") val folderId: Int? = null
)

data class FavoriteToggleResponse(
    val success: Boolean,
    val message: String? = null,
    @SerializedName("is_favorited") val isFavorited: Boolean? = null,
    @SerializedName("favorite_count") val favoriteCount: Int? = null,
    @SerializedName("folder_id") val folderId: Int? = null,
    val error: String? = null
)

// ────────────────── 购物车 ──────────────────

data class CartItemData(
    val book: BookData,
    val quantity: Int,
    @SerializedName("original_amount") val originalAmount: String,
    @SerializedName("discounted_amount") val discountedAmount: String
)

data class CartData(
    val items: List<CartItemData>,
    @SerializedName("original_total") val originalTotal: String,
    @SerializedName("discounted_total") val discountedTotal: String,
    @SerializedName("discount_amount") val discountAmount: String,
    @SerializedName("discount_rate") val discountRate: String,
    @SerializedName("discount_percent") val discountPercent: String,
    val customer: CustomerData
)

data class CartResponse(
    val success: Boolean,
    val cart: CartData? = null,
    val message: String? = null,
    val error: String? = null
)

data class AddToCartRequest(
    val isbn: String,
    val quantity: Int
)

data class UpdateCartRequest(
    val quantity: Int
)

// ────────────────── 订单 ──────────────────

data class OrderDetailLineData(
    @SerializedName("detailid") val detailId: Int,
    val isbn: String,
    val title: String,
    val quantity: Int,
    @SerializedName("unitprice") val unitPrice: String,
    @SerializedName("isshipped") val isShipped: Int,
    @SerializedName("original_amount") val originalAmount: String,
    @SerializedName("discounted_amount") val discountedAmount: String
)

data class OrderData(
    @SerializedName("orderid") val orderId: Int,
    @SerializedName("orderno") val orderNo: String,
    @SerializedName("orderdate") val orderDate: String?,
    @SerializedName("shipaddress") val shipAddress: String,
    @SerializedName("totalamount") val totalAmount: String,
    @SerializedName("actualpaid") val actualPaid: String,
    /** 0=未付 1=已付 3=已退款 */
    @SerializedName("paymentstatus") val paymentStatus: Int,
    val status: Int,
    @SerializedName("original_amount") val originalAmount: String,
    @SerializedName("discount_amount") val discountAmount: String,
    val details: List<OrderDetailLineData>? = null,
    @SerializedName("discount_rate") val discountRate: String? = null,
    @SerializedName("discount_percent") val discountPercent: String? = null
)

data class OrderResponse(
    val success: Boolean,
    val message: String? = null,
    val order: OrderData? = null,
    @SerializedName("checkout_url") val checkoutUrl: String? = null,
    val error: String? = null
)

data class OrdersResponse(
    val success: Boolean,
    val orders: List<OrderData>? = null,
    val error: String? = null
)

data class PreviewResponse(
    val success: Boolean,
    val preview: CartData? = null,
    val error: String? = null
)

data class CreateOrderRequest(
    @SerializedName("shipping_name") val shippingName: String,
    @SerializedName("shipping_contact") val shippingContact: String,
    @SerializedName("shipping_address") val shippingAddress: String,
    @SerializedName("success_url") val successUrl: String? = null,
    @SerializedName("cancel_url") val cancelUrl: String? = null
)

data class PaymentConfirmRequest(
    @SerializedName("session_id") val sessionId: String
)

data class PaymentConfirmResponse(
    val success: Boolean,
    val message: String? = null,
    val account: CustomerData? = null,
    @SerializedName("order_id") val orderId: Int? = null,
    val error: String? = null
)

// ────────────────── 账户 ──────────────────

data class MemberLevelGuideItem(
    val level: Int,
    @SerializedName("points_required") val pointsRequired: Int,
    @SerializedName("discount_percent") val discountPercent: String
)

data class AccountResponse(
    val success: Boolean,
    val message: String? = null,
    val account: CustomerData? = null,
    @SerializedName("stripe_configured") val stripeConfigured: Boolean? = null,
    @SerializedName("member_level_guide") val memberLevelGuide: List<MemberLevelGuideItem>? = null,
    val error: String? = null
)

data class MembershipCheckoutResponse(
    val success: Boolean,
    @SerializedName("checkout_url") val checkoutUrl: String? = null,
    @SerializedName("session_id") val sessionId: String? = null,
    @SerializedName("publishable_key") val publishableKey: String? = null,
    val error: String? = null
)

data class BrowseHistoryResponse(
    val success: Boolean,
    val books: List<BookData>? = null,
    @SerializedName("default_cover_url") val defaultCoverUrl: String? = null,
    val error: String? = null
)

data class MeResponse(
    val success: Boolean,
    val customer: CustomerData? = null,
    val error: String? = null
)

data class MembershipCheckoutRequest(
    @SerializedName("success_url") val successUrl: String? = null,
    @SerializedName("cancel_url") val cancelUrl: String? = null
)

data class UpdateAccountRequest(
    val name: String,
    val email: String,
    val address: String,
    @SerializedName("current_password") val currentPassword: String? = null,
    @SerializedName("new_password") val newPassword: String? = null,
    @SerializedName("confirm_password") val confirmPassword: String? = null
)

// ────────────────── AI 助手 ──────────────────

data class AiMessage(
    val role: String,
    val content: String
)

data class AiStatusResponse(
    val success: Boolean,
    @SerializedName("ai_configured") val aiConfigured: Boolean = false,
    val history: List<AiMessage> = emptyList(),
    val error: String? = null
)

data class AiChatRequest(
    val message: String
)

data class AiChatResponse(
    val success: Boolean,
    val reply: String? = null,
    val error: String? = null
)
