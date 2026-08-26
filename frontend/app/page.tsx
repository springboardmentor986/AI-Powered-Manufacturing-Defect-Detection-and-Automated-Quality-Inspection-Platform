"use client";

import { useEffect, useState } from "react";

interface BackendStatus {
  status: string;
  service: string;
}

export default function Home() {
  const [backend, setBackend] = useState<BackendStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend request failed");
        }
        return response.json();
      })
      .then((data) => {
        setBackend(data);
      })
      .catch(() => {
        setError("Backend is not reachable");
      });
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 p-10 shadow-2xl">
        <div className="mb-8">
          <p className="text-sm font-medium text-blue-400">
            AI MANUFACTURING INSPECTION
          </p>

          <h1 className="mt-2 text-4xl font-bold">
            VisionInspect AI
          </h1>

          <p className="mt-3 text-slate-400">
            Manufacturing Defect Detection & Quality Inspection System
          </p>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-950 p-6">
          <h2 className="text-xl font-semibold">
            Backend Status
          </h2>

          {backend ? (
            <div className="mt-4">
              <p className="text-green-400 text-lg">
                🟢 Connected
              </p>

              <p className="mt-2 text-slate-400">
                Service:{" "}
                <span className="text-white">
                  {backend.service}
                </span>
              </p>

              <p className="mt-1 text-slate-400">
                Status:{" "}
                <span className="text-green-400">
                  {backend.status}
                </span>
              </p>
            </div>
          ) : error ? (
            <p className="mt-4 text-red-400">
              🔴 {error}
            </p>
          ) : (
            <p className="mt-4 text-yellow-400">
              🟡 Connecting to backend...
            </p>
          )}
        </div>
      </div>
    </main>
  );
}