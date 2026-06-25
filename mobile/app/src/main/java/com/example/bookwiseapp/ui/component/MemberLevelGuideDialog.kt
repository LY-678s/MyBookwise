package com.example.bookwiseapp.ui.component

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.bookwiseapp.data.api.model.MemberLevelGuideItem

@Composable
fun MemberLevelGuideDialog(
    guide: List<MemberLevelGuideItem>,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("会员等级说明") },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    "免费开通会员后从 1 级起步；积分按消费 1:1 累计（取整），达到阈值自动升级。",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.outline
                )
                guide.forEach { row ->
                    Text("${row.level} 级 · 累计 ${row.pointsRequired} 积分 · ${row.discountPercent}% 优惠")
                }
                Text(
                    "畅读卡（¥20/月）在等级折扣基础上再乘 7.2 折。",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.outline
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("关闭") }
        }
    )
}
