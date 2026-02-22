import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { scanTicket } from "../api/catalog";

export function TicketScannerPage() {
  const [qrToken, setQrToken] = useState("");
  const [staffToken, setStaffToken] = useState("local-staff");

  const scanMutation = useMutation({
    mutationFn: ({ token, staff }) =>
      scanTicket({ qr_token: token }, { staffToken: staff })
  });

  return (
    <section className="page page-shell">
      <div className="page-header page-header-modern">
        <h2>Ticket Scanner</h2>
        <p>Validate ticket tokens at entry and prevent duplicate usage.</p>
      </div>

      <article className="admin-card scanner-card">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            scanMutation.mutate({ token: qrToken, staff: staffToken });
          }}
        >
          <input
            required
            placeholder="Ticket QR token"
            value={qrToken}
            onChange={(event) => setQrToken(event.target.value)}
          />
          <input
            required
            placeholder="Staff scan token"
            value={staffToken}
            onChange={(event) => setStaffToken(event.target.value)}
          />
          <button type="submit" disabled={scanMutation.isPending}>
            {scanMutation.isPending ? "Scanning..." : "Scan ticket"}
          </button>
        </form>
      </article>

      {scanMutation.isError && <p className="status error">{scanMutation.error.message}</p>}
      {scanMutation.isSuccess && (
        <article className="admin-card scanner-card">
          <h3>Scan result: {scanMutation.data.result}</h3>
          <p className="status">{scanMutation.data.message}</p>
          {scanMutation.data.ticket_id && (
            <p className="status">
              Ticket #{scanMutation.data.ticket_id} • Seat {scanMutation.data.seat_code} •
              Showtime #{scanMutation.data.showtime_id}
            </p>
          )}
        </article>
      )}
    </section>
  );
}
