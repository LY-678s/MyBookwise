package com.example.bookwiseapp.ui.screen

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AccountScreen(
    onProfileClick: () -> Unit,
    onWalletClick: () -> Unit,
    onFavoritesClick: () -> Unit,
    onBrowseHistoryClick: () -> Unit,
    onLogout: () -> Unit
) {
    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        topBar = { TopAppBar(title = { Text("我的") }) }
    ) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Card(Modifier.fillMaxWidth()) {
                Column {
                    AccountMenuItem(
                        icon = Icons.Default.Badge,
                        label = "基本信息",
                        onClick = onProfileClick
                    )
                    HorizontalDivider()
                    AccountMenuItem(
                        icon = Icons.Default.WorkspacePremium,
                        label = "会员与积分",
                        onClick = onWalletClick
                    )
                    HorizontalDivider()
                    AccountMenuItem(
                        icon = Icons.Default.Favorite,
                        label = "收藏夹",
                        onClick = onFavoritesClick
                    )
                    HorizontalDivider()
                    AccountMenuItem(
                        icon = Icons.Default.History,
                        label = "最近浏览",
                        onClick = onBrowseHistoryClick
                    )
                }
            }

            OutlinedButton(
                onClick = onLogout,
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.error
                ),
                modifier = Modifier.fillMaxWidth()
            ) { Text("退出登录") }
        }
    }
}

@Composable
private fun AccountMenuItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    onClick: () -> Unit
) {
    Row(
        Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 18.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.outline)
        Text(label, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
        Icon(Icons.Default.ChevronRight, contentDescription = null, tint = MaterialTheme.colorScheme.outline)
    }
}
