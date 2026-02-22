import { Link, useSearchParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { confirmDemoCheckout } from "../api/catalog";

export function CheckoutProcessingPage() {
  const [searchParams] = useSearchParams();
  const orderId = Number(searchParams.get("order_id"));

  const confirmMutation = useMutation({
    mutationFn: () => confirmDemoCheckout({ order_id: orderId })
  });

  if (!Number.isFinite(orderId) || orderId < 1) {
    return (
      <section className="page page-shell">
        <p className="status error">Invalid checkout URL. Missing order ID.</p>
      </section>
    );
  }

  return (
    <section className="page page-shell checkout-page">
      <div className="checkout-card">
        <p className="hero-kicker">Checkout Processing</p>
        <h2>Complete payment</h2>
        <p>
          Order #{orderId} is pending. For local demo mode, confirm payment to trigger ticket
          generation.
        </p>

        {!confirmMutation.isSuccess && (
          <button
            type="button"
            disabled={confirmMutation.isPending}
            onClick={() => confirmMutation.mutate()}
          >
            {confirmMutation.isPending ? "Confirming..." : "Simulate payment success"}
          </button>
        )}

        {confirmMutation.isError && (
          <p className="status error">{confirmMutation.error.message}</p>
        )}

        {confirmMutation.isSuccess && (
          <div className="checkout-success">
            <p>
              Payment status: <strong>{confirmMutation.data.order_status}</strong>
            </p>
            <p>Tickets generated: {confirmMutation.data.ticket_count}</p>
            {confirmMutation.data.tickets.length > 0 && (
              <ul>
                {confirmMutation.data.tickets.map((ticket) => (
                  <li key={ticket.id}>
                    Seat #{ticket.seat_id} • Token {ticket.qr_token.slice(0, 16)}...
                  </li>
                ))}
              </ul>
            )}
            <Link to="/movies">Back to movies</Link>
          </div>
        )}
      </div>
    </section>
  );
}
