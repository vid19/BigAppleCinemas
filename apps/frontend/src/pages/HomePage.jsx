import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../auth/AuthContext";
import {
  fetchMovies,
  fetchMyRecommendations,
  submitRecommendationFeedback
} from "../api/catalog";

const BOOKING_STEPS = [
  {
    title: "Pick a movie",
    description: "Browse now playing titles and compare theaters in a few taps."
  },
  {
    title: "Choose your seats",
    description: "Seat states update live so you can lock the exact spots you want."
  },
  {
    title: "Checkout securely",
    description: "Complete payment, then access QR tickets instantly from My Tickets."
  }
];

const FALLBACK_SLIDES = [
  {
    id: "fallback-1",
    title: "Lights down. Big stories up.",
    description:
      "Discover what is playing tonight and book premium seats before they sell out.",
    ctaLabel: "Browse movies",
    movieId: null,
    posterUrl: null,
    rating: "All ratings",
    runtimeMinutes: null
  },
  {
    id: "fallback-2",
    title: "Movie night, planned in minutes.",
    description:
      "Compare theaters, lock seats for 8 minutes, and checkout with secure ticket delivery.",
    ctaLabel: "Find showtimes",
    movieId: null,
    posterUrl: null,
    rating: "Family to thriller",
    runtimeMinutes: null
  }
];

