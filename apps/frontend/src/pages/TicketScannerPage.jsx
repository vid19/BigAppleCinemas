import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { scanTicket } from "../api/catalog";

export function TicketScannerPage() {
  const [qrToken, setQrToken] = useState("");
  const [staffToken, setStaffToken] = useState("local-staff");
  const [cameraStatus, setCameraStatus] = useState("idle");
  const [cameraError, setCameraError] = useState("");
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const scannerTimerRef = useRef(null);
  const lastScannedTokenRef = useRef("");

  const scanMutation = useMutation({
    mutationFn: ({ token, staff }) =>
      scanTicket({ qr_token: token }, { staffToken: staff })
  });

  function clearScannerTimer() {
    if (scannerTimerRef.current) {
      window.clearInterval(scannerTimerRef.current);
      scannerTimerRef.current = null;
    }
  }

  function stopCamera() {
    clearScannerTimer();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraStatus("idle");
  }

  async function detectTokenFromFrame() {
    if (!videoRef.current || !detectorRef.current || scanMutation.isPending) {
      return;
    }
    if (videoRef.current.readyState < 2) {
      return;
    }
    try {
      const detections = await detectorRef.current.detect(videoRef.current);
      if (!detections || detections.length === 0) {
        return;
      }
      const candidateToken = detections[0]?.rawValue?.trim();
      if (!candidateToken || candidateToken === lastScannedTokenRef.current) {
        return;
      }
      lastScannedTokenRef.current = candidateToken;
      setQrToken(candidateToken);
      scanMutation.mutate({ token: candidateToken, staff: staffToken.trim() });
    } catch {
      // keep camera running even if one frame fails
    }
  }

  async function startCamera() {
    setCameraError("");
    if (!globalThis.navigator?.mediaDevices?.getUserMedia) {
      setCameraError("Camera access is not supported in this browser.");
      return;
    }
    if (!("BarcodeDetector" in globalThis)) {
      setCameraError("Barcode detection is not supported on this browser. Use manual token entry.");
      return;
    }

    try {
      detectorRef.current = new globalThis.BarcodeDetector({
        formats: ["qr_code"]
      });
      const stream = await globalThis.navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraStatus("active");
      scannerTimerRef.current = window.setInterval(detectTokenFromFrame, 650);
    } catch (error) {
      setCameraStatus("idle");
      setCameraError(error?.message || "Could not start camera.");
      stopCamera();
    }
  }

  useEffect(() => () => stopCamera(), []);

  return (
    <section className="page page-shell">
      <div className="page-header page-header-modern">
        <h2>Ticket Scanner</h2>
        <p>Validate ticket tokens at entry and prevent duplicate usage.</p>
        <div className="scanner-state-strip">
          <span className={`scanner-live-pill ${cameraStatus === "active" ? "active" : ""}`}>
            {cameraStatus === "active" ? "Camera live" : "Camera idle"}
          </span>
          <span className="scanner-live-pill neutral">Manual token scan supported</span>
        </div>
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
        <p className="scanner-tip">
          Keep the QR centered in the preview. Auto scan runs roughly every 650ms.
        </p>
        <div className="scanner-camera-row">
          <div className="scanner-camera-preview">
            {cameraStatus !== "active" && (
              <p className="status">Camera preview is off. Start camera to scan QR automatically.</p>
            )}
            <video
              ref={videoRef}
              className="scanner-camera-video"
              muted
              playsInline
            />
          </div>
          <div className="scanner-camera-actions">
            <button type="button" onClick={startCamera} disabled={cameraStatus === "active"}>
              Start camera
            </button>
            <button type="button" onClick={stopCamera} disabled={cameraStatus !== "active"}>
              Stop camera
            </button>
          </div>
          {cameraError && <p className="status error">{cameraError}</p>}
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
