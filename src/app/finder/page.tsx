"use client"

import { useState } from "react"

export default function FinderPage() {
  const [username, setUsername] = useState("")
  const [results, setResults] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    // Simulate search
    setTimeout(() => {
      setResults({
        premium: true,
        uuid: "8a2a1bcd-1234-5678-abcd-1234567890ab",
        databases: [
          {
            source: "Database 1",
            email: "user@example.com",
            password: "hashedpassword123"
          }
        ]
      })
      setLoading(false)
    }, 1500)
  }

  return (
    <div className="min-h-screen bg-black p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-red-500 text-center mb-8">
          Gang Empire Finder
        </h1>

        <div className="bg-black/50 backdrop-blur-sm p-6 rounded-lg border border-red-900/50 shadow-2xl shadow-red-500/20 mb-8">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="Enter username to search..."
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="flex-1 px-4 py-3 rounded-md bg-black/50 border border-red-900/50 text-red-500 placeholder:text-red-700/50 focus:outline-none focus:ring-2 focus:ring-red-500/50"
                required
              />
              <button
                type="submit"
                className="px-8 py-3 bg-gradient-to-br from-red-900/80 to-red-800/80 hover:from-red-800/80 hover:to-red-700/80 text-red-500 rounded-md font-medium transition-all duration-200 hover:shadow-lg hover:shadow-red-500/20"
                disabled={loading}
              >
                {loading ? "Searching..." : "Search"}
              </button>
            </div>

            <div className="flex gap-4 text-red-700/70 text-sm">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded border-red-900/50 bg-black/50" defaultChecked />
                <span>Check Premium Status</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded border-red-900/50 bg-black/50" defaultChecked />
                <span>Crack Passwords</span>
              </label>
            </div>
          </form>
        </div>

        {loading && (
          <div className="text-center text-red-500 animate-pulse">
            Searching for information...
          </div>
        )}

        {results && !loading && (
          <div className="space-y-6">
            <div className="bg-black/50 backdrop-blur-sm p-6 rounded-lg border border-red-900/50 shadow-xl">
              <h2 className="text-2xl font-bold text-red-500 mb-4">Premium Status</h2>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-sm ${results.premium ? "bg-green-900/50 text-green-500" : "bg-red-900/50 text-red-500"}`}>
                    {results.premium ? "PREMIUM" : "NOT PREMIUM"}
                  </span>
                </div>
                {results.uuid && (
                  <p className="text-red-500">
                    <span className="text-red-700">UUID:</span> {results.uuid}
                  </p>
                )}
              </div>
            </div>

            {results.databases?.map((db: any, i: number) => (
              <div key={i} className="bg-black/50 backdrop-blur-sm p-6 rounded-lg border border-red-900/50 shadow-xl">
                <h3 className="text-xl font-bold text-red-500 mb-4">
                  Database Result #{i + 1}
                </h3>
                <div className="space-y-2">
                  <p className="text-red-500">
                    <span className="text-red-700">Source:</span> {db.source}
                  </p>
                  <p className="text-red-500">
                    <span className="text-red-700">Email:</span> {db.email}
                  </p>
                  <p className="text-red-500">
                    <span className="text-red-700">Password Hash:</span> {db.password}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 text-center">
          <p className="text-red-700/70 text-sm">
            🔥 EL MEJOR FINDER DE MINECRAFT DEL MUNDO 🔥
          </p>
        </div>
      </div>
    </div>
  )
}
