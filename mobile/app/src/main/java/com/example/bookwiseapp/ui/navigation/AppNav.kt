package com.example.bookwiseapp.ui.navigation

import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.example.bookwiseapp.PaymentReturn
import com.example.bookwiseapp.ui.screen.*
import com.example.bookwiseapp.util.PaymentDeepLink
import com.example.bookwiseapp.util.parsePaymentDeepLink
import com.example.bookwiseapp.viewmodel.*
import android.net.Uri
import kotlinx.coroutines.launch

object Routes {
    const val LOGIN = "login"
    const val REGISTER = "register"
    const val HOME = "home"
    const val SEARCH = "search"
    const val AI = "ai"
    const val CART = "cart"
    const val ORDER_LIST = "orders"
    const val ACCOUNT = "account"
    const val ACCOUNT_PROFILE = "account/profile"
    const val ACCOUNT_WALLET = "account/wallet"
    const val BROWSE_HISTORY = "account/browse-history"
    const val CATEGORIES = "categories"
    const val RANKINGS = "rankings"
    const val FAVORITES = "favorites"
    const val BOOK_DETAIL = "book/{isbn}"
    const val ORDER_DETAIL = "order/{orderId}"
    const val CHECKOUT = "checkout"

    fun bookDetail(isbn: String) = "book/$isbn"
    fun orderDetail(orderId: Int) = "order/$orderId"
}

data class BottomNavItem(
    val route: String,
    val label: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector
)

val bottomNavItems = listOf(
    BottomNavItem(Routes.HOME, "首页", Icons.Default.Home),
    BottomNavItem(Routes.SEARCH, "搜索", Icons.Default.Search),
    BottomNavItem(Routes.AI, "AI", Icons.Default.SmartToy),
    BottomNavItem(Routes.CART, "购物车", Icons.Default.ShoppingCart),
    BottomNavItem(Routes.ACCOUNT, "我的", Icons.Default.Person)
)

