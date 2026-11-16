// Draws a candlestick + volume chart for the selected ticker (TradingView lightweight-charts).
(function () {
  const container = document.getElementById("price-chart");
  const legend = document.getElementById("ohlc-legend");
  const select = document.getElementById("ticker-select");

  const UP = "#16a34a";
  const DOWN = "#dc2626";
  const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
  const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

  function showLegend(bar) {
    if (!bar) return;
    const cls = bar.close >= bar.open ? "up" : "down";
    legend.innerHTML =
      `<span>${bar.date}</span>` +
      `<span>O <b>${usd.format(bar.open)}</b></span>` +
      `<span>H <b>${usd.format(bar.high)}</b></span>` +
      `<span>L <b>${usd.format(bar.low)}</b></span>` +
      `<span>C <b class="${cls}">${usd.format(bar.close)}</b></span>` +
      `<span>Vol <b>${compact.format(bar.volume)}</b></span>`;
  }

  async function render(ticker) {
    const resp = await fetch(`/api/stocks/${encodeURIComponent(ticker)}`);
    if (!resp.ok) return;
    const { prices } = await resp.json();
    const byDate = new Map(prices.map((p) => [p.date, p]));

    const chart = LightweightCharts.createChart(container, {
      autoSize: true,
      layout: { background: { type: "solid", color: "#ffffff" }, textColor: "#64748b", fontSize: 12 },
      grid: { vertLines: { color: "#f1f5f9" }, horzLines: { color: "#f1f5f9" } },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.08, bottom: 0.25 } },
      timeScale: { borderVisible: false },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      localization: { priceFormatter: (p) => usd.format(p) },
    });

    const candles = chart.addCandlestickSeries({
      upColor: UP,
      downColor: DOWN,
      borderUpColor: UP,
      borderDownColor: DOWN,
      wickUpColor: UP,
      wickDownColor: DOWN,
    });
    candles.setData(prices.map((p) => ({ time: p.date, open: p.open, high: p.high, low: p.low, close: p.close })));

    const volume = chart.addHistogramSeries({ priceFormat: { type: "volume" }, priceScaleId: "", lastValueVisible: false, priceLineVisible: false });
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    volume.setData(prices.map((p) => ({
      time: p.date,
      value: p.volume,
      color: p.close >= p.open ? "rgba(22, 163, 74, 0.35)" : "rgba(220, 38, 38, 0.35)",
    })));

    chart.timeScale().fitContent();

    // Legend shows the hovered day's OHLC, falling back to the latest day.
    const latest = prices[prices.length - 1];
    showLegend(latest);
    chart.subscribeCrosshairMove((param) => {
      showLegend(param.time ? byDate.get(param.time) : latest);
    });
  }

  select.addEventListener("change", () => select.form.submit());
  render(container.dataset.ticker);
})();
