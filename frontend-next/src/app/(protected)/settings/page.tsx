"use client";
import { useState, useEffect } from "react";
import Navbar from "@/components/layout/Navbar";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { authApi } from "@/lib/api";
import { getUser, saveAuth, getToken } from "@/lib/auth";

export default function SettingsPage() {
  const [user, setUser] = useState(getUser());
  const [name, setName] = useState(user?.name ?? "");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [profileMsg, setProfileMsg] = useState("");
  const [profileErr, setProfileErr] = useState("");
  const [profileLoading, setProfileLoading] = useState(false);

  useEffect(() => {
    authApi.me().then(setUser).catch(() => {});
  }, []);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setProfileMsg("");
    setProfileErr("");
    if (password && password !== confirm) { setProfileErr("Passwords do not match"); return; }
    if (password && password.length < 6) { setProfileErr("Password must be at least 6 characters"); return; }
    setProfileLoading(true);
    try {
      const updated = await authApi.updateProfile({ name: name || undefined, password: password || undefined });
      const token = getToken()!;
      saveAuth(token, updated);
      setUser(updated);
      setPassword("");
      setConfirm("");
      setProfileMsg("Profile updated successfully");
    } catch (e: unknown) {
      setProfileErr(e instanceof Error ? e.message : "Update failed");
    } finally {
      setProfileLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          <div>
            <h1 className="text-xl font-bold text-white">Settings</h1>
            <p className="text-sm text-gray-500 mt-1">Manage your account and preferences</p>
          </div>

          {/* Profile */}
          <Card className="p-6">
            <h2 className="text-sm font-semibold text-white mb-5">Profile</h2>
            <form onSubmit={saveProfile} className="space-y-4">
              <Input label="Email" type="email" value={user?.email ?? ""} disabled className="opacity-50 cursor-not-allowed" />
              <Input
                label="Full Name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
              />
              <Input
                label="New Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Leave blank to keep current"
              />
              {password && (
                <Input
                  label="Confirm New Password"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Repeat new password"
                />
              )}
              {profileErr && <p className="text-xs text-red-400">{profileErr}</p>}
              {profileMsg && <p className="text-xs text-nexus-green">{profileMsg}</p>}
              <Button type="submit" loading={profileLoading}>Save Changes</Button>
            </form>
          </Card>

          {/* System Info */}
          <Card className="p-6">
            <h2 className="text-sm font-semibold text-white mb-4">System</h2>
            <div className="space-y-2 text-sm font-mono text-gray-400">
              {[
                ["Version", "NEXUS 2.0"],
                ["Challenge", "Challenge 1 — Autonomous Content-to-Action Agent"],
                ["Agents", "Orion · Raven · Cipher · Resolver · Executor"],
                ["Model", "Gemini 2.0 Flash"],
                ["Integrations", "Gmail SMTP · Google Sheets · Slack Webhook"],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-3">
                  <span className="w-28 text-gray-600 shrink-0">{k}</span>
                  <span className="text-gray-300">{v}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* API Info */}
          <Card className="p-6">
            <h2 className="text-sm font-semibold text-white mb-4">API Endpoints</h2>
            <div className="space-y-1.5 text-xs font-mono">
              {[
                ["POST", "/auth/register", "Create account"],
                ["POST", "/auth/login", "Sign in"],
                ["POST", "/ingest", "Ingest sources"],
                ["POST", "/analyze", "Run 5-agent consensus"],
                ["POST", "/execute", "Execute action chain"],
                ["POST", "/what-if", "Counterfactual analysis"],
                ["GET", "/export-trace", "Download Antigravity trace"],
                ["GET", "/history", "Your analysis history"],
              ].map(([method, path, desc]) => (
                <div key={path} className="flex items-center gap-3">
                  <span className={`w-10 text-[10px] font-bold ${method === "POST" ? "text-nexus-cyan" : "text-nexus-green"}`}>
                    {method}
                  </span>
                  <span className="text-gray-300 w-36">{path}</span>
                  <span className="text-gray-600">{desc}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
