(function () {
    function parseJsonScript(id, fallback) {
        const el = document.getElementById(id);
        if (!el) {
            return fallback;
        }

        try {
            return JSON.parse(el.textContent);
        } catch (err) {
            return fallback;
        }
    }

    const monthlyGrowth = parseJsonScript("monthly-growth-data", []);
    const monthlyCashflow = parseJsonScript("monthly-cashflow-data", []);
    const expenseBreakdown = parseJsonScript("expense-breakdown-data", {});
    const backendPayload = parseJsonScript("backend-payload-data", {});
    const backendErrors = parseJsonScript("backend-errors-data", []);

    function formatNumber(value) {
        return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
    }

    function normalizedGrowthRows() {
        return monthlyGrowth.map(function (row, idx) {
            return {
                label: row.PeriodLabel || row.MonthName || String(idx + 1),
                revenue: Number(row.MonthRevenue || 0),
                profit: Number(row.MonthProfit || 0),
            };
        });
    }

    function normalizedCashflowRows() {
        return monthlyCashflow.map(function (row, idx) {
            return {
                label: row.PeriodLabel || String(row.MonthNum || idx + 1),
                cashIn: Number(row.CashIn || 0),
                cashOut: Number(row.CashOut || 0),
                netCash: Number(row.NetCash || 0),
            };
        });
    }

    function computePeriodKpis(growthRows, cashflowRows) {
        const revenueEl = document.getElementById("periodRevenue");
        const profitEl = document.getElementById("periodProfit");
        const marginEl = document.getElementById("periodMargin");
        const netCashEl = document.getElementById("periodNetCash");

        if (!growthRows.length || !cashflowRows.length) {
            if (revenueEl) {
                revenueEl.textContent = "N/A";
            }
            if (profitEl) {
                profitEl.textContent = "N/A";
            }
            if (marginEl) {
                marginEl.textContent = "N/A";
            }
            if (netCashEl) {
                netCashEl.textContent = "N/A";
            }
            return;
        }

        const revenue = growthRows.reduce(function (acc, row) { return acc + Number(row.revenue || 0); }, 0);
        const profit = growthRows.reduce(function (acc, row) { return acc + Number(row.profit || 0); }, 0);
        const margin = revenue > 0 ? (profit / revenue) * 100 : 0;
        const netCash = cashflowRows.reduce(function (acc, row) { return acc + Number(row.netCash || 0); }, 0);

        if (revenueEl) {
            revenueEl.textContent = "NPR " + formatNumber(revenue);
        }
        if (profitEl) {
            profitEl.textContent = "NPR " + formatNumber(profit);
        }
        if (marginEl) {
            marginEl.textContent = margin.toFixed(2) + "%";
        }
        if (netCashEl) {
            netCashEl.textContent = "NPR " + formatNumber(netCash);
        }
    }

    function setupCharts() {
        if (typeof ApexCharts !== "function") {
            return null;
        }

        const growthChart = new ApexCharts(document.querySelector("#growthChart"), {
            chart: { type: "line", height: 320, toolbar: { show: false } },
            series: [
                { name: "Revenue", data: [] },
                { name: "Profit", data: [] },
            ],
            noData: { text: "No growth data available" },
            xaxis: { categories: [] },
            stroke: { width: [3, 3], curve: "smooth" },
            colors: ["#0A9396", "#CA6702"],
            legend: { position: "top" },
        });

        const cashflowChart = new ApexCharts(document.querySelector("#cashflowChart"), {
            chart: { type: "bar", height: 320, toolbar: { show: false } },
            series: [
                { name: "Cash In", data: [] },
                { name: "Cash Out", data: [] },
                { name: "Net Cash", data: [] },
            ],
            noData: { text: "No cashflow data available" },
            xaxis: { categories: [] },
            colors: ["#005F73", "#BB3E03", "#94D2BD"],
            plotOptions: { bar: { borderRadius: 4, columnWidth: "45%" } },
            legend: { position: "top" },
        });

        const expenseLabels = Object.keys(expenseBreakdown || {});
        const expenseSeries = expenseLabels.map(function (label) {
            return Number(expenseBreakdown[label] || 0);
        });

        const expenseChart = new ApexCharts(document.querySelector("#expenseChart"), {
            chart: { type: "donut", height: 320 },
            labels: expenseLabels,
            series: expenseSeries,
            noData: { text: "No expense data available" },
            colors: ["#005F73", "#0A9396", "#94D2BD", "#EE9B00", "#CA6702", "#BB3E03", "#AE2012"],
            legend: { position: "bottom" },
        });

        growthChart.render();
        cashflowChart.render();
        expenseChart.render();

        return { growthChart: growthChart, cashflowChart: cashflowChart };
    }

    function renderBucketList(rows) {
        const list = document.getElementById("periodBucketList");
        if (!list) {
            return;
        }
        list.innerHTML = "";
        rows.forEach(function (row) {
            const li = document.createElement("li");
            li.textContent = row.label;
            list.appendChild(li);
        });
    }

    function renderFromBackendPeriod(charts) {
        const growthRows = normalizedGrowthRows();
        const cashRows = normalizedCashflowRows();

        if (charts) {
            charts.growthChart.updateOptions({
                xaxis: { categories: growthRows.map(function (row) { return row.label; }) },
            });
            charts.growthChart.updateSeries([
                { name: "Revenue", data: growthRows.map(function (row) { return row.revenue; }) },
                { name: "Profit", data: growthRows.map(function (row) { return row.profit; }) },
            ]);

            charts.cashflowChart.updateOptions({
                xaxis: { categories: cashRows.map(function (row) { return row.label; }) },
            });
            charts.cashflowChart.updateSeries([
                { name: "Cash In", data: cashRows.map(function (row) { return row.cashIn; }) },
                { name: "Cash Out", data: cashRows.map(function (row) { return row.cashOut; }) },
                { name: "Net Cash", data: cashRows.map(function (row) { return row.netCash; }) },
            ]);
        }

        computePeriodKpis(growthRows, cashRows);
        renderBucketList(growthRows);
    }

    function enableTableFilter(inputId, tableId) {
        const input = document.getElementById(inputId);
        const table = document.getElementById(tableId);
        if (!input || !table) {
            return;
        }

        const rows = Array.from(table.querySelectorAll("tbody tr"));
        input.addEventListener("input", function () {
            const query = input.value.trim().toLowerCase();
            rows.forEach(function (row) {
                const rowText = row.textContent.toLowerCase();
                row.style.display = rowText.indexOf(query) === -1 ? "none" : "";
            });
        });
    }

    function enableSectionSpy() {
        const navLinks = Array.from(document.querySelectorAll(".side-nav a"));
        const sections = navLinks
            .map(function (link) {
                return document.querySelector(link.getAttribute("href"));
            })
            .filter(Boolean);

        navLinks.forEach(function (link) {
            link.addEventListener("click", function (event) {
                event.preventDefault();
                const target = document.querySelector(link.getAttribute("href"));
                if (target) {
                    target.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            });
        });

        if (!sections.length || typeof IntersectionObserver !== "function") {
            return;
        }

        const observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    const id = entry.target.getAttribute("id");
                    navLinks.forEach(function (link) {
                        const active = link.getAttribute("href") === "#" + id;
                        link.classList.toggle("active", active);
                    });
                });
            },
            {
                rootMargin: "-20% 0px -65% 0px",
                threshold: [0.1, 0.4, 0.7],
            }
        );

        sections.forEach(function (section) {
            observer.observe(section);
        });
    }

    function renderBackendInspector() {
        const endpointSelect = document.getElementById("endpointSelect");
        const endpointJson = document.getElementById("endpointJson");
        const errorJson = document.getElementById("errorJson");
        if (!endpointSelect || !endpointJson || !errorJson) {
            return;
        }

        const keys = Object.keys(backendPayload || {}).sort();
        endpointSelect.innerHTML = "";
        keys.forEach(function (key) {
            const option = document.createElement("option");
            option.value = key;
            option.textContent = key;
            endpointSelect.appendChild(option);
        });

        function paintJson() {
            if (!keys.length) {
                endpointJson.textContent = "{}";
                return;
            }
            const selected = endpointSelect.value || keys[0];
            endpointJson.textContent = JSON.stringify(backendPayload[selected], null, 2);
        }

        endpointSelect.addEventListener("change", paintJson);
        paintJson();
        errorJson.textContent = JSON.stringify(backendErrors, null, 2);
    }

    const charts = setupCharts();
    renderFromBackendPeriod(charts);

    enableTableFilter("productsFilter", "productsTable");
    enableTableFilter("reorderFilter", "reorderTable");
    enableTableFilter("breakevenFilter", "breakevenTable");
    enableSectionSpy();
    renderBackendInspector();

    const scopeForm = document.getElementById("scopeForm");
    const periodSelect = document.getElementById("periodSelect");
    const bucketSelect = document.getElementById("bucketSelect");
    if (scopeForm && periodSelect && bucketSelect) {
        periodSelect.addEventListener("change", function () {
            bucketSelect.value = "all";
            scopeForm.submit();
        });
    }
})();
