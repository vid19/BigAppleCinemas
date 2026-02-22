import { useEffect, useState } from "react";
import QRCode from "qrcode";

export function TicketQrCode({ token, movieTitle, ticketId }) {
  const [qrDataUrl, setQrDataUrl] = useState("");

  useEffect(() => {
    let isCancelled = false;
    if (!token) {
      setQrDataUrl("");
      return () => {
        isCancelled = true;
      };
    }

    QRCode.toDataURL(token, {
      width: 220,
      margin: 1,
      color: {
        dark: "#08254a",
        light: "#ffffff"
      }
    })
      .then((value) => {
        if (!isCancelled) {
          setQrDataUrl(value);
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setQrDataUrl("");
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [token]);

  if (!qrDataUrl) {
    return <div className="ticket-qr-placeholder">Generating QR...</div>;
  }

  return (
    <div className="ticket-qr-panel">
      <img alt={`QR ticket ${ticketId}`} className="ticket-qr-image" src={qrDataUrl} />
      <a
        className="ticket-qr-download"
        download={`ticket-${ticketId}.png`}
        href={qrDataUrl}
      >
        Download QR
      </a>
      <p className="ticket-qr-caption">
        Present this code at entry for <strong>{movieTitle}</strong>.
      </p>
    </div>
  );
}
