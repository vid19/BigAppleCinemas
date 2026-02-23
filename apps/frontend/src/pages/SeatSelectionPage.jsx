import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";

import {
  cancelReservation,
  fetchActiveReservation,
  createCheckoutSession,
  createReservation,
  fetchShowtimeSeats
} from "../api/catalog";

const CHECKOUT_PROVIDER = import.meta.env.VITE_CHECKOUT_PROVIDER || "MOCK_STRIPE";

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
  const navigate = useNavigate();
  const [selectedSeatIds, setSelectedSeatIds] = useState([]);
  const [reservation, setReservation] = useState(null);
  const [feedback, setFeedback] = useState("");
  const [nowMs, setNowMs] = useState(Date.now());

  const parsedShowtimeId = Number(showtimeId);
  const seatsQuery = useQuery({
    queryKey: ["showtime-seats", parsedShowtimeId],
    queryFn: () => fetchShowtimeSeats(parsedShowtimeId),
    enabled: Number.isFinite(parsedShowtimeId),
    refetchInterval: 4000
  });
  const { refetch } = seatsQuery;
  const activeReservationQuery = useQuery({
    queryKey: ["reservation-active", parsedShowtimeId],
    queryFn: () => fetchActiveReservation(parsedShowtimeId),
    enabled: Number.isFinite(parsedShowtimeId),
    refetchInterval: 4000,
    retry: false
  });
  const refetchActiveReservation = activeReservationQuery.refetch;

  const createReservationMutation = useMutation({
    mutationFn: createReservation,
    onSuccess: (payload) => {
      setReservation(payload);
      setSelectedSeatIds(payload.seat_ids ?? []);
      setFeedback("Seats are held. Complete checkout before the timer expires.");
      refetch();
      refetchActiveReservation();
    },
    onError: (error) => {
      setFeedback(error.message);
      refetch();
    }
  });

  const cancelReservationMutation = useMutation({
    mutationFn: cancelReservation,
    onSuccess: () => {
      setFeedback("Seat hold released.");
      setReservation(null);
      setSelectedSeatIds([]);
      refetch();
      refetchActiveReservation();
    },
    onError: (error) => setFeedback(error.message)
  });
  const checkoutMutation = useMutation({
    mutationFn: createCheckoutSession,
    onSuccess: (payload) => {
      if (payload.checkout_url?.startsWith("http")) {
        window.location.assign(payload.checkout_url);
        return;
      }
      const params = new globalThis.URLSearchParams({
        order_id: String(payload.order_id),
        session_id: payload.provider_session_id,
        reservation_id: String(payload.reservation_id),
        total_cents: String(payload.total_cents),
        currency: payload.currency,
        provider: payload.provider,
        seat_count: String(reservation?.seat_ids?.length ?? selectedSeatDetails.length)
      });
      navigate(`/checkout/processing?${params.toString()}`);
    },
    onError: (error) => setFeedback(error.message)
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

  const activeHold = reservation?.status === "ACTIVE";
  const remainingSeconds = useMemo(() => {
    if (!activeHold || !reservation?.expires_at) {
      return 0;
    }
    return Math.max(0, Math.floor((new Date(reservation.expires_at).getTime() - nowMs) / 1000));
  }, [activeHold, nowMs, reservation?.expires_at]);

  useEffect(() => {
    const activeReservation = activeReservationQuery.data;
    if (!activeReservation || activeReservation.status !== "ACTIVE") {
      return;
    }
    setReservation((previous) => {
      if (
        previous &&
        previous.id === activeReservation.id &&
        previous.status === activeReservation.status &&
        previous.expires_at === activeReservation.expires_at
      ) {
        return previous;
      }
      return activeReservation;
    });
    setSelectedSeatIds(activeReservation.seat_ids ?? []);
    setFeedback((current) =>
      current || "Resumed your active hold. Complete checkout before the timer expires."
    );
  }, [activeReservationQuery.data]);

  useEffect(() => {
    if (!activeHold) {
      return undefined;
    }
    const intervalId = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => window.clearInterval(intervalId);
  }, [activeHold]);

  useEffect(() => {
    if (activeHold && remainingSeconds === 0) {
      setReservation((previous) => (previous ? { ...previous, status: "EXPIRED" } : previous));
      setFeedback("Your hold expired. Select seats again.");
      setSelectedSeatIds([]);
      refetch();
      refetchActiveReservation();
    }
  }, [activeHold, remainingSeconds, refetch, refetchActiveReservation]);

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
  const holdTimerText = `${Math.floor(remainingSeconds / 60)
    .toString()
    .padStart(2, "0")}:${(remainingSeconds % 60).toString().padStart(2, "0")}`;

  return (
    <section className="page page-shell seat-page seat-page-modern">
      <div className="seat-stage-card">
        <p className="hero-kicker">Showtime #{seatData.showtime_id}</p>
        <h2>Select your seats</h2>
        <p>
          {seatData.theater_name} • {formatDateTime(seatData.starts_at)}
        </p>
        <p className="seat-flow-note">
          Seat availability refreshes automatically every few seconds.
        </p>
        {activeHold && (
          <p className="seat-hold-pill">Hold expires in {holdTimerText}</p>
        )}
      </div>

      <div className="seat-layout-wrap seat-layout-modern">
        <aside className="seat-summary-card seat-booking-panel">
          <h3>Booking summary</h3>
          <p>{seatData.seatmap_name || "Standard layout"}</p>
          <p className="seat-selection-copy">
            {selectedSeatDetails.length > 0
              ? selectedSeatDetails.map((seat) => seat.seat_code).join(", ")
              : "No seats selected yet."}
          </p>

          <div className="seat-price-strip">
            <span>{selectedSeatDetails.length} seats selected</span>
            <strong>${(selectedSeatDetails.length * 15).toFixed(2)}</strong>
          </div>

          <div className="seat-summary-stats">
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

          <div className="seat-summary-actions">
            <Link to={`/movies/${seatData.movie_id}`}>Back to showtimes</Link>
            {!activeHold && (
              <button
                type="button"
                disabled={selectedSeatDetails.length === 0 || createReservationMutation.isPending}
                onClick={() =>
                  createReservationMutation.mutate({
                    showtime_id: seatData.showtime_id,
                    seat_ids: selectedSeatDetails.map((seat) => seat.seat_id)
                  })
                }
              >
                {createReservationMutation.isPending ? "Holding..." : "Hold seats"}
              </button>
            )}
            {activeHold && (
              <button
                type="button"
                disabled={cancelReservationMutation.isPending}
                onClick={() => cancelReservationMutation.mutate(reservation.id)}
              >
                {cancelReservationMutation.isPending ? "Releasing..." : "Release hold"}
              </button>
            )}
            {activeHold && (
              <button
                type="button"
                disabled={checkoutMutation.isPending}
                onClick={() =>
                  checkoutMutation.mutate({
                    reservation_id: reservation.id,
                    provider: CHECKOUT_PROVIDER
                  })
                }
              >
                {checkoutMutation.isPending ? "Preparing checkout..." : "Review and pay"}
              </button>
            )}
            <p className="seat-mode-note">
              Checkout mode: {CHECKOUT_PROVIDER === "STRIPE_CHECKOUT" ? "Stripe" : "Demo mock"}
            </p>
          </div>
          <p className="status">{feedback || "Select seats and start a timed hold."}</p>
        </aside>

        <div className="seat-layout-panel seat-layout-canvas">
          <p className="seat-screen-text">Screen</p>
          <div className="seat-grid-wrap">
            <div
              className="seat-grid"
              style={{ gridTemplateColumns: `repeat(${maxSeatNumber}, minmax(34px, 1fr))` }}
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
                    disabled={!isSelectable || activeHold}
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
          <div className="seat-legend">
            <span>
              <i className="seat-dot available" />
              Available
            </span>
            <span>
              <i className="seat-dot held" />
              Held
            </span>
            <span>
              <i className="seat-dot sold" />
              Sold
            </span>
            <span>
              <i className="seat-dot selected" />
              Selected
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
