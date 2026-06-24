package com.example.bookwiseapp.ui.component

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import coil.compose.SubcomposeAsyncImage
import com.example.bookwiseapp.data.api.ApiClient
import com.example.bookwiseapp.data.api.model.BookData

@Composable
fun LoadingOverlay() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator()
    }
}

@Composable
fun ErrorMessage(message: String, onRetry: (() -> Unit)? = null) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(message, color = MaterialTheme.colorScheme.error, textAlign = TextAlign.Center)
        if (onRetry != null) {
            Spacer(Modifier.height(12.dp))
            Button(onClick = onRetry) { Text("重试") }
        }
    }
}

/** 图书封面：走本域 /api/books/{isbn}/cover/；失败时用 defaultCoverUrl 或书名占位。 */
@Composable
fun BookCover(
    book: BookData,
    modifier: Modifier = Modifier,
    defaultCoverUrl: String? = null
) {
    val primaryUrl = ApiClient.fullImageUrl(book.coverImageUrl)
    val fallbackUrl = ApiClient.fullImageUrl(defaultCoverUrl)

    if (primaryUrl != null) {
        SubcomposeAsyncImage(
            model = primaryUrl,
            contentDescription = book.title,
            modifier = modifier,
            contentScale = ContentScale.Crop,
            loading = {
                Box(modifier, contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(Modifier.size(28.dp))
                }
            },
            error = {
                if (fallbackUrl != null && fallbackUrl != primaryUrl) {
                    SubcomposeAsyncImage(
                        model = fallbackUrl,
                        contentDescription = book.title,
                        modifier = modifier,
                        contentScale = ContentScale.Crop,
                        error = { CoverPlaceholder(book, modifier) }
                    )
                } else {
                    CoverPlaceholder(book, modifier)
                }
            }
        )
    } else if (fallbackUrl != null) {
        SubcomposeAsyncImage(
            model = fallbackUrl,
            contentDescription = book.title,
            modifier = modifier,
            contentScale = ContentScale.Crop,
            error = { CoverPlaceholder(book, modifier) }
        )
    } else {
        CoverPlaceholder(book, modifier)
    }
}

@Composable
private fun CoverPlaceholder(book: BookData, modifier: Modifier) {
    Box(modifier, contentAlignment = Alignment.Center) {
        Surface(
            color = MaterialTheme.colorScheme.primaryContainer,
            modifier = Modifier.fillMaxSize()
        ) {
            Text(
                text = book.title.take(2),
                modifier = Modifier.wrapContentSize(Alignment.Center),
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
                textAlign = TextAlign.Center
            )
        }
    }
}

/** 标签 + 内容行 */
@Composable
fun InfoRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
        Text(label, style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.outline, modifier = Modifier.width(80.dp))
        Text(value, style = MaterialTheme.typography.bodyMedium)
    }
}

/** 订单状态文字（与网页端 order_detail.html 保持一致）*/
fun orderStatusText(status: Int) = when (status) {
    0 -> "已下单"
    1 -> "已发货"
    2 -> "已完成"
    4 -> "已取消"
    else -> "未知"
}

/** 付款状态文字（与网页端 order_detail.html 保持一致）*/
fun paymentStatusText(ps: Int) = when (ps) {
    0 -> "未支付"
    1 -> "已支付"
    2 -> "待补款"
    3 -> "已退款"
    else -> "未知"
}
