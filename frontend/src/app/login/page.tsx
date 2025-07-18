"use client"
import React from "react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import {useForm} from "react-hook-form"
import {z} from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function Login() {

    const router = useRouter();

    const login_url = `https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=${process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}&redirect_uri=${process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline`
    const handleClick = () => {
        router.push(login_url)
    };

    return (

        <div>
            <Button onClick={handleClick}>Login with Google</Button>
        </div>

    );
}
