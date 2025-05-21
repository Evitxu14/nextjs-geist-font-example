"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // For demo, hardcode credentials
    if (username === "admin" && password === "admin") {
      router.push("/finder")
    } else {
      alert("Invalid credentials")
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-black/50 backdrop-blur-sm p-8 rounded-lg border border-red-900/50 shadow-2xl shadow-red-500/20">
          <h1 className="text-4xl font-bold text-red-500 text-center mb-8">
            Gang Empire Finder
          </h1>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-md bg-black/50 border border-red-900/50 text-red-500 placeholder:text-red-700/50 focus:outline-none focus:ring-2 focus:ring-red-500/50"
                required
              />
            </div>
            
            <div>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-md bg-black/50 border border-red-900/50 text-red-500 placeholder:text-red-700/50 focus:outline-none focus:ring-2 focus:ring-red-500/50"
                required
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 px-4 bg-gradient-to-br from-red-900/80 to-red-800/80 hover:from-red-800/80 hover:to-red-700/80 text-red-500 rounded-md font-medium transition-all duration-200 hover:shadow-lg hover:shadow-red-500/20"
            >
              Login
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-red-700/70 text-sm">
              🔥 EL MEJOR FINDER DE MINECRAFT DEL MUNDO 🔥
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
