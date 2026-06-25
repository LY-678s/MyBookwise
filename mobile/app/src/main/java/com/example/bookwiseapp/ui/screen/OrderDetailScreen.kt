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
import com.example.bookwiseapp.ui.component.*
import com.example.bookwiseapp.viewmodel.AccountViewModel
import com.example.bookwiseapp.viewmodel.OrderViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrderDetailScreen(
    orderId: Int,
    orderVm: OrderViewModel,
    accountVm: AccountViewModel,
    onBack: () -> Unit
) {
    val state by orderVm.detailState.collectAsState()
    val snackbarHost = remember { SnackbarHostState() }

    LaunchedEffect(orderId) { orderVm.loadOrderDetail(orderId) }

    LaunchedEffect(state.message) {
        state.message?.let { msg ->
            snackbarHost.showSnackbar(msg)
            orderVm.clearDetailMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("订单详情") },
                navigationIcon = { IconButton(onClick = onBack) {
                    Icon(Icons.Default.ArrowBack, "返回")
                }}
            )
        },
        snackbarHost = { SnackbarHost(snackbarHost) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && state.order == null -> LoadingOverlay()
                state.error != null && state.order == null -> ErrorMessage(
                    state.error!!,
                    onRetry = { orderVm.loadOrderDetail(orderId) }
                )
                state.order != null -> {
                    val order = state.order!!
                    Column(
                        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text("订单信息", style = MaterialTheme.typography.titleSmall)
                                Spacer(Modifier.height(8.dp))
                                InfoRow("订单号", order.orderNo)
                                InfoRow("下单时间", order.orderDate?.take(16) ?: "")
                                InfoRow("收货地址", order.shipAddress)
                                InfoRow("订单状态", orderStatusText(order.status))
                                InfoRow("付款状态", paymentStatusText(order.paymentStatus))
                                InfoRow("应付金额", "¥${order.totalAmount}")
                                InfoRow("实付金额", "¥${order.actualPaid}")
                                if (order.discountAmount != "0.00") {
                                    InfoRow("已优惠", "¥${order.discountAmount}")
                                }
                            }
                        }

                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(12.dp)) {
                                Text("商品明细", style = MaterialTheme.typography.titleSmall)
                                Spacer(Modifier.height(8.dp))
                                order.details?.forEach { detail ->
                                    Row(
                                        Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                    ) {
                                        Column(Modifier.weight(1f)) {
                                            Text(detail.title,
                                                style = MaterialTheme.typography.bodyMedium)
                                            Text("单价 ¥${detail.unitPrice} × ${detail.quantity}",
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.outline)
                                        }
                                        Text("¥${detail.discountedAmount}",
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.primary)
                                    }
                                    HorizontalDivider()
                                }
                            }
                        }

                        if (order.paymentStatus == 0) {
                            Text(
                                "若已在 Stripe 完成付款但状态未更新，可点击下方按钮同步。",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.outline
                            )
                            Button(
                                onClick = {
                                    orderVm.syncOrderPayment(
                                        orderId = orderId,
                                        onSuccess = { _, account, _ ->
                                            account?.let { accountVm.applyAccount(it) }
                                                ?: accountVm.loadAccount()
                                        },
                                        onError = { }
                                    )
                                },
                                enabled = !state.isLoading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("同步支付状态") }
                        }

                        state.error?.let {
                            Text(it, color = MaterialTheme.colorScheme.error,
                                style = MaterialTheme.typography.bodySmall)
                        }

                        if (order.status == 0) {
                            OutlinedButton(
                                onClick = { orderVm.cancelOrder(orderId) },
                                enabled = !state.isLoading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("取消订单") }
                        }
                        if (order.status == 1) {
                            Button(
                                onClick = { orderVm.confirmReceipt(orderId) },
                                enabled = !state.isLoading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("确认收货") }
                        }
                    }
                }
            }
        }
    }
}