export function HomePage() {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const moviesQuery = useQuery({
    queryKey: ["home-featured-movies"],
    queryFn: () => fetchMovies({ limit: 6, offset: 0 }),
    staleTime: 60_000
  });
  const recommendationsQuery = useQuery({
    queryKey: ["home-recommendations"],
    queryFn: () => fetchMyRecommendations({ limit: 6 }),
    enabled: isAuthenticated,
    staleTime: 60_000,
    retry: false
  });

  const featuredMovies = moviesQuery.data?.items ?? [];
  const recommendationItems = recommendationsQuery.data?.items ?? [];
  const [dismissedRecommendationIds, setDismissedRecommendationIds] = useState([]);
  const [savedRecommendationIds, setSavedRecommendationIds] = useState([]);
  const [lastHiddenRecommendation, setLastHiddenRecommendation] = useState(null);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);

  const recommendationFeedbackMutation = useMutation({
    mutationFn: submitRecommendationFeedback,
    onSuccess: (_, variables) => {
      if (variables.event_type === "NOT_INTERESTED" && variables.active) {
        setDismissedRecommendationIds((currentIds) => [...new Set([...currentIds, variables.movie_id])]);
      }
      if (variables.event_type === "SAVE_FOR_LATER" && variables.active) {
        setSavedRecommendationIds((currentIds) => [...new Set([...currentIds, variables.movie_id])]);
      }
      if (!variables.active) {
        setDismissedRecommendationIds((currentIds) =>
          currentIds.filter((movieId) => movieId !== variables.movie_id)
        );
        setSavedRecommendationIds((currentIds) =>
          currentIds.filter((movieId) => movieId !== variables.movie_id)
        );
      }
      queryClient.invalidateQueries({ queryKey: ["home-recommendations"] });
    }
  });

  function formatShowtime(dateValue) {
    return new Date(dateValue).toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    });
  }

  const bannerSlides = useMemo(() => {
    if (featuredMovies.length === 0) {
      return FALLBACK_SLIDES;
    }
    return featuredMovies.slice(0, 6).map((movie) => ({
      id: movie.id,
      title: movie.title,
      description:
        movie.description ??
        "Book seats early for the best view, then checkout and access tickets instantly.",
      ctaLabel: "Book this movie",
      movieId: movie.id,
      posterUrl: movie.poster_url,
      rating: movie.rating,
      runtimeMinutes: movie.runtime_minutes
    }));
  }, [featuredMovies]);

  const visibleRecommendations = useMemo(
    () =>
      recommendationItems.filter(
        (movie) => !dismissedRecommendationIds.includes(movie.movie_id)
      ),
    [dismissedRecommendationIds, recommendationItems]
  );

  const serverSavedRecommendationIds = useMemo(
    () =>
      recommendationItems
        .filter((movie) => movie.reason === "Saved for later")
        .map((movie) => movie.movie_id),
    [recommendationItems]
  );

  const effectiveSavedRecommendationIds = useMemo(
    () => new Set([...serverSavedRecommendationIds, ...savedRecommendationIds]),
    [savedRecommendationIds, serverSavedRecommendationIds]
  );

  function handleRecommendationFeedback(movieId, eventType, { active = true, title } = {}) {
    if (eventType === "NOT_INTERESTED" && active) {
      setLastHiddenRecommendation({ movieId, title: title ?? "movie" });
    }
    recommendationFeedbackMutation.mutate({
      movie_id: movieId,
      event_type: eventType,
      active
    });
  }

  useEffect(() => {
    if (activeSlideIndex >= bannerSlides.length) {
      setActiveSlideIndex(0);
    }
  }, [activeSlideIndex, bannerSlides.length]);

  useEffect(() => {
    if (!isAuthenticated) {
      setDismissedRecommendationIds([]);
      setSavedRecommendationIds([]);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (bannerSlides.length <= 1) {
      return undefined;
    }
    const interval = window.setInterval(() => {
      setActiveSlideIndex((currentIndex) => (currentIndex + 1) % bannerSlides.length);
    }, 6000);

    return () => window.clearInterval(interval);
  }, [bannerSlides.length]);

  const activeSlide = bannerSlides[activeSlideIndex] ?? bannerSlides[0];
  const activeSlidePath = activeSlide?.movieId ? `/movies/${activeSlide.movieId}` : "/movies";

  return (
    <section className="home-page">
      <section className="home-banner home-bleed" aria-label="Featured movies">
        <div className="home-banner-slides" aria-hidden="true">
          {bannerSlides.map((slide, index) => (
            <article
              className={`home-banner-slide ${index === activeSlideIndex ? "is-active" : ""}`}
              key={slide.id}
              style={
                slide.posterUrl
                  ? { backgroundImage: `linear-gradient(110deg, #04070f 36%, #04070fa8), url(${slide.posterUrl})` }
                  : undefined
              }
            >
              {!slide.posterUrl && <div className="home-banner-fallback" />}
            </article>
          ))}
        </div>

        <div className="home-banner-shell">
          <div className="home-banner-copy">
            <p className="hero-kicker">Big Apple Cinemas</p>
            <h2>{activeSlide?.title}</h2>
            <p>{activeSlide?.description}</p>
            <div className="hero-actions">
              <Link className="primary-link" to={activeSlidePath}>
                {activeSlide?.ctaLabel ?? "Browse movies"}
              </Link>
              <Link className="secondary-link" to="/me/tickets">
                View my tickets
              </Link>
            </div>
            <div className="home-banner-meta">
              <span>{activeSlide?.rating ?? "Now playing"}</span>
              {activeSlide?.runtimeMinutes ? <span>{activeSlide.runtimeMinutes} min</span> : null}
              <span>Seat hold 8 min</span>
            </div>
          </div>

          <div className="home-banner-rail" aria-label="Select featured movie">
            {bannerSlides.map((slide, index) => (
              <button
                aria-label={`View banner for ${slide.title}`}
                className={`home-banner-rail-item ${index === activeSlideIndex ? "is-active" : ""}`}
                key={`thumb-${slide.id}`}
                onClick={() => setActiveSlideIndex(index)}
                type="button"
              >
                {slide.posterUrl ? (
                  <img alt={`${slide.title} poster`} loading="lazy" src={slide.posterUrl} />
                ) : (
                  <div className="home-banner-rail-fallback">{slide.title.slice(0, 1)}</div>
                )}
                <span>{slide.title}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="home-banner-dots">
          {bannerSlides.map((slide, index) => (
            <button
              aria-label={`Go to slide ${index + 1}`}
              className={`home-dot ${index === activeSlideIndex ? "is-active" : ""}`}
              key={`dot-${slide.id}`}
              onClick={() => setActiveSlideIndex(index)}
              type="button"
            />
          ))}
        </div>
      </section>

      <div className="home-content-shell">
        {moviesQuery.isError && (
          <p className="status error">
            Could not load featured movies. Browse the full catalog from the Movies page.
          </p>
        )}

        <div className="home-layout">
          <section className="home-panel">
            <div className="home-panel-header">
              <h3>Now playing</h3>
              <Link to="/movies">See all</Link>
            </div>

            {moviesQuery.isLoading && <p className="status">Loading featured movies...</p>}
            {!moviesQuery.isLoading && featuredMovies.length === 0 && (
              <p className="status">No movies available right now. Check back shortly.</p>
            )}

            <div className="home-movie-grid">
              {featuredMovies.map((movie) => (
                <article className="home-movie-card" key={movie.id}>
                  <div className="home-movie-banner">
                    {movie.poster_url ? (
                      <img src={movie.poster_url} alt={`${movie.title} poster`} loading="lazy" />
                    ) : (
                      <span>{movie.title.slice(0, 1)}</span>
                    )}
                    <div className="home-movie-banner-overlay" />
                    <div className="home-movie-banner-copy">
                      <strong>{movie.title}</strong>
                      <small>
                        {movie.rating} • {movie.runtime_minutes} min
                      </small>
                    </div>
                  </div>
                  <div className="home-movie-card-body">
                    <Link to={`/movies/${movie.id}`}>Showtimes</Link>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <div className="home-side-stack">
            <section className="home-panel home-metric-grid">
              <article>
                <p>8 min</p>
                <span>Seat hold window</span>
              </article>
              <article>
                <p>QR</p>
                <span>Instant ticket delivery</span>
              </article>
              <article>
                <p>24/7</p>
                <span>Scan and validation ready</span>
              </article>
            </section>

            <section className="home-panel">
              <h3>Tonight quick start</h3>
              <p className="home-muted">
                Start with movies, select a showtime, lock seats, and finish checkout in under
                2 minutes.
              </p>
              <Link className="home-inline-link" to="/movies">
                Find showtimes
              </Link>
            </section>
          </div>
        </div>

        <section className="home-panel home-recommendation-panel">
          <div className="home-panel-header">
            <h3>Recommended for you</h3>
            <Link to="/movies">Explore all</Link>
          </div>
          {!isAuthenticated && (
            <p className="home-muted">
              Sign in to unlock personalized picks based on your bookings.
              {" "}
              <Link className="home-inline-link" to="/login">
                Sign in
              </Link>
            </p>
          )}
          {isAuthenticated && recommendationsQuery.isLoading && (
            <p className="status">Building recommendations from your history...</p>
          )}
          {isAuthenticated && recommendationsQuery.isError && (
            <p className="status error">Could not load recommendations right now.</p>
          )}
          {isAuthenticated &&
            !recommendationsQuery.isLoading &&
            !recommendationsQuery.isError &&
            visibleRecommendations.length === 0 && (
              <p className="status">
                No personalized picks yet. Book a movie and recommendations will appear here.
              </p>
            )}
          {isAuthenticated && visibleRecommendations.length > 0 && (
            <div className="home-recommendation-grid">
              {visibleRecommendations.map((movie) => (
                <article className="home-recommendation-card" key={movie.movie_id}>
                  <div className="home-recommendation-banner">
                    {movie.poster_url ? (
                      <img alt={`${movie.title} poster`} loading="lazy" src={movie.poster_url} />
                    ) : (
                      <span>{movie.title.slice(0, 1)}</span>
                    )}
                  </div>
                  <div className="home-recommendation-body">
                    <strong>{movie.title}</strong>
                    <p>{movie.reason}</p>
                    <small>
                      Next showtime: {formatShowtime(movie.next_showtime_starts_at)}
                    </small>
                    <Link to={`/movies/${movie.movie_id}`}>View showtimes</Link>
                    <div className="recommendation-actions">
                      <button
                        className={`recommendation-action ${effectiveSavedRecommendationIds.has(movie.movie_id) ? "is-active" : ""}`}
                        disabled={recommendationFeedbackMutation.isPending}
                        onClick={() =>
                          handleRecommendationFeedback(movie.movie_id, "SAVE_FOR_LATER", {
                            active: !effectiveSavedRecommendationIds.has(movie.movie_id),
                            title: movie.title
                          })
                        }
                        type="button"
                      >
                        {effectiveSavedRecommendationIds.has(movie.movie_id)
                          ? "Saved (Undo)"
                          : "Save for later"}
                      </button>
                      <button
                        className="recommendation-action recommendation-action-muted"
                        disabled={recommendationFeedbackMutation.isPending}
                        onClick={() =>
                          handleRecommendationFeedback(movie.movie_id, "NOT_INTERESTED", {
                            active: true,
                            title: movie.title
                          })
                        }
                        type="button"
                      >
                        Not interested
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
          {isAuthenticated && lastHiddenRecommendation && (
            <div className="recommendation-undo-bar" role="status">
              <p>
                Hidden
                {" "}
                <strong>{lastHiddenRecommendation.title}</strong>
                {" "}
                from recommendations.
              </p>
              <button
                disabled={recommendationFeedbackMutation.isPending}
                onClick={() => {
                  handleRecommendationFeedback(
                    lastHiddenRecommendation.movieId,
                    "NOT_INTERESTED",
                    { active: false, title: lastHiddenRecommendation.title }
                  );
                  setLastHiddenRecommendation(null);
                }}
                type="button"
              >
                Undo
              </button>
            </div>
          )}
        </section>

        <section className="home-panel">
          <h3>Book in 3 simple steps</h3>
          <div className="home-steps-grid">
            {BOOKING_STEPS.map((step, index) => (
              <article className="home-step-card" key={step.title}>
                <span>Step {index + 1}</span>
                <h4>{step.title}</h4>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}
