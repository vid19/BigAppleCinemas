import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createMovie,
  createShowtime,
  createTheater,
  deleteMovie,
  deleteShowtime,
  deleteTheater,
  fetchMovies,
  fetchShowtimes,
  fetchTheaters,
  updateMovie,
  updateShowtime,
  updateTheater
} from "../api/catalog";

function toIsoFromLocalDateTime(value) {
  return new Date(value).toISOString();
}

function nowLocalInput(hoursFromNow) {
  const date = new Date();
  date.setHours(date.getHours() + hoursFromNow, 0, 0, 0);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function AdminDashboardPage() {
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState("");

  const [movieForm, setMovieForm] = useState({
    title: "",
    description: "",
    runtime_minutes: 110,
    rating: "PG-13"
  });
  const [theaterForm, setTheaterForm] = useState({
    name: "",
    address: "",
    city: "New York",
    timezone: "America/New_York"
  });
  const [showtimeForm, setShowtimeForm] = useState({
    movie_id: "",
    auditorium_id: 1,
    starts_at: nowLocalInput(4),
    ends_at: nowLocalInput(6),
    status: "SCHEDULED"
  });
  const [editingMovieId, setEditingMovieId] = useState(null);
  const [movieEditForm, setMovieEditForm] = useState({
    title: "",
    runtime_minutes: 120,
    rating: "PG-13"
  });
  const [editingTheaterId, setEditingTheaterId] = useState(null);
  const [theaterEditForm, setTheaterEditForm] = useState({
    name: "",
    city: "",
    timezone: ""
  });
  const [editingShowtimeId, setEditingShowtimeId] = useState(null);
  const [showtimeEditForm, setShowtimeEditForm] = useState({
    status: "SCHEDULED"
  });

  const moviesQuery = useQuery({
    queryKey: ["admin-movies"],
    queryFn: () => fetchMovies({ limit: 50, offset: 0 })
  });

  const showtimesQuery = useQuery({
    queryKey: ["admin-showtimes"],
    queryFn: () => fetchShowtimes({ limit: 25, offset: 0 })
  });
  const theatersQuery = useQuery({
    queryKey: ["admin-theaters"],
    queryFn: () => fetchTheaters({ limit: 100, offset: 0 })
  });

  const refreshQueries = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-movies"] });
    queryClient.invalidateQueries({ queryKey: ["movies"] });
    queryClient.invalidateQueries({ queryKey: ["admin-theaters"] });
    queryClient.invalidateQueries({ queryKey: ["theaters"] });
    queryClient.invalidateQueries({ queryKey: ["admin-showtimes"] });
    queryClient.invalidateQueries({ queryKey: ["showtimes"] });
  };

  const createMovieMutation = useMutation({
    mutationFn: createMovie,
    onSuccess: () => {
      setFeedback("Movie created.");
      setMovieForm((prev) => ({ ...prev, title: "", description: "" }));
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });

  const deleteMovieMutation = useMutation({
    mutationFn: deleteMovie,
    onSuccess: () => {
      setFeedback("Movie deleted.");
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });
  const updateMovieMutation = useMutation({
    mutationFn: ({ movieId, payload }) => updateMovie(movieId, payload),
    onSuccess: () => {
      setFeedback("Movie updated.");
      setEditingMovieId(null);
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });

  const createTheaterMutation = useMutation({
    mutationFn: createTheater,
    onSuccess: () => {
      setFeedback("Theater created.");
      setTheaterForm((prev) => ({ ...prev, name: "", address: "" }));
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });
  const deleteTheaterMutation = useMutation({
    mutationFn: deleteTheater,
    onSuccess: () => {
      setFeedback("Theater deleted.");
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });
  const updateTheaterMutation = useMutation({
    mutationFn: ({ theaterId, payload }) => updateTheater(theaterId, payload),
    onSuccess: () => {
      setFeedback("Theater updated.");
      setEditingTheaterId(null);
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });

  const createShowtimeMutation = useMutation({
    mutationFn: createShowtime,
    onSuccess: () => {
      setFeedback("Showtime created.");
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });
  const deleteShowtimeMutation = useMutation({
    mutationFn: deleteShowtime,
    onSuccess: () => {
      setFeedback("Showtime deleted.");
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });
  const updateShowtimeMutation = useMutation({
    mutationFn: ({ showtimeId, payload }) => updateShowtime(showtimeId, payload),
    onSuccess: () => {
      setFeedback("Showtime updated.");
      setEditingShowtimeId(null);
      refreshQueries();
    },
    onError: (error) => setFeedback(error.message)
  });

  const movieItems = moviesQuery.data?.items ?? [];
  const theaterItems = theatersQuery.data?.items ?? [];
  const showtimeItems = showtimesQuery.data?.items ?? [];
  const movieOptions = useMemo(() => movieItems.map((movie) => ({ id: movie.id, title: movie.title })), [movieItems]);

  return (
    <section className="page">
      <div className="page-header">
        <h2>Admin Dashboard</h2>
        <p>Manage catalog entities for demo environments.</p>
      </div>

      {feedback && <p className="status">{feedback}</p>}

      <div className="admin-grid">
        <article className="admin-card">
          <h3>Create movie</h3>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              createMovieMutation.mutate(movieForm);
            }}
          >
            <input
              required
              placeholder="Title"
              value={movieForm.title}
              onChange={(event) => setMovieForm((prev) => ({ ...prev, title: event.target.value }))}
            />
            <textarea
              placeholder="Description"
              value={movieForm.description}
              onChange={(event) =>
                setMovieForm((prev) => ({ ...prev, description: event.target.value }))
              }
            />
            <div className="inline-fields">
              <input
                type="number"
                min={60}
                max={400}
                value={movieForm.runtime_minutes}
                onChange={(event) =>
                  setMovieForm((prev) => ({
                    ...prev,
                    runtime_minutes: Number(event.target.value)
                  }))
                }
              />
              <input
                value={movieForm.rating}
                onChange={(event) => setMovieForm((prev) => ({ ...prev, rating: event.target.value }))}
              />
            </div>
            <button type="submit" disabled={createMovieMutation.isPending}>
              {createMovieMutation.isPending ? "Creating..." : "Create movie"}
            </button>
          </form>
        </article>

        <article className="admin-card">
          <h3>Create theater</h3>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              createTheaterMutation.mutate(theaterForm);
            }}
          >
            <input
              required
              placeholder="Theater name"
              value={theaterForm.name}
              onChange={(event) =>
                setTheaterForm((prev) => ({ ...prev, name: event.target.value }))
              }
            />
            <input
              required
              placeholder="Address"
              value={theaterForm.address}
              onChange={(event) =>
                setTheaterForm((prev) => ({ ...prev, address: event.target.value }))
              }
            />
            <div className="inline-fields">
              <input
                required
                placeholder="City"
                value={theaterForm.city}
                onChange={(event) =>
                  setTheaterForm((prev) => ({ ...prev, city: event.target.value }))
                }
              />
              <input
                required
                placeholder="Timezone"
                value={theaterForm.timezone}
                onChange={(event) =>
                  setTheaterForm((prev) => ({ ...prev, timezone: event.target.value }))
                }
              />
            </div>
            <button type="submit" disabled={createTheaterMutation.isPending}>
              {createTheaterMutation.isPending ? "Creating..." : "Create theater"}
            </button>
          </form>
        </article>

        <article className="admin-card">
          <h3>Create showtime</h3>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              createShowtimeMutation.mutate({
                movie_id: Number(showtimeForm.movie_id),
                auditorium_id: Number(showtimeForm.auditorium_id),
                starts_at: toIsoFromLocalDateTime(showtimeForm.starts_at),
                ends_at: toIsoFromLocalDateTime(showtimeForm.ends_at),
                status: showtimeForm.status
              });
            }}
          >
            <select
              required
              value={showtimeForm.movie_id}
              onChange={(event) =>
                setShowtimeForm((prev) => ({ ...prev, movie_id: event.target.value }))
              }
            >
              <option value="">Select movie</option>
              {movieOptions.map((movie) => (
                <option key={movie.id} value={movie.id}>
                  {movie.title}
                </option>
              ))}
            </select>
            <div className="inline-fields">
              <input
                type="number"
                min={1}
                value={showtimeForm.auditorium_id}
                onChange={(event) =>
                  setShowtimeForm((prev) => ({
                    ...prev,
                    auditorium_id: Number(event.target.value)
                  }))
                }
              />
              <input
                value={showtimeForm.status}
                onChange={(event) =>
                  setShowtimeForm((prev) => ({ ...prev, status: event.target.value }))
                }
              />
            </div>
            <input
              type="datetime-local"
              value={showtimeForm.starts_at}
              onChange={(event) =>
                setShowtimeForm((prev) => ({ ...prev, starts_at: event.target.value }))
              }
            />
            <input
              type="datetime-local"
              value={showtimeForm.ends_at}
              onChange={(event) =>
                setShowtimeForm((prev) => ({ ...prev, ends_at: event.target.value }))
              }
            />
            <button type="submit" disabled={createShowtimeMutation.isPending}>
              {createShowtimeMutation.isPending ? "Creating..." : "Create showtime"}
            </button>
          </form>
        </article>
      </div>

      <div className="admin-grid">
        <article className="admin-card">
          <h3>Movies</h3>
          {moviesQuery.isLoading && <p className="status">Loading movies...</p>}
          {moviesQuery.isError && <p className="status error">Could not load movies.</p>}
          {!moviesQuery.isLoading && !moviesQuery.isError && (
            <ul className="admin-list">
              {movieItems.map((movie) => (
                <li key={movie.id}>
                  <div className="admin-list-main">
                    <span>
                      #{movie.id} {movie.title}
                    </span>
                    <div className="admin-actions">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingMovieId(movie.id);
                          setMovieEditForm({
                            title: movie.title,
                            runtime_minutes: movie.runtime_minutes,
                            rating: movie.rating
                          });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteMovieMutation.mutate(movie.id)}
                        disabled={deleteMovieMutation.isPending}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  {editingMovieId === movie.id && (
                    <form
                      className="admin-inline-form"
                      onSubmit={(event) => {
                        event.preventDefault();
                        updateMovieMutation.mutate({
                          movieId: movie.id,
                          payload: {
                            title: movieEditForm.title,
                            runtime_minutes: Number(movieEditForm.runtime_minutes),
                            rating: movieEditForm.rating
                          }
                        });
                      }}
                    >
                      <input
                        value={movieEditForm.title}
                        onChange={(event) =>
                          setMovieEditForm((prev) => ({ ...prev, title: event.target.value }))
                        }
                      />
                      <input
                        type="number"
                        min={1}
                        value={movieEditForm.runtime_minutes}
                        onChange={(event) =>
                          setMovieEditForm((prev) => ({
                            ...prev,
                            runtime_minutes: Number(event.target.value)
                          }))
                        }
                      />
                      <input
                        value={movieEditForm.rating}
                        onChange={(event) =>
                          setMovieEditForm((prev) => ({ ...prev, rating: event.target.value }))
                        }
                      />
                      <div className="admin-actions">
                        <button type="submit" disabled={updateMovieMutation.isPending}>
                          Save
                        </button>
                        <button type="button" onClick={() => setEditingMovieId(null)}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="admin-card">
          <h3>Theaters</h3>
          {theatersQuery.isLoading && <p className="status">Loading theaters...</p>}
          {theatersQuery.isError && <p className="status error">Could not load theaters.</p>}
          {!theatersQuery.isLoading && !theatersQuery.isError && (
            <ul className="admin-list">
              {theaterItems.map((theater) => (
                <li key={theater.id}>
                  <div className="admin-list-main">
                    <span>
                      #{theater.id} {theater.name} ({theater.city})
                    </span>
                    <div className="admin-actions">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingTheaterId(theater.id);
                          setTheaterEditForm({
                            name: theater.name,
                            city: theater.city,
                            timezone: theater.timezone
                          });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteTheaterMutation.mutate(theater.id)}
                        disabled={deleteTheaterMutation.isPending}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  {editingTheaterId === theater.id && (
                    <form
                      className="admin-inline-form"
                      onSubmit={(event) => {
                        event.preventDefault();
                        updateTheaterMutation.mutate({
                          theaterId: theater.id,
                          payload: {
                            name: theaterEditForm.name,
                            city: theaterEditForm.city,
                            timezone: theaterEditForm.timezone
                          }
                        });
                      }}
                    >
                      <input
                        value={theaterEditForm.name}
                        onChange={(event) =>
                          setTheaterEditForm((prev) => ({ ...prev, name: event.target.value }))
                        }
                      />
                      <input
                        value={theaterEditForm.city}
                        onChange={(event) =>
                          setTheaterEditForm((prev) => ({ ...prev, city: event.target.value }))
                        }
                      />
                      <input
                        value={theaterEditForm.timezone}
                        onChange={(event) =>
                          setTheaterEditForm((prev) => ({
                            ...prev,
                            timezone: event.target.value
                          }))
                        }
                      />
                      <div className="admin-actions">
                        <button type="submit" disabled={updateTheaterMutation.isPending}>
                          Save
                        </button>
                        <button type="button" onClick={() => setEditingTheaterId(null)}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </li>
              ))}
            </ul>
          )}
        </article>

        <article className="admin-card">
          <h3>Recent showtimes</h3>
          {showtimesQuery.isLoading && <p className="status">Loading showtimes...</p>}
          {showtimesQuery.isError && <p className="status error">Could not load showtimes.</p>}
          {!showtimesQuery.isLoading && !showtimesQuery.isError && (
            <ul className="admin-list">
              {showtimeItems.map((showtime) => (
                <li key={showtime.id}>
                  <div className="admin-list-main">
                    <span>
                      #{showtime.id} {showtime.theater_name} ({showtime.status})
                    </span>
                    <div className="admin-actions">
                      <button
                        type="button"
                        onClick={() => {
                          setEditingShowtimeId(showtime.id);
                          setShowtimeEditForm({ status: showtime.status });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteShowtimeMutation.mutate(showtime.id)}
                        disabled={deleteShowtimeMutation.isPending}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  {editingShowtimeId === showtime.id && (
                    <form
                      className="admin-inline-form"
                      onSubmit={(event) => {
                        event.preventDefault();
                        updateShowtimeMutation.mutate({
                          showtimeId: showtime.id,
                          payload: { status: showtimeEditForm.status }
                        });
                      }}
                    >
                      <input
                        value={showtimeEditForm.status}
                        onChange={(event) =>
                          setShowtimeEditForm((prev) => ({
                            ...prev,
                            status: event.target.value
                          }))
                        }
                      />
                      <div className="admin-actions">
                        <button type="submit" disabled={updateShowtimeMutation.isPending}>
                          Save
                        </button>
                        <button type="button" onClick={() => setEditingShowtimeId(null)}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>
    </section>
  );
}
