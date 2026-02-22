import { useMemo } from "react";
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

  return (
    <section className="page">
      <div className="page-header">
        <h2>My Tickets</h2>
        <p>View active QR tickets and your recent order history.</p>
      </div>

      {(ticketsQuery.isLoading || ordersQuery.isLoading) && (
        <p className="status">Loading tickets and orders...</p>
      )}
      {(ticketsQuery.isError || ordersQuery.isError) && (
        <p className="status error">Could not load your ticket data.</p>
      )}

      {!ticketsQuery.isLoading && !ticketsQuery.isError && (
        <div className="ticket-grid">
          <article className="admin-card">
            <h3>Active tickets ({activeTickets.length})</h3>
            {activeTickets.length === 0 && <p className="status">No active tickets yet.</p>}
            {activeTickets.length > 0 && (
              <ul className="admin-list">
                {activeTickets.map((ticket) => (
                  <li key={ticket.ticket_id}>
                    <div className="admin-list-main">
                      <span>
                        {ticket.movie_title} • {ticket.seat_code}
                      </span>
                      <span>{formatDateTime(ticket.showtime_starts_at)}</span>
                    </div>
                    <p className="status">
                      {ticket.theater_name} • Token {ticket.qr_token.slice(0, 18)}...
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="admin-card">
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
                      <span>{ticket.ticket_status}</span>
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
        <article className="admin-card">
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
