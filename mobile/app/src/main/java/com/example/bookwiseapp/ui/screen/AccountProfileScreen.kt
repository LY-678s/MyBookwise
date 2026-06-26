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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.ui.component.ErrorMessage
import com.example.bookwiseapp.ui.component.InfoRow
import com.example.bookwiseapp.ui.component.LoadingOverlay
import com.example.bookwiseapp.viewmodel.AccountViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountProfileScreen(
    viewModel: AccountViewModel,
    onBack: () -> Unit
) {
    val state by viewModel.state.collectAsState()
    val account = state.account
    var showEdit by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.loadAccount()
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
                title = { Text("基本信息") },
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
                        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            InfoRow("用户名", account.username)
                            InfoRow("姓名", account.name)
                            InfoRow("邮箱", account.email ?: "未设置")
                            InfoRow("地址", account.address ?: "未设置")
                            account.registerDate?.let { InfoRow("注册时间", it.take(10)) }
                        }
                    }
                    Button(
                        onClick = { showEdit = true },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("编辑资料") }
                }
            }
        }
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
fun EditProfileDialog(
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
