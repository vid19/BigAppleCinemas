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

      <article className="admin-card scanner-card scanner-layout-card">
        <div className="scanner-help-row">
          <p className="status">
            Demo token for local: <code>local-staff</code>
          </p>
          <button type="button" onClick={() => setStaffToken("local-staff")}>
            Reset staff token
          </button>
        </div>
        <form
          className="scanner-form"
          onSubmit={(event) => {
            event.preventDefault();
            scanMutation.mutate({ token: qrToken.trim(), staff: staffToken.trim() });
          }}
        >
          <label>
            Ticket QR token
            <input
              required
              placeholder="Paste ticket token"
              value={qrToken}
              onChange={(event) => setQrToken(event.target.value)}
            />
          </label>
          <label>
            Staff scan token
            <input
              required
              placeholder="Staff scan token"
              value={staffToken}
              onChange={(event) => setStaffToken(event.target.value)}
            />
          </label>
          <button type="submit" disabled={scanMutation.isPending}>
            {scanMutation.isPending ? "Scanning..." : "Scan ticket"}
          </button>
        </form>
      </article>

      {scanMutation.isError && <p className="status error">{scanMutation.error.message}</p>}
      {scanMutation.isSuccess && (
        <article className="admin-card scanner-card scanner-result-card">
          <h3>
            Scan result:{" "}
            <span
              className={`scanner-result-pill ${scanMutation.data.result.toLowerCase()}`}
            >
              {scanMutation.data.result}
            </span>
          </h3>
          <p className="status">{scanMutation.data.message}</p>
          {scanMutation.data.ticket_id && (
            <div className="scanner-result-meta">
              <p className="status">Ticket #{scanMutation.data.ticket_id}</p>
              <p className="status">Seat {scanMutation.data.seat_code}</p>
              <p className="status">Showtime #{scanMutation.data.showtime_id}</p>
            </div>
          )}
        </article>
      )}
    </section>
  );
}
