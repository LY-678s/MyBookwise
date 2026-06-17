/**
 * 在 htmlcov_order/function_index.html 浏览器 DevTools Console 中粘贴运行。
 * 作用：仅显示成员 B 订单模块的被测函数，并重算 footer / 顶部总覆盖率。
 * 用法：
 *   1. 浏览器打开 d:\Engineering\MyBookwise\htmlcov_order\function_index.html
 *   2. F12 → Console 标签
 *   3. 全选本文件内容粘贴运行
 */
(function () {
    const ORDER_FUNCS = new Set([
        // models.py 订单相关
        "Orders.__str__",
        "Orderdetail.__str__",
        // views.py 订单视图
        "cart_add",
        "cart_update",
        "cart_remove",
        "cart_detail",
        "order_confirm",
        "order_list",
        "order_detail",
        "cancel_order",
        "confirm_receipt",
        // 订单模块依赖的辅助
        "customer_required",
        "_get_cart",
        "_save_cart",
    ]);

    const table = document.querySelector("table.index");
    if (!table) {
        console.error("未找到 table.index");
        return;
    }
    const tbody = table.querySelector("tbody");
    const rows = tbody.querySelectorAll("tr.region");
    const footer = table.tFoot.rows[0];

    // 区分 footer 中的数值列与百分比列
    const ratioCells = [];
    const numCells = [];
    for (let i = 0; i < footer.cells.length; i++) {
        const c = footer.cells[i];
        if (c.matches(".name, .spacer")) continue;
        if (c.dataset.ratio !== undefined) ratioCells.push(i);
        else numCells.push(i);
    }

    const ratioAcc = {};
    ratioCells.forEach((i) => (ratioAcc[i] = { n: 0, d: 0 }));
    const numAcc = {};
    numCells.forEach((i) => (numAcc[i] = 0));

    let visible = 0;
    rows.forEach((row) => {
        const fnName = (row.cells[1] && row.cells[1].textContent || "").trim();
        if (ORDER_FUNCS.has(fnName)) {
            row.style.display = "";
            visible++;
            ratioCells.forEach((i) => {
                const r = row.cells[i].dataset.ratio;
                if (r) {
                    const [n, d] = r.split(" ").map(Number);
                    ratioAcc[i].n += n;
                    ratioAcc[i].d += d;
                }
            });
            numCells.forEach((i) => {
                const v = parseInt(row.cells[i].textContent, 10);
                if (!isNaN(v)) numAcc[i] += v;
            });
        } else {
            row.style.display = "none";
        }
    });

    ratioCells.forEach((i) => {
        const c = footer.cells[i];
        const match = /\.([0-9]+)/.exec(c.textContent);
        const places = match ? match[1].length : 0;
        const { n, d } = ratioAcc[i];
        c.dataset.ratio = `${n} ${d}`;
        c.textContent = d ? `${((n * 100) / d).toFixed(places)}%` : "100%";
    });
    numCells.forEach((i) => {
        footer.cells[i].textContent = numAcc[i];
    });

    // 更新顶部大字总覆盖率
    const lastRatio = ratioCells[ratioCells.length - 1];
    const total = lastRatio !== undefined ? ratioAcc[lastRatio] : null;
    if (total && total.d) {
        const pct = Math.round((total.n * 100) / total.d);
        const h = document.querySelector("h1 .pc_cov");
        if (h) h.textContent = `${pct}%`;
    }

    console.log(`[订单模块过滤] 已显示 ${visible} 个函数，其余已隐藏。截图前请勿再动 filter / hide 100 控件。`);
})();