@Composable
fun AppNav(
    startLoggedIn: Boolean,
    paymentReturn: MutableState<PaymentReturn?>
) {
    val navController = rememberNavController()
    val authVm: AuthViewModel = viewModel()
    val bookVm: BookViewModel = viewModel()
    val cartVm: CartViewModel = viewModel()
    val orderVm: OrderViewModel = viewModel()
    val accountVm: AccountViewModel = viewModel()
    val aiVm: AiViewModel = viewModel()
    val favoriteVm: FavoriteViewModel = viewModel()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val cartState by cartVm.state.collectAsState()

    LaunchedEffect(cartState.message) {
        cartState.message?.let { msg ->
            snackbarHostState.showSnackbar(msg)
            cartVm.clearMessage()
        }
    }
    LaunchedEffect(cartState.error) {
        cartState.error?.let { err ->
            snackbarHostState.showSnackbar(err)
            cartVm.clearMessage()
        }
    }

    val startDest = if (startLoggedIn) Routes.HOME else Routes.LOGIN

    val mainRoutes = bottomNavItems.map { it.route }
    /** 自带底栏或需贴底的页面，不保留 Tab 栏占位 padding */
    val fullBleedBottomRoutes = setOf(
        Routes.CATEGORIES,
        Routes.RANKINGS,
        Routes.FAVORITES,
        Routes.BROWSE_HISTORY,
        Routes.ORDER_LIST,
    )
    val navBackStack by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStack?.destination?.route

    val showBottomBar = currentRoute in mainRoutes

    val handleOrderPaid: (Int, String?, com.example.bookwiseapp.data.api.model.CustomerData?) -> Unit =
        { orderId, message, account ->
            cartVm.loadCart()
            orderVm.loadOrders()
            orderVm.clearCheckoutAfterPayment()
            if (account != null) {
                accountVm.applyAccount(account, message)
            } else {
                accountVm.loadAccount()
            }
            navController.popBackStack(Routes.CHECKOUT, inclusive = true)
            navController.navigate(Routes.orderDetail(orderId)) {
                popUpTo(Routes.HOME) { saveState = true }
                launchSingleTop = true
            }
            if (account == null) {
                message?.let { msg ->
                    scope.launch { snackbarHostState.showSnackbar(msg) }
                }
            }
        }

    LaunchedEffect(startLoggedIn) {
        if (!startLoggedIn) return@LaunchedEffect
        orderVm.tryRecoverStoredPayment(
            onSuccess = handleOrderPaid,
            onSkip = {}
        )
    }

    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(lifecycleOwner, startLoggedIn) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME && startLoggedIn) {
                orderVm.tryRecoverStoredPayment(
                    onSuccess = handleOrderPaid,
                    onSkip = {}
                )
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    LaunchedEffect(paymentReturn.value?.nonce) {
        val payload = paymentReturn.value ?: return@LaunchedEffect
        val uri = payload.uri
        if (!startLoggedIn) return@LaunchedEffect
        val link = parsePaymentDeepLink(uri)

        when (link) {
            is PaymentDeepLink.OrderSuccess -> {
                orderVm.confirmStripePayment(
                    sessionId = link.sessionId,
                    orderIdHint = link.orderId,
                    onSuccess = handleOrderPaid,
                    onError = { msg ->
                        scope.launch { snackbarHostState.showSnackbar(msg) }
                    }
                )
            }
            null -> {
                val sessionId = uri.getQueryParameter("session_id")
                if (!sessionId.isNullOrBlank()) {
                    orderVm.confirmStripePayment(
                        sessionId = sessionId,
                        onSuccess = handleOrderPaid,
                        onError = { msg ->
                            scope.launch { snackbarHostState.showSnackbar(msg) }
                        }
                    )
                }
            }
            is PaymentDeepLink.OrderCancel -> {
                orderVm.abandonCheckoutOrder(link.orderId) { message ->
                    cartVm.loadCart()
                    navController.navigate(Routes.CART) {
                        popUpTo(Routes.HOME) { saveState = true }
                        launchSingleTop = true
                    }
                    scope.launch {
                        snackbarHostState.showSnackbar(message ?: "已取消支付")
                    }
                }
            }
            is PaymentDeepLink.MembershipSuccess -> {
                accountVm.confirmStripePayment(
                    sessionId = link.sessionId,
                    onSuccess = {
                        navController.navigate(Routes.ACCOUNT_WALLET) {
                            popUpTo(Routes.HOME) { saveState = true }
                            launchSingleTop = true
                        }
                    },
                    onError = { msg ->
                        scope.launch { snackbarHostState.showSnackbar(msg) }
                    }
                )
            }
            PaymentDeepLink.MembershipCancel -> {
                navController.navigate(Routes.ACCOUNT_WALLET) {
                    popUpTo(Routes.HOME) { saveState = true }
                    launchSingleTop = true
                }
                snackbarHostState.showSnackbar("已取消畅读卡支付")
            }
        }
    }

    // 记住底部导航高度：进入详情页隐藏底栏时仍保留相同 bottom padding，
    // 避免返回首页时列表区域高度突变导致滚动位置跳动。
    var stableBottomPadding by remember { mutableStateOf(Dp.Unspecified) }

    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        snackbarHost = { SnackbarHost(snackbarHostState) },
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    bottomNavItems.forEach { item ->
                        NavigationBarItem(
                            icon = { Icon(item.icon, contentDescription = item.label) },
                            label = { Text(item.label) },
                            selected = navBackStack?.destination?.hierarchy
                                ?.any { it.route == item.route } == true,
                            onClick = {
                                navController.popBackStack(Routes.CHECKOUT, inclusive = true)
                                navController.navigate(item.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        val liveBottomPadding = innerPadding.calculateBottomPadding()
        if (showBottomBar && liveBottomPadding > Dp.Hairline) {
            stableBottomPadding = liveBottomPadding
        }
        val navHostBottomPadding = when {
            showBottomBar -> liveBottomPadding
            currentRoute in fullBleedBottomRoutes -> 0.dp
            stableBottomPadding != Dp.Unspecified -> stableBottomPadding
            else -> 0.dp
        }

        NavHost(
            navController = navController,
            startDestination = startDest,
            modifier = Modifier
                .fillMaxSize()
                .padding(bottom = navHostBottomPadding)
        ) {
            // 认证
            composable(Routes.LOGIN) {
                LoginScreen(
                    viewModel = authVm,
                    onLoginSuccess = {
                        navController.navigate(Routes.HOME) {
                            popUpTo(Routes.LOGIN) { inclusive = true }
                        }
                    },
                    onGoRegister = { navController.navigate(Routes.REGISTER) }
                )
            }
            composable(Routes.REGISTER) {
                RegisterScreen(
                    viewModel = authVm,
                    onRegisterSuccess = {
                        navController.navigate(Routes.HOME) {
                            popUpTo(Routes.LOGIN) { inclusive = true }
                        }
                    },
                    onBack = { navController.popBackStack() }
                )
            }

            // 主 Tab
            composable(Routes.HOME) {
                HomeScreen(
                    viewModel = bookVm,
                    cartVm = cartVm,
                    onBookClick = { isbn -> navController.navigate(Routes.bookDetail(isbn)) }
                )
            }
            composable(Routes.SEARCH) {
                SearchScreen(
                    viewModel = bookVm,
                    cartVm = cartVm,
                    onBookClick = { isbn -> navController.navigate(Routes.bookDetail(isbn)) },
                    onCategoriesClick = { navController.navigate(Routes.CATEGORIES) },
                    onRankingsClick = { navController.navigate(Routes.RANKINGS) }
                )
            }
            composable(Routes.AI) {
                AiChatScreen(viewModel = aiVm)
            }
            composable(Routes.CART) {
                CartScreen(
                    viewModel = cartVm,
                    onCheckout = {
                        navController.navigate(Routes.CHECKOUT) {
                            launchSingleTop = true
                        }
                    },
                    onOrdersClick = { navController.navigate(Routes.ORDER_LIST) }
                )
            }
            composable(Routes.ACCOUNT) {
                AccountScreen(
                    onProfileClick = { navController.navigate(Routes.ACCOUNT_PROFILE) },
                    onWalletClick = { navController.navigate(Routes.ACCOUNT_WALLET) },
                    onFavoritesClick = { navController.navigate(Routes.FAVORITES) },
                    onBrowseHistoryClick = { navController.navigate(Routes.BROWSE_HISTORY) },
                    onLogout = {
                        authVm.logout {
                            navController.navigate(Routes.LOGIN) {
                                popUpTo(0) { inclusive = true }
                            }
                        }
                    }
                )
            }

            composable(Routes.ACCOUNT_PROFILE) {
                AccountProfileScreen(
                    viewModel = accountVm,
                    onBack = { navController.popBackStack() }
                )
            }

            composable(Routes.ACCOUNT_WALLET) { backStackEntry ->
                LaunchedEffect(backStackEntry) {
                    accountVm.loadAccount()
                }
                AccountWalletScreen(
                    viewModel = accountVm,
                    onBack = { navController.popBackStack() }
                )
            }

            composable(Routes.BROWSE_HISTORY) {
                BrowseHistoryScreen(
                    viewModel = accountVm,
                    onBookClick = { isbn -> navController.navigate(Routes.bookDetail(isbn)) },
                    onBack = { navController.popBackStack() }
                )
            }

            composable(Routes.ORDER_LIST) {
                OrderListScreen(
                    viewModel = orderVm,
                    onOrderClick = { id -> navController.navigate(Routes.orderDetail(id)) },
                    onBack = { navController.popBackStack() }
                )
            }

            composable(Routes.CATEGORIES) {
                CategoriesScreen(
                    viewModel = bookVm,
                    onBookClick = { isbn -> navController.navigate(Routes.bookDetail(isbn)) },
                    onBack = { navController.popBackStack() }
                )
            }
            composable(Routes.RANKINGS) {
                RankingsScreen(
                    viewModel = bookVm,
                    onBookClick = { isbn -> navController.navigate(Routes.bookDetail(isbn)) },
                    onBack = { navController.popBackStack() }
                )
            }
            composable(Routes.FAVORITES) {
                FavoriteFoldersScreen(
                    viewModel = favoriteVm,
                    onBookClick = { isbn -> navController.navigate(Routes.bookDetail(isbn)) },
                    onBack = { navController.popBackStack() }
                )
            }

            // 详情页
            composable(
                route = Routes.BOOK_DETAIL,
                arguments = listOf(navArgument("isbn") { type = NavType.StringType })
            ) { backStack ->
                val isbn = backStack.arguments?.getString("isbn") ?: return@composable
                BookDetailScreen(
                    isbn = isbn,
                    viewModel = bookVm,
                    cartVm = cartVm,
                    onBack = { navController.popBackStack() }
                )
            }
            composable(
                route = Routes.ORDER_DETAIL,
                arguments = listOf(navArgument("orderId") { type = NavType.IntType })
            ) { backStack ->
                val orderId = backStack.arguments?.getInt("orderId") ?: return@composable
                OrderDetailScreen(
                    orderId = orderId,
                    orderVm = orderVm,
                    accountVm = accountVm,
                    onBack = { navController.popBackStack() }
                )
            }
            composable(Routes.CHECKOUT) { backStackEntry ->
                LaunchedEffect(backStackEntry) {
                    orderVm.beginCheckout(
                        onEmptyCart = {
                            navController.popBackStack(Routes.CHECKOUT, inclusive = true)
                        }
                    )
                    accountVm.loadAccount()
                }
                CheckoutScreen(
                    orderVm = orderVm,
                    accountVm = accountVm,
                    onBack = {
                        orderVm.clearCheckoutAfterPayment()
                        navController.popBackStack()
                    },
                    onOrderPaid = handleOrderPaid
                )
            }
        }
    }
}
