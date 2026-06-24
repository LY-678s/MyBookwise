package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.InfoRow
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.AccountViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountScreen(
    viewModel: AccountViewModel,
    onLogout: () -> Unit,
    onFavoritesClick: () -> Unit = {},
    onOrdersClick: () -> Unit = {}
) {
    val state by viewModel.state.collectAsState()
    val account = state.account

    var showRecharge by remember { mutableStateOf(false) }
    var showEdit by remember { mutableStateOf(false) }
    var rechargeAmount by remember { mutableStateOf("") }

    LaunchedEffect(Unit) { viewModel.loadAccount() }

    val snackbarHost = remember { SnackbarHostState() }
    LaunchedEffect(state.message) {
        state.message?.let {
            snackbarHost.showSnackbar(it)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("我的") }) },
        snackbarHost = { SnackbarHost(snackbarHost) }
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when {
                state.isLoading && account == null -> LoadingOverlay()
                state.error != null && account == null ->
                    ErrorMessage(state.error!!, onRetry = { viewModel.loadAccount() })
                else ->
                    PullToRefreshBox(
                        isRefreshing = state.isLoading,
                        onRefresh = { viewModel.loadAccount() },
                        modifier = Modifier.fillMaxSize()
                    ) {
                        Column(
                            Modifier
                                .fillMaxSize()
                                .verticalScroll(rememberScrollState())
                                .padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            account?.let { acc ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(16.dp)) {
                                        Text(acc.name, style = MaterialTheme.typography.titleLarge)
                                        Text("@${acc.username}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.outline)
                                        Spacer(Modifier.height(12.dp))
                                        InfoRow("余额", "¥${acc.balance}")
                                        InfoRow("信用等级", "${acc.levelId} 级  (${acc.discountPercent}% 折扣)")
                                        if (acc.canUseCredit) {
                                            InfoRow("可用信用", "¥${acc.availableCredit}")
                                            InfoRow("已用信用", "¥${acc.usedCredit}")
                                        }
                                        InfoRow("累计消费", "¥${acc.totalSpent}")
                                        acc.nextLevelAmount?.let {
                                            InfoRow("距下一级", "还需消费 ¥$it")
                                        } ?: InfoRow("等级", "已达最高级 🎉")
                                        acc.email?.let { InfoRow("邮箱", it) }
                                        acc.address?.let { InfoRow("地址", it) }
                                    }
                                }
                            }

                            state.error?.let {
                                Text(it, color = MaterialTheme.colorScheme.error,
                                    style = MaterialTheme.typography.bodySmall)
                            }

                            Button(
                                onClick = { showRecharge = true },
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("充值") }

                            OutlinedButton(
                                onClick = onOrdersClick,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("我的订单") }

                            OutlinedButton(
                                onClick = onFavoritesClick,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("我的收藏") }

                            if (account?.usedCredit?.let { it != "0.00" } == true) {
                                OutlinedButton(
                                    onClick = { viewModel.repay(onSuccess = {}) },
                                    enabled = !state.isLoading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("一键还款（欠款 ¥${account.usedCredit}）") }
                            }

                            OutlinedButton(
                                onClick = { showEdit = true },
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("编辑资料") }

                            OutlinedButton(
                                onClick = onLogout,
                                colors = ButtonDefaults.outlinedButtonColors(
                                    contentColor = MaterialTheme.colorScheme.error
                                ),
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("退出登录") }

                            Spacer(Modifier.height(16.dp))
                        }
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

    if (showEdit && account != null) {
        EditProfileDialog(
            account = account,
            onDismiss = { showEdit = false },
            onConfirm = { name, email, address, curPwd, newPwd, confirmPwd ->
                viewModel.updateAccount(name, email, address, curPwd, newPwd, confirmPwd) {
                    showEdit = false
                }
            }
        )
    }
}

@Composable
private fun EditProfileDialog(
    account: com.example.bookwiseapp.data.api.model.CustomerData,
    onDismiss: () -> Unit,
    onConfirm: (String, String, String, String?, String?, String?) -> Unit
) {
    var name by remember { mutableStateOf(account.name) }
    var email by remember { mutableStateOf(account.email ?: "") }
    var address by remember { mutableStateOf(account.address ?: "") }
    var changePwd by remember { mutableStateOf(false) }
    var curPwd by remember { mutableStateOf("") }
    var newPwd by remember { mutableStateOf("") }
    var confirmPwd by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("编辑资料") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it },
                    label = { Text("姓名") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = email, onValueChange = { email = it },
                    label = { Text("邮箱") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = address, onValueChange = { address = it },
                    label = { Text("地址") }, modifier = Modifier.fillMaxWidth())
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Checkbox(checked = changePwd, onCheckedChange = { changePwd = it })
                    Text("修改密码")
                }
                if (changePwd) {
                    OutlinedTextField(value = curPwd, onValueChange = { curPwd = it },
                        label = { Text("当前密码") }, singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(value = newPwd, onValueChange = { newPwd = it },
                        label = { Text("新密码") }, singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(value = confirmPwd, onValueChange = { confirmPwd = it },
                        label = { Text("确认新密码") }, singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth())
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onConfirm(name, email, address,
                    if (changePwd) curPwd else null,
                    if (changePwd) newPwd else null,
                    if (changePwd) confirmPwd else null)
            }) { Text("保存") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("取消") } }
    )
}
