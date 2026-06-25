package com.example.bookwiseapp.ui.screen

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
import com.example.bookwiseapp.ui.component.InfoRow
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.ui.component.MemberLevelGuideDialog
import com.example.bookwiseapp.util.StripeCheckout
import com.example.bookwiseapp.viewmodel.AccountViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountWalletScreen(
    viewModel: AccountViewModel,
    onBack: () -> Unit
) {
    val state by viewModel.state.collectAsState()
    val account = state.account
    val context = LocalContext.current
    var showLevelGuide by remember { mutableStateOf(false) }

    val snackbarHost = remember { SnackbarHostState() }
    LaunchedEffect(state.message) {
        state.message?.let {
            snackbarHost.showSnackbar(it)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = {
            TopAppBar(
                title = { Text("会员与积分") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                },
                actions = {
                    TextButton(onClick = { showLevelGuide = true }) {
                        Text("详情")
                    }
                }
            )
        },
        snackbarHost = { SnackbarHost(snackbarHost) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && account == null -> LoadingOverlay()
                state.error != null && account == null ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadAccount() })
                account != null -> Column(
                    Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    val pointsDisplay = if (account.nextLevelPoints == "max") {
                        "max"
                    } else {
                        "${account.points ?: 0} 分"
                    }

                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp)) {
                            Text("累计积分", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            Text(
                                pointsDisplay,
                                style = MaterialTheme.typography.displaySmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                            Text(
                                if (account.isMember == true) "购物消费与人民币 1:1 累计"
                                else "开通会员后购物才累计积分",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                    }

                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("会员状态", style = MaterialTheme.typography.titleMedium)
                            if (account.isMember == true) {
                                Text("已开通会员", color = MaterialTheme.colorScheme.primary)
                                Text(
                                    "${account.memberLevel} 级 · ${account.effectiveDiscountPercent ?: account.discountPercent}% 优惠",
                                    style = MaterialTheme.typography.bodySmall
                                )
                                account.nextLevelPoints?.let { nxt ->
                                    Text(
                                        if (nxt == "max") "已达最高会员等级 max"
                                        else "距下一级还需 $nxt 积分",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                }
                            } else {
                                Text("尚未开通会员", color = MaterialTheme.colorScheme.outline)
                                Button(
                                    onClick = { viewModel.activateMembership() },
                                    enabled = !state.isLoading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("免费开通会员") }
                            }

                            if (account.isMember == true) {
                                HorizontalDivider(Modifier.padding(vertical = 4.dp))
                                Text("畅读卡（¥20/月）", style = MaterialTheme.typography.titleSmall)
                                if (account.hasReadingPass == true) {
                                    Text(
                                        "畅读卡生效中 · 7.2 折购书",
                                        color = MaterialTheme.colorScheme.primary,
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                    account.readingPassExpiresAt?.let {
                                        Text("有效期至 $it", style = MaterialTheme.typography.bodySmall)
                                    }
                                } else {
                                    Text(
                                        "开通后 30 天内再享 7.2 折（与等级折扣乘算）",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.outline
                                    )
                                }
                                Button(
                                    onClick = {
                                        viewModel.startReadingPassCheckout { url ->
                                            StripeCheckout.open(context, url)
                                        }
                                    },
                                    enabled = !state.isLoading && state.stripeConfigured == true,
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text(
                                        if (account.hasReadingPass == true) "续费畅读卡"
                                        else "购买畅读卡"
                                    )
                                }
                                if (state.stripeConfigured != true) {
                                    Text(
                                        "在线支付暂不可用",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.error
                                    )
                                }
                            }
                        }
                    }

                    if (account.isMember == true) {
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text("会员等级", style = MaterialTheme.typography.titleMedium)
                                InfoRow("当前等级", "${account.memberLevel} 级")
                            }
                        }
                    }
                }
            }

            if (showLevelGuide) {
                MemberLevelGuideDialog(
                    guide = state.memberLevelGuide,
                    onDismiss = { showLevelGuide = false }
                )
            }
        }
    }
}
