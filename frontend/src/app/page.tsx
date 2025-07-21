"use client";

import { useRouter } from "next/navigation";
import React, { useRef, useEffect, useState } from "react";
import mapboxgl, { Map } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { Button } from "@/components/ui/button";
import clsx from "clsx";

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

type Report = {
  report_id: number;
  country_lat: number;
  country_long: number;
  primary_country: string;
  headline_title: string;
  headline_summary: string;
  source_name: string;
  source_homepage: string;
  report_url_alias: string;
};

type GroupedEvent = {
  lat: number;
  long: number;
  reports: Report[];
};

export default function Home() {
  const router = useRouter();
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const [LoggedIn, setLoggedIn] = useState(false);
  const [selectedReports, setSelectedReports] = useState<Report[] | null>(null);

  const validateToken = async (t: string | null) => {
    if (!t) return false;
    try {
      const res = await fetch(`http://localhost:8000/validate-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: t }),
      });
      return await res.json();
    } catch (error) {
      console.error(error);
      return false;
    }
  };

  const grabInitialEvents = async (): Promise<GroupedEvent[]> => {
    const res = await fetch("http://localhost:8000/grab-initial-events");
    return await res.json();
  };

  const handleLogout = () => {
    localStorage.clear();
    setLoggedIn(false);
    router.push("/");
  };

  const handleLogin = () => {
    localStorage.clear();
    router.push("/login");
  };

  const checkLoginStatus = async (token: string | null) => {
    const isValid = await validateToken(token);
    setLoggedIn(isValid);
    if (!isValid) handleLogout();
  };

  useEffect(() => {
    const token = localStorage.getItem("jwt");
    checkLoginStatus(token);

    if (!mapContainerRef.current) return;

    let map: Map;

    (async () => {
      const groupedEvents = await grabInitialEvents();

      const geojson = {
        type: "FeatureCollection" as const,
        features: groupedEvents.map((group) => ({
          type: "Feature" as const,
          geometry: {
            type: "Point" as const,
            coordinates: [group.long, group.lat],
          },
          properties: {
            reports: JSON.stringify(group.reports),
            intensity: group.reports.length,
          },
        })),
      };

      map = new mapboxgl.Map({
        container: mapContainerRef.current!,
        style: "mapbox://styles/mapbox/dark-v11",
        center: [-74.5, 40],
        zoom: 3,
      });

      map.on("load", () => {
        map.addSource("report-clusters", {
          type: "geojson",
          data: geojson,
        });

        map.addLayer({
          id: "report-circles",
          type: "circle",
          source: "report-clusters",
          paint: {
            "circle-radius": [
              "interpolate",
              ["linear"],
              ["get", "intensity"],
              1,
              6,
              10,
              18,
            ],
            "circle-color": "rgba(0,200,255,0.6)",
            "circle-blur": 0.4,
          },
        });

        map.on("click", "report-circles", (e) => {
          const feature = e.features?.[0];
          if (feature && feature.properties?.reports) {
            const reports = JSON.parse(feature.properties.reports);
            setSelectedReports(reports);
          }
        });

        map.on("mouseenter", "report-circles", () => {
          map.getCanvas().style.cursor = "pointer";
        });

        map.on("mouseleave", "report-circles", () => {
          map.getCanvas().style.cursor = "";
        });

        const bounds = new mapboxgl.LngLatBounds();
        geojson.features.forEach((f) => {
          bounds.extend(f.geometry.coordinates as [number, number]);
        });
        map.fitBounds(bounds, { padding: 50 });
      });
    })();

    return () => {
      if (map) map.remove();
    };
  }, [router]);

  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <div ref={mapContainerRef} className="fixed inset-0 z-0" style={{height: "100vh", width: "100vw"}} />

      <h1 className="absolute top-4 left-4 text-white text-2xl font-semibold z-50 drop-shadow-[0_0_6px_rgba(255,255,255,0.7)]">
        Atlascope
      </h1>

      <div className="absolute top-4 right-4 z-50">
        {LoggedIn ? (
          <Button
            onClick={handleLogout}
            className="bg-black/40 text-white border border-white/30 backdrop-blur-md shadow-md hover:shadow-[0_0_12px_4px_rgba(255,77,77,0.6)] transition"
          >
            Logout
          </Button>
        ) : (
          <Button
            onClick={handleLogin}
            className="bg-black/40 text-white border border-white/30 backdrop-blur-md shadow-md hover:shadow-[0_0_12px_4px_rgba(80,180,255,0.6)] transition"
          >
            Login
          </Button>
        )}
      </div>

      <div
        className={clsx(
          "fixed top-0 right-0 h-full w-[28rem] max-w-full bg-black/90 text-white p-6 overflow-y-auto z-[100] transform transition-transform duration-300 ease-in-out shadow-lg",
          selectedReports ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Reports</h2>
          <button
            onClick={() => setSelectedReports(null)}
            className="text-sm text-blue-400 hover:underline"
          >
            Close
          </button>
        </div>
        <ul className="space-y-6">
          {selectedReports?.map((report) => (
            <li key={report.report_id} className="border-b border-white/20 pb-4">
              <h3 className="font-semibold text-lg mb-1">{report.headline_title}</h3>
              <p className="text-sm mb-1">{report.headline_summary}</p>
              <p className="text-xs italic text-gray-400 mb-1">{report.source_name}</p>
              <a
                href={report.report_url_alias}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-300 text-sm hover:underline"
              >
                Read full report
              </a>
            </li>
          ))}
        </ul>
      </div>
      {LoggedIn && (
  <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-50 w-[40rem] max-w-[90vw]">
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        const input = (e.currentTarget.elements.namedItem("query") as HTMLInputElement).value;
        if (!input) return;

        try {
          const res = await fetch("http://localhost:8000/llm-response", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ user_input: input }),
          });
          const data = await res.json();
          console.log("LLM Result:", data);

          setSelectedReports(data.prompt_results);
        } catch (err) {
          console.error("Failed to fetch:", err);
        }
      }}
      className="flex bg-black/60 border border-white/20 rounded-xl shadow-xl backdrop-blur-md"
    >
      <input
        name="query"
        type="text"
        placeholder="Ask Atlascope (e.g. disasters in Asia last month)"
        className="flex-1 px-4 py-2 bg-transparent text-white placeholder-gray-400 focus:outline-none"
      />
      <button
        type="submit"
        className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-r-xl"
      >
        Search
      </button>
    </form>
  </div>
)}

    </div>
  );
}
