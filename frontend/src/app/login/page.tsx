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

    const loginSchema = z.object({
        email: z.string().email({message: "Invalid email address."}),
        password: z.string().min(6, {message: "Password must be at least 6 characters."})
    })

    const [submitMessage, setSubmitMessage] = useState('');
    
    const handleSubmit = async () => {
        try {
            const res = await fetch("http://localhost:8000/confirmLogin", {
                method: "POST",
                
            })
            if (res.ok) {
                const data = await res.json();
                setSubmitMessage(data.message)
                
            }

        }

        catch (err) {
            console.error(err)

        }


    }

}