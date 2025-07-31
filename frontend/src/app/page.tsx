"use client";

import { useRouter } from "next/navigation";
import React, { useRef, useEffect, useState } from "react";
import mapboxgl, { Map } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { Button } from "@/components/ui/button";
import clsx from "clsx";
import { Slider } from "@/components/ui/slider";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Github } from "lucide-react";

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;

type Report = {
  report_id: number;
  country_lat: number;
  country_long: number;
  primary_country: string;
  primary_country_shortname: string;
  headline_title: string;
  headline_summary: string;
  source_name: string;
  source_homepage: string;
  report_url_alias: string;
  date_report_created: Date;
};

type GroupedEvent = {
  lat: number;
  long: number;
  reports: Report[];
};

function createReportClickHandler(
  cutoff: Date,
  setSelectedReports: (reports: Report[]) => void
) {
  return (e: mapboxgl.MapMouseEvent) => {
    const feature = e.features?.[0];
    if (feature && feature.properties?.reports) {
      const rawReports: Report[] = JSON.parse(feature.properties.reports);

      const filteredReports = rawReports.filter((report) => {
        const reportDate = new Date(report.date_report_created);
        return reportDate >= cutoff;
      });

      setSelectedReports(filteredReports);
    }
  };
}

export default function Home() {
  const router = useRouter();
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const [LoggedIn, setLoggedIn] = useState(false);
  const [selectedReports, setSelectedReports] = useState<Report[] | null>(null);
  const [allReports, setAllReports] = useState<GroupedEvent[] | null>(null);
  const [lastUpdated, setLastUpdated] = useState("");
  const [daysAgo, setDaysAgo] = useState(14);
  const [openCards, setOpenCards] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(false);

  const FASTAPI_BACKEND = process.env.NEXT_PUBLIC_FASTAPI_BACKEND;

  const toggleCard = (id: number) => {
    const newSet = new Set(openCards);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setOpenCards(newSet);
  };

  const mapRef = useRef<Map | null>(null);

  const login_url = `https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=${process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}&redirect_uri=${process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline`;
  const handleLogin = () => {
    localStorage.clear();
    router.push(login_url);
  };

  const validateToken = async (t: string | null) => {
    if (!t) return false;
    try {
      const res = await fetch(`${FASTAPI_BACKEND}/validate-token`, {
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

  const getLastUpdatedTime = async () => {
    const res = await fetch(`${FASTAPI_BACKEND}/last-updated`);
    return await res.json();
  };

  const grabInitialEvents = async (): Promise<GroupedEvent[]> => {
    const res = await fetch(`${FASTAPI_BACKEND}/grab-initial-events`);
    const data = await res.json();

    data.forEach((group: GroupedEvent) => {
      group.reports.forEach((report: Report) => {
        report.date_report_created = new Date(report.date_report_created);
      });
    });

    setAllReports(data);
    return data;
  };

  const handleLogout = () => {
    localStorage.clear();
    setLoggedIn(false);
    router.push("/");
  };

  const checkLoginStatus = async (token: string | null) => {
    const isValid = await validateToken(token);
    setLoggedIn(isValid);
    if (!isValid) handleLogout();
  };

  type MapWithHandler = mapboxgl.Map & {
    _reportClickHandler?: (e: mapboxgl.MapMouseEvent) => void;
  };

  const handleSliderChange = (value: number) => {
    setDaysAgo(value);

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - value);

    const filtered: GroupedEvent[] = [];

    allReports?.forEach((group) => {
      const reports = group.reports.filter(
        (report) => new Date(report.date_report_created) >= cutoff
      );
      if (reports.length > 0) {
        filtered.push({ lat: group.lat, long: group.long, reports });
      }
    });

    const updatedGeoJSON = {
      type: "FeatureCollection" as const,
      features: filtered.map((group) => ({
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

    const map = mapRef.current as MapWithHandler;
    if (map && map.isStyleLoaded()) {
      const source = map.getSource("report-clusters") as mapboxgl.GeoJSONSource;
      source.setData(updatedGeoJSON);

      if (map._reportClickHandler) {
        map.off("click", "report-circles", map._reportClickHandler);
      }

      const handleReportClick = (e: mapboxgl.MapMouseEvent) => {
        const feature = e.features?.[0];
        if (feature && feature.properties?.reports) {
          const rawReports: Report[] = JSON.parse(feature.properties.reports);

          const filteredReports = rawReports.filter((report) => {
            const reportDate = new Date(report.date_report_created);
            return reportDate >= cutoff;
          });

          setSelectedReports(filteredReports);
        }
      };
      map._reportClickHandler = handleReportClick;
      map.on("click", "report-circles", handleReportClick);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("jwt");
    checkLoginStatus(token);

    if (!mapContainerRef.current) return;

    (async () => {
      const groupedEvents = await grabInitialEvents();
      handleSliderChange(daysAgo);
      const updateTime = await getLastUpdatedTime();
      setLastUpdated(updateTime);

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

      const map = new mapboxgl.Map({
        container: mapContainerRef.current!,
        style: "mapbox://styles/mapbox/dark-v11",
        center: [-74.5, 40],
        zoom: 3,
        scrollZoom: true,
      });
      map.scrollZoom.enable({ around: "center" });

      mapRef.current = map;

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
            "circle-color": [
              "interpolate",
              ["linear"],
              ["get", "intensity"],
              1,
              "#68D391",
              5,
              "#F6E05E",
              10,
              "#F56565",
            ],

            "circle-blur": 0.3,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-opacity": 0.35,
            "circle-stroke-width": 0.75,
          },
        });

        const initialCutoff = new Date();
        initialCutoff.setDate(initialCutoff.getDate() - daysAgo);

        const reportClickHandler = createReportClickHandler(
          initialCutoff,
          setSelectedReports
        );
        (map as MapWithHandler)._reportClickHandler = reportClickHandler;
        map.on("click", "report-circles", reportClickHandler);

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
        map.scrollZoom.enable({ around: "center" });

        map.addSource("llm-highlights", {
          type: "geojson",
          data: {
            type: "FeatureCollection",
            features: [],
          },
        });

        map.addLayer({
          id: "llm-highlight-layer",
          type: "circle",
          source: "llm-highlights",
          paint: {
            "circle-radius": 10,
            "circle-color": "#FF7F50",
            "circle-opacity": 0.7,
            "circle-stroke-width": 2,
            "circle-stroke-color": "#fff",
          },
        });
      });
    })();

    return () => {
      const map = mapRef.current as MapWithHandler;
      if (map && map._reportClickHandler) {
        map.off("click", "report-circles", map._reportClickHandler);
      }
      if (mapRef.current) {
        mapRef.current.remove();
      }
    };
  }, [router]);

  return (
    <div className="relative h-screen w-screen overflow-hidden">
      <div
        ref={mapContainerRef}
        className="fixed inset-0 z-0"
        style={{ height: "100vh", width: "100vw" }}
      />
      <div className="absolute top-4 left-4 z-50 bg-gradient-to-r from-slate-800 to-slate-900 border border-white/20 text-sm text-neutral-300 px-4 py-2 rounded-xl shadow-lg backdrop-blur-md">
        {lastUpdated ? (
          <p>
            <span className="text-white font-semibold">Last updated:</span>{" "}
            {lastUpdated}
          </p>
        ) : (
          <motion.div
            initial={{ opacity: 0.4 }}
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
            className="mt-3 text-center text-sm text-white/80"
          >
            Loading...
          </motion.div>
        )}
      </div>
      <div className="absolute top-4 right-4 z-50 flex gap-2 items-center">
        <a
          href="https://github.com/akashm6/geosynth"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button
            variant="ghost"
            className="border border-white/20 text-white hover:text-sky-300 transition cursor-pointer hover:shadow-[0_0_10px_1px_rgba(0,212,255,0.4)]"
          >
            <Github className="w-4 h-4 mr-2" />
            GitHub
          </Button>
        </a>

        {LoggedIn ? (
          <Button
            onClick={handleLogout}
            className="bg-gradient-to-r from-slate-800 to-slate-900 border border-white/20 text-white text-sm px-4 py-2 rounded-xl shadow-lg backdrop-blur-md transition hover:ring-1 hover:ring-red-300/30 hover:scale-[1.02] cursor-pointer"
          >
            Logout
          </Button>
        ) : (
          <Button
            onClick={handleLogin}
            className="bg-gradient-to-r from-slate-800 to-slate-900 border border-white/20 text-white text-sm px-4 py-2 rounded-xl shadow-lg backdrop-blur-md transition hover:ring-1 hover:ring-sky-300/30 hover:scale-[1.02] cursor-pointer"
          >
            Login with Google
          </Button>
        )}
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.35 }}
        className="absolute top-20 left-4 z-50 w-[260px] bg-gradient-to-r from-slate-800 to-slate-900 border border-white/20 text-sm text-neutral-300 px-4 py-3 rounded-xl shadow-lg backdrop-blur-md"
      >
        <div className="mb-3">
          <p className="text-white text-sm font-semibold">Filter by recency</p>
          <p className="text-xs text-gray-400">
            Showing reports from last{" "}
            <span className="text-blue-300">
              {daysAgo} day{daysAgo > 1 && "s"}
            </span>
          </p>
        </div>

        <Slider
          min={1}
          max={21}
          step={1}
          value={[daysAgo]}
          onValueChange={([val]) => handleSliderChange(val)}
          className="w-full"
        />
        <div className="mt-3 space-y-1 text-xs text-gray-400">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-[#68D391] hover:scale-105" />
            <span>Low event intensity</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-[#F6E05E] hover:scale-105" />
            <span>Moderate event intensity</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-[#F56565] hover:scale-105" />
            <span>High event intensity</span>
          </div>
        </div>
      </motion.div>
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
        <ul className="space-y-3">
          {selectedReports?.map((report) => {
            const isOpen = openCards.has(report.report_id);
            return (
              <li
                key={report.report_id || report.primary_country}
                className="bg-white/10 rounded-md p-3 shadow hover:shadow-lg transition duration-200"
              >
                <div
                  className="flex justify-between items-center cursor-pointer"
                  onClick={() => toggleCard(report.report_id)}
                >
                  <div className="flex flex-col">
                    <h3 className="font-semibold text-base">
                      {report.headline_title}
                    </h3>
                    <h4 className="text-gray-400 text-xs pt-1">
                      {report.primary_country}
                    </h4>
                    <h5 className="text-xs text-gray-400 mt-1">
                      {new Date(report.date_report_created).toLocaleDateString(
                        undefined,
                        {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        }
                      )}
                    </h5>
                  </div>{" "}
                  <span className="text-xs text-blue-300">
                    {isOpen ? "Hide" : "More"}
                  </span>
                </div>

                {isOpen && (
                  <div className="mt-2 text-sm text-white/90 space-y-1">
                    {report.report_url_alias && (
                      <a
                        href={report.report_url_alias}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:underline text-sm"
                      >
                        Read Full Report →
                      </a>
                    )}
                    {report.headline_summary && (
                      <p className="text-xs text-gray-300 mt-1 line-clamp-3">
                        {report.headline_summary}
                      </p>
                    )}

                    <p className="italic text-gray-500 text-xs">
                      Source: {report.source_name}
                    </p>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </div>
      <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-50 w-[40rem] max-w-[90vw]">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            const input = (
              e.currentTarget.elements.namedItem("query") as HTMLInputElement
            ).value;
            if (!input) return;

            try {
              setIsLoading(true);
              const res = await fetch(`${FASTAPI_BACKEND}/llm-response`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_input: input, loggedIn: LoggedIn }),
              });

              const data = await res.json();
              if (data.detail) {
                toast.error(data.detail, {
                  description: "Log in or try again later.",
                  action: {
                    label: "Okay",
                    onClick: () => console.log("User acknowledged limit."),
                  },
                });
                return;
              }

              const rows = data.prompt_results || [];
              if (rows.length === 0) {
                setSelectedReports([
                  {
                    report_id: -1,
                    country_lat: 0,
                    country_long: 0,
                    primary_country: "",
                    primary_country_shortname: "",
                    headline_title: `No reports were found for your query. Slow news day!`,
                    headline_summary: "No reports available for this query.",
                    source_name: "",
                    source_homepage: "",
                    report_url_alias: "",
                    date_report_created: new Date(),
                  },
                ]);
              } else if (rows[0].event_count) {
                setSelectedReports([
                  {
                    report_id: -1,
                    country_lat: 0,
                    country_long: 0,
                    primary_country: "",
                    primary_country_shortname: "",
                    headline_title: `Total events: ${rows[0].event_count}`,
                    headline_summary:
                      "Summary data only — no individual reports returned.",
                    source_name: "",
                    source_homepage: "",
                    date_report_created: new Date(),
                    report_url_alias: "#",
                  },
                ]);
              } else {
                setSelectedReports(rows);
              }

              const validFeatures = rows
                .filter(
                  (row: Report) =>
                    typeof row.country_lat === "number" &&
                    typeof row.country_long === "number" &&
                    !isNaN(row.country_lat) &&
                    !isNaN(row.country_long)
                )
                .map((row: Report) => ({
                  type: "Feature",
                  geometry: {
                    type: "Point",
                    coordinates: [row.country_long, row.country_lat],
                  },
                  properties: { ...row },
                }));

              const map = mapRef.current;
              if (map && map.isStyleLoaded()) {
                const source = map.getSource(
                  "llm-highlights"
                ) as mapboxgl.GeoJSONSource;
                source.setData({
                  type: "FeatureCollection",
                  features: validFeatures,
                });
                setIsLoading(false);
                const bounds = new mapboxgl.LngLatBounds();
                validFeatures.forEach((f: GeoJSON.Feature<GeoJSON.Point>) => {
                  bounds.extend(f.geometry.coordinates as [number, number]);
                });
                if (!bounds.isEmpty()) {
                  map.fitBounds(bounds, {
                    padding: 100,
                    maxZoom: 5,
                  });
                  map.scrollZoom.enable({ around: "center" });
                }
              } else {
                setIsLoading(false);
                console.warn("Map not loaded or no valid coordinates found.");
              }
            } catch (err) {
              setIsLoading(false);
              console.error("Failed to fetch:", err);
            }
          }}
          className="flex bg-black/60 border border-white/20 rounded-xl shadow-xl backdrop-blur-md"
        >
          <input
            name="query"
            type="text"
            placeholder="Ask GeoSynth (e.g. disasters in Asia last week)"
            className="flex-1 px-4 py-2 bg-transparent text-white placeholder-gray-400 focus:outline-none"
          />
          <button
            type="submit"
            className="bg-gradient-to-r from-slate-800 to-slate-900 border border-white/20 text-white text-sm px-4 py-2 rounded-xl shadow-lg  transition hover:ring-1 hover:ring-sky-300/30 hover:scale-[1.02] cursor-pointer"
          >
            Search
          </button>
        </form>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0.4 }}
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
            className="mt-3 text-center text-sm text-white/80"
          >
            Answering question...
          </motion.div>
        )}
      </div>
    </div>
  );
}
