package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
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
    onOrderCreated: (Int) -> Unit,
    onBack: () -> Unit
) {
    val checkoutState by orderVm.checkoutState.collectAsState()
    val accountState by accountVm.state.collectAsState()

    val preview = checkoutState.preview
    val customer = preview?.customer ?: accountState.account

    var shippingName by remember { mutableStateOf(customer?.name ?: "") }
    var shippingContact by remember { mutableStateOf(customer?.email ?: "") }
    var shippingAddress by remember { mutableStateOf(customer?.address ?: "") }
    var paymentChoice by remember { mutableStateOf("balance") }

    LaunchedEffect(Unit) {
        orderVm.loadCheckoutPreview()
        if (accountState.account == null) accountVm.loadAccount()
    }

    // 用账户信息填充默认值
    LaunchedEffect(customer) {
        if (shippingName.isEmpty()) shippingName = customer?.name ?: ""
        if (shippingContact.isEmpty()) shippingContact = customer?.email ?: ""
        if (shippingAddress.isEmpty()) shippingAddress = customer?.address ?: ""
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("确认订单") },
                navigationIcon = { IconButton(onClick = onBack) {
                    Icon(Icons.Default.ArrowBack, "返回")
                }}
            )
        }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            if (checkoutState.isLoading) {
                LoadingOverlay()
            } else if (checkoutState.error != null) {
                ErrorMessage(checkoutState.error!!)
            } else {
                Column(
                    Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // 订单预览
                    preview?.let { cart ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text("订单商品", style = MaterialTheme.typography.titleSmall)
                                Spacer(Modifier.height(8.dp))
                                cart.items.forEach { item ->
                                    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
                                        Text(item.book.title, Modifier.weight(1f),
                                            style = MaterialTheme.typography.bodySmall)
                                        Text("×${item.quantity}  ¥${item.discountedAmount}",
                                            style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                                Divider(Modifier.padding(vertical = 8.dp))
                                Row(Modifier.fillMaxWidth()) {
                                    Text("合计", Modifier.weight(1f),
                                        style = MaterialTheme.typography.bodyMedium)
                                    Text("¥${cart.discountedTotal}",
                                        style = MaterialTheme.typography.titleSmall,
                                        color = MaterialTheme.colorScheme.primary)
                                }
                                if (cart.discountAmount != "0.00") {
                                    Text("已优惠 ¥${cart.discountAmount}",
                                        style = MaterialTheme.typography.labelSmall,
                                        color = MaterialTheme.colorScheme.secondary)
                                }
                            }
                        }
                    }

                    // 发货信息
                    Text("收货信息", style = MaterialTheme.typography.titleSmall)
                    OutlinedTextField(value = shippingName, onValueChange = { shippingName = it },
                        label = { Text("收货人") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(value = shippingContact, onValueChange = { shippingContact = it },
                        label = { Text("联系方式") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(value = shippingAddress, onValueChange = { shippingAddress = it },
                        label = { Text("收货地址 *") }, modifier = Modifier.fillMaxWidth())

                    // 付款方式
                    Text("付款方式", style = MaterialTheme.typography.titleSmall)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        FilterChip(
                            selected = paymentChoice == "balance",
                            onClick = { paymentChoice = "balance" },
                            label = { Text("余额优先") }
                        )
                        if (customer?.canUseCredit == true) {
                            FilterChip(
                                selected = paymentChoice == "credit",
                                onClick = { paymentChoice = "credit" },
                                label = { Text("纯信用支付") }
                            )
                        }
                    }

                    // 账户余额提示
                    customer?.let {
                        Card(
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.secondaryContainer)
                        ) {
                            Column(Modifier.padding(12.dp)) {
                                Text("账户余额：¥${it.balance}",
                                    style = MaterialTheme.typography.bodySmall)
                                if (it.canUseCredit) {
                                    Text("可用信用额度：¥${it.availableCredit}",
                                        style = MaterialTheme.typography.bodySmall)
                                }
                            }
                        }
                    }

                    checkoutState.error?.let {
                        Text(it, color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall)
                    }

                    Button(
                        onClick = {
                            orderVm.createOrder(
                                paymentChoice = paymentChoice,
                                shippingName = shippingName.trim(),
                                shippingContact = shippingContact.trim(),
                                shippingAddress = shippingAddress.trim(),
                                onSuccess = { orderId -> onOrderCreated(orderId) }
                            )
                        },
                        enabled = shippingAddress.isNotBlank() && !checkoutState.isLoading,
                        modifier = Modifier.fillMaxWidth().height(48.dp)
                    ) {
                        if (checkoutState.isLoading) {
                            CircularProgressIndicator(Modifier.size(20.dp),
                                color = MaterialTheme.colorScheme.onPrimary)
                        } else {
                            Text("提交订单")
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                }
            }
        }
    }
}
