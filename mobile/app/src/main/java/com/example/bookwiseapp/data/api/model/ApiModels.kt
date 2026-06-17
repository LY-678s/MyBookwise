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
    val balance: String,
    @SerializedName("totalspent") val totalSpent: String,
    @SerializedName("usedcredit") val usedCredit: String,
    @SerializedName("creditlimit") val creditLimit: String,
    @SerializedName("available_credit") val availableCredit: String,
    @SerializedName("levelid") val levelId: Int,
    @SerializedName("discount_rate") val discountRate: String,
    @SerializedName("discount_percent") val discountPercent: String,
    @SerializedName("can_use_credit") val canUseCredit: Boolean,
    @SerializedName("registerdate") val registerDate: String?,
    @SerializedName("next_level_amount") val nextLevelAmount: String?
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
    val authors: List<String>? = null
)

data class BooksResponse(
    val success: Boolean,
    val books: List<BookData>? = null,
    @SerializedName("default_cover_url") val defaultCoverUrl: String? = null,
    val error: String? = null
)

data class BookDetailResponse(
    val success: Boolean,
    val book: BookData? = null,
    @SerializedName("default_cover_url") val defaultCoverUrl: String? = null,
    val error: String? = null
)

data class SearchResponse(
    val success: Boolean,
    val query: String? = null,
    val books: List<BookData>? = null,
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
    @SerializedName("unpaid_amount") val unpaidAmount: String,
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
    @SerializedName("payment_choice") val paymentChoice: String,      // "balance" | "credit"
    @SerializedName("shipping_name") val shippingName: String,
    @SerializedName("shipping_contact") val shippingContact: String,
    @SerializedName("shipping_address") val shippingAddress: String
)

// ────────────────── 账户 ──────────────────

data class AccountResponse(
    val success: Boolean,
    val message: String? = null,
    val account: CustomerData? = null,
    val error: String? = null
)

data class MeResponse(
    val success: Boolean,
    val customer: CustomerData? = null,
    val error: String? = null
)

data class RechargeRequest(
    val amount: String
)

data class UpdateAccountRequest(
    val name: String,
    val email: String,
    val address: String,
    @SerializedName("current_password") val currentPassword: String? = null,
    @SerializedName("new_password") val newPassword: String? = null,
    @SerializedName("confirm_password") val confirmPassword: String? = null
)
