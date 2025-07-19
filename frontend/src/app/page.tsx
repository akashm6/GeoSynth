"use client";

import { useRouter } from "next/navigation";
import React, { useRef, useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css"; 
import { Button } from "@/components/ui/button";

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!;


export default function Home() {

  const router = useRouter();

  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  const [LoggedIn, setLoggedIn] = useState(false)

  const validateToken = async (t: string | null) => {
    
    if(!t) {
      return false;
    }
    const payload = {
      token: t
    }

    try {

      const res = await fetch(`http://localhost:8000/validate-token`, {
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify(payload),
      });

      const tokenValid = await res.json();

      return tokenValid
    }

    catch (error) {
      console.error(error);
      return false;
    }
  }

  const handleLogout = () => {
    localStorage.clear();
    setLoggedIn(false)
    router.push("/");
  }

  const handleLogin = () => {
    localStorage.clear();
    router.push("/login");
    
  }

  const checkLoginStatus = async (token: string | null) => {
      const isValid = await validateToken(token);
      if(isValid) {
        setLoggedIn(true)
      }
      else {
        handleLogout();
      }
    }

  useEffect(() => {

    const token = localStorage.getItem("jwt")
    checkLoginStatus(token);

    if (!mapContainerRef.current) return;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [-74.5, 40],
      zoom: 9,
    });

    return () => map.remove();
  }, [router]);

  return (
    <div style={{ height: "100vh", width: "100%" }}>
      <h1 style={{ position: "absolute", zIndex: 1, color: "white", padding: "1rem" }}>
        Home Page!
      </h1>
        {LoggedIn && (
          <div style={{ position: "absolute", zIndex: 1, color: "white", top: "1rem", right: "1rem" }}>
          <Button style = {{ cursor: "pointer" }} onClick={handleLogout}>Logout</Button>
          </div>
        )}

        {!LoggedIn && (
          <div style={{ position: "absolute", zIndex: 1, color: "white", top: "1rem", right: "1rem" }}>
          <Button style = {{ cursor: "pointer" }} onClick={handleLogin}>Login</Button>
          </div>
        )}
      
      <div ref={mapContainerRef} style={{ height: "100%", width: "100%" }} />
    </div>
  );
}
