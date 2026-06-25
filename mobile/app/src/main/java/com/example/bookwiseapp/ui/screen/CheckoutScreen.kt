package com.example.bookwiseapp.ui.screen

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.AccountViewModel
import com.example.bookwiseapp.viewmodel.OrderViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CheckoutScreen(
    orderVm: OrderViewModel,
    accountVm: AccountViewModel,
    onBack: () -> Unit
) {
    val checkoutState by orderVm.checkoutState.collectAsState()
    val accountState by accountVm.state.collectAsState()
    val context = LocalContext.current

    val preview = checkoutState.preview
    val customer = preview?.customer ?: accountState.account

    var shippingName by remember { mutableStateOf(customer?.name ?: "") }
    var shippingContact by remember { mutableStateOf(customer?.email ?: "") }
    var shippingAddress by remember { mutableStateOf(customer?.address ?: "") }

    LaunchedEffect(Unit) {
        orderVm.loadCheckoutPreview()
        if (accountState.account == null) accountVm.loadAccount()
    }

    LaunchedEffect(customer) {
        if (shippingName.isEmpty()) shippingName = customer?.name ?: ""
        if (shippingContact.isEmpty()) shippingContact = customer?.email ?: ""
        if (shippingAddress.isEmpty()) shippingAddress = customer?.address ?: ""
    }

    LaunchedEffect(accountState.message) {
        accountState.message?.let {
            orderVm.loadCheckoutPreview()
            accountVm.clearMessage()
        }
    }

    val canSubmit = shippingAddress.isNotBlank() && !checkoutState.isLoading &&
        accountState.stripeConfigured == true

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("确认订单") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, "返回")
                    }
                }
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            if (checkoutState.isLoading && preview == null) {
                LoadingOverlay()
            } else if (checkoutState.error != null && preview == null) {
                ErrorMessage(checkoutState.error!!)
            } else {
                Column(
                    Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    preview?.let { cart ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text("订单商品", style = MaterialTheme.typography.titleSmall)
                                Spacer(Modifier.height(8.dp))
                                cart.items.forEach { item ->
                                    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
                                        Text(
                                            item.book.title,
                                            Modifier.weight(1f),
                                            style = MaterialTheme.typography.bodySmall
                                        )
                                        Text(
                                            "×${item.quantity}  ¥${item.discountedAmount}",
                                            style = MaterialTheme.typography.bodySmall
                                        )
                                    }
                                }
                                HorizontalDivider(Modifier.padding(vertical = 8.dp))
                                Row(Modifier.fillMaxWidth()) {
                                    Text("合计", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                                    Text(
                                        "¥${cart.discountedTotal}",
                                        style = MaterialTheme.typography.titleSmall,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                                if (cart.discountAmount != "0.00") {
                                    Text(
                                        "已优惠 ¥${cart.discountAmount}",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.secondary
                                    )
                                }
                            }
                        }
                    }

                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("会员与优惠", style = MaterialTheme.typography.titleSmall)
                            if (customer?.isMember != true) {
                                Text(
                                    "无会员折扣",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.outline
                                )
                                Button(
                                    onClick = {
                                        accountVm.activateMembership {
                                            orderVm.loadCheckoutPreview()
                                        }
                                    },
                                    enabled = !accountState.isLoading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("免费开通会员") }
                            } else {
                                Text(
                                    "${customer?.memberLevel} 级 · ${customer?.effectiveDiscountPercent ?: customer?.discountPercent}% 优惠" +
                                        if (customer?.hasReadingPass == true) "（含畅读卡乘算）" else "",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                if (customer?.hasReadingPass != true) {
                                    Text(
                                        "畅读卡 ¥20/月：等级折扣 × 7.2 折",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                    Button(
                                        onClick = {
                                            accountVm.startReadingPassCheckout { url ->
                                                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                            }
                                        },
                                        enabled = !accountState.isLoading && accountState.stripeConfigured == true,
                                        modifier = Modifier.fillMaxWidth()
                                    ) { Text("购买畅读卡") }
                                } else {
                                    Text(
                                        "畅读卡生效中 · 等级折扣 × 7.2 折",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                            }
                        }
                    }

                    Text("收货信息", style = MaterialTheme.typography.titleSmall)
                    OutlinedTextField(
                        value = shippingName,
                        onValueChange = { shippingName = it },
                        label = { Text("收货人") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = shippingContact,
                        onValueChange = { shippingContact = it },
                        label = { Text("联系方式") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = shippingAddress,
                        onValueChange = { shippingAddress = it },
                        label = { Text("收货地址 *") },
                        modifier = Modifier.fillMaxWidth()
                    )

                    Text("付款方式", style = MaterialTheme.typography.titleSmall)
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.secondaryContainer
                        )
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text("在线支付", style = MaterialTheme.typography.bodyMedium)
                            Text(
                                "提交后跳转收银台完成付款",
                                style = MaterialTheme.typography.bodySmall
                            )
                            if (accountState.stripeConfigured != true) {
                                Text(
                                    "在线支付暂不可用",
                                    color = MaterialTheme.colorScheme.error,
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        }
                    }

                    checkoutState.error?.let {
                        Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                    }

                    Button(
                        onClick = {
                            orderVm.createOrder(
                                shippingName = shippingName.trim(),
                                shippingContact = shippingContact.trim(),
                                shippingAddress = shippingAddress.trim(),
                                onStripeUrl = { url ->
                                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                                }
                            )
                        },
                        enabled = canSubmit,
                        modifier = Modifier.fillMaxWidth().height(48.dp)
                    ) {
                        if (checkoutState.isLoading) {
                            CircularProgressIndicator(
                                Modifier.size(20.dp),
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                        } else {
                            Text("确认并支付")
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                }
            }
        }
    }
}
