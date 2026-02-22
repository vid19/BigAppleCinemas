import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import {
  confirmDemoCheckout,
  fetchCheckoutOrderStatus,
  fetchReservation
} from "../api/catalog";

const PAYMENT_METHODS = [
  { id: "CARD", label: "Card" },
  { id: "APPLE_PAY", label: "Apple Pay" },
  { id: "PAYPAL", label: "PayPal" }
];

function toCurrency(totalCents, currency) {
  if (!Number.isFinite(totalCents) || totalCents < 0) {
    return "TBD";
  }
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: currency || "USD"
  }).format(totalCents / 100);
}

function normalizeCardNumber(value) {
  return value.replace(/\D/g, "").slice(0, 16);
}

function formatCardNumberInput(value) {
  return normalizeCardNumber(value).replace(/(\d{4})(?=\d)/g, "$1 ");
}

export function CheckoutProcessingPage() {
  const [searchParams] = useSearchParams();
  const orderId = Number(searchParams.get("order_id"));
  const reservationId = Number(searchParams.get("reservation_id"));
  const totalCents = Number(searchParams.get("total_cents"));
  const currency = searchParams.get("currency") || "USD";
  const provider = searchParams.get("provider") || "MOCK_STRIPE";
  const checkoutStatus = searchParams.get("status");
  const seatCountFromParams = Number(searchParams.get("seat_count"));

  const [paymentMethod, setPaymentMethod] = useState("CARD");
  const [isProcessing, setIsProcessing] = useState(false);
  const [formError, setFormError] = useState("");
  const [paymentForm, setPaymentForm] = useState({
    email: "",
    cardholder: "",
    cardNumber: "4242 4242 4242 4242",
    expiry: "12/30",
    cvc: "123"
  });

  const reservationQuery = useQuery({
    queryKey: ["reservation", reservationId],
    queryFn: () => fetchReservation(reservationId),
    enabled: Number.isFinite(reservationId) && reservationId > 0
  });
  const orderStatusQuery = useQuery({
    queryKey: ["checkout-order-status", orderId],
    queryFn: () => fetchCheckoutOrderStatus(orderId),
    enabled: Number.isFinite(orderId) && orderId > 0,
    refetchInterval: (query) => {
      const statusValue = query.state.data?.order_status;
      return statusValue === "PAID" || statusValue === "FAILED" ? false : 3000;
    }
  });

  const heldSeatIds = reservationQuery.data?.seat_ids ?? [];
  const seatCount = heldSeatIds.length || (Number.isFinite(seatCountFromParams) ? seatCountFromParams : 0);
  const summaryTotal = Number.isFinite(totalCents) ? totalCents : seatCount * 1500;
  const totalLabel = useMemo(() => toCurrency(summaryTotal, currency), [summaryTotal, currency]);

  const confirmMutation = useMutation({
    mutationFn: () => confirmDemoCheckout({ order_id: orderId })
  });
  const liveOrderStatus = orderStatusQuery.data?.order_status;
  const isPaid = liveOrderStatus === "PAID" || confirmMutation.data?.order_status === "PAID";
  const shouldShowDemoForm = provider === "MOCK_STRIPE" && !isPaid;
  const paymentResultTickets = confirmMutation.data?.tickets ?? orderStatusQuery.data?.tickets ?? [];
  const paymentResultTicketCount =
    confirmMutation.data?.ticket_count ?? orderStatusQuery.data?.ticket_count ?? 0;

  function validateForm() {
    if (paymentMethod !== "CARD") {
      return true;
    }
    const digits = normalizeCardNumber(paymentForm.cardNumber);
    if (!paymentForm.email.includes("@")) {
      setFormError("Enter a valid email for receipt delivery.");
      return false;
    }
    if (paymentForm.cardholder.trim().length < 2) {
      setFormError("Enter the cardholder name.");
      return false;
    }
    if (digits.length !== 16) {
      setFormError("Enter a valid 16-digit card number.");
      return false;
    }
    if (!/^\d{2}\/\d{2}$/.test(paymentForm.expiry)) {
      setFormError("Use expiry in MM/YY format.");
      return false;
    }
    if (!/^\d{3,4}$/.test(paymentForm.cvc)) {
      setFormError("Enter a valid CVC.");
      return false;
    }
    if (digits.endsWith("0002")) {
      setFormError("Card declined in demo mode. Try 4242 4242 4242 4242.");
      return false;
    }
    return true;
  }

  function handleSubmitPayment(event) {
    event.preventDefault();
    setFormError("");
    if (!validateForm()) {
      return;
    }
    setIsProcessing(true);
    window.setTimeout(() => {
      setIsProcessing(false);
      confirmMutation.mutate();
    }, 1000);
  }

  if (!Number.isFinite(orderId) || orderId < 1) {
    return (
      <section className="page page-shell">
        <p className="status error">Invalid checkout URL. Missing order ID.</p>
      </section>
    );
  }

  return (
    <section className="page page-shell checkout-page checkout-page-modern">
      <div className="checkout-grid">
        <div className="checkout-card checkout-payment-card">
          <p className="hero-kicker">Checkout</p>
          <h2>Complete payment</h2>
          <p>
            Order #{orderId} is reserved. Finish payment before your seat hold expires.
          </p>

          {provider !== "MOCK_STRIPE" && (
            <p className="checkout-demo-note">
              {checkoutStatus === "success"
                ? "Stripe redirected back. Waiting for webhook confirmation..."
                : checkoutStatus === "cancel"
                  ? "Stripe checkout was canceled. You can retry from seat selection."
                  : "Complete payment in Stripe, then return here for status."}
            </p>
          )}

          {shouldShowDemoForm && (
            <form className="checkout-form" onSubmit={handleSubmitPayment}>
              <div className="payment-method-grid">
                {PAYMENT_METHODS.map((method) => (
                  <button
                    className={`payment-method-chip ${paymentMethod === method.id ? "is-active" : ""}`}
                    key={method.id}
                    onClick={() => setPaymentMethod(method.id)}
                    type="button"
                  >
                    {method.label}
                  </button>
                ))}
              </div>

              {paymentMethod === "CARD" && (
                <div className="checkout-fields">
                  <label>
                    Email receipt
                    <input
                      placeholder="you@example.com"
                      type="email"
                      value={paymentForm.email}
                      onChange={(event) =>
                        setPaymentForm((prev) => ({ ...prev, email: event.target.value }))
                      }
                    />
                  </label>
                  <label>
                    Cardholder name
                    <input
                      placeholder="Cardholder"
                      value={paymentForm.cardholder}
                      onChange={(event) =>
                        setPaymentForm((prev) => ({ ...prev, cardholder: event.target.value }))
                      }
                    />
                  </label>
                  <label>
                    Card number
                    <input
                      inputMode="numeric"
                      placeholder="4242 4242 4242 4242"
                      value={paymentForm.cardNumber}
                      onChange={(event) =>
                        setPaymentForm((prev) => ({
                          ...prev,
                          cardNumber: formatCardNumberInput(event.target.value)
                        }))
                      }
                    />
                  </label>
                  <div className="checkout-inline-fields">
                    <label>
                      Expiry
                      <input
                        inputMode="numeric"
                        maxLength={5}
                        placeholder="MM/YY"
                        value={paymentForm.expiry}
                        onChange={(event) =>
                          setPaymentForm((prev) => ({ ...prev, expiry: event.target.value }))
                        }
                      />
                    </label>
                    <label>
                      CVC
                      <input
                        inputMode="numeric"
                        maxLength={4}
                        placeholder="123"
                        value={paymentForm.cvc}
                        onChange={(event) =>
                          setPaymentForm((prev) => ({ ...prev, cvc: event.target.value }))
                        }
                      />
                    </label>
                  </div>
                  <p className="checkout-demo-note">
                    Demo cards: `4242 4242 4242 4242` (success), `4000 0000 0000 0002`
                    (declined).
                  </p>
                </div>
              )}

              {paymentMethod !== "CARD" && (
                <p className="checkout-demo-note">
                  {paymentMethod === "APPLE_PAY"
                    ? "Apple Pay demo mode will process instantly."
                    : "PayPal demo mode will process instantly."}
                </p>
              )}

              <button type="submit" disabled={isProcessing || confirmMutation.isPending}>
                {isProcessing || confirmMutation.isPending
                  ? "Processing payment..."
                  : `Pay ${totalLabel}`}
              </button>
            </form>
          )}

          {(formError || confirmMutation.isError) && (
            <p className="status error">{formError || confirmMutation.error.message}</p>
          )}
          {orderStatusQuery.isError && (
            <p className="status error">Could not fetch live order status.</p>
          )}
          {provider !== "MOCK_STRIPE" && orderStatusQuery.isLoading && (
            <p className="status">Checking payment status...</p>
          )}
          {provider !== "MOCK_STRIPE" && !isPaid && liveOrderStatus === "PENDING" && (
            <p className="status">Payment pending confirmation from webhook...</p>
          )}

          {isPaid && (
            <div className="checkout-success">
              <p>
                Payment status: <strong>PAID</strong>
              </p>
              <p>Tickets generated: {paymentResultTicketCount}</p>
              {paymentResultTickets.length > 0 && (
                <ul>
                  {paymentResultTickets.map((ticket) => (
                    <li key={ticket.id}>
                      Seat #{ticket.seat_id} • Token {ticket.qr_token.slice(0, 16)}...
                    </li>
                  ))}
                </ul>
              )}
              <div className="checkout-success-links">
                <Link to="/me/tickets">Open my tickets</Link>
                <Link to="/movies">Back to movies</Link>
              </div>
            </div>
          )}
        </div>

        <aside className="checkout-card checkout-summary-card">
          <h3>Order summary</h3>
          <p>
            <strong>Order:</strong> #{orderId}
          </p>
          <p>
            <strong>Provider:</strong> {provider}
          </p>
          <p>
            <strong>Seats:</strong>{" "}
            {seatCount > 0 ? `${seatCount} selected` : "Loading seat details..."}
          </p>
          {reservationQuery.isSuccess && heldSeatIds.length > 0 && (
            <p className="checkout-seat-list">Seat IDs: {heldSeatIds.join(", ")}</p>
          )}
          <p>
            <strong>Total:</strong> {totalLabel}
          </p>
          <p className="checkout-secure-note">
            {provider === "MOCK_STRIPE"
              ? "Secure demo checkout • idempotent order handling"
              : "Secure Stripe checkout • webhook idempotency enabled"}
          </p>
        </aside>
      </div>
    </section>
  );
}
