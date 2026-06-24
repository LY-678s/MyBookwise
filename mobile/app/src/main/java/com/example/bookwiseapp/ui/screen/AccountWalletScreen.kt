package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.InfoRow
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.AccountViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountWalletScreen(
    viewModel: AccountViewModel,
    onBack: () -> Unit,
    onOrdersClick: () -> Unit = {}
) {
    val state by viewModel.state.collectAsState()
    val account = state.account
    var showRecharge by remember { mutableStateOf(false) }
    var rechargeAmount by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        if (account == null) viewModel.loadAccount()
    }

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
                title = { Text("账户") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
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
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp)) {
                            Text("账户余额", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(8.dp))
                            Text(
                                "¥${account.balance}",
                                style = MaterialTheme.typography.displaySmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                            Spacer(Modifier.height(12.dp))
                            Button(onClick = { showRecharge = true }) { Text("充值") }
                        }
                    }

                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("信用信息", style = MaterialTheme.typography.titleMedium)
                            InfoRow("当前等级", "${account.levelId} 级")
                            InfoRow("累计消费", "¥${account.totalSpent}")
                            InfoRow("折扣", "${account.discountPercent}%")
                            if (account.canUseCredit) {
                                InfoRow("信用额度", "¥${account.usedCredit} / ¥${account.creditLimit}")
                                InfoRow("可用信用", "¥${account.availableCredit}")
                            }
                            account.nextLevelAmount?.let {
                                InfoRow("距下一级", "还需消费 ¥$it")
                            }
                        }
                    }

                    if (account.canUseCredit && account.usedCredit != "0.00") {
                        OutlinedButton(
                            onClick = { viewModel.repay(onSuccess = {}) },
                            enabled = !state.isLoading,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("一键还款（欠款 ¥${account.usedCredit}）") }
                    }

                    OutlinedButton(
                        onClick = onOrdersClick,
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("我的订单") }

                    CreditLevelTable(currentLevel = account.levelId)
                }
            }
        }
    }

    if (showRecharge) {
        AlertDialog(
            onDismissRequest = { showRecharge = false; rechargeAmount = "" },
            title = { Text("账户充值") },
            text = {
                OutlinedTextField(
                    value = rechargeAmount,
                    onValueChange = { rechargeAmount = it },
                    label = { Text("充值金额") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.recharge(rechargeAmount) {
                        showRecharge = false
                        rechargeAmount = ""
                    }
                }) { Text("确认") }
            },
            dismissButton = {
                TextButton(onClick = { showRecharge = false; rechargeAmount = "" }) { Text("取消") }
            }
        )
    }
}

@Composable
private fun CreditLevelTable(currentLevel: Int) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text("信用等级说明", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            val rows = listOf(
                Triple(1, "< ¥1000", "9折 / 不可透支"),
                Triple(2, "≥ ¥1000", "8.5折 / 不可透支"),
                Triple(3, "≥ ¥2000", "8.5折 / ¥500"),
                Triple(4, "≥ ¥5000", "8折 / ¥1000"),
                Triple(5, "≥ ¥10000", "7.5折 / 几乎无限")
            )
            rows.forEach { (level, req, benefit) ->
                val highlighted = level == currentLevel
                Surface(
                    color = if (highlighted) MaterialTheme.colorScheme.primaryContainer
                    else MaterialTheme.colorScheme.surface,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        Modifier.padding(vertical = 8.dp, horizontal = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("${level}级", style = MaterialTheme.typography.bodyMedium)
                        Text(req, style = MaterialTheme.typography.bodySmall)
                        Text(benefit, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}
