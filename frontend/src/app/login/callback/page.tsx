"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {motion} from 'framer-motion';

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const FASTAPI_BACKEND = process.env.NEXT_PUBLIC_FASTAPI_BACKEND;

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) return;

    const authenticateUser = async () => {
      try {
        const res = await fetch(`${FASTAPI_BACKEND}/auth/google/redirect?code=${code}`);
        const data = await res.json();

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
  }, [searchParams, router, FASTAPI_BACKEND]);

  return (
  
  <motion.div
      initial={{ opacity: 0.4 }}
      animate={{ opacity: [0.4, 1, 0.4] }}
      transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
      className="mt-3 text-center text-sm text-white/80"
    >
      Logging in...
    </motion.div>
  )

}
