'use client'
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Logout() {

    const router = useRouter();

    const redirect = () => {
        localStorage.clear();
        router.push("/")
    }

    useEffect(() => {
        redirect();
    }, [])
    
    return (
        <div>
            Logging out...
        </div>
    )
}