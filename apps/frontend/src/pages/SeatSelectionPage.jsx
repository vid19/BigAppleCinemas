import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { fetchShowtimeSeats } from "../api/catalog";

function formatDateTime(dateValue) {
  return new Date(dateValue).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function countByStatus(seats, status) {
  return seats.reduce((total, seat) => total + (seat.status === status ? 1 : 0), 0);
}

export function SeatSelectionPage() {
  const { showtimeId } = useParams();
  const [selectedSeatIds, setSelectedSeatIds] = useState([]);

  const parsedShowtimeId = Number(showtimeId);
  const seatsQuery = useQuery({
    queryKey: ["showtime-seats", parsedShowtimeId],
    queryFn: () => fetchShowtimeSeats(parsedShowtimeId),
    enabled: Number.isFinite(parsedShowtimeId)
  });

  const seatData = seatsQuery.data;
  const seats = seatData?.seats ?? [];

  const maxSeatNumber = useMemo(() => {
    if (seats.length === 0) {
      return 12;
    }
    return seats.reduce((maxValue, seat) => Math.max(maxValue, seat.seat_number), 0);
  }, [seats]);

  const selectedSeatDetails = useMemo(() => {
    const selectedSet = new Set(selectedSeatIds);
    return seats.filter((seat) => selectedSet.has(seat.seat_id));
  }, [seats, selectedSeatIds]);

  if (!Number.isFinite(parsedShowtimeId)) {
    return <p className="status error">Invalid showtime URL.</p>;
  }

  if (seatsQuery.isLoading) {
    return <p className="status">Loading seat map...</p>;
  }

  if (seatsQuery.isError) {
    return <p className="status error">Could not load seat map.</p>;
  }

  if (!seatData || seats.length === 0) {
    return (
      <section className="page">
        <div className="page-header">
          <h2>Seat Selection</h2>
          <p>No seats are configured for this showtime yet.</p>
        </div>
      </section>
    );
  }

  const availableCount = countByStatus(seats, "AVAILABLE");
  const heldCount = countByStatus(seats, "HELD");
  const soldCount = countByStatus(seats, "SOLD");

  return (
    <section className="page seat-page">
      <div className="seat-stage-card">
        <p className="hero-kicker">Showtime #{seatData.showtime_id}</p>
        <h2>Select your seats</h2>
        <p>
          {seatData.theater_name} • {formatDateTime(seatData.starts_at)}
        </p>
        <p className="seat-layout-label">Screen this way</p>
      </div>

      <div className="seat-layout-wrap">
        <div className="seat-layout-panel">
          <div className="seat-legend">
            <span>
              <i className="seat-dot available" />
              Available ({availableCount})
            </span>
            <span>
              <i className="seat-dot held" />
              Held ({heldCount})
            </span>
            <span>
              <i className="seat-dot sold" />
              Sold ({soldCount})
            </span>
            <span>
              <i className="seat-dot selected" />
              Selected ({selectedSeatIds.length})
            </span>
          </div>

          <div className="seat-grid-wrap">
            <div
              className="seat-grid"
              style={{ gridTemplateColumns: `repeat(${maxSeatNumber}, minmax(36px, 1fr))` }}
            >
              {seats.map((seat) => {
                const isSelected = selectedSeatIds.includes(seat.seat_id);
                const isSelectable = seat.status === "AVAILABLE";
                return (
                  <button
                    key={seat.seat_id}
                    type="button"
                    className={`seat-button ${seat.status.toLowerCase()} ${
                      isSelected ? "selected" : ""
                    }`}
                    disabled={!isSelectable}
                    title={`${seat.seat_code} • ${seat.seat_type}`}
                    onClick={() => {
                      if (!isSelectable) {
                        return;
                      }
                      setSelectedSeatIds((previous) =>
                        previous.includes(seat.seat_id)
                          ? previous.filter((value) => value !== seat.seat_id)
                          : [...previous, seat.seat_id]
                      );
                    }}
                  >
                    {seat.seat_code}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <aside className="seat-summary-card">
          <h3>Booking summary</h3>
          <p>{seatData.seatmap_name || "Standard layout"}</p>
          <p>
            {selectedSeatDetails.length > 0
              ? selectedSeatDetails.map((seat) => seat.seat_code).join(", ")
              : "No seats selected yet."}
          </p>
          <div className="seat-summary-actions">
            <Link to={`/movies/${seatData.movie_id}`}>Back to showtimes</Link>
            <button type="button" disabled={selectedSeatDetails.length === 0}>
              Continue to hold
            </button>
          </div>
          <p className="status">
            Hold + checkout finalize in the next milestone. This screen now reflects live seat
            inventory from the backend.
          </p>
        </aside>
      </div>
    </section>
  );
}
