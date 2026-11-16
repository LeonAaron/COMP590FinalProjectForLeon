from patchlib import DISCLAIMER, INDEX_CONTEXT, TEMPLATE, append, insert_before, write

write(
    "stockapp/alerts.py",
    '''
    """In-memory price alerts, stored per Flask app instance."""

    from __future__ import annotations

    from dataclasses import dataclass, field

    from flask import current_app

    from stockapp.stocks import latest_bar


    @dataclass
    class AlertStore:
        alerts: dict[int, dict] = field(default_factory=dict)
        next_id: int = 1

        def add(self, ticker: str, direction: str, price: float) -> dict:
            alert = {"id": self.next_id, "ticker": ticker, "direction": direction, "price": float(price)}
            self.alerts[self.next_id] = alert
            self.next_id += 1
            return with_status(alert)

        def list(self, ticker: str | None = None) -> list[dict]:
            return [with_status(a) for a in self.alerts.values() if ticker is None or a["ticker"] == ticker]


    def with_status(alert: dict) -> dict:
        close = latest_bar(alert["ticker"]).close
        hit = close >= alert["price"] if alert["direction"] == "above" else close <= alert["price"]
        return {**alert, "triggered": hit}


    def store() -> AlertStore:
        return current_app.extensions.setdefault("alerts", AlertStore())
    ''',
)

insert_before(
    "stockapp/routes.py",
    INDEX_CONTEXT,
    "        alerts=alert_store().list(selected),\n",
)
append(
    "stockapp/routes.py",
    '''
    from stockapp.alerts import store as alert_store  # noqa: E402


    @bp.post("/api/alerts")
    def create_alert() -> ResponseReturnValue:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify({"error": "body must be a JSON object"}), 400
        ticker, direction, price = body.get("ticker"), body.get("direction"), body.get("price")
        if not isinstance(ticker, str):
            return jsonify({"error": "ticker must be a string"}), 400
        try:
            symbol = normalize_ticker(ticker)
        except UnknownTickerError:
            return jsonify({"error": f"Unknown ticker: {ticker}"}), 400
        if direction not in ("above", "below"):
            return jsonify({"error": "direction must be 'above' or 'below'"}), 400
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price <= 0:
            return jsonify({"error": "price must be a number greater than 0"}), 400
        return jsonify(alert_store().add(symbol, direction, price)), 201


    @bp.get("/api/alerts")
    def list_alerts() -> ResponseReturnValue:
        raw = request.args.get("ticker")
        try:
            symbol = normalize_ticker(raw) if raw is not None else None
        except UnknownTickerError:
            return jsonify({"error": f"Unknown ticker: {raw}"}), 400
        return jsonify({"alerts": alert_store().list(symbol)})


    @bp.delete("/api/alerts/<int:alert_id>")
    def delete_alert(alert_id: int) -> ResponseReturnValue:
        if alert_store().alerts.pop(alert_id, None) is None:
            return jsonify({"error": f"no alert with id {alert_id}"}), 404
        return "", 204
    ''',
)

insert_before(
    TEMPLATE,
    DISCLAIMER,
    """      <section id="alerts" class="panel">
        <div class="panel-head"><h3 class="panel-title">Price Alerts</h3></div>
        {% if alerts %}
        <ul>
          {% for a in alerts %}
          <li class="alert-item{{ ' triggered' if a.triggered }}" data-alert-id="{{ a.id }}">{{ a.direction }} {{ "%.2f"|format(a.price) }}</li>
          {% endfor %}
        </ul>
        {% else %}
        <p class="empty">No alerts for {{ selected }}</p>
        {% endif %}
      </section>

""",
)
