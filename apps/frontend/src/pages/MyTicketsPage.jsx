import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchMyOrders, fetchMyTickets } from "../api/catalog";

function formatDateTime(dateValue) {
  return new Date(dateValue).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

export function MyTicketsPage() {
  const [copiedTicketId, setCopiedTicketId] = useState(null);
  const ticketsQuery = useQuery({
    queryKey: ["me-tickets"],
    queryFn: fetchMyTickets
  });
  const ordersQuery = useQuery({
    queryKey: ["me-orders"],
    queryFn: fetchMyOrders
  });

  const tickets = ticketsQuery.data?.items ?? [];
  const activeTickets = useMemo(
    () => tickets.filter((ticket) => ticket.ticket_status === "VALID"),
    [tickets]
  );
  const pastTickets = useMemo(
    () => tickets.filter((ticket) => ticket.ticket_status !== "VALID"),
    [tickets]
  );
  const orders = ordersQuery.data?.items ?? [];
  const usedTicketsCount = tickets.filter((ticket) => ticket.ticket_status === "USED").length;

  async function copyToken(ticketId, token) {
    try {
      await globalThis.navigator?.clipboard?.writeText(token);
      setCopiedTicketId(ticketId);
      window.setTimeout(() => setCopiedTicketId(null), 1800);
    } catch {
      setCopiedTicketId(null);
    }
  }

  return (
    <section className="page page-shell">
      <div className="page-header page-header-modern">
        <h2>My Tickets</h2>
        <p>View active QR tickets and your recent order history.</p>
      </div>

      {(ticketsQuery.isLoading || ordersQuery.isLoading) && (
        <p className="status">Loading tickets and orders...</p>
      )}
      {(ticketsQuery.isError || ordersQuery.isError) && (
        <p className="status error">Could not load your ticket data.</p>
      )}

      {!ticketsQuery.isLoading && !ticketsQuery.isError && !ordersQuery.isLoading && (
        <div className="ticket-summary-grid">
          <article className="ticket-summary-stat">
            <p>Active tickets</p>
            <strong>{activeTickets.length}</strong>
          </article>
          <article className="ticket-summary-stat">
            <p>Used tickets</p>
            <strong>{usedTicketsCount}</strong>
          </article>
          <article className="ticket-summary-stat">
            <p>Past/void tickets</p>
            <strong>{pastTickets.length}</strong>
          </article>
          <article className="ticket-summary-stat">
            <p>Total orders</p>
            <strong>{orders.length}</strong>
          </article>
        </div>
      )}

      {!ticketsQuery.isLoading && !ticketsQuery.isError && (
        <div className="ticket-grid">
          <article className="admin-card ticket-card">
            <h3>Active tickets ({activeTickets.length})</h3>
            {activeTickets.length === 0 && <p className="status">No active tickets yet.</p>}
            {activeTickets.length > 0 && (
              <ul className="ticket-active-grid">
                {activeTickets.map((ticket) => (
                  <li className="ticket-item-card" key={ticket.ticket_id}>
                    <div className="ticket-item-top">
                      <strong>{ticket.movie_title}</strong>
                      <span className="ticket-pill">VALID</span>
                    </div>
                    <p className="status">
                      {ticket.theater_name} • {formatDateTime(ticket.showtime_starts_at)}
                    </p>
                    <div className="ticket-meta-row">
                      <span>Seat {ticket.seat_code}</span>
                      <span>{ticket.seat_type}</span>
                    </div>
                    <div className="ticket-token-row">
                      <code>{ticket.qr_token}</code>
                      <button
                        type="button"
                        onClick={() => copyToken(ticket.ticket_id, ticket.qr_token)}
                      >
                        {copiedTicketId === ticket.ticket_id ? "Copied" : "Copy token"}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="admin-card ticket-card">
            <h3>Past tickets ({pastTickets.length})</h3>
            {pastTickets.length === 0 && <p className="status">No used or void tickets.</p>}
            {pastTickets.length > 0 && (
              <ul className="admin-list">
                {pastTickets.map((ticket) => (
                  <li key={ticket.ticket_id}>
                    <div className="admin-list-main">
                      <span>
                        {ticket.movie_title} • {ticket.seat_code}
                      </span>
                      <span className="ticket-pill muted">{ticket.ticket_status}</span>
                    </div>
                    <p className="status">
                      Used {ticket.used_at ? formatDateTime(ticket.used_at) : "N/A"}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </div>
      )}

      {!ordersQuery.isLoading && !ordersQuery.isError && (
        <article className="admin-card ticket-card">
          <h3>Orders ({orders.length})</h3>
          {orders.length === 0 && <p className="status">No orders found.</p>}
          {orders.length > 0 && (
            <ul className="admin-list">
              {orders.map((order) => (
                <li key={order.order_id}>
                  <div className="admin-list-main">
                    <span>
                      Order #{order.order_id} • {order.status}
                    </span>
                    <span>
                      ${(order.total_cents / 100).toFixed(2)} {order.currency}
                    </span>
                  </div>
                  <p className="status">
                    {order.provider} • {order.ticket_count} tickets •{" "}
                    {formatDateTime(order.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </article>
      )}
    </section>
  );
}
