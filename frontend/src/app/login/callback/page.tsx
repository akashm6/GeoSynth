"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) return;

    const authenticateUser = async () => {
      try {
        const res = await fetch(`http://localhost:8000/auth/google/redirect?code=${code}`);
        const data = await res.json();
        console.log(data)

        if (data.token) {
          localStorage.setItem("jwt", data.token);
          localStorage.setItem("user", JSON.stringify(data.user_data));
          router.push("/"); 
        } else {
          router.push("/login?error=auth_failed");
        }
      } catch (err) {
        console.error("Auth error:", err);
        router.push("/login?error=auth_exception");
      }
    };

    authenticateUser();
  }, [searchParams, router]);

  return <div>Logging in...</div>;
}
