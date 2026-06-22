package com.example.bookwiseapp.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.example.bookwiseapp.ui.screen.*
import com.example.bookwiseapp.viewmodel.*

object Routes {
    const val LOGIN = "login"
    const val REGISTER = "register"
    const val HOME = "home"
    const val SEARCH = "search"
    const val AI = "ai"
    const val CART = "cart"
    const val ORDER_LIST = "orders"
    const val ACCOUNT = "account"
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
    BottomNavItem(Routes.ORDER_LIST, "订单", Icons.Default.List),
    BottomNavItem(Routes.ACCOUNT, "我的", Icons.Default.Person)
)

@Composable
fun AppNav(startLoggedIn: Boolean) {
    val navController = rememberNavController()
    val authVm: AuthViewModel = viewModel()
    val bookVm: BookViewModel = viewModel()
    val cartVm: CartViewModel = viewModel()
    val orderVm: OrderViewModel = viewModel()
    val accountVm: AccountViewModel = viewModel()
    val aiVm: AiViewModel = viewModel()

    val startDest = if (startLoggedIn) Routes.HOME else Routes.LOGIN

    val mainRoutes = bottomNavItems.map { it.route }
    val navBackStack by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStack?.destination?.route

    val showBottomBar = currentRoute in mainRoutes

    Scaffold(
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
        NavHost(
            navController = navController,
            startDestination = startDest,
            modifier = Modifier.padding(innerPadding)
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
                    onBookClick = { isbn -> navController.navigate(Routes.bookDetail(isbn)) }
                )
            }
            composable(Routes.AI) {
                AiChatScreen(viewModel = aiVm)
            }
            composable(Routes.CART) {
                CartScreen(
                    viewModel = cartVm,
                    onCheckout = { navController.navigate(Routes.CHECKOUT) }
                )
            }
            composable(Routes.ORDER_LIST) {
                OrderListScreen(
                    viewModel = orderVm,
                    onOrderClick = { id -> navController.navigate(Routes.orderDetail(id)) }
                )
            }
            composable(Routes.ACCOUNT) {
                AccountScreen(
                    viewModel = accountVm,
                    onLogout = {
                        authVm.logout {
                            navController.navigate(Routes.LOGIN) {
                                popUpTo(0) { inclusive = true }
                            }
                        }
                    }
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
                    viewModel = orderVm,
                    onBack = { navController.popBackStack() }
                )
            }
            composable(Routes.CHECKOUT) {
                CheckoutScreen(
                    orderVm = orderVm,
                    accountVm = accountVm,
                    onOrderCreated = { orderId ->
                        navController.navigate(Routes.orderDetail(orderId)) {
                            popUpTo(Routes.CHECKOUT) { inclusive = true }
                        }
                    },
                    onBack = { navController.popBackStack() }
                )
            }
        }
    }
}
